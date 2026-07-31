"""Storage interface shared by apps/api (accepts uploads) and
services/ingestion_worker (fetches raw bytes for parsing, persists
fetched GitHub/website content for provenance and reprocessing).

A Protocol, not an ABC — each call site type-hints against this and
constructs its own concrete backend (S3ObjectStorage in every real
deployment, LocalObjectStorage for dev/tests without a bucket). There's
no shared base-class state to own, so a Protocol is the whole contract.
"""

from typing import Protocol


class ObjectStorage(Protocol):
    async def put(self, key: str, data: bytes, content_type: str) -> None:
        """Write `data` at `key`, creating or overwriting it."""
        ...

    async def get(self, key: str) -> bytes:
        """Read the full object at `key`. Raises if it doesn't exist."""
        ...

    async def delete(self, key: str) -> None:
        """Remove the object at `key`. Idempotent — deleting a
        already-missing key is not an error."""
        ...

    async def exists(self, key: str) -> bool: ...
