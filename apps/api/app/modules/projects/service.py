"""Project Workspace — service layer.

All business logic lives here, not in router.py — same "thin router,
real logic in the module" split as every other module (see
auth/service.py's own docstring). Every public function either returns
what the caller asked for or raises app.modules.projects.exceptions;
never a bare HTTPException, never a silent None for a failure case.

Update functions take a plain `changes: dict` (from
`Payload.model_dump(exclude_unset=True)`, built in router.py) rather
than a schemas.py object directly — the dict is what lets these stay
decoupled from FastAPI/Pydantic and callable from a future non-HTTP
caller, and `exclude_unset` is what distinguishes "field omitted"
(leave unchanged) from "field explicitly sent as null/empty" (clear
it) for PATCH semantics.
"""

import uuid
from datetime import UTC, datetime

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import get_settings
from app.modules.projects.exceptions import (
    InvalidProjectStateError,
    ProjectLimitExceededError,
    ProjectNotFoundError,
)
from app.modules.projects.models import Project, ProjectSettings, RecentProject

settings = get_settings()


def _now() -> datetime:
    return datetime.now(UTC)


# --- Projects: CRUD ---


async def create_project(
    db: AsyncSession, owner_id: uuid.UUID, name: str, description: str | None
) -> Project:
    active_count = await count_projects_by_status(db, owner_id, "active")
    if active_count >= settings.max_active_projects_per_owner:
        raise ProjectLimitExceededError(settings.max_active_projects_per_owner)

    project = Project(owner_id=owner_id, name=name, description=description)
    db.add(project)
    await db.flush()  # assigns project.id, needed by the settings FK below
    db.add(ProjectSettings(project_id=project.id))
    await db.commit()
    await db.refresh(project)
    return project


async def _get_owned_project_row(
    db: AsyncSession, project_id: uuid.UUID, owner_id: uuid.UUID, *, exclude_deleted: bool = True
) -> Project | None:
    query = select(Project).where(Project.id == project_id, Project.owner_id == owner_id)
    if exclude_deleted:
        query = query.where(Project.status != "deleted")
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def get_project(db: AsyncSession, project_id: uuid.UUID, owner_id: uuid.UUID) -> Project:
    """The one enforcement point behind `dependencies.get_owned_project`
    — 404s (never 403) whether the project doesn't exist, belongs to
    someone else, or is already soft-deleted, so a caller can't
    distinguish "not yours" from "doesn't exist" by status code alone."""
    project = await _get_owned_project_row(db, project_id, owner_id)
    if project is None:
        raise ProjectNotFoundError()
    return project


async def list_projects(
    db: AsyncSession, owner_id: uuid.UUID, status: str, limit: int, offset: int
) -> tuple[list[Project], int]:
    base = select(Project).where(Project.owner_id == owner_id, Project.status == status)

    count_result = await db.execute(select(func.count()).select_from(base.subquery()))
    total = count_result.scalar_one()

    result = await db.execute(base.order_by(Project.updated_at.desc()).limit(limit).offset(offset))
    return list(result.scalars().all()), total


async def update_project(db: AsyncSession, project: Project, changes: dict) -> Project:
    if not changes:
        return project
    for field, value in changes.items():
        setattr(project, field, value)
    await db.commit()
    await db.refresh(project)
    return project


async def archive_project(db: AsyncSession, project: Project) -> Project:
    """Idempotent — archiving an already-archived project is a no-op,
    not an error; the end state the caller wants is the same either
    way (matches revoke_session's idempotent-logout reasoning)."""
    if project.status == "archived":
        return project
    project.status = "archived"
    project.archived_at = _now()
    await db.commit()
    await db.refresh(project)
    return project


async def delete_project(db: AsyncSession, project: Project) -> None:
    """Soft delete only — sets status + deleted_at. Reachable only via
    `dependencies.get_owned_project`, which already excludes projects
    that are status='deleted', so this never double-deletes."""
    project.status = "deleted"
    project.deleted_at = _now()
    await db.commit()


