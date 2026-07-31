"""add mentoring engine tables: conversations + messages

Revision ID: 202607302200
Revises: 202607302100
Create Date: 2026-07-30

Implements the conversational-memory half of ARCHITECTURE.md's
"Mentoring / Hint Ladder Engine" (Section 3) — see
docs/architecture/mentor-engine-v1.md. One `Conversation` per project;
`Message.milestone_id` optionally anchors a turn to a curriculum
concept (see 202607302100_add_curriculum_engine_tables.py). The formal
Effort-Evidence-gated hint-ladder rung state machine is explicitly
deferred — this is the conversational memory/prompting substrate it
would sit on top of.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "202607302200"
down_revision: str | None = "202607302100"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "conversations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("summary", sa.String(), nullable=True),
        sa.Column("summarized_up_to", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )
    op.execute(
        "CREATE TRIGGER trg_conversations_set_updated_at BEFORE UPDATE ON conversations "
        "FOR EACH ROW EXECUTE FUNCTION set_updated_at()"
    )

    op.create_table(
        "messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "conversation_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("conversations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "milestone_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("milestones.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("content", sa.String(), nullable=False),
        sa.Column("detected_misconceptions", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column(
            "created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.CheckConstraint("role IN ('user', 'assistant')", name="ck_messages_role"),
    )
    op.create_index("ix_messages_conversation_created", "messages", ["conversation_id", "created_at"])


def downgrade() -> None:
    op.drop_table("messages")
    op.execute("DROP TRIGGER IF EXISTS trg_conversations_set_updated_at ON conversations")
    op.drop_table("conversations")
