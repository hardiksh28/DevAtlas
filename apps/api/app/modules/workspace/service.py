"""Interactive Learning Workspace — service layer. Function-based, `db`
first arg — same convention as every other module.
"""

import hashlib
import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.modules.workspace.exceptions import (
    ContentConflictError,
    FileLimitExceededError,
    FileTooLargeError,
    PathAlreadyExistsError,
    WorkspaceFileNotFoundError,
)
from app.modules.workspace.models import WorkspaceFile, WorkspaceLayout

settings = get_settings()


def _hash_content(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def _check_size(content: str) -> int:
    size_bytes = len(content.encode("utf-8"))
    if size_bytes > settings.workspace_file_max_bytes:
        raise FileTooLargeError(settings.workspace_file_max_bytes)
    return size_bytes


async def list_tree(db: AsyncSession, project_id: uuid.UUID) -> list[WorkspaceFile]:
    result = await db.execute(
        select(WorkspaceFile)
        .where(WorkspaceFile.project_id == project_id)
        .order_by(WorkspaceFile.path)
    )
    return list(result.scalars().all())


async def get_file(db: AsyncSession, project_id: uuid.UUID, file_id: uuid.UUID) -> WorkspaceFile:
    result = await db.execute(
        select(WorkspaceFile).where(
            WorkspaceFile.id == file_id, WorkspaceFile.project_id == project_id
        )
    )
    file = result.scalar_one_or_none()
    if file is None:
        raise WorkspaceFileNotFoundError()
    return file


async def _path_taken(db: AsyncSession, project_id: uuid.UUID, path: str) -> bool:
    existing = await db.scalar(
        select(WorkspaceFile.id).where(
            WorkspaceFile.project_id == project_id, WorkspaceFile.path == path
        )
    )
    return existing is not None


async def create_file(
    db: AsyncSession, project_id: uuid.UUID, path: str, content: str
) -> WorkspaceFile:
    current_count = await db.scalar(
        select(func.count())
        .select_from(WorkspaceFile)
        .where(WorkspaceFile.project_id == project_id)
    )
    if (current_count or 0) >= settings.max_workspace_files_per_project:
        raise FileLimitExceededError(settings.max_workspace_files_per_project)
    if await _path_taken(db, project_id, path):
        raise PathAlreadyExistsError(path)

    size_bytes = _check_size(content)
    file = WorkspaceFile(
        project_id=project_id,
        path=path,
        content=content,
        content_hash=_hash_content(content),
        size_bytes=size_bytes,
    )
    db.add(file)
    await db.commit()
    await db.refresh(file)
    return file


async def update_file_content(
    db: AsyncSession,
    file: WorkspaceFile,
    content: str,
    expected_content_hash: str | None,
) -> WorkspaceFile:
    # Optimistic concurrency: a client that has actually read this file
    # before always has a hash to send. Omitting it is only valid the
    # very first time content is saved after creation, when the file's
    # hash already matches empty-string content anyway.
    if expected_content_hash is not None and expected_content_hash != file.content_hash:
        raise ContentConflictError()

    size_bytes = _check_size(content)
    file.content = content
    file.content_hash = _hash_content(content)
    file.size_bytes = size_bytes
    await db.commit()
    await db.refresh(file)
    return file


async def rename_file(
    db: AsyncSession, project_id: uuid.UUID, file: WorkspaceFile, new_path: str
) -> WorkspaceFile:
    if new_path != file.path and await _path_taken(db, project_id, new_path):
        raise PathAlreadyExistsError(new_path)
    file.path = new_path
    await db.commit()
    await db.refresh(file)
    return file


async def delete_file(db: AsyncSession, project_id: uuid.UUID, file: WorkspaceFile) -> None:
    file_id = file.id
    file_id_str = str(file_id)
    await db.delete(file)
    # `active_tab_id`'s FK declares ON DELETE SET NULL as a DB-level
    # backstop, but that's only enforced when the target dialect has FK
    # enforcement switched on (Postgres always; the SQLite test fallback
    # doesn't by default) — clearing it here explicitly means correctness
    # never depends on that being the case. open_tabs is a plain JSONB
    # array (no FK possible on array elements) and always needed the
    # explicit prune anyway.
    layout_result = await db.execute(
        select(WorkspaceLayout).where(WorkspaceLayout.project_id == project_id)
    )
    layout = layout_result.scalar_one_or_none()
    if layout is not None:
        if file_id_str in layout.open_tabs:
            layout.open_tabs = [tab_id for tab_id in layout.open_tabs if tab_id != file_id_str]
        if layout.active_tab_id == file_id:
            layout.active_tab_id = None
    await db.commit()


async def get_or_create_layout(db: AsyncSession, project_id: uuid.UUID) -> WorkspaceLayout:
    result = await db.execute(
        select(WorkspaceLayout).where(WorkspaceLayout.project_id == project_id)
    )
    layout = result.scalar_one_or_none()
    if layout is None:
        layout = WorkspaceLayout(project_id=project_id)
        db.add(layout)
        await db.commit()
        await db.refresh(layout)
    return layout


async def update_layout(
    db: AsyncSession, layout: WorkspaceLayout, changes: dict
) -> WorkspaceLayout:
    if "open_tabs" in changes and changes["open_tabs"] is not None:
        changes["open_tabs"] = [str(tab_id) for tab_id in changes["open_tabs"]]
    for key, value in changes.items():
        setattr(layout, key, value)
    await db.commit()
    await db.refresh(layout)
    return layout
