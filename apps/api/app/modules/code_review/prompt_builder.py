"""Code Review Engine — prompt assembly. Pure, DB-free (see
prompt_templates.py's docstring) — `service.py` gathers everything real
(concept metadata, RAG context, experience level) and hands it here as
plain strings.
"""

from app.modules.code_review.prompt_templates import (
    CODE_REVIEW_PROMPT_TEMPLATE,
    CODE_REVIEW_SYSTEM_PROMPT,
    tone_guidance_for,
)


def number_lines(code: str) -> tuple[str, int]:
    """Returns (numbered code block, total line count). Numbering the
    code is what lets the prompt tell the model "only cite line numbers
    that appear below" — see content_builder.parse_review_output for
    the matching defensive check."""
    lines = code.splitlines() or [""]
    numbered = "\n".join(f"{i}: {line}" for i, line in enumerate(lines, start=1))
    return numbered, len(lines)


def build_review_prompt(
    *,
    experience_level: str,
    max_comments: int,
    concept_context: str,
    retrieved_context: str,
    file_path: str,
    language: str,
    numbered_code: str,
) -> str:
    system = CODE_REVIEW_SYSTEM_PROMPT.format(
        experience_level=experience_level,
        max_comments=max_comments,
        tone_guidance=tone_guidance_for(experience_level),
    )
    concept_section = f"Concept being practiced:\n{concept_context}\n\n" if concept_context else ""
    retrieved_section = (
        f"Reference material from the project's own docs:\n{retrieved_context}\n\n"
        if retrieved_context
        else ""
    )

    return CODE_REVIEW_PROMPT_TEMPLATE.format(
        system=system,
        concept_context=concept_section,
        retrieved_context=retrieved_section,
        file_path=file_path,
        language=language,
        numbered_code=numbered_code,
    )
