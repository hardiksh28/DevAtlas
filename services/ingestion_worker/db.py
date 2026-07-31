"""Database access for the ingestion worker.

Plain SQLAlchemy Core against hand-mirrored `Table` objects — not the
ORM, and not a shared import of apps/api's declarative models. Alembic
(owned entirely by apps/api) is the single migration authority; these
`Table` definitions describe the same physical columns independently,
the same way settings.py's WorkerConfig independently mirrors fields
from apps/api's Settings. If the schema ever drifts, it drifts loudly
(a column-not-found error at runtime), which is the acceptable cost of
keeping the worker importable/deployable without apps/api on the path.

Every `updated_at` column is maintained by the `set_updated_at()`
Postgres trigger (apps/api/alembic/versions/202607291200_*) — this
module never sets it explicitly, on inserts or updates, from either
side of the extraction boundary.
"""

import uuid
from collections.abc import Mapping, Sequence
from typing import Any

import sqlalchemy as sa
from pgvector.sqlalchemy import Vector
from schemas import EMBEDDING_DIMENSIONS
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import create_async_engine

from settings import config

metadata = sa.MetaData()

ingestion_jobs = sa.Table(
    "ingestion_jobs",
    metadata,
    sa.Column("id", PG_UUID(as_uuid=True), primary_key=True),
    sa.Column("project_id", PG_UUID(as_uuid=True)),
    sa.Column("requested_by", PG_UUID(as_uuid=True)),
    sa.Column("source_type", sa.String(20)),
    sa.Column("source_input", JSONB),
    sa.Column("status", sa.String(30)),
    sa.Column("error_code", sa.String(50)),
    sa.Column("error_message", sa.String()),
    sa.Column("documents_discovered", sa.Integer),
    sa.Column("documents_succeeded", sa.Integer),
    sa.Column("documents_failed", sa.Integer),
    sa.Column("attempts", sa.SmallInteger),
    sa.Column("started_at", sa.TIMESTAMP(timezone=True)),
    sa.Column("completed_at", sa.TIMESTAMP(timezone=True)),
    sa.Column("created_at", sa.TIMESTAMP(timezone=True)),
    sa.Column("updated_at", sa.TIMESTAMP(timezone=True)),
)

project_documents = sa.Table(
    "project_documents",
    metadata,
    sa.Column("id", PG_UUID(as_uuid=True), primary_key=True),
    sa.Column("project_id", PG_UUID(as_uuid=True)),
    sa.Column("ingestion_job_id", PG_UUID(as_uuid=True)),
    sa.Column("source_type", sa.String(20)),
    sa.Column("source_path", sa.String(2048)),
    sa.Column("source_url", sa.String(2048)),
    sa.Column("title", sa.String(500)),
    sa.Column("checksum", sa.String(64)),
    sa.Column("mime_type", sa.String(100)),
    sa.Column("byte_size", sa.Integer),
    sa.Column("raw_storage_key", sa.String(1024)),
    sa.Column("status", sa.String(30)),
    sa.Column("error_code", sa.String(50)),
    sa.Column("error_message", sa.String()),
    sa.Column("chunk_count", sa.Integer),
    sa.Column("doc_metadata", JSONB),
    sa.Column("deleted_at", sa.TIMESTAMP(timezone=True)),
    sa.Column("created_at", sa.TIMESTAMP(timezone=True)),
    sa.Column("updated_at", sa.TIMESTAMP(timezone=True)),
)

project_document_chunks = sa.Table(
    "project_document_chunks",
    metadata,
    sa.Column("id", PG_UUID(as_uuid=True), primary_key=True),
    sa.Column("document_id", PG_UUID(as_uuid=True)),
    sa.Column("project_id", PG_UUID(as_uuid=True)),
    sa.Column("chunk_index", sa.Integer),
    sa.Column("content", sa.String()),
    sa.Column("token_count", sa.Integer),
    sa.Column("char_count", sa.Integer),
    sa.Column("heading_path", JSONB),
    sa.Column("chunk_metadata", JSONB),
    sa.Column("content_hash", sa.String(64)),
    sa.Column("embedding_status", sa.String(20)),
    sa.Column("created_at", sa.TIMESTAMP(timezone=True)),
)

project_embeddings = sa.Table(
    "project_embeddings",
    metadata,
    sa.Column("id", PG_UUID(as_uuid=True), primary_key=True),
    sa.Column("chunk_id", PG_UUID(as_uuid=True)),
    sa.Column("project_id", PG_UUID(as_uuid=True)),
    sa.Column("embedding", Vector(EMBEDDING_DIMENSIONS)),
    sa.Column("model", sa.String(100)),
    sa.Column("created_at", sa.TIMESTAMP(timezone=True)),
)

engine = create_async_engine(config.database_url, pool_pre_ping=True)


# --- ingestion_jobs ---


async def get_job(job_id: uuid.UUID) -> Mapping[str, Any] | None:
    async with engine.connect() as conn:
        result = await conn.execute(sa.select(ingestion_jobs).where(ingestion_jobs.c.id == job_id))
        return result.mappings().first()


async def update_job(job_id: uuid.UUID, **values: Any) -> None:
    async with engine.begin() as conn:
        await conn.execute(sa.update(ingestion_jobs).where(ingestion_jobs.c.id == job_id).values(**values))


