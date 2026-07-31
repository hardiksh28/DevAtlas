"""Curriculum Engine — service layer.

Function-based, `db: AsyncSession` first arg — same convention as every
other module (see knowledge/service.py). Two concerns, cleanly split:

- `generate_or_regenerate_roadmap` / `get_roadmap` / `get_milestone` /
  `update_milestone_status` — pure structure, no LLM involved. This is
  the deterministic half ARCHITECTURE.md insists stays deterministic.
- `generate_milestone_content` — the one place this module calls the
  LLM Gateway, lazily, per milestone, on demand.
"""

import logging
import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import get_settings
from app.modules.curriculum import content_builder, sequencing
from app.modules.curriculum.content_builder import LessonContentParseError
from app.modules.curriculum.exceptions import (
    ContentGenerationError,
    InvalidMilestoneTransitionError,
    MilestoneNotFoundError,
    RoadmapNotFoundError,
)
from app.modules.curriculum.models import Milestone, Roadmap
from app.modules.curriculum.prompt_templates import MILESTONE_CONTENT_RETRY_REMINDER
from app.modules.curriculum.sequencing import ConceptNode, ExistingMilestone
from app.modules.knowledge.exceptions import RetrievalServiceUnavailableError
from app.modules.knowledge.retrieval.context_builder import build_context
from app.modules.knowledge.retrieval.rag_service import retrieve_chunks
from app.modules.llm_gateway.gateway import LLMGateway
from app.modules.progress_tracking import service as progress_tracking_service
from app.modules.projects.models import Project
from app.modules.taxonomy import service as taxonomy_service

settings = get_settings()
logger = logging.getLogger(__name__)

# Only forward transitions a learner action can request directly (see
# schemas.UpdateMilestoneStatusRequest) — "available"/"locked" are
# server-computed by _recompute_unlocks, never client-settable.
_ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    "available": {"in_progress"},
    "in_progress": {"completed"},
}

_MINUTES_BY_SEVERITY_SETTING = {
    "foundational": "curriculum_minutes_foundational",
    "intermediate": "curriculum_minutes_intermediate",
    "advanced": "curriculum_minutes_advanced",
}


def _now() -> datetime:
    return datetime.now(UTC)


def _title_from_concept_id(concept_id: str) -> str:
    # "python.async_await" -> "Async Await" — a readable default; a
    # future Lesson Engine pass could narrate a nicer title, but this
    # needs no LLM call to be good enough for a roadmap list view.
    suffix = concept_id.split(".", 1)[-1]
    return suffix.replace("_", " ").title()


def _minutes_for_severity(severity: str) -> int:
    attr = _MINUTES_BY_SEVERITY_SETTING[severity]
    return getattr(settings, attr)


def _recompute_unlocks(milestones: list[Milestone]) -> None:
    """Sequential unlock: a not-yet-started milestone becomes 'available'
    only if every milestone before it (by sequence_index) is
    'completed'; otherwise it's 'locked'. Milestones already
    in_progress/completed are left untouched. `milestones` must already
    be sorted by sequence_index.
    """
    prev_completed = True
    for m in milestones:
        if m.status in ("in_progress", "completed"):
            prev_completed = m.status == "completed"
            continue
        m.status = "available" if prev_completed else "locked"
        prev_completed = False


async def _load_roadmap(db: AsyncSession, project_id: uuid.UUID) -> Roadmap | None:
    result = await db.execute(
        select(Roadmap)
        .where(Roadmap.project_id == project_id)
        .options(selectinload(Roadmap.milestones))
    )
    return result.scalar_one_or_none()


