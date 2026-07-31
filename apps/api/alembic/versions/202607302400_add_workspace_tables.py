"""add interactive learning workspace tables: workspace_files + workspace_layouts

Revision ID: 202607302400
Revises: 202607302300
Create Date: 2026-07-30

Implements the persisted half of docs/architecture/interactive-workspace-v1.md:
one `workspace_files` row per file (content lives directly in Postgres,
not the ObjectStorage/MinIO abstraction — see that doc's storage-choice
section) and one 1:1 `workspace_layouts` row per project (open tabs,
panel sizes, which right-rail/bottom-panel tab is active). Deliberately
no `is_directory`/folder concept — folders are derived from `path` at
render time, same as a git tree.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "202607302400"
down_revision: str | None = "202607302300"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "workspace_files",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("path", sa.String(length=500), nullable=False),
        sa.Column("content", sa.String(), nullable=False, server_default=""),
        sa.Column("content_hash", sa.String(length=64), nullable=True),
        sa.Column("size_bytes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.UniqueConstraint("project_id", "path", name="uq_workspace_files_project_path"),
    )
    op.execute(
        "CREATE TRIGGER trg_workspace_files_set_updated_at BEFORE UPDATE ON workspace_files "
        "FOR EACH ROW EXECUTE FUNCTION set_updated_at()"
    )

    op.create_table(
        "workspace_layouts",
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("open_tabs", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column(
            "active_tab_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("workspace_files.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("panel_sizes", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("bottom_panel_visible", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("right_rail_tab", sa.String(length=20), nullable=False, server_default="lesson"),
        sa.Column(
            "bottom_panel_tab", sa.String(length=20), nullable=False, server_default="terminal"
        ),
        sa.Column(
            "updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.CheckConstraint(
            "right_rail_tab IN ('lesson', 'chat')", name="ck_workspace_layouts_right_rail_tab"
        ),
        sa.CheckConstraint(
            "bottom_panel_tab IN ('terminal', 'preview')",
            name="ck_workspace_layouts_bottom_panel_tab",
        ),
    )
    op.execute(
        "CREATE TRIGGER trg_workspace_layouts_set_updated_at BEFORE UPDATE ON workspace_layouts "
        "FOR EACH ROW EXECUTE FUNCTION set_updated_at()"
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_workspace_layouts_set_updated_at ON workspace_layouts")
    op.drop_table("workspace_layouts")
    op.execute("DROP TRIGGER IF EXISTS trg_workspace_files_set_updated_at ON workspace_files")
    op.drop_table("workspace_files")
