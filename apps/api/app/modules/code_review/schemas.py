"""Code Review Engine — request/response schemas.

`ReviewOutput` (and its `CommentOutput` children) is validated twice,
same convention as curriculum's `LessonContent`: once here as the LLM's
structured-output contract (content_builder.parse_review_output
validates the raw JSON against it), and implicitly again on the way out
since `ReviewDetailRead` is built from the persisted rows, not from
`ReviewOutput` directly.
"""

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

ReviewCategory = Literal[
    "correctness",
    "bug",
    "readability",
    "maintainability",
    "security",
    "performance",
    "scalability",
    "best_practice",
]
ReviewSeverity = Literal["info", "minor", "major", "critical"]


class SubmitReviewRequest(BaseModel):
    code: str = Field(..., min_length=1, max_length=20000)
    language: str = Field(..., min_length=1, max_length=50)
    file_path: str | None = Field(None, max_length=500)
    milestone_id: uuid.UUID | None = None

    @field_validator("code")
    @classmethod
    def _code_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("code cannot be blank")
        return value

    @field_validator("language")
    @classmethod
    def _normalize_language(cls, value: str) -> str:
        stripped = value.strip().lower()
        if not stripped:
            raise ValueError("language cannot be blank")
        return stripped


class CommentOutput(BaseModel):
    """One inline comment as the LLM must produce it."""

    file_path: str = Field(..., min_length=1)
    line_start: int = Field(..., ge=1)
    line_end: int = Field(..., ge=1)
    category: ReviewCategory
    severity: ReviewSeverity
    body: str = Field(..., min_length=1)
    suggestion: str | None = None
    concept_tags: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _line_range_valid(self) -> "CommentOutput":
        if self.line_end < self.line_start:
            raise ValueError("line_end must be >= line_start")
        return self


class ReviewOutput(BaseModel):
    """The LLM's full structured response shape."""

    overall_score: int = Field(..., ge=0, le=100)
    summary: str = Field(..., min_length=1)
    strengths: list[str] = Field(default_factory=list)
    comments: list[CommentOutput] = Field(default_factory=list)
    refactoring_ideas: list[str] = Field(default_factory=list)


class ReviewCommentRead(BaseModel):
    id: uuid.UUID
    file_path: str
    line_start: int
    line_end: int
    category: str
    severity: str
    body: str
    suggestion: str | None
    concept_tags: list[str]

    @classmethod
    def from_model(cls, comment: "object") -> "ReviewCommentRead":
        return cls(
            id=comment.id,  # type: ignore[attr-defined]
            file_path=comment.file_path,  # type: ignore[attr-defined]
            line_start=comment.line_start,  # type: ignore[attr-defined]
            line_end=comment.line_end,  # type: ignore[attr-defined]
            category=comment.category,  # type: ignore[attr-defined]
            severity=comment.severity,  # type: ignore[attr-defined]
            body=comment.body,  # type: ignore[attr-defined]
            suggestion=comment.suggestion,  # type: ignore[attr-defined]
            concept_tags=comment.concept_tags,  # type: ignore[attr-defined]
        )


class ReviewDetailRead(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    milestone_id: uuid.UUID | None
    language: str
    file_path: str | None
    overall_score: int
    summary: str
    strengths: list[str]
    refactoring_ideas: list[str]
    comments: list[ReviewCommentRead]
    created_at: datetime

    @classmethod
    def from_model(cls, review: "object") -> "ReviewDetailRead":
        return cls(
            id=review.id,  # type: ignore[attr-defined]
            project_id=review.project_id,  # type: ignore[attr-defined]
            milestone_id=review.milestone_id,  # type: ignore[attr-defined]
            language=review.language,  # type: ignore[attr-defined]
            file_path=review.file_path,  # type: ignore[attr-defined]
            overall_score=review.overall_score,  # type: ignore[attr-defined]
            summary=review.summary,  # type: ignore[attr-defined]
            strengths=review.strengths,  # type: ignore[attr-defined]
            refactoring_ideas=review.refactoring_ideas,  # type: ignore[attr-defined]
            comments=[ReviewCommentRead.from_model(c) for c in review.comments],  # type: ignore[attr-defined]
            created_at=review.created_at,  # type: ignore[attr-defined]
        )


class ReviewSummaryRead(BaseModel):
    """Lighter row for the history list — no code, no comment bodies, so
    listing a project's review history doesn't ship every past
    submission's full text on every page load."""

    id: uuid.UUID
    milestone_id: uuid.UUID | None
    language: str
    file_path: str | None
    overall_score: int
    summary: str
    comment_count: int
    created_at: datetime

    @classmethod
    def from_model(cls, review: "object", comment_count: int) -> "ReviewSummaryRead":
        return cls(
            id=review.id,  # type: ignore[attr-defined]
            milestone_id=review.milestone_id,  # type: ignore[attr-defined]
            language=review.language,  # type: ignore[attr-defined]
            file_path=review.file_path,  # type: ignore[attr-defined]
            overall_score=review.overall_score,  # type: ignore[attr-defined]
            summary=review.summary,  # type: ignore[attr-defined]
            comment_count=comment_count,
            created_at=review.created_at,  # type: ignore[attr-defined]
        )


class ReviewListResponse(BaseModel):
    items: list[ReviewSummaryRead]
    total: int
    limit: int
    offset: int
