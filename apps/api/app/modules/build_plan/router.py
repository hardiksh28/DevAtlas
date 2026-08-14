"""Build Plan — router.

Thin HTTP layer only: every handler extracts what it needs, calls
service.py, and shapes the result via a schemas.py adapter. Same
project-scoped nesting as curriculum's roadmap_router.
"""

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.build_plan import service
from app.modules.build_plan.schemas import (
    BuildPlanRead,
    BuildPlanStepRead,
    GenerateBuildPlanRequest,
    UpdateStepModeRequest,
    UpdateStepStatusRequest,
)
from app.modules.cost_control.limits import llm_rate_limit
from app.modules.llm_gateway.gateway import LLMGateway, get_llm_gateway
from app.modules.projects.dependencies import get_owned_project
from app.modules.projects.models import Project

router = APIRouter(prefix="/v1/projects/{project_id}/build-plan", tags=["Build Plan"])


@router.post(
    "/generate",
    response_model=BuildPlanRead,
    dependencies=[llm_rate_limit("build_plan_generation", times=10, seconds=3600)],
)
async def generate_build_plan(
    payload: GenerateBuildPlanRequest,
    project: Project = Depends(get_owned_project),
    db: AsyncSession = Depends(get_db),
    gateway: LLMGateway = Depends(get_llm_gateway),
) -> BuildPlanRead:
    """Generates this project's build plan from its description, or
    regenerates it in place (full replace — see
    service.generate_or_regenerate_build_plan's ponytail note)."""
    plan = await service.generate_or_regenerate_build_plan(
        db, gateway, project=project, additional_context=payload.additional_context
    )
    return BuildPlanRead.from_model(plan)


@router.get("", response_model=BuildPlanRead)
async def get_build_plan(
    project: Project = Depends(get_owned_project),
    db: AsyncSession = Depends(get_db),
) -> BuildPlanRead:
    plan = await service.get_build_plan(db, project.id)
    return BuildPlanRead.from_model(plan)


@router.patch("/steps/{step_id}/mode", response_model=BuildPlanStepRead)
async def update_step_mode(
    step_id: uuid.UUID,
    payload: UpdateStepModeRequest,
    project: Project = Depends(get_owned_project),
    db: AsyncSession = Depends(get_db),
) -> BuildPlanStepRead:
    step = await service.update_step_mode(db, project.id, step_id, payload.build_mode)
    return BuildPlanStepRead.from_model(step)


@router.patch("/steps/{step_id}/status", response_model=BuildPlanStepRead)
async def update_step_status(
    step_id: uuid.UUID,
    payload: UpdateStepStatusRequest,
    project: Project = Depends(get_owned_project),
    db: AsyncSession = Depends(get_db),
) -> BuildPlanStepRead:
    step = await service.update_step_status(db, project.id, step_id, payload.status)
    return BuildPlanStepRead.from_model(step)
