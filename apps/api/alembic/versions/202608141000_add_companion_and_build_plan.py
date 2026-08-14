"""add AI companion identity to users, add build_plan tables

Revision ID: 202608141000
Revises: 202608011000
Create Date: 2026-08-14

Two independent additions landing together since they're both small:
- `users.companion_name` / `companion_avatar` — the user's named,
  customized mentor persona (see app/modules/auth/models.py). Lives on
  `users`, not a separate table, because it's 1:1 scalar profile data
  with no independent lifecycle — same reasoning as `display_name`.
- `build_plans` / `build_plan_steps` — Build Mode's LLM-generated
  technical plan, structurally parallel to `roadmaps`/`milestones` but
  deliberately a separate table pair, not a reuse of those — a build
  plan's steps aren't taxonomy concepts and don't belong in the
  concept-mastery-tracking system roadmap milestones feed into.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "202608141000"
down_revision: str | None = "202608011000"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("users", sa.Column("companion_name", sa.String(length=50), nullable=True))
    op.add_column("users", sa.Column("companion_avatar", sa.String(length=30), nullable=True))

    op.create_table(
        "build_plans",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("recommended_stack", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "build_plan_steps",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "build_plan_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("build_plans.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("sequence_index", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column(
            "status",
            sa.String(length=20),
            nullable=False,
            server_default="pending",
        ),
        # "guided" = learner writes it with Socratic review, "generated" =
        # the AI wrote it — set once the learner picks a path for this
        # step, null until then. Per-step (not per-plan) because a
        # learner may reasonably want the AI to scaffold boilerplate on
        # one step and write the interesting logic themselves on another.
        sa.Column("build_mode", sa.String(length=20), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint(
            "status IN ('pending', 'in_progress', 'completed')", name="ck_build_plan_steps_status"
        ),
        sa.CheckConstraint(
            "build_mode IS NULL OR build_mode IN ('guided', 'generated')",
            name="ck_build_plan_steps_build_mode",
        ),
        sa.UniqueConstraint("build_plan_id", "sequence_index", name="uq_build_plan_steps_sequence"),
    )
    op.create_index(
        "ix_build_plan_steps_build_plan_id", "build_plan_steps", ["build_plan_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_build_plan_steps_build_plan_id", table_name="build_plan_steps")
    op.drop_table("build_plan_steps")
    op.drop_table("build_plans")
    op.drop_column("users", "companion_avatar")
    op.drop_column("users", "companion_name")
