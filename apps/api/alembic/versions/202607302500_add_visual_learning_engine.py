"""add visual learning engine: diagrams table + widen workspace_layouts.right_rail_tab

Revision ID: 202607302500
Revises: 202607302400
Create Date: 2026-07-30

Implements the persisted half of the Visual Learning Engine: one
`diagrams` row per generated Mermaid diagram (immutable history, same
shape as `code_reviews` — see app/modules/visuals/models.py's docstring).
Also widens workspace_layouts.right_rail_tab's check constraint to accept
'diagrams' alongside the existing 'lesson'/'chat', since the workspace UI
gains a third right-rail tab for browsing/generating diagrams.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "202607302500"
down_revision: str | None = "202607302400"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "diagrams",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "milestone_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("milestones.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("diagram_type", sa.String(length=20), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("subject", sa.String(), nullable=False),
        sa.Column("mermaid_source", sa.String(), nullable=False),
        sa.Column(
            "created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.CheckConstraint(
            "diagram_type IN ('erd', 'flowchart', 'architecture', 'state', 'sequence', 'component')",
            name="ck_diagrams_diagram_type",
        ),
    )
    op.create_index("ix_diagrams_project_created", "diagrams", ["project_id", "created_at"])

    op.drop_constraint(
        "ck_workspace_layouts_right_rail_tab", "workspace_layouts", type_="check"
    )
    op.create_check_constraint(
        "ck_workspace_layouts_right_rail_tab",
        "workspace_layouts",
        "right_rail_tab IN ('lesson', 'chat', 'diagrams')",
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_workspace_layouts_right_rail_tab", "workspace_layouts", type_="check"
    )
    op.create_check_constraint(
        "ck_workspace_layouts_right_rail_tab",
        "workspace_layouts",
        "right_rail_tab IN ('lesson', 'chat')",
    )

    op.drop_index("ix_diagrams_project_created", table_name="diagrams")
    op.drop_table("diagrams")