async def generate_or_regenerate_roadmap(
    db: AsyncSession,
    *,
    project_id: uuid.UUID,
    stack: str,
    stack_version: str,
    experience_level: str,
) -> Roadmap:
    """Generates a new roadmap, or regenerates an existing one in place.

    Regeneration never loses progress: sequencing.diff_milestones keys
    the merge on concept_id, so a milestone the learner has started or
    completed keeps its id, status, and lesson_content untouched — only
    its sequence_index may move, and only relative to newly-added or
    newly-dropped milestones, never relative to other started ones.
    """
    concepts = await taxonomy_service.get_concepts_for_stack(db, stack, stack_version)
    concepts_by_id = {c.id: ConceptNode(id=c.id, severity=c.severity) for c in concepts}
    edges = await taxonomy_service.get_prerequisite_edges(db, list(concepts_by_id))

    ordered_ids = sequencing.topological_order(list(concepts_by_id.values()), edges)
    selected_ids = sequencing.select_concepts_for_level(
        ordered_ids, concepts_by_id, edges, experience_level
    )

    roadmap = await _load_roadmap(db, project_id)
    if roadmap is None:
        roadmap = Roadmap(
            project_id=project_id,
            stack=stack,
            stack_version=stack_version,
            experience_level=experience_level,
            version=1,
        )
        db.add(roadmap)
        existing_milestones: list[ExistingMilestone] = []
    else:
        roadmap.stack = stack
        roadmap.stack_version = stack_version
        roadmap.experience_level = experience_level
        roadmap.version += 1
        existing_milestones = [
            ExistingMilestone(id=m.id, concept_id=m.concept_id, status=m.status)
            for m in roadmap.milestones
        ]

    plan = sequencing.diff_milestones(existing_milestones, selected_ids)

    # Keyed by str(id) rather than the raw uuid.UUID — entry.existing_id
    # arrives as `object` (sequencing.py deliberately has no uuid/ORM
    # coupling, see ExistingMilestone's docstring), so a plain dict[UUID,
    # Milestone] can't be indexed by it without narrowing first.
    by_id = {str(m.id): m for m in roadmap.milestones}
    new_ordered: list[Milestone] = []
    for index, entry in enumerate(plan.entries):
        existing_key = str(entry.existing_id) if entry.existing_id is not None else None
        if existing_key is not None and existing_key in by_id:
            milestone = by_id[existing_key]
            milestone.sequence_index = index
        else:
            concept = concepts_by_id[entry.concept_id]
            milestone = Milestone(
                concept_id=entry.concept_id,
                sequence_index=index,
                status="locked",
                title=_title_from_concept_id(entry.concept_id),
                estimated_minutes=_minutes_for_severity(concept.severity),
            )
        new_ordered.append(milestone)

    # Bulk-replace the collection with exactly the kept + new milestones,
    # in final order. SQLAlchemy diffs this against the previously-loaded
    # collection: anything present before but absent here becomes an
    # orphan and is deleted by the `cascade="all, delete-orphan"` on
    # Roadmap.milestones (see models.py) — this is what actually removes
    # plan.dropped_ids from the database. A raw Core `DELETE` was tried
    # here first and looked correct in isolation, but left this same
    # Python-side collection stale in the session's identity map, so a
    # later `selectinload` re-query (get_roadmap, below) kept returning
    # the "deleted" rows — the ORM assumes an already-loaded collection
    # doesn't need re-fetching unless something explicitly changes it.
    roadmap.milestones = new_ordered

    _recompute_unlocks(new_ordered)
    roadmap.estimated_total_minutes = sum(m.estimated_minutes for m in new_ordered)

    await db.commit()
    return await get_roadmap(db, project_id)


async def get_roadmap(db: AsyncSession, project_id: uuid.UUID) -> Roadmap:
    roadmap = await _load_roadmap(db, project_id)
    if roadmap is None:
        raise RoadmapNotFoundError()
    return roadmap


async def get_milestone(db: AsyncSession, project_id: uuid.UUID, milestone_id: uuid.UUID) -> Milestone:
    result = await db.execute(
        select(Milestone)
        .join(Roadmap, Milestone.roadmap_id == Roadmap.id)
        .where(Milestone.id == milestone_id, Roadmap.project_id == project_id)
    )
    milestone = result.scalar_one_or_none()
    if milestone is None:
        raise MilestoneNotFoundError()
    return milestone


async def update_milestone_status(
    db: AsyncSession, project_id: uuid.UUID, milestone_id: uuid.UUID, new_status: str
) -> Milestone:
    milestone = await get_milestone(db, project_id, milestone_id)
    allowed = _ALLOWED_TRANSITIONS.get(milestone.status, set())
    if new_status not in allowed:
        raise InvalidMilestoneTransitionError(milestone.status, new_status)

    now = _now()
    milestone.status = new_status
    if new_status == "in_progress":
        milestone.started_at = now
    elif new_status == "completed":
        milestone.completed_at = now
        # Unlock the immediate next milestone in this roadmap, if it's
        # still locked — this is what "locked" means operationally:
        # sequential unlock, not all-available-at-once.
        next_result = await db.execute(
            select(Milestone)
            .where(
                Milestone.roadmap_id == milestone.roadmap_id,
                Milestone.sequence_index > milestone.sequence_index,
                Milestone.status == "locked",
            )
            .order_by(Milestone.sequence_index)
            .limit(1)
        )
        next_milestone = next_result.scalar_one_or_none()
        if next_milestone is not None:
            next_milestone.status = "available"

        # Report completion evidence to the Progress Tracker
        # (ARCHITECTURE.md Section 4's "RE->>PT: Report concept evidence"
        # edge, applied here to milestone completion) — flushed into this
        # same transaction, not committed separately, so a mastery update
        # never persists without the completion that produced it.
        owner_id = (await db.execute(select(Project.owner_id).where(Project.id == project_id))).scalar_one()
        duration_seconds = (
            int((now - milestone.started_at).total_seconds()) if milestone.started_at else None
        )
        await progress_tracking_service.record_milestone_completion(
            db,
            user_id=owner_id,
            project_id=project_id,
            concept_id=milestone.concept_id,
            duration_seconds=duration_seconds,
        )

    await db.commit()
    await db.refresh(milestone)
    return milestone


