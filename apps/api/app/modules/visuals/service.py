"""Visual Learning Engine — service layer. Function-based, `db` first arg —
same convention as every other module (see code_review/service.py)."""

import logging
import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.modules.curriculum import service as curriculum_service
from app.modules.knowledge.exceptions import RetrievalServiceUnavailableError
from app.modules.knowledge.retrieval.context_builder import build_context
from app.modules.knowledge.retrieval.rag_service import retrieve_chunks
from app.modules.llm_gateway.gateway import LLMGateway
from app.modules.taxonomy import service as taxonomy_service
from app.modules.visuals import content_builder, prompt_builder
from app.modules.visuals.content_builder import DiagramParseError
from app.modules.visuals.exceptions import DiagramGenerationError, DiagramNotFoundError
from app.modules.visuals.models import Diagram
from app.modules.visuals.prompt_templates import DIAGRAM_RETRY_REMINDER

settings = get_settings()
logger = logging.getLogger(__name__)


async def _resolve_subject(
    db: AsyncSession, *, project_id: uuid.UUID, milestone_id: uuid.UUID | None, subject: str | None
) -> str:
    parts: list[str] = []
    if milestone_id is not None:
        milestone = await curriculum_service.get_milestone(db, project_id, milestone_id)
        concept = await taxonomy_service.get_concept(db, milestone.concept_id)
        if concept is not None:
            parts.append(f"Concept: {concept.id} (severity: {concept.severity})")
            if concept.mastery_criteria:
                parts.append("Mastery criteria: " + "; ".join(concept.mastery_criteria))
    if subject:
        parts.append(subject)
    return "\n".join(parts) if parts else "the code provided below"


async def _gather_retrieved_context(
    db: AsyncSession, gateway: LLMGateway, project_id: uuid.UUID, query: str
) -> str:
    """Best-effort grounding in the project's own ingested docs —
    swallow-and-continue, same shape as code_review.service's own copy."""
    try:
        chunks = await retrieve_chunks(
            db, gateway, project_id, query, mode="keyword", top_k=settings.retrieval_top_k
        )
    except RetrievalServiceUnavailableError as exc:
        logger.info("RAG context unavailable for diagram generation, continuing without it: %s", exc)
        return ""
    if not chunks:
        return ""
    return build_context(chunks, max_tokens=settings.context_max_tokens).text


async def _generate_and_parse(gateway: LLMGateway, prompt: str, *, diagram_type: str):
    raw = await gateway.generate("diagram_generation", prompt)
    return content_builder.parse_diagram_output(raw, diagram_type=diagram_type)


async def generate_diagram(
    db: AsyncSession,
    gateway: LLMGateway,
    *,
    project_id: uuid.UUID,
    diagram_type: str,
    subject: str | None,
    milestone_id: uuid.UUID | None,
    code: str | None,
) -> Diagram:
    resolved_subject = await _resolve_subject(
        db, project_id=project_id, milestone_id=milestone_id, subject=subject
    )
    retrieved_context = await _gather_retrieved_context(
        db, gateway, project_id, query=subject or diagram_type
    )

    prompt = prompt_builder.build_diagram_prompt(
        diagram_type=diagram_type,
        subject=resolved_subject,
        code=code,
        retrieved_context=retrieved_context,
    )

    try:
        parsed = await _generate_and_parse(gateway, prompt, diagram_type=diagram_type)
    except DiagramParseError:
        logger.warning("Diagram parse failed once for project %s, retrying", project_id)
        try:
            parsed = await _generate_and_parse(
                gateway, f"{prompt}\n\n{DIAGRAM_RETRY_REMINDER}", diagram_type=diagram_type
            )
        except DiagramParseError as exc:
            raise DiagramGenerationError(
                "The diagram generator returned an invalid response twice in a row."
            ) from exc
    except (
        Exception
    ) as exc:  # deliberately broad — any generate failure means the diagram service is unavailable
        logger.warning("Diagram generation failed: %s", exc)
        raise DiagramGenerationError(
            "Could not generate a diagram — the LLM service is unavailable."
        ) from exc

    diagram = Diagram(
        project_id=project_id,
        milestone_id=milestone_id,
        diagram_type=diagram_type,
        title=parsed.title,
        subject=resolved_subject,
        mermaid_source=parsed.mermaid_source,
    )
    db.add(diagram)
    await db.commit()
    await db.refresh(diagram)
    return diagram


async def get_diagram(db: AsyncSession, project_id: uuid.UUID, diagram_id: uuid.UUID) -> Diagram:
    result = await db.execute(
        select(Diagram).where(Diagram.id == diagram_id, Diagram.project_id == project_id)
    )
    diagram = result.scalar_one_or_none()
    if diagram is None:
        raise DiagramNotFoundError()
    return diagram


async def list_diagrams(
    db: AsyncSession, project_id: uuid.UUID, limit: int, offset: int
) -> tuple[list[Diagram], int]:
    total = await db.scalar(
        select(func.count()).select_from(Diagram).where(Diagram.project_id == project_id)
    )
    result = await db.execute(
        select(Diagram)
        .where(Diagram.project_id == project_id)
        .order_by(Diagram.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    return list(result.scalars().all()), total or 0
