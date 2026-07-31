"""add curriculum engine tables: roadmaps + milestones

Revision ID: 202607302100
Revises: 202607302000
Create Date: 2026-07-30

Implements the `roadmaps`/`milestones` half of ARCHITECTURE.md Section 7
— generated per project, referencing `concepts` (see
202607302000_add_taxonomy_tables.py). See docs/architecture/
curriculum-engine-v1.md for the deterministic sequencing algorithm that
populates these tables and the regenerate-without-losing-progress merge
that updates them in place.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "202607302100"
down_revision: str | None = "202607302000"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "roadmaps",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("stack", sa.String(length=50), nullable=False),
        sa.Column("stack_version", sa.String(length=20), nullable=False),
        sa.Column("experience_level", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="active"),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("estimated_total_minutes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("source_document_ids", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column(
            "created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.CheckConstraint(
            "experience_level IN ('beginner', 'intermediate', 'advanced')",
            name="ck_roadmaps_experience_level",
        ),
        sa.CheckConstraint("status IN ('active', 'archived')", name="ck_roadmaps_status"),
    )
    op.execute(
        "CREATE TRIGGER trg_roadmaps_set_updated_at BEFORE UPDATE ON roadmaps "
        "FOR EACH ROW EXECUTE FUNCTION set_updated_at()"
    )

    op.create_table(
        "milestones",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "roadmap_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("roadmaps.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "concept_id",
            sa.String(length=200),
            sa.ForeignKey("concepts.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("sequence_index", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="locked"),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("estimated_minutes", sa.Integer(), nullable=False),
        sa.Column("lesson_content", postgresql.JSONB(), nullable=True),
        sa.Column("content_version", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("content_generated_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("started_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("completed_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.CheckConstraint(
            "status IN ('locked', 'available', 'in_progress', 'completed')",
            name="ck_milestones_status",
        ),
        sa.UniqueConstraint("roadmap_id", "concept_id", name="uq_milestones_roadmap_concept"),
    )
    op.create_index("ix_milestones_roadmap_sequence", "milestones", ["roadmap_id", "sequence_index"])
    op.execute(
        "CREATE TRIGGER trg_milestones_set_updated_at BEFORE UPDATE ON milestones "
        "FOR EACH ROW EXECUTE FUNCTION set_updated_at()"
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_milestones_set_updated_at ON milestones")
    op.drop_table("milestones")
    op.execute("DROP TRIGGER IF EXISTS trg_roadmaps_set_updated_at ON roadmaps")
    op.drop_table("roadmaps")
