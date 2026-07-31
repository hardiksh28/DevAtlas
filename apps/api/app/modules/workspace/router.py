"""Interactive Learning Workspace — router.

Two routers, mirroring mentoring/curriculum's own split: `router`
(`/v1/workspace`) is an empty stub, reserved the same way
`lessons/router.py` is. `workspace_files_router`
(`/v1/projects/{project_id}/workspace`) is the real, file-tree +
layout-persistence surface built in this pass, nested under its
owning project.

Lesson content and AI chat are deliberately NOT routes here — they're
served by the already-built `curriculum.roadmap_router` and
`mentoring.mentor_router`; the frontend workspace page consumes those
directly rather than this module proxying them.
"""

import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.projects.dependencies import get_owned_project
from app.modules.projects.models import Project
from app.modules.workspace import service
from app.modules.workspace.schemas import (
    WorkspaceFileContentUpdate,
    WorkspaceFileCreate,
    WorkspaceFileDetail,
    WorkspaceFileListResponse,
    WorkspaceFileMeta,
    WorkspaceFileRename,
    WorkspaceLayoutRead,
    WorkspaceLayoutUpdate,
)

router = APIRouter(prefix="/v1/workspace", tags=["Interactive Learning Workspace"])

workspace_files_router = APIRouter(
    prefix="/v1/projects/{project_id}/workspace", tags=["Interactive Learning Workspace"]
)


@workspace_files_router.get("/tree", response_model=WorkspaceFileListResponse)
async def get_tree(
    project: Project = Depends(get_owned_project),
    db: AsyncSession = Depends(get_db),
) -> WorkspaceFileListResponse:
    files = await service.list_tree(db, project.id)
    return WorkspaceFileListResponse(items=[WorkspaceFileMeta.from_model(f) for f in files])


@workspace_files_router.post(
    "/files", response_model=WorkspaceFileDetail, status_code=status.HTTP_201_CREATED
)
async def create_file(
    payload: WorkspaceFileCreate,
    project: Project = Depends(get_owned_project),
    db: AsyncSession = Depends(get_db),
) -> WorkspaceFileDetail:
    file = await service.create_file(db, project.id, payload.path, payload.content)
    return WorkspaceFileDetail.from_model(file)


@workspace_files_router.get("/files/{file_id}", response_model=WorkspaceFileDetail)
async def get_file(
    file_id: uuid.UUID,
    project: Project = Depends(get_owned_project),
    db: AsyncSession = Depends(get_db),
) -> WorkspaceFileDetail:
    file = await service.get_file(db, project.id, file_id)
    return WorkspaceFileDetail.from_model(file)


@workspace_files_router.patch("/files/{file_id}", response_model=WorkspaceFileDetail)
async def update_file_content(
    file_id: uuid.UUID,
    payload: WorkspaceFileContentUpdate,
    project: Project = Depends(get_owned_project),
    db: AsyncSession = Depends(get_db),
) -> WorkspaceFileDetail:
    file = await service.get_file(db, project.id, file_id)
    updated = await service.update_file_content(
        db, file, payload.content, payload.expected_content_hash
    )
    return WorkspaceFileDetail.from_model(updated)


@workspace_files_router.patch("/files/{file_id}/path", response_model=WorkspaceFileDetail)
async def rename_file(
    file_id: uuid.UUID,
    payload: WorkspaceFileRename,
    project: Project = Depends(get_owned_project),
    db: AsyncSession = Depends(get_db),
) -> WorkspaceFileDetail:
    file = await service.get_file(db, project.id, file_id)
    updated = await service.rename_file(db, project.id, file, payload.new_path)
    return WorkspaceFileDetail.from_model(updated)


@workspace_files_router.delete("/files/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_file(
    file_id: uuid.UUID,
    project: Project = Depends(get_owned_project),
    db: AsyncSession = Depends(get_db),
) -> None:
    file = await service.get_file(db, project.id, file_id)
    await service.delete_file(db, project.id, file)


@workspace_files_router.get("/layout", response_model=WorkspaceLayoutRead)
async def get_layout(
    project: Project = Depends(get_owned_project),
    db: AsyncSession = Depends(get_db),
) -> WorkspaceLayoutRead:
    layout = await service.get_or_create_layout(db, project.id)
    return WorkspaceLayoutRead.from_model(layout)


@workspace_files_router.patch("/layout", response_model=WorkspaceLayoutRead)
async def update_layout(
    payload: WorkspaceLayoutUpdate,
    project: Project = Depends(get_owned_project),
    db: AsyncSession = Depends(get_db),
) -> WorkspaceLayoutRead:
    layout = await service.get_or_create_layout(db, project.id)
    changes = payload.model_dump(exclude_unset=True)
    updated = await service.update_layout(db, layout, changes)
    return WorkspaceLayoutRead.from_model(updated)
