"""add taxonomy & concept graph tables

Revision ID: 202607302000
Revises: 202607301800
Create Date: 2026-07-30

Implements the `concepts` half of ARCHITECTURE.md Section 7's
"Curriculum & Taxonomy" domain (`stack_versions` is folded into
`concepts.stack_version` rather than a separate table — see
taxonomy/models.py's docstring for why a surrogate table wasn't
justified yet). `concept_prerequisites` is the self-referencing edge
table the architecture doc calls for. Content is seeded from curated
YAML (packages/taxonomy-data/concepts/) via scripts/seed_taxonomy.py,
never written by request handlers — see taxonomy-engine-v1.md /
curriculum-engine-v1.md.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "202607302000"
down_revision: str | None = "202607301800"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_SEVERITY_CHECK = "severity IN ('foundational', 'intermediate', 'advanced')"


def upgrade() -> None:
    op.create_table(
        "concepts",
        sa.Column("id", sa.String(length=200), primary_key=True),
        sa.Column("stack", sa.String(length=50), nullable=False),
        sa.Column("stack_version", sa.String(length=20), nullable=False),
        sa.Column("severity", sa.String(length=20), nullable=False),
        sa.Column("mastery_criteria", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("common_misconceptions", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("docs", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column(
            "created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.CheckConstraint(_SEVERITY_CHECK, name="ck_concepts_severity"),
    )
    op.create_index("ix_concepts_stack_version", "concepts", ["stack", "stack_version"])
    op.execute(
        "CREATE TRIGGER trg_concepts_set_updated_at BEFORE UPDATE ON concepts "
        "FOR EACH ROW EXECUTE FUNCTION set_updated_at()"
    )

    op.create_table(
        "concept_prerequisites",
        sa.Column(
            "concept_id",
            sa.String(length=200),
            sa.ForeignKey("concepts.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "prerequisite_id",
            sa.String(length=200),
            sa.ForeignKey("concepts.id", ondelete="CASCADE"),
            primary_key=True,
        ),
    )
    op.create_index(
        "ix_concept_prerequisites_prerequisite", "concept_prerequisites", ["prerequisite_id"]
    )


def downgrade() -> None:
    op.drop_table("concept_prerequisites")
    op.execute("DROP TRIGGER IF EXISTS trg_concepts_set_updated_at ON concepts")
    op.drop_table("concepts")
