import asyncio
import json
import logging
import sys
import uuid
from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any, ClassVar

import httpx
from arq import cron, func
from arq.connections import ArqRedis, RedisSettings
from arq.cron import CronJob
from arq.typing import WorkerCoroutine

import db
from embeddings import embed_batch
from pipeline import cleaning
from pipeline.chunking import ChunkDraft, chunk_markdown_like, chunk_pdf_pages
from pipeline.errors import PermanentIngestionError, RetryableIngestionError
from pipeline.metadata import sha256_hex, slugify
from pipeline.parsers import github, markdown, website
from pipeline.parsers.pdf import PdfReadError, parse_pdf
from settings import config
from storage import get_storage


class _JSONFormatter(logging.Formatter):
    """Same shape as apps/api/app/core/logging.py's formatter — duplicated
    rather than imported, per this module's no-import-from-apps/api rule."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload)


# Configured at import time (before arq's CLI calls logging.config.dictConfig
# for its own 'arq' logger namespace) so every logger in this codebase — not
# just arq's internal ones — emits JSON in production.
_handler = logging.StreamHandler(sys.stdout)
_handler.setFormatter(
    _JSONFormatter()
    if config.environment == "production"
    else logging.Formatter("%(levelname)s %(name)s: %(message)s")
)
logging.getLogger().handlers = [_handler]
logging.getLogger().setLevel(logging.INFO)

logger = logging.getLogger(__name__)

# Mirrored in WorkerSettings.functions' func(..., max_tries=...) below — kept
# as named constants (not duplicated literals) so the "is this the last try"
# checks in the job bodies can never silently drift out of sync with what
# arq is actually configured to allow.
_DISCOVERY_MAX_TRIES = 2
_PROCESS_MAX_TRIES = 3
_EMBED_MAX_TRIES = 3

_GITHUB_TEXT_EXTENSIONS = (".md", ".mdx", ".markdown", ".rst", ".txt")
_MIME_BY_EXTENSION = {
    ".md": "text/markdown",
    ".mdx": "text/markdown",
    ".markdown": "text/markdown",
    ".rst": "text/x-rst",
    ".txt": "text/plain",
}


def _now() -> datetime:
    return datetime.now(UTC)


def _extension_for_path(path: str) -> str:
    lower = path.lower()
    for ext in _GITHUB_TEXT_EXTENSIONS:
        if lower.endswith(ext):
            return ext
    return ""


def _mime_for_path(path: str) -> str:
    return _MIME_BY_EXTENSION.get(_extension_for_path(path), "text/plain")


async def refresh_global_corpus(ctx: dict) -> None:
    """Freshness / re-crawl scheduler (ARCHITECTURE.md Section 2).

    Placeholder body: real implementation will diff each curated stack's
    docs against `global_documents.last_refreshed` and enqueue
    `ingest_document` jobs for anything stale. Left unimplemented here —
    there's no curated source list yet to crawl. Unrelated to the
    Documentation Ingestion Engine below (that's the *project* corpus;
    this is the *global* one — see ARCHITECTURE.md Section 3).
    """
    print("refresh_global_corpus: no-op (no curated sources configured yet)")


async def ingest_document(ctx: dict, document_url: str) -> None:
    """Global Corpus Ingestion Worker (ARCHITECTURE.md Section 2).

    Fetches one document, chunks it, generates embeddings, and writes to
    `global_documents` / `global_embeddings` (pgvector). Placeholder body
    — the curated global corpus doesn't exist yet. Unrelated to
    `process_document` below, which handles per-project ingestion.
    """
    print(f"ingest_document: would ingest {document_url}")


# ============================================================
# Documentation Ingestion Engine (docs/architecture/ingestion-engine-v1.md)
# Pipeline: Upload (apps/api) → Validation → Parsing → Cleaning →
# Chunking → Metadata Extraction → Embedding Queue → Database Storage.
# ============================================================


async def discover_github_documents(ctx: dict, job_id: str) -> None:
    """Discovery stage for github_repo jobs: validates the repo exists,
    is public, and is under the size ceiling, lists every documentation
    file in it, creates one ProjectDocument row per file, then fans out
    one `process_document` job per file. `documents_discovered` is
    written once, after the full file list is known — never
    incremented as files are found — so `increment_job_progress`'s "are
    we done" check downstream can never race against a still-growing
    denominator (see docs/architecture/ingestion-engine-v1.md Section 4).
    """
    job_uuid = uuid.UUID(job_id)
    job = await db.get_job(job_uuid)
    if job is None:
        return
    await db.update_job(job_uuid, status="discovering", started_at=_now())

    source_input = job["source_input"]
    owner, repo, ref = source_input["owner"], source_input["repo"], source_input.get("ref")

    async with httpx.AsyncClient(timeout=config.ingestion_fetch_timeout_seconds) as client:
        try:
            repo_info = await github.get_repo_metadata(client, owner, repo)
            resolved_ref = ref or repo_info.get("default_branch", "main")
            files = await github.list_doc_files(client, owner, repo, resolved_ref)
        except PermanentIngestionError as exc:
            await db.update_job(
                job_uuid,
                status="failed",
                error_code=exc.error_code,
                error_message=exc.message,
                completed_at=_now(),
            )
            return
        except RetryableIngestionError as exc:
            # Re-raised while retries remain, so arq retries this whole
            # discovery job per WorkerSettings' max_tries. On the last
            # allowed try, arq won't invoke this coroutine again to try
            # once more — so this is the last chance to record a terminal
            # status instead of leaving the job stuck at 'discovering'
            # forever once retries are silently exhausted.
            if ctx.get("job_try", 1) >= _DISCOVERY_MAX_TRIES:
                await db.update_job(
                    job_uuid,
                    status="failed",
                    error_code=exc.error_code,
                    error_message=exc.message,
                    completed_at=_now(),
                )
                return
            raise

    if not files:
        await db.update_job(
            job_uuid,
            status="failed",
            error_code="no_documents_found",
            error_message=f"No documentation files found in {owner}/{repo}.",
            completed_at=_now(),
        )
        return

    document_ids: list[uuid.UUID] = []
    document_rows: list[dict[str, Any]] = []
    for file in files:
        document_id = uuid.uuid4()
        document_ids.append(document_id)
        document_rows.append(
            {
                "id": document_id,
                "project_id": job["project_id"],
                "ingestion_job_id": job_uuid,
                "source_type": "github_repo",
                "source_path": file["path"],
                "source_url": github.raw_content_url(owner, repo, resolved_ref, file["path"]),
                "title": None,
                # Content (and therefore its checksum) isn't known until
                # process_document fetches it — see get_repo_metadata's
                # docstring for why github discovery only lists paths.
                "checksum": "pending",
                "mime_type": _mime_for_path(file["path"]),
                "byte_size": file["size"],
                "raw_storage_key": None,
                "status": "pending",
                "chunk_count": 0,
                "doc_metadata": {"repo": f"{owner}/{repo}", "ref": resolved_ref},
            }
        )

    await db.upsert_documents(document_rows)
    await db.set_job_documents_discovered(job_uuid, len(document_rows))

    redis: ArqRedis = ctx["redis"]
    for document_id in document_ids:
        await redis.enqueue_job("process_document", str(document_id))


async def discover_website_documents(ctx: dict, job_id: str) -> None:
    """Discovery stage for website jobs: crawls same-origin pages up to
    the job's max_pages/max_depth. Unlike GitHub discovery, the crawl
    already has to fetch each page's full HTML to find outgoing links —
    so that fetch is the one and only network request per page; the
    raw HTML is stored immediately (real checksum, real byte_size, real
    raw_storage_key at insert time) rather than re-fetched later in
    process_document.
    """
    job_uuid = uuid.UUID(job_id)
    job = await db.get_job(job_uuid)
    if job is None:
        return
    await db.update_job(job_uuid, status="discovering", started_at=_now())

    source_input = job["source_input"]
    root_url = source_input["url"]
    max_pages = source_input["max_pages"]
    max_depth = source_input["max_depth"]

    async with httpx.AsyncClient(timeout=config.ingestion_fetch_timeout_seconds) as client:
        try:
            pages = await website.crawl(client, root_url, max_pages=max_pages, max_depth=max_depth)
        except PermanentIngestionError as exc:
            await db.update_job(
                job_uuid,
                status="failed",
                error_code=exc.error_code,
                error_message=exc.message,
                completed_at=_now(),
            )
            return
        except RetryableIngestionError as exc:
            # Same last-try terminal-failure handling as discover_github_documents.
            if ctx.get("job_try", 1) >= _DISCOVERY_MAX_TRIES:
                await db.update_job(
                    job_uuid,
                    status="failed",
                    error_code=exc.error_code,
                    error_message=exc.message,
                    completed_at=_now(),
                )
                return
            raise

    if not pages:
        await db.update_job(
            job_uuid,
            status="failed",
            error_code="no_pages_found",
            error_message=f"No pages could be crawled from {root_url}.",
            completed_at=_now(),
        )
        return

    storage_client = get_storage()
    document_ids: list[uuid.UUID] = []
    document_rows: list[dict[str, Any]] = []
    for page in pages:
        document_id = uuid.uuid4()
        html_bytes = page["html"].encode("utf-8")
        storage_key = f"projects/{job['project_id']}/ingestion/{job_uuid}/{document_id}/original.html"
        await storage_client.put(storage_key, html_bytes, "text/html")

        document_ids.append(document_id)
        document_rows.append(
            {
                "id": document_id,
                "project_id": job["project_id"],
                "ingestion_job_id": job_uuid,
                "source_type": "website",
                "source_path": page["url"],
                "source_url": page["url"],
                "title": None,
                "checksum": sha256_hex(html_bytes),
                "mime_type": "text/html",
                "byte_size": len(html_bytes),
                "raw_storage_key": storage_key,
                "status": "pending",
                "chunk_count": 0,
                "doc_metadata": {},
            }
        )

    await db.upsert_documents(document_rows)
    await db.set_job_documents_discovered(job_uuid, len(document_rows))

    redis: ArqRedis = ctx["redis"]
    for document_id in document_ids:
        await redis.enqueue_job("process_document", str(document_id))


async def _obtain_raw_content(document: Mapping[str, Any]) -> bytes:
    """Fetches (or reads back) the document's raw bytes. Uploads and
    website pages already have `raw_storage_key` set by the time this
    runs (apps/api's upload endpoint, and discover_website_documents,
    respectively); only github_repo documents still need their one
    network fetch here, since discovery only listed paths."""
    storage_client = get_storage()
    if document["raw_storage_key"]:
        return await storage_client.get(document["raw_storage_key"])

    if document["source_type"] != "github_repo":
        raise PermanentIngestionError(
            f"Document {document['id']} has no stored content to process.",
            error_code="missing_content",
        )

    owner_repo = document["doc_metadata"].get("repo", "")
    owner, _, repo = owner_repo.partition("/")
    ref = document["doc_metadata"].get("ref", "main")

    async with httpx.AsyncClient(timeout=config.ingestion_fetch_timeout_seconds) as client:
        raw_bytes = await github.fetch_file_content(client, owner, repo, ref, document["source_path"])

    storage_key = (
        f"projects/{document['project_id']}/ingestion/{document['ingestion_job_id']}/"
        f"{document['id']}/original{_extension_for_path(document['source_path'])}"
    )
    await storage_client.put(storage_key, raw_bytes, document["mime_type"])
    await db.update_document(document["id"], raw_storage_key=storage_key)
    return raw_bytes


async def _parse(document: Mapping[str, Any], raw_bytes: bytes) -> tuple[Any, str | None, dict[str, Any]]:
    """Parsing + Cleaning, combined per source type since cleaning's
    boilerplate-stripping (PDF running headers, in particular) needs
    the parser's own page boundaries. Returns (parsed_content, title,
    extra_doc_metadata) — `parsed_content` is `list[str]` pages for
    pdf_file, plain heading-prefixed text for everything else."""
    source_type = document["source_type"]

    if source_type == "pdf_file":
        try:
            pages, doc_meta = await asyncio.to_thread(
                parse_pdf,
                raw_bytes,
                max_pages=config.ingestion_max_pdf_pages,
                max_extracted_chars=config.ingestion_max_pdf_extracted_chars,
            )
        except PdfReadError as exc:
            raise PermanentIngestionError(
                f"Could not parse PDF: {exc}", error_code="pdf_parse_error"
            ) from exc
        pages = [cleaning.normalize_text(p) for p in cleaning.strip_repeated_boilerplate(pages)]
        title = doc_meta.get("pdf_title") or document["source_path"]
        return pages, title, doc_meta

    if source_type == "website":
        html = raw_bytes.decode("utf-8", errors="replace")
        # BeautifulSoup parsing is CPU-bound and can be slow on a large
        # page — offloaded so it doesn't stall the event loop (and every
        # other concurrently-running job) the way the PDF path above does.
        text, page_title = await asyncio.to_thread(website.html_to_markdown_like, html)
        text = cleaning.normalize_text(text)
        title = page_title or document["source_path"]
        return text, title, {}

    # markdown_file, and github_repo's .md/.mdx/.markdown/.rst/.txt files
    try:
        raw_text = raw_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise PermanentIngestionError(
            f"File is not valid UTF-8 text: {document['source_path']}",
            error_code="invalid_encoding",
        ) from exc

    body, front_matter = markdown.parse_markdown(raw_text)
    body = cleaning.normalize_text(body)
    title = markdown.extract_title(body, front_matter) or document["source_path"]
    doc_meta: dict[str, Any] = {"heading_outline": markdown.extract_heading_outline(body)}
    if front_matter:
        doc_meta["front_matter"] = front_matter
    return body, title, doc_meta


def _chunk(source_type: str, parsed_content: Any) -> list[ChunkDraft]:
    if source_type == "pdf_file":
        return chunk_pdf_pages(
            parsed_content,
            target_tokens=config.chunk_target_tokens,
            overlap_tokens=config.chunk_overlap_tokens,
        )
    return chunk_markdown_like(
        parsed_content,
        target_tokens=config.chunk_target_tokens,
        overlap_tokens=config.chunk_overlap_tokens,
    )


def _build_chunk_rows(
    chunks: list[ChunkDraft], source_type: str
) -> list[dict[str, Any]]:
    rows = []
    for index, chunk in enumerate(chunks):
        chunk_meta = dict(chunk.chunk_metadata)
        if source_type == "website" and chunk.heading_path:
            chunk_meta["url_anchor"] = slugify(chunk.heading_path[-1])
        rows.append(
            {
                "id": uuid.uuid4(),
                "chunk_index": index,
                "content": chunk.content,
                "token_count": chunk.token_count,
                "char_count": chunk.char_count,
                "heading_path": chunk.heading_path,
                "chunk_metadata": chunk_meta,
                "content_hash": sha256_hex(chunk.content),
                "embedding_status": "pending",
            }
        )
    return rows


async def process_document(ctx: dict, document_id: str) -> None:
    """Validation → Parsing → Cleaning → Chunking → Metadata Extraction
    → Embedding Queue → Database Storage for exactly one document.

    Runs once per document rather than once per job, which is the
    scalability decision the architecture doc calls out: a 500-file
    GitHub repo or a 200-page website crawl becomes 500/200 independent,
    horizontally-scalable jobs instead of one long-running job blocking
    a single worker slot. One document failing (a corrupt PDF, a 404'd
    file) never aborts the others — see `succeeded` below and
    `db.increment_job_progress`'s per-document accounting.
    """
    doc_uuid = uuid.UUID(document_id)
    document = await db.get_document(doc_uuid)
    if document is None:
        return

    succeeded = False
    try:
        await db.update_document(doc_uuid, status="validating")
        raw_bytes = await _obtain_raw_content(document)
        checksum = sha256_hex(raw_bytes)

        await db.update_document(doc_uuid, status="parsing")
        parsed_content, title, extra_doc_meta = await _parse(document, raw_bytes)

        await db.update_document(doc_uuid, status="chunking")
        # Offloaded for the same reason as the parsing stage above —
        # chunking a large document is real CPU work, not I/O.
        chunk_drafts = await asyncio.to_thread(_chunk, document["source_type"], parsed_content)

        await db.update_document(doc_uuid, status="extracting_metadata")
        chunk_rows = _build_chunk_rows(chunk_drafts, document["source_type"])
        await db.replace_document_chunks(doc_uuid, document["project_id"], chunk_rows)

        # Embedding Queue stage: chunks are durably stored with
        # embedding_status='pending'; embed_document_chunks (below) is
        # the queue's consumer — it flips the document to 'completed'
        # once every chunk has been embedded (docs/architecture/rag-engine-v1.md).
        await db.update_document(
            doc_uuid,
            status="queued_for_embedding",
            title=title,
            checksum=checksum,
            byte_size=len(raw_bytes),
            doc_metadata={**document["doc_metadata"], **extra_doc_meta},
            error_code=None,
            error_message=None,
        )
        redis: ArqRedis = ctx["redis"]
        await redis.enqueue_job("embed_document_chunks", str(doc_uuid))
        succeeded = True
    except PermanentIngestionError as exc:
        await db.update_document(doc_uuid, status="failed", error_code=exc.error_code, error_message=exc.message)
    except RetryableIngestionError as exc:
        # Re-raised while retries remain, so arq retries this one
        # document's job alone (job-level counters below are correctly
        # skipped for a retry-in-progress). On the last allowed try,
        # arq won't invoke this coroutine again — so this is the last
        # chance to record a terminal 'failed' status instead of leaving
        # the document stuck mid-pipeline forever once retries are
        # silently exhausted.
        if ctx.get("job_try", 1) >= _PROCESS_MAX_TRIES:
            await db.update_document(doc_uuid, status="failed", error_code=exc.error_code, error_message=exc.message)
        else:
            raise

    await db.increment_job_progress(document["ingestion_job_id"], succeeded=succeeded)
    await db.finalize_job_if_complete(document["ingestion_job_id"])


async def embed_document_chunks(ctx: dict, document_id: str) -> None:
    """Embedding Queue stage's consumer (docs/architecture/rag-engine-v1.md).

    Batch-embeds every chunk still `embedding_status='pending'` for this
    document via Ollama, upserts each vector into `project_embeddings`
    (keyed by chunk_id), and flips each chunk to 'completed' immediately
    after its own batch is durably written — not all at the end. That
    ordering is what makes a retried job (mid-run crash, or a transient
    Ollama outage between batches) safe to just re-run: it only
    re-selects chunks still 'pending' (see
    `db.get_pending_embedding_chunks`'s status filter), so already-
    embedded batches from the failed attempt are never redone.

    A chunk that permanently fails to embed (bad request, unresolvable
    model) is marked `embedding_status='failed'` and does not block the
    rest of the document's chunks. A `RetryableIngestionError` (Ollama
    unreachable, a timeout) aborts the whole job for arq to retry, since
    continuing to try more batches against a downed embedding service
    wastes calls without changing the outcome — *while retries remain*.
    On the last allowed try it's caught instead: the batch's chunks are
    marked 'failed' rather than left at 'pending' forever once arq gives
    up (see `_EMBED_MAX_TRIES`), matching the same terminal handling a
    permanent failure already gets above.

    The document itself is marked 'completed' once every chunk has been
    attempted — a document-level status describes ingestion pipeline
    completion, not "every chunk embedded successfully"; per-chunk
    embedding failures remain visible (and re-triable) via each chunk's
    own `embedding_status`.
    """
    doc_uuid = uuid.UUID(document_id)
    pending_chunks = await db.get_pending_embedding_chunks(doc_uuid)
    if not pending_chunks:
        await db.update_document(doc_uuid, status="completed")
        return

    async with httpx.AsyncClient() as client:
        for batch_start in range(0, len(pending_chunks), config.embedding_batch_size):
            batch = pending_chunks[batch_start : batch_start + config.embedding_batch_size]
            batch_ids = [chunk["id"] for chunk in batch]

            try:
                vectors = await embed_batch(client, [chunk["content"] for chunk in batch])
            except PermanentIngestionError as exc:
                logger.warning("Chunk batch failed to embed permanently: %s", exc.message)
                await db.set_chunks_embedding_status(batch_ids, "failed")
                continue
            except RetryableIngestionError as exc:
                # Re-raised while retries remain, aborting the whole job
                # for arq to retry — see this function's docstring. On
                # the last allowed try, arq won't invoke this coroutine
                # again, so falling through here (rather than propagating
                # into the void) is what keeps this batch's chunks from
                # being stuck at embedding_status='pending' forever;
                # marking them 'failed' matches the same terminal
                # handling PermanentIngestionError already gets above.
                if ctx.get("job_try", 1) >= _EMBED_MAX_TRIES:
                    logger.warning(
                        "Chunk batch failed to embed after exhausting retries: %s", exc.message
                    )
                    await db.set_chunks_embedding_status(batch_ids, "failed")
                    continue
                raise

            await db.upsert_embeddings(
                [
                    {
                        "id": uuid.uuid4(),
                        "chunk_id": chunk["id"],
                        "project_id": chunk["project_id"],
                        "embedding": vector,
                        "model": config.ollama_embedding_model,
                    }
                    for chunk, vector in zip(batch, vectors, strict=True)
                ]
            )
            await db.set_chunks_embedding_status(batch_ids, "completed")

    await db.update_document(doc_uuid, status="completed")


class WorkerSettings:
    """arq reads this class by name (`arq worker.WorkerSettings`, see
    services/ingestion_worker/Dockerfile). `functions` is the closed set
    of jobs this worker can run — enqueueing anything not listed here
    fails loudly instead of silently doing nothing.
    """

    # ClassVar: arq reads these as class-level attributes, not per-instance
    # state — annotating them tells the type checker (and RUF012) that's
    # intentional rather than an accidentally-shared mutable default.
    functions: ClassVar[list[WorkerCoroutine | Any]] = [
        ingest_document,
        # Discovery jobs retry sparingly — a github_repo/website
        # submission that fails after one retry is almost always a
        # permanent problem (bad URL, private repo, unreachable site),
        # not a network blip worth hammering the source over.
        func(discover_github_documents, max_tries=_DISCOVERY_MAX_TRIES),
        func(discover_website_documents, max_tries=_DISCOVERY_MAX_TRIES),
        # process_document retries more since its failure modes are
        # dominated by one-off transient fetch errors across potentially
        # hundreds of independent per-file/per-page jobs.
        func(process_document, max_tries=_PROCESS_MAX_TRIES),
        # Same reasoning as process_document — an Ollama outage is
        # transient and worth retrying; a malformed batch is not (and
        # is caught/recorded per-chunk inside the job, never reaches
        # arq's retry machinery at all — see its docstring).
        func(embed_document_chunks, max_tries=_EMBED_MAX_TRIES),
    ]
    cron_jobs: ClassVar[list[CronJob]] = [
        # Runs daily at 03:00 — cheap enough to be conservative by
        # default; tune per-stack once real release-velocity data exists.
        cron(refresh_global_corpus, hour=3, minute=0),
    ]
    redis_settings = RedisSettings.from_dsn(config.redis_url)
    # Default is 3600s — far too coarse for the Dockerfile's HEALTHCHECK
    # (`arq ... --check`) to catch a wedged worker in any useful time.
    health_check_interval = 30
