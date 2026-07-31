"""Visual Learning Engine — prompt assembly. Pure string building, no I/O
— same split as code_review/prompt_builder.py."""

from app.modules.visuals.prompt_templates import (
    DIAGRAM_PROMPT_TEMPLATE,
    DIAGRAM_SYSTEM_PROMPT,
    DIAGRAM_TYPE_GUIDANCE,
)


def diagram_header(diagram_type: str) -> str:
    return DIAGRAM_TYPE_GUIDANCE[diagram_type][0]


def build_diagram_prompt(
    *, diagram_type: str, subject: str, code: str | None, retrieved_context: str
) -> str:
    header, guidance = DIAGRAM_TYPE_GUIDANCE[diagram_type]
    system = DIAGRAM_SYSTEM_PROMPT.format(header=header, guidance=guidance)

    code_section = f"\nRelevant code:\n```\n{code}\n```\n" if code else ""
    context_section = f"Reference material:\n{retrieved_context}\n" if retrieved_context else ""

    return DIAGRAM_PROMPT_TEMPLATE.format(
        system=system,
        diagram_type=diagram_type,
        subject=subject,
        code_section=code_section,
        retrieved_context=context_section,
    )
