"""Mentoring Engine — service layer. Function-based, `db` first arg —
same convention as every other module (see knowledge/service.py).
"""

import logging
import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import get_settings
from app.modules.curriculum import service as curriculum_service
from app.modules.curriculum.exceptions import RoadmapNotFoundError
from app.modules.curriculum.models import Milestone
from app.modules.knowledge.exceptions import RetrievalServiceUnavailableError
from app.modules.knowledge.retrieval.context_builder import build_context
from app.modules.knowledge.retrieval.rag_service import retrieve_chunks
from app.modules.llm_gateway.gateway import LLMGateway
from app.modules.mentoring import content_builder, prompt_builder
from app.modules.mentoring.content_builder import MentorReplyParseError
from app.modules.mentoring.exceptions import MentorReplyGenerationError
from app.modules.mentoring.models import Conversation, Message
from app.modules.mentoring.prompt_templates import MENTOR_REPLY_RETRY_REMINDER
from app.modules.mentoring.schemas import MentorReply
from app.modules.taxonomy import service as taxonomy_service

settings = get_settings()
logger = logging.getLogger(__name__)

_DEFAULT_EXPERIENCE_LEVEL = "intermediate"
# Turns always kept verbatim, outside the summary, regardless of how
# far compaction advances — the mentor's immediately preceding exchange
# should never be paraphrased out from under a follow-up question.
_SUMMARY_TAIL_KEEP = 4


async def get_or_create_conversation(db: AsyncSession, project_id: uuid.UUID) -> Conversation:
    # `.messages` is touched synchronously later (building the prompt,
    # compaction) — eager-load it here (existing conversation) or
    # pre-initialize it as empty (new one) so nothing ever triggers an
    # implicit lazy-load outside an awaited context, which raises
    # MissingGreenlet under the async engine (see curriculum.service's
    # own `selectinload(Roadmap.milestones)` for the same reasoning).
    result = await db.execute(
        select(Conversation)
        .where(Conversation.project_id == project_id)
        .options(selectinload(Conversation.messages))
    )
    conversation = result.scalar_one_or_none()
    if conversation is None:
        conversation = Conversation(project_id=project_id, messages=[])
        db.add(conversation)
        await db.flush()
    return conversation


async def _resolve_experience_level(db: AsyncSession, project_id: uuid.UUID) -> str:
    try:
        roadmap = await curriculum_service.get_roadmap(db, project_id)
    except RoadmapNotFoundError:
        # The mentor must work before a roadmap exists — a sane default
        # beats blocking the whole conversation on curriculum generation.
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
    if concept.common_misconceptions:
        # Curated ground truth for misconception detection — the model
        # matches against this closed set when a concept is given,
        # rather than inventing labels (mirrors ARCHITECTURE.md's
        # "closed-set concept taxonomy" reasoning applied to detection).
        lines.append("Known common misconceptions: " + "; ".join(concept.common_misconceptions))
    return "\n".join(lines)


async def _gather_retrieved_context(
    db: AsyncSession, gateway: LLMGateway, project_id: uuid.UUID, query: str
) -> str:
    """Best-effort grounding in the project's own ingested docs — same
    keyword-mode, swallow-and-continue shape as
    curriculum.service._gather_context_text."""
    try:
        chunks = await retrieve_chunks(
            db, gateway, project_id, query, mode="keyword", top_k=settings.retrieval_top_k
        )
    except RetrievalServiceUnavailableError as exc:
        logger.info("RAG context unavailable for mentor reply, continuing without it: %s", exc)
        return ""
    if not chunks:
        return ""
    return build_context(chunks, max_tokens=settings.context_max_tokens).text


def _uncompacted_messages(conversation: Conversation) -> list[Message]:
    if conversation.summarized_up_to is None:
        return list(conversation.messages)
    return [m for m in conversation.messages if m.created_at > conversation.summarized_up_to]


def _recent_turns(conversation: Conversation) -> list[tuple[str, str]]:
    tail = _uncompacted_messages(conversation)[-settings.mentor_recent_message_limit :]
    return [(m.role, m.content) for m in tail]


async def _generate_and_parse(gateway: LLMGateway, prompt: str) -> MentorReply:
    raw = await gateway.generate("mentor_reply", prompt)
    return content_builder.parse_mentor_reply(raw)


