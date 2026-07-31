"""add documentation ingestion engine tables

Revision ID: 202607301000
Revises: 202607292100
Create Date: 2026-07-30

Implements docs/architecture/ingestion-engine-v1.md: promotes the
`project_documents` shell reserved (but not built) in
ARCHITECTURE.md Section 7, and adds `ingestion_jobs` (one row per
user-submitted upload/repo/website request) plus
`project_document_chunks` (chunked, cleaned, metadata-tagged text).

Deliberately does NOT add a `project_embeddings` table or any vector
column yet — see the models' module docstring and the architecture
doc's "Explicitly deferred" section; that's a separate future migration
once an embedding model is chosen.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "202607301000"
down_revision: str | None = "202607292100"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_SOURCE_TYPE_CHECK = "source_type IN ('markdown_file', 'pdf_file', 'github_repo', 'website')"


def upgrade() -> None:
    op.create_table(
        "ingestion_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "requested_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("source_type", sa.String(length=20), nullable=False),
        sa.Column("source_input", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="queued"),
        sa.Column("error_code", sa.String(length=50), nullable=True),
        sa.Column("error_message", sa.String(), nullable=True),
        sa.Column("documents_discovered", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("documents_succeeded", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("documents_failed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("attempts", sa.SmallInteger(), nullable=False, server_default="0"),
        sa.Column("started_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("completed_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.CheckConstraint(_SOURCE_TYPE_CHECK, name="ck_ingestion_jobs_source_type"),
        sa.CheckConstraint(
            "status IN ('queued', 'discovering', 'processing', 'completed', "
            "'completed_with_errors', 'failed')",
            name="ck_ingestion_jobs_status",
        ),
    )
    op.create_index("ix_ingestion_jobs_project_created", "ingestion_jobs", ["project_id", "created_at"])
    op.execute(
        "CREATE TRIGGER trg_ingestion_jobs_set_updated_at BEFORE UPDATE ON ingestion_jobs "
        "FOR EACH ROW EXECUTE FUNCTION set_updated_at()"
    )

    op.create_table(
        "project_documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "ingestion_job_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("ingestion_jobs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("source_type", sa.String(length=20), nullable=False),
        sa.Column("source_path", sa.String(length=2048), nullable=False),
        sa.Column("source_url", sa.String(length=2048), nullable=True),
        sa.Column("title", sa.String(length=500), nullable=True),
        sa.Column("checksum", sa.String(length=64), nullable=False),
        sa.Column("mime_type", sa.String(length=100), nullable=False),
        sa.Column("byte_size", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("raw_storage_key", sa.String(length=1024), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="pending"),
        sa.Column("error_code", sa.String(length=50), nullable=True),
        sa.Column("error_message", sa.String(), nullable=True),
        sa.Column("chunk_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("doc_metadata", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("deleted_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.CheckConstraint(_SOURCE_TYPE_CHECK, name="ck_project_documents_source_type"),
        sa.CheckConstraint(
            "status IN ('pending', 'validating', 'parsing', 'cleaning', 'chunking', "
            "'extracting_metadata', 'queued_for_embedding', 'completed', 'failed')",
            name="ck_project_documents_status",
        ),
    )
    op.create_index(
        "ix_project_documents_project_path",
        "project_documents",
        ["project_id", "source_type", "source_path"],
    )
    op.create_index("ix_project_documents_job", "project_documents", ["ingestion_job_id"])
    op.execute(
        "CREATE TRIGGER trg_project_documents_set_updated_at BEFORE UPDATE ON project_documents "
        "FOR EACH ROW EXECUTE FUNCTION set_updated_at()"
    )

    op.create_table(
        "project_document_chunks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "document_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("project_documents.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("content", sa.String(), nullable=False),
        sa.Column("token_count", sa.Integer(), nullable=False),
        sa.Column("char_count", sa.Integer(), nullable=False),
        sa.Column("heading_path", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("chunk_metadata", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("embedding_status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column(
            "created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.CheckConstraint(
            "embedding_status IN ('pending', 'queued', 'completed', 'skipped', 'failed')",
            name="ck_project_document_chunks_embedding_status",
        ),
    )
    op.create_index(
        "ix_project_document_chunks_document_index",
        "project_document_chunks",
        ["document_id", "chunk_index"],
        unique=True,
    )
    op.create_index(
        "ix_project_document_chunks_project_embedding_status",
        "project_document_chunks",
        ["project_id", "embedding_status"],
    )


def downgrade() -> None:
    op.drop_table("project_document_chunks")
    op.execute("DROP TRIGGER IF EXISTS trg_project_documents_set_updated_at ON project_documents")
    op.drop_table("project_documents")
    op.execute("DROP TRIGGER IF EXISTS trg_ingestion_jobs_set_updated_at ON ingestion_jobs")
    op.drop_table("ingestion_jobs")
