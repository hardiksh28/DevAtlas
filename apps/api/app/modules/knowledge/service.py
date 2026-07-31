"""Documentation Ingestion Engine — service layer.

All business logic lives here, not in router.py (see projects/service.py's
own docstring for why). This module only ever does the fast, request-path
half of the pipeline — Upload (store raw bytes) and enqueue — everything
from Validation onward (see docs/architecture/ingestion-engine-v1.md's
pipeline diagram) runs in services/ingestion_worker, off the request path,
which is the entire reason ingestion is async in the first place (Section 7
of that doc).
"""

import hashlib
import uuid
from datetime import UTC, datetime

from arq import ArqRedis
from object_storage import ObjectStorage
from schemas import IngestionJobStatus, SourceType
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.modules.knowledge.exceptions import (
    IngestionJobLimitExceededError,
    IngestionJobNotFoundError,
    ProjectDocumentNotFoundError,
)
from app.modules.knowledge.models import IngestionJob, ProjectDocument, ProjectDocumentChunk
from app.modules.knowledge.validation import (
    parse_github_repo_url,
    validate_upload_source,
    validate_website_url,
)

settings = get_settings()

# Job statuses that count against max_active_ingestion_jobs_per_project —
# everything except the three terminal ones.
_TERMINAL_JOB_STATUSES = (
    IngestionJobStatus.COMPLETED,
    IngestionJobStatus.COMPLETED_WITH_ERRORS,
    IngestionJobStatus.FAILED,
)


def _now() -> datetime:
    return datetime.now(UTC)


async def _count_active_jobs(db: AsyncSession, project_id: uuid.UUID) -> int:
    result = await db.execute(
        select(func.count())
        .select_from(IngestionJob)
        .where(
            IngestionJob.project_id == project_id,
            IngestionJob.status.not_in([s.value for s in _TERMINAL_JOB_STATUSES]),
        )
    )
    return result.scalar_one()


async def _enforce_job_limit(db: AsyncSession, project_id: uuid.UUID) -> None:
    active = await _count_active_jobs(db, project_id)
    if active >= settings.max_active_ingestion_jobs_per_project:
        raise IngestionJobLimitExceededError(settings.max_active_ingestion_jobs_per_project)


# --- Uploads (markdown / PDF) ---


async def create_upload_job(
    db: AsyncSession,
    storage: ObjectStorage,
    queue: ArqRedis,
    *,
    project_id: uuid.UUID,
    user_id: uuid.UUID,
    filename: str,
    content_type: str,
    data: bytes,
) -> tuple[IngestionJob, ProjectDocument]:
    await _enforce_job_limit(db, project_id)
    source_type = validate_upload_source(
        filename=filename,
        content_type=content_type,
        size=len(data),
        head=data,
        max_bytes=settings.ingestion_max_upload_bytes,
    )

    job = IngestionJob(
        project_id=project_id,
        requested_by=user_id,
        source_type=source_type.value,
        source_input={"filename": filename, "content_type": content_type},
        # Uploads know their one document immediately — no discovery
        # phase needed, so this skips straight to `processing`.
        status=IngestionJobStatus.PROCESSING.value,
        documents_discovered=1,
        started_at=_now(),
    )
    db.add(job)
    await db.flush()  # assigns job.id, needed for the storage key + document FK below

    document = ProjectDocument(
        project_id=project_id,
        ingestion_job_id=job.id,
        source_type=source_type.value,
        source_path=filename,
        source_url=None,
        checksum=hashlib.sha256(data).hexdigest(),
        mime_type=content_type,
        byte_size=len(data),
    )
    db.add(document)
    await db.flush()  # assigns document.id, needed for the storage key

    extension = ".pdf" if source_type is SourceType.PDF_FILE else ".md"
    storage_key = f"projects/{project_id}/ingestion/{job.id}/{document.id}/original{extension}"
    await storage.put(storage_key, data, content_type)
    document.raw_storage_key = storage_key

    await db.commit()
    await db.refresh(job)
    await db.refresh(document)

    await queue.enqueue_job("process_document", str(document.id))
    return job, document


# --- GitHub repositories ---