async def _maybe_compact_history(
    db: AsyncSession, gateway: LLMGateway, conversation: Conversation
) -> None:
    """Folds everything except the last `_SUMMARY_TAIL_KEEP` uncompacted
    messages into `conversation.summary` once the uncompacted tail
    exceeds `mentor_summary_trigger_messages` — see
    docs/architecture/mentor-engine-v1.md's memory-strategy section.
    Best-effort: a failed compaction just means the next call carries a
    slightly longer tail, not a broken conversation.
    """
    uncompacted = _uncompacted_messages(conversation)
    if len(uncompacted) <= settings.mentor_summary_trigger_messages:
        return
    to_summarize = uncompacted[:-_SUMMARY_TAIL_KEEP]
    if not to_summarize:
        return

    prompt = prompt_builder.build_summary_prompt([(m.role, m.content) for m in to_summarize])
    try:
        new_summary_text = await gateway.generate("mentor_summarize", prompt)
    except Exception as exc:  # noqa: BLE001 — best-effort compaction, swallowed not re-raised on purpose
        logger.warning("History compaction skipped for conversation %s: %s", conversation.id, exc)
        return

    conversation.summary = (
        f"{conversation.summary}\n\n{new_summary_text.strip()}"
        if conversation.summary
        else new_summary_text.strip()
    )
    conversation.summarized_up_to = to_summarize[-1].created_at


async def send_message(
    db: AsyncSession,
    gateway: LLMGateway,
    *,
    project_id: uuid.UUID,
    milestone_id: uuid.UUID | None,
    content: str,
) -> tuple[Message, Message]:
    conversation = await get_or_create_conversation(db, project_id)

    user_message = Message(
        conversation=conversation, milestone_id=milestone_id, role="user", content=content
    )
    db.add(user_message)
    await db.flush()

    experience_level = await _resolve_experience_level(db, project_id)
    concept_context = await _resolve_concept_context(db, milestone_id)
    retrieved_context = await _gather_retrieved_context(db, gateway, project_id, query=content[:200])

    prompt = prompt_builder.build_mentor_prompt(
        experience_level=experience_level,
        concept_context=concept_context,
        retrieved_context=retrieved_context,
        summary=conversation.summary,
        recent_messages=_recent_turns(conversation),
        question=content,
    )

    try:
        parsed = await _generate_and_parse(gateway, prompt)
    except MentorReplyParseError:
        logger.warning("Mentor reply parse failed once for conversation %s, retrying", conversation.id)
        try:
            parsed = await _generate_and_parse(gateway, f"{prompt}\n\n{MENTOR_REPLY_RETRY_REMINDER}")
        except MentorReplyParseError as exc:
            raise MentorReplyGenerationError(
                "The mentor returned an invalid response twice in a row."
            ) from exc
    except Exception as exc:  # deliberately broad — any generate failure means the mentor is unavailable
        logger.warning("Mentor reply generation failed: %s", exc)
        raise MentorReplyGenerationError(
            "Could not generate a mentor reply — the LLM service is unavailable."
        ) from exc

    assistant_message = Message(
        conversation=conversation,
        milestone_id=milestone_id,
        role="assistant",
        content=parsed.reply,
        detected_misconceptions=parsed.misconceptions_detected,
    )
    db.add(assistant_message)
    await db.flush()

    await _maybe_compact_history(db, gateway, conversation)

    await db.commit()
    await db.refresh(user_message)
    await db.refresh(assistant_message)
    return user_message, assistant_message


async def list_messages(
    db: AsyncSession, project_id: uuid.UUID, limit: int, offset: int
) -> tuple[list[Message], int]:
    # Look up only — a read must never have the side effect of creating
    # a conversation row (unlike send_message, which is the one place
    # "lazily create" is appropriate).
    result_conv = await db.execute(select(Conversation).where(Conversation.project_id == project_id))
    conversation = result_conv.scalar_one_or_none()
    if conversation is None:
        return [], 0

    total = await db.scalar(
        select(func.count()).select_from(Message).where(Message.conversation_id == conversation.id)
    )
    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation.id)
        .order_by(Message.created_at)
        .offset(offset)
        .limit(limit)
    )
    return list(result.scalars().all()), total or 0
