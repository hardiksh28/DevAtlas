"""Build Plan — service layer.

Function-based, `db: AsyncSession` first arg — same convention as
curriculum/service.py. One LLM call per generate/regenerate; everything
else is plain CRUD over the already-generated plan.
"""

import logging
import uuid

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.build_plan import content_builder
from app.modules.build_plan.content_builder import PlanContentParseError
from app.modules.build_plan.exceptions import (
    BuildPlanNotFoundError,
    InvalidStepTransitionError,
    PlanGenerationError,
    ProjectDescriptionMissingError,
    StepNotFoundError,
)
from app.modules.build_plan.models import BuildPlan, BuildPlanStep
from app.modules.build_plan.prompt_templates import BUILD_PLAN_RETRY_REMINDER
from app.modules.llm_gateway.gateway import LLMGateway
from app.modules.projects.models import Project

logger = logging.getLogger(__name__)

_ALLOWED_STEP_TRANSITIONS: dict[str, set[str]] = {
    "pending": {"in_progress"},
    "in_progress": {"completed"},
}


async def _load_plan(db: AsyncSession, project_id: uuid.UUID) -> BuildPlan | None:
    result = await db.execute(
        select(BuildPlan)
        .where(BuildPlan.project_id == project_id)
        .options(selectinload(BuildPlan.steps))
    )
    return result.scalar_one_or_none()


async def _generate_and_parse(gateway: LLMGateway, prompt: str) -> content_builder.GeneratedPlanContent:
    raw = await gateway.generate("build_plan_generation", prompt)
    return content_builder.parse_build_plan(raw)


async def generate_or_regenerate_build_plan(
    db: AsyncSession,
    gateway: LLMGateway,
    *,
    project: Project,
    additional_context: str | None,
) -> BuildPlan:
    """Generates a new plan, or regenerates one in place.

    # ponytail: regeneration fully replaces every step rather than a
    # progress-preserving merge like curriculum's diff_milestones — a
    # generated step has no stable identity (no concept_id equivalent)
    # to diff a new step list against. Add a title/description
    # similarity-based merge if regeneration-losing-progress turns out
    # to matter in practice; not built now since it's real complexity
    # for a case (regenerating an already-started plan) that may be rare.
    """
    if not project.description or not project.description.strip():
        raise ProjectDescriptionMissingError()

    prompt = content_builder.build_plan_prompt(
        project_name=project.name,
        project_description=project.description,
        additional_context=additional_context,
    )

    try:
        content = await _generate_and_parse(gateway, prompt)
    except PlanContentParseError:
        logger.warning("Project %s: first build-plan response failed to parse, retrying", project.id)
        try:
            content = await _generate_and_parse(gateway, f"{prompt}\n\n{BUILD_PLAN_RETRY_REMINDER}")
        except PlanContentParseError as exc:
            raise PlanGenerationError(
                "The build plan generator returned an invalid response twice in a row."
            ) from exc
    except Exception as exc:  # deliberately broad — any generate failure means the plan is unavailable
        logger.warning("Project %s: build plan generation failed: %s", project.id, exc)
        raise PlanGenerationError(
            "Could not generate a build plan — the LLM service is unavailable."
        ) from exc

    plan = await _load_plan(db, project.id)
    if plan is None:
        plan = BuildPlan(project_id=project.id, summary=content.summary, version=1)
        db.add(plan)
    else:
        plan.summary = content.summary
        plan.version += 1
        # Explicit delete + flush *before* assigning the new collection.
        # Every new step is a fresh row (full replace, no id reuse — see
        # this function's ponytail note), all starting again at
        # sequence_index 0, so reassigning `plan.steps` directly would
        # ask the unit of work to INSERT the new rows in the same flush
        # as the old ones' DELETE-on-orphan, and nothing orders that
        # DELETE before the INSERT — it 500s on
        # uq_build_plan_steps_sequence. Deleting old rows in their own
        # flush first removes the collision entirely.
        await db.execute(delete(BuildPlanStep).where(BuildPlanStep.build_plan_id == plan.id))
        await db.flush()

    plan.recommended_stack = [item.model_dump() for item in content.recommended_stack]
    plan.steps = [
        BuildPlanStep(
            sequence_index=index,
            title=step.title,
            description=step.description,
        )
        for index, step in enumerate(content.steps)
    ]

    await db.commit()
    return await get_build_plan(db, project.id)


async def get_build_plan(db: AsyncSession, project_id: uuid.UUID) -> BuildPlan:
    plan = await _load_plan(db, project_id)
    if plan is None:
        raise BuildPlanNotFoundError()
    return plan


async def _get_step(db: AsyncSession, project_id: uuid.UUID, step_id: uuid.UUID) -> BuildPlanStep:
    result = await db.execute(
        select(BuildPlanStep)
        .join(BuildPlan, BuildPlanStep.build_plan_id == BuildPlan.id)
        .where(BuildPlanStep.id == step_id, BuildPlan.project_id == project_id)
    )
    step = result.scalar_one_or_none()
    if step is None:
        raise StepNotFoundError()
    return step


async def update_step_mode(
    db: AsyncSession, project_id: uuid.UUID, step_id: uuid.UUID, build_mode: str
) -> BuildPlanStep:
    """Records whether the learner wants this step built by themselves
    (Socratic-guided, same as Learn Mode) or generated by the AI —
    per-step, set once the learner chooses, changeable any time before
    the step is completed."""
    step = await _get_step(db, project_id, step_id)
    step.build_mode = build_mode
    await db.commit()
    await db.refresh(step)
    return step


async def update_step_status(
    db: AsyncSession, project_id: uuid.UUID, step_id: uuid.UUID, new_status: str
) -> BuildPlanStep:
    step = await _get_step(db, project_id, step_id)
    allowed = _ALLOWED_STEP_TRANSITIONS.get(step.status, set())
    if new_status not in allowed:
        raise InvalidStepTransitionError(step.status, new_status)
    step.status = new_status
    await db.commit()
    await db.refresh(step)
    return step
