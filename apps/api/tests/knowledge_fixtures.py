"""Shared test helpers for seeding ingestion/RAG data directly via the
ORM — there's no API endpoint that creates chunks (only the ingestion
worker does, and it's a separate process/service these tests don't run),
so retrieval/RAG tests seed rows directly instead. Not a test file itself
(no `test_` prefix — pytest won't collect it).
"""

import hashlib
import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.knowledge.models import (
    IngestionJob,
    ProjectDocument,
    ProjectDocumentChunk,
    ProjectEmbedding,
)


async def create_ingestion_job(db: AsyncSession, project_id: uuid.UUID, user_id: uuid.UUID) -> IngestionJob:
    job = IngestionJob(
        project_id=project_id,
        requested_by=user_id,
        source_type="markdown_file",
        source_input={"filename": "seed.md"},
        status="completed",
        documents_discovered=1,
        documents_succeeded=1,
    )
    db.add(job)
    await db.flush()
    return job


async def create_document(
    db: AsyncSession,
    project_id: uuid.UUID,
    ingestion_job_id: uuid.UUID,
    *,
    source_path: str = "intro.md",
    title: str | None = "Intro",
    source_type: str = "markdown_file",
) -> ProjectDocument:
    document = ProjectDocument(
        project_id=project_id,
        ingestion_job_id=ingestion_job_id,
        source_type=source_type,
        source_path=source_path,
        title=title,
        checksum=hashlib.sha256(source_path.encode()).hexdigest(),
        mime_type="text/markdown",
        byte_size=100,
        status="completed",
    )
    db.add(document)
    await db.flush()
    return document


async def create_chunk(
    db: AsyncSession,
    document: ProjectDocument,
    *,
    content: str,
    chunk_index: int = 0,
    heading_path: list[str] | None = None,
    chunk_metadata: dict[str, Any] | None = None,
    embedding_status: str = "completed",
) -> ProjectDocumentChunk:
    chunk = ProjectDocumentChunk(
        document_id=document.id,
        project_id=document.project_id,
        chunk_index=chunk_index,
        content=content,
        token_count=max(1, len(content) // 4),
        char_count=len(content),
        heading_path=heading_path or [],
        chunk_metadata=chunk_metadata or {},
        content_hash=hashlib.sha256(content.encode()).hexdigest(),
        embedding_status=embedding_status,
    )
    db.add(chunk)
    await db.flush()
    return chunk


async def create_embedding(
    db: AsyncSession, chunk: ProjectDocumentChunk, *, vector: list[float], model: str = "test-embed"
) -> ProjectEmbedding:
    embedding = ProjectEmbedding(chunk_id=chunk.id, project_id=chunk.project_id, embedding=vector, model=model)
    db.add(embedding)
    await db.flush()
    return embedding


async def seed_chunk(
    db: AsyncSession,
    project_id: uuid.UUID,
    user_id: uuid.UUID,
    *,
    content: str,
    source_path: str = "intro.md",
    heading_path: list[str] | None = None,
    vector: list[float] | None = None,
) -> ProjectDocumentChunk:
    """Convenience one-shot: job + document + chunk (+ embedding, if a
    vector is given) in a single call, for tests that don't care about
    the intermediate rows."""
    job = await create_ingestion_job(db, project_id, user_id)
    document = await create_document(db, project_id, job.id, source_path=source_path)
    chunk = await create_chunk(db, document, content=content, heading_path=heading_path)
    if vector is not None:
        await create_embedding(db, chunk, vector=vector)
    await db.commit()
    return chunk