async def create_github_job(
    db: AsyncSession,
    queue: ArqRedis,
    *,
    project_id: uuid.UUID,
    user_id: uuid.UUID,
    repo_url: str,
    ref: str | None,
) -> IngestionJob:
    await _enforce_job_limit(db, project_id)
    owner, repo = parse_github_repo_url(repo_url)

    job = IngestionJob(
        project_id=project_id,
        requested_by=user_id,
        source_type=SourceType.GITHUB_REPO.value,
        source_input={"repo_url": repo_url, "owner": owner, "repo": repo, "ref": ref},
        status=IngestionJobStatus.QUEUED.value,
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)

    await queue.enqueue_job("discover_github_documents", str(job.id))
    return job


# --- Documentation websites ---


async def create_website_job(
    db: AsyncSession,
    queue: ArqRedis,
    *,
    project_id: uuid.UUID,
    user_id: uuid.UUID,
    url: str,
    max_pages: int | None,
    max_depth: int | None,
) -> IngestionJob:
    await _enforce_job_limit(db, project_id)
    normalized_url = validate_website_url(url)
    effective_max_pages = min(max_pages or settings.ingestion_max_website_pages, 2000)
    effective_max_depth = min(max_depth or settings.ingestion_max_website_crawl_depth, 10)

    job = IngestionJob(
        project_id=project_id,
        requested_by=user_id,
        source_type=SourceType.WEBSITE.value,
        source_input={
            "url": normalized_url,
            "max_pages": effective_max_pages,
            "max_depth": effective_max_depth,
        },
        status=IngestionJobStatus.QUEUED.value,
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)

    await queue.enqueue_job("discover_website_documents", str(job.id))
    return job


# --- Reads ---


async def get_job(db: AsyncSession, project_id: uuid.UUID, job_id: uuid.UUID) -> IngestionJob:
    result = await db.execute(
        select(IngestionJob).where(IngestionJob.id == job_id, IngestionJob.project_id == project_id)
    )
    job = result.scalar_one_or_none()
    if job is None:
        raise IngestionJobNotFoundError()
    return job


async def list_jobs(
    db: AsyncSession, project_id: uuid.UUID, limit: int, offset: int
) -> tuple[list[IngestionJob], int]:
    base = select(IngestionJob).where(IngestionJob.project_id == project_id)
    total = (await db.execute(select(func.count()).select_from(base.subquery()))).scalar_one()
    result = await db.execute(base.order_by(IngestionJob.created_at.desc()).limit(limit).offset(offset))
    return list(result.scalars().all()), total


async def get_document(
    db: AsyncSession, project_id: uuid.UUID, document_id: uuid.UUID
) -> ProjectDocument:
    result = await db.execute(
        select(ProjectDocument).where(
            ProjectDocument.id == document_id,
            ProjectDocument.project_id == project_id,
            ProjectDocument.deleted_at.is_(None),
        )
    )
    document = result.scalar_one_or_none()
    if document is None:
        raise ProjectDocumentNotFoundError()
    return document


async def list_documents(
    db: AsyncSession,
    project_id: uuid.UUID,
    *,
    source_type: str | None,
    status: str | None,
    limit: int,
    offset: int,
) -> tuple[list[ProjectDocument], int]:
    base = select(ProjectDocument).where(
        ProjectDocument.project_id == project_id, ProjectDocument.deleted_at.is_(None)
    )
    if source_type is not None:
        base = base.where(ProjectDocument.source_type == source_type)
    if status is not None:
        base = base.where(ProjectDocument.status == status)

    total = (await db.execute(select(func.count()).select_from(base.subquery()))).scalar_one()
    result = await db.execute(
        base.order_by(ProjectDocument.created_at.desc()).limit(limit).offset(offset)
    )
    return list(result.scalars().all()), total


async def list_chunks(
    db: AsyncSession, document_id: uuid.UUID, limit: int, offset: int
) -> tuple[list[ProjectDocumentChunk], int]:
    base = select(ProjectDocumentChunk).where(ProjectDocumentChunk.document_id == document_id)
    total = (await db.execute(select(func.count()).select_from(base.subquery()))).scalar_one()
    result = await db.execute(
        base.order_by(ProjectDocumentChunk.chunk_index.asc()).limit(limit).offset(offset)
    )
    return list(result.scalars().all()), total


async def delete_document(db: AsyncSession, document: ProjectDocument) -> None:
    """Soft delete only — same rationale as projects.service.delete_project.
    Storage cleanup (the raw object at raw_storage_key) is a deferred
    reaper-job concern, same category as the sessions/*_tokens reaper
    noted in database-schema-v1.md, not implemented in this pass."""
    document.deleted_at = _now()
    await db.commit()
