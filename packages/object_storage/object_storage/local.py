"""Filesystem-backed ObjectStorage — dev/tests without a running
MinIO/S3 endpoint. Mirrors the SQLite-fallback pattern already used for
the database in apps/api/tests/conftest.py: same interface, a cheaper
backend, selected explicitly (OBJECT_STORAGE_BACKEND=local) rather than
ever being a silent production fallback.
"""

import asyncio
from pathlib import Path


class LocalObjectStorage:
    def __init__(self, root: str | Path) -> None:
        self._root = Path(root)
        self._root.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        # Keys are always API/worker-generated (project/job/document
        # UUIDs joined with "/"), never raw user input — but normalize
        # defensively so a malformed key can't escape `root` via `..`.
        safe_parts = [part for part in key.split("/") if part not in ("", ".", "..")]
        path = self._root.joinpath(*safe_parts)
        path.parent.mkdir(parents=True, exist_ok=True)
        return path

    async def put(self, key: str, data: bytes, content_type: str) -> None:
        # content_type is part of the interface (S3 needs it) but a
        # plain filesystem has no side-channel to store it in; nothing
        # in this codebase reads content_type back from storage — every
        # caller already knows it from the DB row that references `key`.
        await asyncio.to_thread(self._path(key).write_bytes, data)

    async def get(self, key: str) -> bytes:
        return await asyncio.to_thread(self._path(key).read_bytes)

    async def delete(self, key: str) -> None:
        await asyncio.to_thread(self._path(key).unlink, True)  # missing_ok=True

    async def exists(self, key: str) -> bool:
        return await asyncio.to_thread(self._path(key).exists)