async def set_job_documents_discovered(job_id: uuid.UUID, count: int) -> None:
    """Written once, after discovery fully enumerates the file/page
    list — never incremented as discovery streams results — so that
    `increment_job_progress`'s "are we done" check (below) can never
    observe a still-growing denominator. See
    docs/architecture/ingestion-engine-v1.md Section 4."""
    await update_job(job_id, documents_discovered=count, status="processing")


async def increment_job_progress(job_id: uuid.UUID, *, succeeded: bool) -> Mapping[str, Any]:
    """Atomically increments the relevant counter and returns the
    post-increment row via RETURNING — this is what makes "am I the
    last process_document job for this ingestion job" race-free: each
    concurrent caller's UPDATE is serialized by Postgres, and only the
    call that observes (succeeded + failed) == documents_discovered in
    its own RETURNING result finalizes the job."""
    column = ingestion_jobs.c.documents_succeeded if succeeded else ingestion_jobs.c.documents_failed
    async with engine.begin() as conn:
        result = await conn.execute(
            sa.update(ingestion_jobs)
            .where(ingestion_jobs.c.id == job_id)
            .values(**{column.name: column + 1})
            .returning(ingestion_jobs)
        )
        row = result.mappings().one()
    return row


async def finalize_job_if_complete(job_id: uuid.UUID) -> None:
    job = await get_job(job_id)
    if job is None or job["status"] in ("completed", "completed_with_errors", "failed"):
        return
    discovered = job["documents_discovered"]
    processed = job["documents_succeeded"] + job["documents_failed"]
    if discovered == 0 or processed < discovered:
        return

    if job["documents_succeeded"] == 0:
        final_status = "failed"
    elif job["documents_failed"] > 0:
        final_status = "completed_with_errors"
    else:
        final_status = "completed"
    await update_job(job_id, status=final_status, completed_at=sa.func.now())


# --- project_documents ---


async def get_document(document_id: uuid.UUID) -> Mapping[str, Any] | None:
    async with engine.connect() as conn:
        result = await conn.execute(
            sa.select(project_documents).where(project_documents.c.id == document_id)
        )
        return result.mappings().first()


async def upsert_documents(rows: Sequence[dict[str, Any]]) -> None:
    """Bulk-inserts newly discovered documents (github_repo/website fan-
    out). IDs are generated client-side (uuid.uuid4()) by the caller
    before this runs, specifically so the caller already knows each
    document's id and can enqueue its `process_document` job in the
    same breath without a round-trip to read generated ids back."""
    if not rows:
        return
    async with engine.begin() as conn:
        await conn.execute(sa.insert(project_documents), rows)


async def update_document(document_id: uuid.UUID, **values: Any) -> None:
    async with engine.begin() as conn:
        await conn.execute(
            sa.update(project_documents).where(project_documents.c.id == document_id).values(**values)
        )


async def replace_document_chunks(
    document_id: uuid.UUID, project_id: uuid.UUID, chunks: Sequence[dict[str, Any]]
) -> None:
    """Delete-then-insert, in one transaction — makes reprocessing a
    document (arq retry after a mid-pipeline crash, or a future
    "re-ingest this file" action) idempotent: a retried run always ends
    with exactly one row per chunk_index, never duplicates."""
    async with engine.begin() as conn:
        await conn.execute(
            sa.delete(project_document_chunks).where(project_document_chunks.c.document_id == document_id)
        )
        if chunks:
            await conn.execute(
                sa.insert(project_document_chunks),
                [{**chunk, "document_id": document_id, "project_id": project_id} for chunk in chunks],
            )
    await update_document(document_id, chunk_count=len(chunks))


async def get_pending_embedding_chunks(document_id: uuid.UUID) -> Sequence[Mapping[str, Any]]:
    async with engine.connect() as conn:
        result = await conn.execute(
            sa.select(project_document_chunks).where(
                project_document_chunks.c.document_id == document_id,
                project_document_chunks.c.embedding_status == "pending",
            )
        )
        return result.mappings().all()


async def set_chunks_embedding_status(chunk_ids: Sequence[uuid.UUID], status: str) -> None:
    if not chunk_ids:
        return
    async with engine.begin() as conn:
        await conn.execute(
            sa.update(project_document_chunks)
            .where(project_document_chunks.c.id.in_(chunk_ids))
            .values(embedding_status=status)
        )


# --- project_embeddings ---


async def upsert_embeddings(rows: Sequence[dict[str, Any]]) -> None:
    """Insert-or-replace, keyed on `chunk_id` — idempotent under arq
    retry: if `embed_document_chunks` fails partway through (after
    writing some embeddings but before marking their chunks
    'completed'), a retried run re-embeds the same chunks and this
    upsert overwrites the prior vector rather than violating
    `project_embeddings.chunk_id`'s UNIQUE constraint."""
    if not rows:
        return
    async with engine.begin() as conn:
        stmt = pg_insert(project_embeddings).values(rows)
        stmt = stmt.on_conflict_do_update(
            index_elements=[project_embeddings.c.chunk_id],
            set_={"embedding": stmt.excluded.embedding, "model": stmt.excluded.model},
        )
        await conn.execute(stmt)
