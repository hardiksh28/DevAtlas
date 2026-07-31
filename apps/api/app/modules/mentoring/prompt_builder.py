"""Mentoring Engine — prompt assembly. Pure, DB-free (see
prompt_templates.py's docstring) — `service.py` gathers everything real
(concept metadata, RAG context, message history) and hands it here as
plain strings/tuples.
"""

from app.modules.mentoring.prompt_templates import (
    MENTOR_PROMPT_TEMPLATE,
    MENTOR_SYSTEM_PROMPT,
    SUMMARY_PROMPT_TEMPLATE,
    SUMMARY_SYSTEM_PROMPT,
)

# (role, content) pairs, oldest first — role is "user" or "assistant".
ConversationTurn = tuple[str, str]


def _format_messages(messages: list[ConversationTurn]) -> str:
    if not messages:
        return "(no prior messages)"
    return "\n".join(f"{role}: {content}" for role, content in messages)


def build_mentor_prompt(
    *,
    experience_level: str,
    concept_context: str,
    retrieved_context: str,
    summary: str | None,
    recent_messages: list[ConversationTurn],
    question: str,
) -> str:
    concept_section = f"Concept being discussed:\n{concept_context}\n" if concept_context else ""
    retrieved_section = (
        f"Reference material from the project's own docs:\n{retrieved_context}\n"
        if retrieved_context
        else ""
    )
    summary_section = f"Summary of earlier conversation:\n{summary}\n" if summary else ""

    return MENTOR_PROMPT_TEMPLATE.format(
        system=MENTOR_SYSTEM_PROMPT,
        experience_level=experience_level,
        concept_context=concept_section,
        retrieved_context=retrieved_section,
        summary_section=summary_section,
        recent_messages=_format_messages(recent_messages),
        question=question,
    )


def build_summary_prompt(messages: list[ConversationTurn]) -> str:
    return SUMMARY_PROMPT_TEMPLATE.format(
        system=SUMMARY_SYSTEM_PROMPT, messages=_format_messages(messages)
    )
