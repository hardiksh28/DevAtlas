"""Knowledge System — Documentation Ingestion Engine + RAG Knowledge
Engine models.

Implements the `project_documents` shell reserved (but not built) in
ARCHITECTURE.md Section 7, plus `ingestion_jobs` (one row per user-
submitted upload/repo/website request), `project_document_chunks` (the
chunked, cleaned, metadata-tagged text the ingestion pipeline produces),
and `project_embeddings` (one vector per chunk, added in this pass — see
docs/architecture/rag-engine-v1.md). `project_embeddings` was
deliberately deferred past the ingestion pass (see
docs/architecture/ingestion-engine-v1.md, "Explicitly deferred") until an
embedding model was actually chosen; `EMBEDDING_DIMENSIONS` (packages/schemas)
is that choice, shared with services/ingestion_worker so neither side can
declare a mismatched vector width.
"""

import uuid
from datetime import datetime

from pgvector.sqlalchemy import Vector
from schemas import EMBEDDING_DIMENSIONS
from sqlalchemy import CheckConstraint, ForeignKey, Index, Integer, SmallInteger, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from sqlalchemy.types import JSON

from app.core.database import Base

# JSONB on Postgres, plain JSON elsewhere — same reasoning as
# projects/models.py: lets tests/conftest.py's SQLite fallback engine
# create these tables at all.
_JSONB_OR_JSON = JSON().with_variant(JSONB(), "postgresql")

_SOURCE_TYPES = "('markdown_file', 'pdf_file', 'github_repo', 'website')"


class IngestionJob(Base):
    """One user-submitted ingestion request — an upload, a GitHub repo
    URL, or a documentation website URL. For uploads the API already
    knows the single resulting document; for github_repo/website the
    worker's `discover_*` job must crawl before any `ProjectDocument`
    exists, which is what `status='discovering'` and
    `documents_discovered` (written once, after enumeration finishes)
    are for — see ingestion-engine-v1.md Section 4 for why the discovery
    count is written in one shot rather than incremented as it goes.
    """

    __tablename__ = "ingestion_jobs"
    __table_args__ = (
        CheckConstraint(f"source_type IN {_SOURCE_TYPES}", name="ck_ingestion_jobs_source_type"),
        CheckConstraint(
            "status IN ('queued', 'discovering', 'processing', 'completed', "
            "'completed_with_errors', 'failed')",
            name="ck_ingestion_jobs_status",
        ),
        Index("ix_ingestion_jobs_project_created", "project_id", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))
    requested_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))

    source_type: Mapped[str] = mapped_column(String(20))
    # The raw submission — {"url": "..."} for github_repo/website,
    # {"filename": "...", "content_type": "..."} for uploads. Kept for
    # provenance/replay (e.g. a future "re-crawl this job" action)
    # without needing a second table shaped around each source type.
    source_input: Mapped[dict] = mapped_column(_JSONB_OR_JSON, server_default="{}")

    status: Mapped[str] = mapped_column(String(30), server_default="queued")
    error_code: Mapped[str | None] = mapped_column(String(50), default=None)
    error_message: Mapped[str | None] = mapped_column(String, default=None)

    documents_discovered: Mapped[int] = mapped_column(Integer, server_default="0")
    documents_succeeded: Mapped[int] = mapped_column(Integer, server_default="0")
    documents_failed: Mapped[int] = mapped_column(Integer, server_default="0")
    # arq's own retry counter is per-job-function-call, not per logical
    # ingestion request — this tracks retries of the *discovery* step
    # specifically (process_document retries are tracked on the
    # ProjectDocument row instead, since that's the unit that fails).
    attempts: Mapped[int] = mapped_column(SmallInteger, server_default="0")

    started_at: Mapped[datetime | None] = mapped_column(default=None)
    completed_at: Mapped[datetime | None] = mapped_column(default=None)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now())

    documents: Mapped[list["ProjectDocument"]] = relationship(back_populates="ingestion_job")