async def restore_project(db: AsyncSession, project_id: uuid.UUID, owner_id: uuid.UUID) -> Project:
    """Valid from either `archived` or `deleted`; always returns to
    `active`. Bypasses the shared `get_owned_project` dependency (which
    excludes deleted projects) since restoring a deleted project is
    exactly the case that dependency is meant to hide from every other
    route."""
    project = await _get_owned_project_row(db, project_id, owner_id, exclude_deleted=False)
    if project is None:
        raise ProjectNotFoundError()
    if project.status == "active":
        raise InvalidProjectStateError("Project is already active.")

    # Restoring also lands on `active`, so it's the same growth vector
    # `create_project`'s cap guards against — without this check here
    # too, archive-then-create-to-the-cap-then-restore-the-archived-ones
    # would let an owner exceed max_active_projects_per_owner.
    active_count = await count_projects_by_status(db, owner_id, "active")
    if active_count >= settings.max_active_projects_per_owner:
        raise ProjectLimitExceededError(settings.max_active_projects_per_owner)

    project.status = "active"
    project.archived_at = None
    project.deleted_at = None
    await db.commit()
    await db.refresh(project)
    return project


# --- Project settings ---


async def get_project_settings(db: AsyncSession, project_id: uuid.UUID) -> ProjectSettings:
    result = await db.execute(
        select(ProjectSettings).where(ProjectSettings.project_id == project_id)
    )
    settings = result.scalar_one_or_none()
    if settings is None:
        # Should be unreachable in practice — a settings row is created
        # transactionally with every project — but the caller already
        # proved the project exists via get_owned_project, so a missing
        # settings row means the same "not found" contract, not a 500.
        raise ProjectNotFoundError()
    return settings


async def update_project_settings(
    db: AsyncSession, settings: ProjectSettings, changes: dict
) -> ProjectSettings:
    if not changes:
        return settings
    for field, value in changes.items():
        setattr(settings, field, value)
    await db.commit()
    await db.refresh(settings)
    return settings


# --- Recent projects / dashboard ---


async def record_project_view(db: AsyncSession, user_id: uuid.UUID, project_id: uuid.UUID) -> None:
    """Update-then-insert rather than a dialect-specific `ON CONFLICT`
    upsert — this app's tests fall back to SQLite (see
    tests/conftest.py), and a plain UPDATE followed by a conditional
    INSERT is portable across both engines. A rare concurrent first-view
    race (two simultaneous inserts for the same brand-new pair) is an
    acceptable risk for a last-viewed timestamp with no correctness
    implications elsewhere."""
    now = _now()
    result = await db.execute(
        update(RecentProject)
        .where(RecentProject.user_id == user_id, RecentProject.project_id == project_id)
        .values(last_viewed_at=now)
    )
    # CursorResult always has rowcount at runtime; Result[Any]'s static
    # type just doesn't expose it generically.
    if result.rowcount == 0:  # type: ignore[attr-defined]
        db.add(RecentProject(user_id=user_id, project_id=project_id, last_viewed_at=now))
    await db.commit()


async def list_recent_projects(
    db: AsyncSession, user_id: uuid.UUID, limit: int
) -> list[RecentProject]:
    result = await db.execute(
        select(RecentProject)
        .join(Project, RecentProject.project_id == Project.id)
        .where(RecentProject.user_id == user_id, Project.status != "deleted")
        .options(selectinload(RecentProject.project))
        .order_by(RecentProject.last_viewed_at.desc())
        .limit(limit)
    )
    return list(result.scalars().all())


async def count_projects_by_status(db: AsyncSession, owner_id: uuid.UUID, status: str) -> int:
    result = await db.execute(
        select(func.count())
        .select_from(Project)
        .where(Project.owner_id == owner_id, Project.status == status)
    )
    return result.scalar_one()
