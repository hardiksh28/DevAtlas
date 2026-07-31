"""Mentoring Engine — LLM response parsing.

Same defensive shape as curriculum/content_builder.py's
`parse_milestone_content` (strip an accidental code fence, parse JSON,
validate against the Pydantic schema) — re-written small here rather
than imported, since modules in this codebase don't reach into each
other's internals (the same boundary convention services/ingestion_worker
follows relative to apps/api).
"""

import json
import re

from app.modules.mentoring.schemas import MentorReply

_CODE_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.MULTILINE)


class MentorReplyParseError(Exception):
    """Raised when the LLM's response isn't valid JSON, or doesn't match
    MentorReply's shape. Not a MentoringError subclass — this module has
    no FastAPI/HTTP awareness; service.py decides whether to retry or
    translate this into MentorReplyGenerationError."""


def parse_mentor_reply(raw: str) -> MentorReply:
    cleaned = _CODE_FENCE_RE.sub("", raw.strip()).strip()
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise MentorReplyParseError(f"Response was not valid JSON: {exc}") from exc

    try:
        return MentorReply.model_validate(data)
    except Exception as exc:  # pydantic.ValidationError, deliberately broad at the boundary
        raise MentorReplyParseError(f"Response JSON didn't match the expected shape: {exc}") from exc
