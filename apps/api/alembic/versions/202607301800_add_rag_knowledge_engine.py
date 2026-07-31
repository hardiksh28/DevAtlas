"""add RAG knowledge engine: project_embeddings + full-text search index

Revision ID: 202607301800
Revises: 202607301000
Create Date: 2026-07-30

Implements docs/architecture/rag-engine-v1.md. Adds `project_embeddings`
(one pgvector row per chunk, split from `project_document_chunks` per
that table's own docstring) with an HNSW cosine-distance index for
semantic search, and a GIN expression index on
`project_document_chunks.content` for the keyword half of hybrid
retrieval — no new column needed for that (see rag-engine-v1.md Section
3): the same `to_tsvector('english', content)` expression is indexed
here and reused verbatim in retrieval_service.py's query, so the planner
can use this index without a stored/generated column to keep in sync.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "202607301800"
down_revision: str | None = "202607301000"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_EMBEDDING_DIMENSIONS = 768  # must match schemas.EMBEDDING_DIMENSIONS — see that module's docstring


def upgrade() -> None:
    op.create_table(
        "project_embeddings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "chunk_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("project_document_chunks.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("embedding", Vector(_EMBEDDING_DIMENSIONS), nullable=False),
        sa.Column("model", sa.String(length=100), nullable=False),
        sa.Column(
            "created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )

    op.create_index("ix_project_embeddings_project_id", "project_embeddings", ["project_id"])
    op.execute(
        "CREATE INDEX ix_project_embeddings_embedding_hnsw ON project_embeddings "
        "USING hnsw (embedding vector_cosine_ops)"
    )

    # Keyword half of hybrid retrieval — an expression (not generated
    # column) index, so retrieval_service.py's query and this index
    # share the exact same to_tsvector(...) expression with nothing to
    # keep in sync.
    op.execute(
        "CREATE INDEX ix_project_document_chunks_content_tsv ON project_document_chunks "
        "USING gin (to_tsvector('english', content))"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_project_document_chunks_content_tsv")
    op.execute("DROP INDEX IF EXISTS ix_project_embeddings_embedding_hnsw")
    op.drop_table("project_embeddings")
