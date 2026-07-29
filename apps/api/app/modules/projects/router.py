"""Project Workspace — router.

Thin HTTP layer only: every handler extracts what it needs, calls
exactly one service.py function, and shapes the result into a
schemas.py response via `ProjectRead.from_model` — the same explicit-
adapter pattern `auth.schemas.UserRead.from_model` already established,
used here because `icon`/`color` live on the related `ProjectSettings`
row, not as plain attributes of `Project` itself, so FastAPI's
automatic `from_attributes` conversion can't shape it alone.

Two routers, not one: `router` (`/v1/projects`) owns the resource
itself; `dashboard_router` (`/v1/dashboard`) owns the one aggregate
endpoint that composes across projects for a single page load (see
docs/architecture/project-workspace-v1.md Section 4 for why that
endpoint doesn't just live under /v1/projects too).
"""

import uuid
from typing import Literal

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.models import User
from app.modules.projects import service
from app.modules.projects.dependencies import get_owned_project
from app.modules.projects.models import Project
from app.modules.projects.schemas import (
    DashboardResponse,
    ProjectCreate,
    ProjectListResponse,
    ProjectRead,
    ProjectSettingsRead,
    ProjectSettingsUpdate,
    ProjectUpdate,
    RecentProjectRead,
)

router = APIRouter(prefix="/v1/projects", tags=["Project Workspace"])
dashboard_router = APIRouter(prefix="/v1/dashboard", tags=["Project Workspace"])

_DEFAULT_RECENT_LIMIT = 5


@router.post("", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
async def create_project(
    payload: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProjectRead:
    project = await service.create_project(db, current_user.id, payload.name, payload.description)
    return ProjectRead.from_model(project)


@router.get("", response_model=ProjectListResponse)
async def list_projects(
    project_status: Literal["active", "archived", "deleted"] = Query("active", alias="status"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProjectListResponse:
    items, total = await service.list_projects(db, current_user.id, project_status, limit, offset)
    return ProjectListResponse(
        items=[ProjectRead.from_model(p) for p in items], total=total, limit=limit, offset=offset
    )


# Declared before the `/{project_id}` routes below so "recent" is never
# swallowed by FastAPI trying to parse it as a project_id path param.
@router.get("/recent", response_model=list[RecentProjectRead])
async def recent_projects(
    limit: int = Query(_DEFAULT_RECENT_LIMIT, ge=1, le=20),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[RecentProjectRead]:
    recents = await service.list_recent_projects(db, current_user.id, limit)
    return [
        RecentProjectRead(project=ProjectRead.from_model(r.project), last_viewed_at=r.last_viewed_at)
        for r in recents
    ]


@router.get("/{project_id}", response_model=ProjectRead)
async def get_project(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    project: Project = Depends(get_owned_project),
    db: AsyncSession = Depends(get_db),
) -> ProjectRead:
    await service.record_project_view(db, current_user.id, project_id)
    return ProjectRead.from_model(project)


@router.patch("/{project_id}", response_model=ProjectRead)
async def update_project(
    payload: ProjectUpdate,
    project: Project = Depends(get_owned_project),
    db: AsyncSession = Depends(get_db),
) -> ProjectRead:
    changes = payload.model_dump(exclude_unset=True)
    updated = await service.update_project(db, project, changes)
    return ProjectRead.from_model(updated)


@router.post("/{project_id}/archive", response_model=ProjectRead)
async def archive_project(
    project: Project = Depends(get_owned_project),
    db: AsyncSession = Depends(get_db),
) -> ProjectRead:
    archived = await service.archive_project(db, project)
    return ProjectRead.from_model(archived)


@router.post("/{project_id}/restore", response_model=ProjectRead)
async def restore_project(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProjectRead:
    # Deliberately does not depend on get_owned_project — that
    # dependency excludes soft-deleted projects, which is exactly the
    # state this route needs to reach.
    restored = await service.restore_project(db, project_id, current_user.id)
    return ProjectRead.from_model(restored)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project: Project = Depends(get_owned_project),
    db: AsyncSession = Depends(get_db),
) -> None:
    await service.delete_project(db, project)


@router.get("/{project_id}/settings", response_model=ProjectSettingsRead)
async def get_project_settings(
    project: Project = Depends(get_owned_project),
    db: AsyncSession = Depends(get_db),
) -> ProjectSettingsRead:
    settings = await service.get_project_settings(db, project.id)
    return ProjectSettingsRead.model_validate(settings)


@router.patch("/{project_id}/settings", response_model=ProjectSettingsRead)
async def update_project_settings(
    payload: ProjectSettingsUpdate,
    project: Project = Depends(get_owned_project),
    db: AsyncSession = Depends(get_db),
) -> ProjectSettingsRead:
    settings = await service.get_project_settings(db, project.id)
    changes = payload.model_dump(exclude_unset=True)
    updated = await service.update_project_settings(db, settings, changes)
    return ProjectSettingsRead.model_validate(updated)


@dashboard_router.get("", response_model=DashboardResponse)
async def get_dashboard(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DashboardResponse:
    active_count = await service.count_projects_by_status(db, current_user.id, "active")
    archived_count = await service.count_projects_by_status(db, current_user.id, "archived")
    recents = await service.list_recent_projects(db, current_user.id, _DEFAULT_RECENT_LIMIT)
    return DashboardResponse(
        active_count=active_count,
        archived_count=archived_count,
        recent_projects=[
            RecentProjectRead(
                project=ProjectRead.from_model(r.project), last_viewed_at=r.last_viewed_at
            )
            for r in recents
        ],
    )
