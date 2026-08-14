"""Build Plan — Build Mode's LLM-generated technical plan.

Structurally parallel to curriculum's Roadmap/Milestone (one plan per
project, ordered steps) but a deliberately separate table pair — a
build plan's steps are concrete implementation tasks the LLM proposed
from a free-text project description, not taxonomy concepts, and don't
belong in the concept-mastery-tracking system Roadmap/Milestone feed
into (progress_tracking, ARCHITECTURE.md Section 7).
"""

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from sqlalchemy.types import JSON, Text

from app.core.database import Base

_JSONB_OR_JSON = JSON().with_variant(JSONB(), "postgresql")

STEP_STATUSES = ("pending", "in_progress", "completed")
STEP_BUILD_MODES = ("guided", "generated")


class BuildPlan(Base):
    """One active plan per project — regeneration replaces `summary`,
    `recommended_stack`, and every step in place (full replace, not a
    progress-preserving merge like Roadmap's regeneration; a build
    plan's steps aren't identified by anything as stable as a concept_id
    to diff against — see service.py for the explicit trade-off)."""

    __tablename__ = "build_plans"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), unique=True
    )

    summary: Mapped[str] = mapped_column(Text)
    # [{"name": str, "reason": str}, ...] — validated shape lives in
    # schemas.RecommendedStackItem; stored as plain JSON since it's never
    # queried, only round-tripped.
    recommended_stack: Mapped[list] = mapped_column(_JSONB_OR_JSON, server_default="[]")

    version: Mapped[int] = mapped_column(Integer, server_default="1")

    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now())

    steps: Mapped[list["BuildPlanStep"]] = relationship(
        back_populates="build_plan",
        cascade="all, delete-orphan",
        order_by="BuildPlanStep.sequence_index",
    )


class BuildPlanStep(Base):
    __tablename__ = "build_plan_steps"
    __table_args__ = (
        CheckConstraint(f"status IN {STEP_STATUSES!r}", name="ck_build_plan_steps_status"),
        CheckConstraint(
            f"build_mode IS NULL OR build_mode IN {STEP_BUILD_MODES!r}",
            name="ck_build_plan_steps_build_mode",
        ),
        UniqueConstraint("build_plan_id", "sequence_index", name="uq_build_plan_steps_sequence"),
        Index("ix_build_plan_steps_build_plan_id", "build_plan_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    build_plan_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("build_plans.id", ondelete="CASCADE"))

    sequence_index: Mapped[int] = mapped_column(Integer)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), server_default="pending")
    # Null until the learner picks a path for this step (see
    # schemas.UpdateStepModeRequest) — "guided" (Socratic review, learner
    # writes it) or "generated" (the AI writes it). Per-step, not
    # per-plan: a learner may reasonably want boilerplate generated on
    # one step and to write the interesting logic themselves on another.
    build_mode: Mapped[str | None] = mapped_column(String(20), default=None)

    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now())

    build_plan: Mapped["BuildPlan"] = relationship(back_populates="steps")
