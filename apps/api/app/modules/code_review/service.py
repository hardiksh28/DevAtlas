"""Code Review Engine — service layer. Function-based, `db` first arg —
same convention as every other module (see mentoring/service.py)."""

import logging
import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import get_settings
from app.modules.code_review import content_builder, prompt_builder
from app.modules.code_review.content_builder import ReviewParseError
from app.modules.code_review.exceptions import ReviewGenerationError, ReviewNotFoundError
from app.modules.code_review.models import CodeReview, CodeReviewComment
from app.modules.code_review.prompt_templates import CODE_REVIEW_RETRY_REMINDER
from app.modules.curriculum import service as curriculum_service
from app.modules.curriculum.exceptions import RoadmapNotFoundError
from app.modules.curriculum.models import Milestone
from app.modules.knowledge.exceptions import RetrievalServiceUnavailableError
from app.modules.knowledge.retrieval.context_builder import build_context
from app.modules.knowledge.retrieval.rag_service import retrieve_chunks
from app.modules.llm_gateway.gateway import LLMGateway
from app.modules.progress_tracking import service as progress_tracking_service
from app.modules.projects.models import Project
from app.modules.taxonomy import service as taxonomy_service

settings = get_settings()
logger = logging.getLogger(__name__)

_DEFAULT_EXPERIENCE_LEVEL = "intermediate"
# Overwhelm control by learner level (prompt_templates.py's docstring) —
# a plain dict, not a Settings field: unlike curriculum's per-severity
# minute estimates, there's no product signal yet that these need
# tuning without a deploy.
_MAX_COMMENTS_BY_LEVEL = {"beginner": 5, "intermediate": 10, "advanced": 20}


async def _resolve_experience_level(db: AsyncSession, project_id: uuid.UUID) -> str:
    try:
        roadmap = await curriculum_service.get_roadmap(db, project_id)
    except RoadmapNotFoundError:
        # A review must work before a roadmap exists — same reasoning as
        # mentoring.service._resolve_experience_level.
        return _DEFAULT_EXPERIENCE_LEVEL
    return roadmap.experience_level


async def _resolve_concept_context(db: AsyncSession, milestone_id: uuid.UUID | None) -> str:
    if milestone_id is None:
        return ""
    milestone = await db.get(Milestone, milestone_id)
    if milestone is None:
        return ""
    concept = await taxonomy_service.get_concept(db, milestone.concept_id)
    if concept is None:
        return ""

    lines = [f"{concept.id} (severity: {concept.severity})"]
    if concept.mastery_criteria:
        lines.append("Mastery criteria: " + "; ".join(concept.mastery_criteria))
    return "\n".join(lines)


async def _gather_retrieved_context(
    db: AsyncSession, gateway: LLMGateway, project_id: uuid.UUID, query: str
) -> str:
    """Best-effort grounding in the project's own ingested docs —
    swallow-and-continue, same shape as mentoring.service's own copy."""
    try:
        chunks = await retrieve_chunks(
            db, gateway, project_id, query, mode="keyword", top_k=settings.retrieval_top_k
        )
    except RetrievalServiceUnavailableError as exc:
        logger.info("RAG context unavailable for code review, continuing without it: %s", exc)
        return ""
    if not chunks:
        return ""
    return build_context(chunks, max_tokens=settings.context_max_tokens).text


async def _generate_and_parse(
    gateway: LLMGateway, prompt: str, *, total_lines: int, max_comments: int
):
    raw = await gateway.generate("code_review", prompt)
    return content_builder.parse_review_output(
        raw, total_lines=total_lines, max_comments=max_comments
    )


