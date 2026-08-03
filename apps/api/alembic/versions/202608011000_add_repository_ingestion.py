"""add repository ingestion engine table: repository_connections

Revision ID: 202608011000
Revises: 202607302600
Create Date: 2026-08-01

Fills in the `repository_connections` FK slot `projects/models.py`'s
`Project` docstring reserved. One row per project (1:1, see
app/modules/repo_ingestion/models.py) holding the last successful
ingestion's structural metadata — language, framework, package manager,
file/folder counts — for a project's connected public GitHub repo.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "202608011000"
down_revision: str | None = "202607302600"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "repository_connections",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("repo_url", sa.String(length=2048), nullable=False),
        sa.Column("owner", sa.String(length=255), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("default_branch", sa.String(length=255), nullable=False),
        sa.Column("primary_language", sa.String(length=100), nullable=True),
        sa.Column("framework", sa.String(length=100), nullable=True),
        sa.Column("package_manager", sa.String(length=20), nullable=True),
        sa.Column("total_files", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_folders", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("repo_metadata", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("repository_connections")
