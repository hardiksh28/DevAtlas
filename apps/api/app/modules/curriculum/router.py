"""Curriculum Engine — router.

Two routers, deliberately, mirroring knowledge/router.py's own split:
`router` (`/v1/curriculum`) stays the pre-existing stub — nothing in
this pass needs a non-project-scoped curriculum route. `roadmap_router`
(`/v1/projects/{project_id}/roadmap`) is the actual Curriculum Engine
built in this pass, nested under its owning project the same way
`project_documents_router` is.

Thin HTTP layer only: every handler extracts what it needs, calls
service.py, and shapes the result via a schemas.py adapter.
"""

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.cost_control.limits import llm_rate_limit
from app.modules.curriculum import service
from app.modules.curriculum.schemas import (
    GenerateRoadmapRequest,
    MilestoneDetailRead,
    RoadmapRead,
    UpdateMilestoneStatusRequest,
)
from app.modules.llm_gateway.gateway import LLMGateway, get_llm_gateway
from app.modules.projects.dependencies import get_owned_project
from app.modules.projects.models import Project

router = APIRouter(prefix="/v1/curriculum", tags=["Curriculum Engine"])

roadmap_router = APIRouter(
    prefix="/v1/projects/{project_id}/roadmap", tags=["Curriculum Engine — Roadmap"]
)


@roadmap_router.post("/generate", response_model=RoadmapRead)
async def generate_roadmap(
    payload: GenerateRoadmapRequest,
    project: Project = Depends(get_owned_project),
    db: AsyncSession = Depends(get_db),
) -> RoadmapRead:
    """Generates this project's roadmap, or regenerates it in place if
    one already exists — see service.generate_or_regenerate_roadmap for
    the progress-preserving merge. Pure graph traversal: no LLM call
    happens here (see docs/architecture/curriculum-engine-v1.md)."""
    roadmap = await service.generate_or_regenerate_roadmap(
        db,
        project_id=project.id,
        stack=payload.stack,
        stack_version=payload.stack_version,
        experience_level=payload.experience_level,
    )
    return RoadmapRead.from_model(roadmap)


@roadmap_router.get("", response_model=RoadmapRead)
async def get_roadmap(
    project: Project = Depends(get_owned_project),
    db: AsyncSession = Depends(get_db),
) -> RoadmapRead:
    roadmap = await service.get_roadmap(db, project.id)
    return RoadmapRead.from_model(roadmap)


@roadmap_router.get("/milestones/{milestone_id}", response_model=MilestoneDetailRead)
async def get_milestone(
    milestone_id: uuid.UUID,
    project: Project = Depends(get_owned_project),
    db: AsyncSession = Depends(get_db),
) -> MilestoneDetailRead:
    milestone = await service.get_milestone(db, project.id, milestone_id)
    return MilestoneDetailRead.from_model(milestone)


@roadmap_router.post(
    "/milestones/{milestone_id}/content",
    response_model=MilestoneDetailRead,
    dependencies=[llm_rate_limit("milestone_content", times=30, seconds=3600)],
)
async def generate_milestone_content(
    milestone_id: uuid.UUID,
    project: Project = Depends(get_owned_project),
    db: AsyncSession = Depends(get_db),
    gateway: LLMGateway = Depends(get_llm_gateway),
) -> MilestoneDetailRead:
    """Lazily (re)generates one milestone's explanation/exercises/quiz
    via the LLM Gateway — never triggered automatically by /generate."""
    milestone = await service.generate_milestone_content(
        db, gateway, project_id=project.id, milestone_id=milestone_id
    )
    return MilestoneDetailRead.from_model(milestone)


@roadmap_router.patch("/milestones/{milestone_id}", response_model=MilestoneDetailRead)
async def update_milestone_status(
    milestone_id: uuid.UUID,
    payload: UpdateMilestoneStatusRequest,
    project: Project = Depends(get_owned_project),
    db: AsyncSession = Depends(get_db),
) -> MilestoneDetailRead:
    milestone = await service.update_milestone_status(
        db, project.id, milestone_id, payload.status
    )
    return MilestoneDetailRead.from_model(milestone)
