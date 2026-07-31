"""add progress & weakness tracking tables: mastery_profiles,
mastery_evidence, quiz_attempts, activity_events

Revision ID: 202607302600
Revises: 202607302500
Create Date: 2026-07-30

Implements the persisted half of ARCHITECTURE.md's "Progress & Weakness
Tracking Service" (Section 3) — one MasteryProfile per (user, concept)
pair with its append-only MasteryEvidence history, plus QuizAttempt
(nothing previously persisted a quiz submission) and ActivityEvent (one
generic append-only log powering streaks/time-spent/coding-activity
analytics — see app/modules/progress_tracking/models.py's docstring).
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "202607302600"
down_revision: str | None = "202607302500"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "mastery_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column(
            "concept_id", sa.String(length=200), sa.ForeignKey("concepts.id", ondelete="RESTRICT"), nullable=False
        ),
        sa.Column("confidence_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("resolution_state", sa.String(length=20), nullable=False, server_default="detected"),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint(
            "resolution_state IN ('detected', 'practicing', 'improving', 'mastered', 'monitor')",
            name="ck_mastery_profiles_state",
        ),
        sa.CheckConstraint(
            "confidence_score >= 0 AND confidence_score <= 1", name="ck_mastery_profiles_confidence_range"
        ),
        sa.UniqueConstraint("user_id", "concept_id", name="uq_mastery_profiles_user_concept"),
    )

    op.create_table(
        "mastery_evidence",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "profile_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("mastery_profiles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("source", sa.String(length=20), nullable=False),
        sa.Column("signal", sa.String(length=20), nullable=False),
        sa.Column("weight", sa.Float(), nullable=False),
        sa.Column("note", sa.String(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint(
            "source IN ('milestone', 'quiz', 'code_review')", name="ck_mastery_evidence_source"
        ),
        sa.CheckConstraint("signal IN ('positive', 'negative')", name="ck_mastery_evidence_signal"),
    )
    op.create_index(
        "ix_mastery_evidence_profile_created", "mastery_evidence", ["profile_id", "created_at"]
    )

    op.create_table(
        "quiz_attempts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column(
            "milestone_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("milestones.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("total", sa.Integer(), nullable=False),
        sa.Column("answers", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_quiz_attempts_user_milestone", "quiz_attempts", ["user_id", "milestone_id"])

    op.create_table(
        "activity_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("event_type", sa.String(length=30), nullable=False),
        sa.Column("occurred_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
        sa.Column("event_metadata", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.CheckConstraint(
            "event_type IN ('milestone_completed', 'quiz_submitted', 'code_review_submitted')",
            name="ck_activity_events_type",
        ),
    )
    op.create_index("ix_activity_events_user_occurred", "activity_events", ["user_id", "occurred_at"])


def downgrade() -> None:
    op.drop_table("activity_events")
    op.drop_table("quiz_attempts")
    op.drop_table("mastery_evidence")
    op.drop_table("mastery_profiles")
