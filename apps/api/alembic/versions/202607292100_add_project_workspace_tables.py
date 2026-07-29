"""add project workspace tables (projects, project_settings, recent_projects)

Revision ID: 202607292100
Revises: 202607291200
Create Date: 2026-07-29

Implements docs/architecture/project-workspace-v1.md: promotes the
`projects` shell drafted (but not implemented) in
docs/architecture/database-schema-v1.md into a full CRUD-able table,
and adds `project_settings` (1:1, same shape as auth's
`user_preferences`) and `recent_projects` (per-user last-viewed marker
backing the dashboard's recent-projects rail).
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "202607292100"
down_revision: str | None = "202607291200"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "projects",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "owner_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="active"),
        sa.Column("archived_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("deleted_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.CheckConstraint(
            "status IN ('active', 'archived', 'deleted')", name="ck_projects_status"
        ),
    )
    # Serves the dashboard's dominant query — "this owner's projects in
    # a given status, most-recently-updated first" — without a sort at
    # read time (docs/architecture/project-workspace-v1.md Section 2.1).
    op.create_index(
        "ix_projects_owner_status_updated", "projects", ["owner_id", "status", "updated_at"]
    )
    op.execute(
        "CREATE TRIGGER trg_projects_set_updated_at BEFORE UPDATE ON projects "
        "FOR EACH ROW EXECUTE FUNCTION set_updated_at()"
    )

    op.create_table(
        "project_settings",
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("icon", sa.String(length=16), nullable=False, server_default="📁"),
        sa.Column("color", sa.String(length=20), nullable=False, server_default="slate"),
        sa.Column("settings", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column(
            "updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.CheckConstraint(
            "color IN ('slate', 'blue', 'green', 'amber', 'rose', 'violet')",
            name="ck_project_settings_color",
        ),
    )
    op.execute(
        "CREATE TRIGGER trg_project_settings_set_updated_at BEFORE UPDATE ON project_settings "
        "FOR EACH ROW EXECUTE FUNCTION set_updated_at()"
    )

    op.create_table(
        "recent_projects",
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "last_viewed_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index(
        "ix_recent_projects_user_viewed", "recent_projects", ["user_id", "last_viewed_at"]
    )


def downgrade() -> None:
    op.drop_table("recent_projects")
    op.execute("DROP TRIGGER IF EXISTS trg_project_settings_set_updated_at ON project_settings")
    op.drop_table("project_settings")
    op.execute("DROP TRIGGER IF EXISTS trg_projects_set_updated_at ON projects")
    op.drop_table("projects")
