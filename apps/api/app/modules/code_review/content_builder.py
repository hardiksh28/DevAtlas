"""Code Review Engine — LLM response parsing.

Same defensive shape as mentoring/content_builder.py (strip an
accidental code fence, parse JSON, validate against the Pydantic
schema), plus two review-specific guards that back up the prompt's own
instructions rather than trusting them:

1. **Line-range grounding.** Any comment whose line_start/line_end
   falls outside the code that was actually submitted is dropped, not
   clamped — a hallucinated line reference is worse than a missing
   comment. This is the enforced half of prompt_templates.py's
   "only cite line numbers that appear below" instruction.
2. **Overwhelm control.** Comments are ranked by severity (critical
   first) and truncated to `max_comments`, backing up the prompt's own
   count request in case the model ignores it.
"""

import json
import re

from app.modules.code_review.schemas import CommentOutput, ReviewOutput

_CODE_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.MULTILINE)
_SEVERITY_RANK = {"critical": 0, "major": 1, "minor": 2, "info": 3}


class ReviewParseError(Exception):
    """Raised when the LLM's response isn't valid JSON, or doesn't match
    ReviewOutput's shape. Not a CodeReviewError subclass — this module
    has no FastAPI/HTTP awareness; service.py decides whether to retry
    or translate this into ReviewGenerationError."""


def _in_range(comment: CommentOutput, total_lines: int) -> bool:
    return 1 <= comment.line_start <= comment.line_end <= total_lines


def _rank_and_truncate(comments: list[CommentOutput], max_comments: int) -> list[CommentOutput]:
    ranked = sorted(comments, key=lambda c: (_SEVERITY_RANK.get(c.severity, 99), c.line_start))
    return ranked[:max_comments]


def parse_review_output(raw: str, *, total_lines: int, max_comments: int) -> ReviewOutput:
    cleaned = _CODE_FENCE_RE.sub("", raw.strip()).strip()
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise ReviewParseError(f"Response was not valid JSON: {exc}") from exc

    try:
        parsed = ReviewOutput.model_validate(data)
    except Exception as exc:  # pydantic.ValidationError, deliberately broad at the boundary
        raise ReviewParseError(f"Response JSON didn't match the expected shape: {exc}") from exc

    grounded = [c for c in parsed.comments if _in_range(c, total_lines)]
    return ReviewOutput(
        overall_score=parsed.overall_score,
        summary=parsed.summary,
        strengths=parsed.strengths,
        comments=_rank_and_truncate(grounded, max_comments),
        refactoring_ideas=parsed.refactoring_ideas,
    )
