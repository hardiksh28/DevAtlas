"""Documentation Ingestion Engine — FastAPI dependencies.

Project ownership itself is enforced by
`app.modules.projects.dependencies.get_owned_project` (every route below
is nested under `/v1/projects/{project_id}/documents`) — this module
only adds the one further resolution step routes scoped to a single
document need.
"""

import uuid

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.knowledge import service
from app.modules.knowledge.models import ProjectDocument
from app.modules.projects.dependencies import get_owned_project
from app.modules.projects.models import Project


async def get_project_document(
    document_id: uuid.UUID,
    project: Project = Depends(get_owned_project),
    db: AsyncSession = Depends(get_db),
) -> ProjectDocument:
    return await service.get_document(db, project.id, document_id)
