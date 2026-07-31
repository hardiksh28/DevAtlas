"""Curriculum Engine — milestone narration prompt building + response
parsing.

Pure functions, no DB/network I/O — `service.py` is responsible for
gathering RAG context and calling the LLM gateway; this module only
turns already-fetched inputs into a prompt string, and turns the raw
LLM response back into a validated `LessonContent`. Kept pure for the
same reason sequencing.py is: it's directly unit-testable without a
running LLM or database (see tests/test_content_builder.py).
"""

import json
import re

from app.modules.curriculum.prompt_templates import (
    MILESTONE_CONTENT_PROMPT_TEMPLATE,
    MILESTONE_SYSTEM_PROMPT,
)
from app.modules.curriculum.schemas import Exercise, LessonContent, QuizQuestion

_CODE_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.MULTILINE)


class LessonContentParseError(Exception):
    """Raised when the LLM's response isn't valid JSON, or is valid JSON
    that doesn't match LessonContent's shape. Deliberately not a
    CurriculumError subclass — this module has no FastAPI/HTTP
    awareness; service.py decides whether to retry or translate this
    into a ContentGenerationError.
    """


def build_milestone_prompt(
    *,
    concept_id: str,
    severity: str,
    mastery_criteria: list[str],
    common_misconceptions: list[str],
    experience_level: str,
    context_text: str,
) -> str:
    """Builds the full prompt for one milestone's narration. `context_text`
    is the already-assembled RAG context (knowledge.retrieval.context_builder
    output, or "" if the project has no ingested documentation relevant to
    this concept) — this function doesn't know or care where it came from.
    """
    return MILESTONE_CONTENT_PROMPT_TEMPLATE.format(
        system=MILESTONE_SYSTEM_PROMPT,
        concept_id=concept_id,
        severity=severity,
        experience_level=experience_level,
        mastery_criteria="\n".join(f"- {m}" for m in mastery_criteria) or "(none provided)",
        common_misconceptions="\n".join(f"- {m}" for m in common_misconceptions) or "(none provided)",
        context=context_text or "(no project documentation available for this concept)",
    )


def _strip_code_fence(raw: str) -> str:
    # Models frequently wrap JSON in a ```json ... ``` fence despite
    # instructions not to — stripped defensively rather than treated as
    # an immediate parse failure, since it's the single most common,
    # entirely benign deviation.
    return _CODE_FENCE_RE.sub("", raw.strip()).strip()


def _normalize(text: str) -> str:
    return " ".join(text.strip().lower().split())


def _dedupe_exercises(exercises: list[Exercise]) -> list[Exercise]:
    seen: set[str] = set()
    deduped = []
    for ex in exercises:
        key = _normalize(ex.prompt)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(ex)
    return deduped


def _dedupe_quiz(quiz: list[QuizQuestion]) -> list[QuizQuestion]:
    seen: set[str] = set()
    deduped = []
    for q in quiz:
        key = _normalize(q.question)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(q)
    return deduped


def parse_milestone_content(raw: str) -> LessonContent:
    """Parses + validates the LLM's raw response, then de-dupes exercises
    and quiz questions by exact-normalized-text match (dropping the
    duplicate rather than erroring — near-duplicate LLM output is common
    and low-stakes, and a milestone with 3 good exercises instead of 4
    isn't a failure worth surfacing to the caller).
    """
    cleaned = _strip_code_fence(raw)
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise LessonContentParseError(f"Response was not valid JSON: {exc}") from exc

    try:
        content = LessonContent.model_validate(data)
    except Exception as exc:  # pydantic.ValidationError, deliberately broad at the boundary
        raise LessonContentParseError(f"Response JSON didn't match the expected shape: {exc}") from exc

    return LessonContent(
        explanation=content.explanation,
        key_points=content.key_points,
        exercises=_dedupe_exercises(content.exercises),
        quiz=_dedupe_quiz(content.quiz),
    )