async def _generate_and_parse(gateway: LLMGateway, prompt: str) -> content_builder.LessonContent:
    raw = await gateway.generate("milestone_narration", prompt)
    return content_builder.parse_milestone_content(raw)


async def _gather_context_text(
    db: AsyncSession, gateway: LLMGateway, project_id: uuid.UUID, query: str
) -> str:
    """Best-effort RAG grounding — reuses the RAG Knowledge Engine's own
    retrieval + context-building path (knowledge/retrieval/rag_service.py
    and context_builder.py) so narration is grounded in the project's own
    ingested documentation when there is any. A project with no ingested
    docs, or a retrieval failure, degrades to an empty context rather
    than failing the whole narration request — the concept's curated
    mastery criteria/misconceptions (always present) are enough to
    narrate a lesson on their own.

    Uses keyword search, not hybrid/vector — narration doesn't need the
    recall/precision hybrid search buys /ask (there's no user-typed
    question to match nuance in; the query here is just the concept's
    own name), and skipping the embed call keeps this lazy, per-milestone
    step to a single LLM call instead of two. Revisit if narration
    quality turns out to depend on better-grounded retrieval.
    """
    try:
        chunks = await retrieve_chunks(
            db, gateway, project_id, query, mode="keyword", top_k=settings.retrieval_top_k
        )
    except RetrievalServiceUnavailableError as exc:
        logger.info("RAG context unavailable for milestone narration, continuing without it: %s", exc)
        return ""

    if not chunks:
        return ""
    return build_context(chunks, max_tokens=settings.context_max_tokens).text


async def generate_milestone_content(
    db: AsyncSession, gateway: LLMGateway, *, project_id: uuid.UUID, milestone_id: uuid.UUID
) -> Milestone:
    """Lazily (re)generates one milestone's lesson content. Never called
    as part of roadmap generation — see sequencing/generate_or_regenerate_roadmap's
    docstring for why that stays LLM-free.
    """
    milestone = await get_milestone(db, project_id, milestone_id)
    concept = await taxonomy_service.get_concept(db, milestone.concept_id)
    assert concept is not None  # RESTRICT FK guarantees this

    roadmap_result = await db.execute(select(Roadmap).where(Roadmap.id == milestone.roadmap_id))
    roadmap = roadmap_result.scalar_one()

    context_text = await _gather_context_text(
        db, gateway, project_id, query=_title_from_concept_id(concept.id)
    )
    prompt = content_builder.build_milestone_prompt(
        concept_id=concept.id,
        severity=concept.severity,
        mastery_criteria=concept.mastery_criteria,
        common_misconceptions=concept.common_misconceptions,
        experience_level=roadmap.experience_level,
        context_text=context_text,
    )

    try:
        content = await _generate_and_parse(gateway, prompt)
    except LessonContentParseError:
        logger.warning("Milestone %s: first narration response failed to parse, retrying", milestone_id)
        try:
            content = await _generate_and_parse(
                gateway, f"{prompt}\n\n{MILESTONE_CONTENT_RETRY_REMINDER}"
            )
        except LessonContentParseError as exc:
            raise ContentGenerationError(
                "The lesson content generator returned an invalid response twice in a row."
            ) from exc
    except Exception as exc:  # deliberately broad — any generate failure means narration is unavailable
        logger.warning("Milestone %s: narration generation failed: %s", milestone_id, exc)
        raise ContentGenerationError(
            "Could not generate lesson content — the LLM service is unavailable."
        ) from exc

    milestone.lesson_content = content.model_dump()
    milestone.content_version += 1
    milestone.content_generated_at = _now()

    await db.commit()
    await db.refresh(milestone)
    return milestone
