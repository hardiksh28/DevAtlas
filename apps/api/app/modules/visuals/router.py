"""Visual Learning Engine — router.

Nested under its owning project, same shape as code_review's review_router
(`/v1/projects/{project_id}/diagrams`) — a diagram is always generated
for, and scoped to, one project.
"""

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.llm_gateway.gateway import LLMGateway, get_llm_gateway
from app.modules.projects.dependencies import get_owned_project
from app.modules.projects.models import Project
from app.modules.visuals import service
from app.modules.visuals.schemas import (
    DiagramListResponse,
    DiagramRead,
    GenerateDiagramRequest,
)

router = APIRouter(prefix="/v1/projects/{project_id}/diagrams", tags=["Visual Learning Engine"])


@router.post("", response_model=DiagramRead)
async def generate_diagram(
    payload: GenerateDiagramRequest,
    project: Project = Depends(get_owned_project),
    db: AsyncSession = Depends(get_db),
    gateway: LLMGateway = Depends(get_llm_gateway),
) -> DiagramRead:
    diagram = await service.generate_diagram(
        db,
        gateway,
        project_id=project.id,
        diagram_type=payload.diagram_type,
        subject=payload.subject,
        milestone_id=payload.milestone_id,
        code=payload.code,
    )
    return DiagramRead.from_model(diagram)


@router.get("", response_model=DiagramListResponse)
async def list_diagrams(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    project: Project = Depends(get_owned_project),
    db: AsyncSession = Depends(get_db),
) -> DiagramListResponse:
    items, total = await service.list_diagrams(db, project.id, limit, offset)
    return DiagramListResponse(
        items=[DiagramRead.from_model(d) for d in items], total=total, limit=limit, offset=offset
    )


@router.get("/{diagram_id}", response_model=DiagramRead)
async def get_diagram(
    diagram_id: uuid.UUID,
    project: Project = Depends(get_owned_project),
    db: AsyncSession = Depends(get_db),
) -> DiagramRead:
    diagram = await service.get_diagram(db, project_id=project.id, diagram_id=diagram_id)
    return DiagramRead.from_model(diagram)