class ProjectDocument(Base):
    """One document produced by an ingestion job: the whole file for a
    markdown/PDF upload, or one file/page for a github_repo/website job
    that fans out into many. `source_path` + `source_type` scoped to
    `project_id` is the natural identity of "this doc, in this
    project" — enforced as an application-layer invariant in service.py
    (check-then-upsert), not a DB partial-unique index, matching
    `password_reset_tokens`' "only one active token" precedent
    (database-schema-v1.md) rather than fighting SQLite's partial-index
    support in the test fallback engine.
    """

    __tablename__ = "project_documents"
    __table_args__ = (
        CheckConstraint(f"source_type IN {_SOURCE_TYPES}", name="ck_project_documents_source_type"),
        CheckConstraint(
            "status IN ('pending', 'validating', 'parsing', 'cleaning', 'chunking', "
            "'extracting_metadata', 'queued_for_embedding', 'completed', 'failed')",
            name="ck_project_documents_status",
        ),
        Index(
            "ix_project_documents_project_path", "project_id", "source_type", "source_path"
        ),
        Index("ix_project_documents_job", "ingestion_job_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))
    ingestion_job_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("ingestion_jobs.id", ondelete="CASCADE")
    )

    source_type: Mapped[str] = mapped_column(String(20))
    # Filename (upload), repo-relative path (github_repo), or page URL
    # (website) — the thing a human would recognize as "which doc is
    # this" within the project.
    source_path: Mapped[str] = mapped_column(String(2048))
    # Canonical fetch URL (GitHub raw URL / website page URL). NULL for
    # direct uploads — there's nothing to re-fetch from.
    source_url: Mapped[str | None] = mapped_column(String(2048), default=None)
    title: Mapped[str | None] = mapped_column(String(500), default=None)

    checksum: Mapped[str] = mapped_column(String(64))  # sha256 of raw fetched bytes
    mime_type: Mapped[str] = mapped_column(String(100))
    byte_size: Mapped[int] = mapped_column(Integer, server_default="0")
    # Object storage key for the *raw* fetched bytes — provenance and
    # what lets reprocessing skip re-fetching from GitHub/the website.
    # NULL until the worker's fetch step completes (uploads get this
    # written synchronously at upload time instead — see knowledge/service.py).
    raw_storage_key: Mapped[str | None] = mapped_column(String(1024), default=None)

    status: Mapped[str] = mapped_column(String(30), server_default="pending")
    error_code: Mapped[str | None] = mapped_column(String(50), default=None)
    error_message: Mapped[str | None] = mapped_column(String, default=None)
    chunk_count: Mapped[int] = mapped_column(Integer, server_default="0")

    # Document-level metadata: page_count (PDF), heading_outline
    # (markdown), repo_ref/commit_sha (github_repo), last_modified
    # (website Last-Modified header) — see ingestion-engine-v1.md's
    # metadata strategy section for the full field list per source type.
    doc_metadata: Mapped[dict] = mapped_column(_JSONB_OR_JSON, server_default="{}")

    # Soft delete — same rationale as Project: a document a learner
    # removed from their corpus should be recoverable, not gone.
    deleted_at: Mapped[datetime | None] = mapped_column(default=None)

    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now())

    ingestion_job: Mapped["IngestionJob"] = relationship(back_populates="documents")
    chunks: Mapped[list["ProjectDocumentChunk"]] = relationship(
        back_populates="document", cascade="all, delete-orphan"
    )