async def submit_review(
    db: AsyncSession,
    gateway: LLMGateway,
    *,
    project_id: uuid.UUID,
    milestone_id: uuid.UUID | None,
    code: str,
    language: str,
    file_path: str | None,
) -> CodeReview:
    experience_level = await _resolve_experience_level(db, project_id)
    concept_context = await _resolve_concept_context(db, milestone_id)
    retrieved_context = await _gather_retrieved_context(
        db, gateway, project_id, query=f"{language} best practices"
    )
    numbered_code, total_lines = prompt_builder.number_lines(code)
    max_comments = _MAX_COMMENTS_BY_LEVEL.get(
        experience_level, _MAX_COMMENTS_BY_LEVEL["intermediate"]
    )

    prompt = prompt_builder.build_review_prompt(
        experience_level=experience_level,
        max_comments=max_comments,
        concept_context=concept_context,
        retrieved_context=retrieved_context,
        file_path=file_path or "submission",
        language=language,
        numbered_code=numbered_code,
    )

    try:
        parsed = await _generate_and_parse(
            gateway, prompt, total_lines=total_lines, max_comments=max_comments
        )
    except ReviewParseError:
        logger.warning("Review parse failed once for project %s, retrying", project_id)
        try:
            parsed = await _generate_and_parse(
                gateway,
                f"{prompt}\n\n{CODE_REVIEW_RETRY_REMINDER}",
                total_lines=total_lines,
                max_comments=max_comments,
            )
        except ReviewParseError as exc:
            raise ReviewGenerationError(
                "The reviewer returned an invalid response twice in a row."
            ) from exc
    except (
        Exception
    ) as exc:  # deliberately broad — any generate failure means the reviewer is unavailable
        logger.warning("Review generation failed: %s", exc)
        raise ReviewGenerationError(
            "Could not generate a review — the LLM service is unavailable."
        ) from exc

    review = CodeReview(
        project_id=project_id,
        milestone_id=milestone_id,
        language=language,
        file_path=file_path,
        code=code,
        overall_score=parsed.overall_score,
        summary=parsed.summary,
        strengths=parsed.strengths,
        refactoring_ideas=parsed.refactoring_ideas,
    )
    db.add(review)
    for comment in parsed.comments:
        db.add(
            CodeReviewComment(
                review=review,
                file_path=comment.file_path,
                line_start=comment.line_start,
                line_end=comment.line_end,
                category=comment.category,
                severity=comment.severity,
                body=comment.body,
                suggestion=comment.suggestion,
                concept_tags=comment.concept_tags,
            )
        )

    # Report review evidence to the Progress Tracker — same "flush into
    # this transaction, one shared commit" reasoning as curriculum's own
    # record_milestone_completion call site.
    owner_id = (await db.execute(select(Project.owner_id).where(Project.id == project_id))).scalar_one()
    await progress_tracking_service.record_review_evidence(
        db,
        user_id=owner_id,
        project_id=project_id,
        milestone_id=milestone_id,
        overall_score=review.overall_score,
    )

    await db.commit()

    # Re-fetch with comments eagerly loaded rather than touching
    # `review.comments` post-commit — same MissingGreenlet-avoidance
    # reasoning as mentoring.service.get_or_create_conversation.
    return await get_review(db, project_id=project_id, review_id=review.id)


async def get_review(db: AsyncSession, project_id: uuid.UUID, review_id: uuid.UUID) -> CodeReview:
    result = await db.execute(
        select(CodeReview)
        .where(CodeReview.id == review_id, CodeReview.project_id == project_id)
        .options(selectinload(CodeReview.comments))
    )
    review = result.scalar_one_or_none()
    if review is None:
        raise ReviewNotFoundError()
    return review


async def list_reviews(
    db: AsyncSession, project_id: uuid.UUID, limit: int, offset: int
) -> tuple[list[tuple[CodeReview, int]], int]:
    total = await db.scalar(
        select(func.count()).select_from(CodeReview).where(CodeReview.project_id == project_id)
    )
    result = await db.execute(
        select(CodeReview, func.count(CodeReviewComment.id))
        .outerjoin(CodeReviewComment, CodeReviewComment.review_id == CodeReview.id)
        .where(CodeReview.project_id == project_id)
        .group_by(CodeReview.id)
        .order_by(CodeReview.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    return [(review, count) for review, count in result.all()], total or 0
