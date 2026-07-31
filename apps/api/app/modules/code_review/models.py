"""Code Review Engine — models.

`CodeReview` is one submitted-code review (score, summary, strengths,
refactoring ideas); `CodeReviewComment` is one line-anchored inline
comment on it (ARCHITECTURE.md Section 3: "inline comments, a holistic
summary"). No soft delete on either — same "historical record, never
edited or removed" reasoning as mentoring's `messages` (review history
is meant to be browsable, not mutable).

The interactive discussion thread per comment (ARCHITECTURE.md Section
3) is deferred: it's gated through the Effort Evaluator, which is still
a stub with no service to call — adding thread tables now would just be
dead schema until that gate exists.
"""

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, ForeignKey, Index, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from sqlalchemy.types import JSON

from app.core.database import Base

_JSONB_OR_JSON = JSON().with_variant(JSONB(), "postgresql")

REVIEW_CATEGORIES = (
    "correctness",
    "bug",
    "readability",
    "maintainability",
    "security",
    "performance",
    "scalability",
    "best_practice",
)
REVIEW_SEVERITIES = ("info", "minor", "major", "critical")


class CodeReview(Base):
    """One review of one code submission. `code` is stored verbatim — a
    review is meaningless without the exact snapshot it was written
    against (same reasoning as keeping `content` on a mentor `Message`).
    """

    __tablename__ = "code_reviews"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))
    # Optional concept anchor, same shape as Message.milestone_id — lets
    # a review ground itself in the milestone being worked on without
    # requiring every review to be milestone-scoped.
    milestone_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("milestones.id", ondelete="SET NULL"), default=None
    )

    language: Mapped[str] = mapped_column(String(50))
    file_path: Mapped[str | None] = mapped_column(String(500), default=None)
    code: Mapped[str] = mapped_column(String)

    overall_score: Mapped[int] = mapped_column(Integer)
    summary: Mapped[str] = mapped_column(String)
    strengths: Mapped[list] = mapped_column(_JSONB_OR_JSON, server_default="[]")
    refactoring_ideas: Mapped[list] = mapped_column(_JSONB_OR_JSON, server_default="[]")

    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    comments: Mapped[list["CodeReviewComment"]] = relationship(
        back_populates="review",
        cascade="all, delete-orphan",
        order_by="CodeReviewComment.line_start",
    )


class CodeReviewComment(Base):
    """One inline, line-anchored comment. `severity` + `category` are
    plain CheckConstraint-backed strings (not a native enum type), same
    convention as every other module's closed-set string columns.
    """

    __tablename__ = "code_review_comments"
    __table_args__ = (
        CheckConstraint(
            f"category IN {REVIEW_CATEGORIES!r}", name="ck_code_review_comments_category"
        ),
        CheckConstraint(
            f"severity IN {REVIEW_SEVERITIES!r}", name="ck_code_review_comments_severity"
        ),
        Index("ix_code_review_comments_review_line", "review_id", "line_start"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    review_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("code_reviews.id", ondelete="CASCADE"))

    file_path: Mapped[str] = mapped_column(String(500))
    line_start: Mapped[int] = mapped_column(Integer)
    line_end: Mapped[int] = mapped_column(Integer)
    category: Mapped[str] = mapped_column(String(20))
    severity: Mapped[str] = mapped_column(String(20))
    body: Mapped[str] = mapped_column(String)
    suggestion: Mapped[str | None] = mapped_column(String, default=None)
    # Free-text concept ids/descriptions, not validated against the
    # taxonomy's closed set — same "free-text, not enforced" choice
    # mentoring made for detected_misconceptions, for the same reason
    # (the review LLM call has no business rejecting its own output over
    # a taxonomy mismatch; unmapped tags are a product-review concern).
    concept_tags: Mapped[list] = mapped_column(_JSONB_OR_JSON, server_default="[]")

    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    review: Mapped["CodeReview"] = relationship(back_populates="comments")