class ProjectDocumentChunk(Base):
    """One chunk of cleaned text plus the metadata that lets it be
    presented or embedded meaningfully. No vector column *here* — the
    embedding lives in the separate `ProjectEmbedding` table below,
    mirroring the global corpus's `global_documents`/`global_embeddings`
    split (ARCHITECTURE.md Section 7): a chunk's text and its embedding
    have different write patterns (text is written once by
    `process_document`; the embedding is written moments later by
    `embed_document_chunks`, and would be rewritten wholesale if the
    embedding model ever changes) and keeping them in one table would
    make "re-embed everything" mean rewriting rows that didn't actually
    change."""

    __tablename__ = "project_document_chunks"
    __table_args__ = (
        CheckConstraint(
            "embedding_status IN ('pending', 'queued', 'completed', 'skipped', 'failed')",
            name="ck_project_document_chunks_embedding_status",
        ),
        Index("ix_project_document_chunks_document_index", "document_id", "chunk_index", unique=True),
        # The exact query a future embedding worker needs — "give me
        # this project's chunks still waiting to be embedded" — built
        # now even though the consumer doesn't exist yet, matching the
        # projects module's own "index for the query the next known
        # consumer will need" habit.
        Index("ix_project_document_chunks_project_embedding_status", "project_id", "embedding_status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("project_documents.id", ondelete="CASCADE")
    )
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))

    chunk_index: Mapped[int] = mapped_column(Integer)
    content: Mapped[str] = mapped_column(String)
    token_count: Mapped[int] = mapped_column(Integer)
    char_count: Mapped[int] = mapped_column(Integer)

    # Breadcrumb of open headings at this chunk, e.g. ["Installation",
    # "Requirements"] — see chunking.py. Empty list for PDF chunks
    # (page_number in `chunk_metadata` is the section unit there instead).
    heading_path: Mapped[list] = mapped_column(_JSONB_OR_JSON, server_default="[]")
    # page_number (PDF), url_anchor (website), code_language / is_code_heavy
    # — see ingestion-engine-v1.md's metadata strategy section.
    chunk_metadata: Mapped[dict] = mapped_column(_JSONB_OR_JSON, server_default="{}")
    content_hash: Mapped[str] = mapped_column(String(64))  # sha256 of `content`

    embedding_status: Mapped[str] = mapped_column(String(20), server_default="pending")

    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    document: Mapped["ProjectDocument"] = relationship(back_populates="chunks")
    embedding: Mapped["ProjectEmbedding | None"] = relationship(
        back_populates="chunk", uselist=False, cascade="all, delete-orphan"
    )


class ProjectEmbedding(Base):
    """One embedding vector per chunk — 1:1, split from
    `ProjectDocumentChunk` for the reasons in that class's docstring.

    No SQLite variant for the `Vector` column (unlike `_JSONB_OR_JSON`
    elsewhere in this file): pgvector is a hard requirement for this
    feature (semantic/hybrid search needs a real `<=>` cosine-distance
    operator and an ANN index, neither of which SQLite can ever provide),
    not a nice-to-have this module works around for tests. SQLite's
    permissive type affinity happens to accept the `VECTOR(n)` column
    type at `CREATE TABLE` time (so this table doesn't break the shared
    SQLite test fixture other modules' tests rely on), but any test that
    actually needs real similarity ordering runs against Postgres only —
    see tests/test_retrieval_service.py.
    """

    __tablename__ = "project_embeddings"
    __table_args__ = (Index("ix_project_embeddings_project_id", "project_id"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # 1:1 with the chunk — a chunk is re-embedded in place (delete +
    # insert, see retrieval/embedding_service.py), never given a second
    # embedding row, so this FK is unique rather than a plain index.
    chunk_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("project_document_chunks.id", ondelete="CASCADE"), unique=True
    )
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))

    embedding: Mapped[list[float]] = mapped_column(Vector(EMBEDDING_DIMENSIONS))
    # Which model produced this vector — not read by any query in this
    # pass, but without it there's no way to tell "stale" embeddings
    # (produced by a since-replaced model) apart from current ones when
    # a future migration changes OLLAMA_EMBEDDING_MODEL.
    model: Mapped[str] = mapped_column(String(100))

    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    chunk: Mapped["ProjectDocumentChunk"] = relationship(back_populates="embedding")
