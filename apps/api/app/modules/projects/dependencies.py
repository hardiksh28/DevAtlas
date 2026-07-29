"""Project Workspace — FastAPI dependencies.

`get_owned_project` is this module's equivalent of
`auth.dependencies.get_current_user`: the one enforcement point every
project-scoped route depends on. It resolves the `project_id` path
param, checks ownership, and 404s (never 403 — see
exceptions.ProjectNotFoundError) if the project doesn't exist, isn't
the caller's, or is already soft-deleted.
"""

import uuid

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.models import User
from app.modules.projects import service
from app.modules.projects.models import Project


async def get_owned_project(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Project:
    return await service.get_project(db, project_id, current_user.id)
