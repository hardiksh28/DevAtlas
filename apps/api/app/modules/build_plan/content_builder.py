"""Build Plan — prompt building + response parsing.

Pure functions, no DB/network I/O — same split as
curriculum/content_builder.py, for the same reason: directly
unit-testable without a running LLM or database.
"""

import json
import re

from app.modules.build_plan.prompt_templates import (
    BUILD_PLAN_PROMPT_TEMPLATE,
    BUILD_PLAN_SYSTEM_PROMPT,
)
from app.modules.build_plan.schemas import GeneratedPlanContent

_CODE_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.MULTILINE)


class PlanContentParseError(Exception):
    """Raised when the LLM's response isn't valid JSON, or is valid JSON
    that doesn't match GeneratedPlanContent's shape. Deliberately not a
    BuildPlanError subclass — this module has no FastAPI/HTTP awareness;
    service.py decides whether to retry or translate this into a
    PlanGenerationError.
    """


def build_plan_prompt(
    *, project_name: str, project_description: str, additional_context: str | None
) -> str:
    description = project_description.strip()
    if additional_context:
        description = f"{description}\n\nAdditional context from the learner:\n{additional_context}"
    return BUILD_PLAN_PROMPT_TEMPLATE.format(
        system=BUILD_PLAN_SYSTEM_PROMPT,
        project_name=project_name,
        project_description=description,
    )


def _strip_code_fence(raw: str) -> str:
    # Models frequently wrap JSON in a ```json ... ``` fence despite
    # instructions not to — stripped defensively, same as curriculum's
    # content_builder.
    return _CODE_FENCE_RE.sub("", raw.strip()).strip()


def parse_build_plan(raw: str) -> GeneratedPlanContent:
    cleaned = _strip_code_fence(raw)
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise PlanContentParseError(f"Response was not valid JSON: {exc}") from exc

    try:
        content = GeneratedPlanContent.model_validate(data)
    except Exception as exc:  # pydantic.ValidationError, deliberately broad at the boundary
        raise PlanContentParseError(f"Response JSON didn't match the expected shape: {exc}") from exc

    if not content.steps:
        raise PlanContentParseError("Response had an empty steps list.")

    return content
