"""Knowledge System — routers.

Two routers, deliberately: `router` (`/v1/knowledge`) is the pre-existing
stub for the *global* corpus (curated docs, shared across every user —
still unbuilt, see ARCHITECTURE.md Section 3). `project_documents_router`
(`/v1/projects/{project_id}/documents`) is the Documentation Ingestion
Engine built in this pass — the *project* corpus half of the Knowledge
System. Nested under /v1/projects the same way project_settings is (see
projects/router.py's own docstring for why a resource-scoped route lives
under its parent's prefix).

Thin HTTP layer only: every handler extracts what it needs, calls
service.py, and shapes the result via a schemas.py adapter — same
pattern as every other module.
"""

import uuid

from arq import ArqRedis
from fastapi import APIRouter, Depends, File, Query, UploadFile, status
from object_storage import ObjectStorage
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db
from app.core.queue import get_queue
from app.core.redis import get_redis
from app.core.storage import get_storage
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.models import User
from app.modules.cost_control.limits import llm_rate_limit
from app.modules.knowledge import service
from app.modules.knowledge.dependencies import get_project_document
from app.modules.knowledge.exceptions import UploadTooLargeError
from app.modules.knowledge.models import ProjectDocument
from app.modules.knowledge.retrieval import rag_service
from app.modules.knowledge.retrieval.retrieval_service import (
    RetrievalFilters,
)
from app.modules.knowledge.schemas import (
    AskRequest,
    AskResponse,
    GithubRepoIngestRequest,
    IngestionJobListResponse,
    IngestionJobRead,
    ProjectDocumentChunkListResponse,
    ProjectDocumentChunkRead,
    ProjectDocumentListResponse,
    ProjectDocumentRead,
    RetrievedChunkRead,
    SearchRequest,
    SearchResponse,
    UploadIngestResponse,
    WebsiteIngestRequest,
)
from app.modules.llm_gateway.gateway import LLMGateway, get_llm_gateway
from app.modules.projects.dependencies import get_owned_project
from app.modules.projects.models import Project

router = APIRouter(prefix="/v1/knowledge", tags=["Knowledge System"])

project_documents_router = APIRouter(
    prefix="/v1/projects/{project_id}/documents", tags=["Documentation Ingestion"]
)

settings = get_settings()


async def _read_upload_bounded(upload: UploadFile, max_bytes: int) -> bytes:
    """Reads the upload in 1 MB chunks, aborting the instant the running
    total exceeds `max_bytes` rather than buffering an arbitrarily large
    body fully into memory first just to reject it — the cap is meant
    to bound memory use, not just eventual storage."""
    chunks: list[bytes] = []
    total = 0
    while True:
        chunk = await upload.read(1024 * 1024)
        if not chunk:
            break
        total += len(chunk)
        if total > max_bytes:
            raise UploadTooLargeError(max_bytes)
        chunks.append(chunk)
    return b"".join(chunks)


@project_documents_router.post(
    "/uploads", response_model=UploadIngestResponse, status_code=status.HTTP_201_CREATED
)
async def upload_document(
    file: UploadFile = File(...),
    project: Project = Depends(get_owned_project),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    storage: ObjectStorage = Depends(get_storage),
    queue: ArqRedis = Depends(get_queue),
) -> UploadIngestResponse:
    data = await _read_upload_bounded(file, settings.ingestion_max_upload_bytes)
    job, document = await service.create_upload_job(
        db,
        storage,
        queue,
        project_id=project.id,
        user_id=current_user.id,
        filename=file.filename or "upload",
        content_type=file.content_type or "application/octet-stream",
        data=data,
    )
    return UploadIngestResponse(
        job=IngestionJobRead.model_validate(job),
        document=ProjectDocumentRead.from_model(document),
    )


@project_documents_router.post(
    "/github", response_model=IngestionJobRead, status_code=status.HTTP_201_CREATED
)
async def ingest_github_repo(
    payload: GithubRepoIngestRequest,
    project: Project = Depends(get_owned_project),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    queue: ArqRedis = Depends(get_queue),
) -> IngestionJobRead:
    job = await service.create_github_job(
        db,
        queue,
        project_id=project.id,
        user_id=current_user.id,
        repo_url=payload.repo_url,
        ref=payload.ref,
    )
    return IngestionJobRead.model_validate(job)


@project_documents_router.post(
    "/website", response_model=IngestionJobRead, status_code=status.HTTP_201_CREATED
)
async def ingest_website(
    payload: WebsiteIngestRequest,
    project: Project = Depends(get_owned_project),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    queue: ArqRedis = Depends(get_queue),
) -> IngestionJobRead:
    job = await service.create_website_job(
        db,
        queue,
        project_id=project.id,
        user_id=current_user.id,
        url=payload.url,
        max_pages=payload.max_pages,
        max_depth=payload.max_depth,
    )
    return IngestionJobRead.model_validate(job)


# --- Jobs — declared before "/{document_id}" below so "jobs" is never
# swallowed by FastAPI trying to parse it as a document_id path param
# (same ordering rule projects/router.py uses for "recent"). ---


@project_documents_router.get("/jobs", response_model=IngestionJobListResponse)
async def list_ingestion_jobs(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    project: Project = Depends(get_owned_project),
    db: AsyncSession = Depends(get_db),
) -> IngestionJobListResponse:
    items, total = await service.list_jobs(db, project.id, limit, offset)
    return IngestionJobListResponse(
        items=[IngestionJobRead.model_validate(j) for j in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@project_documents_router.get("/jobs/{job_id}", response_model=IngestionJobRead)
async def get_ingestion_job(
    job_id: uuid.UUID,
    project: Project = Depends(get_owned_project),
    db: AsyncSession = Depends(get_db),
) -> IngestionJobRead:
    job = await service.get_job(db, project.id, job_id)
    return IngestionJobRead.model_validate(job)


@project_documents_router.get("", response_model=ProjectDocumentListResponse)
async def list_documents(
    source_type: str | None = Query(None),
    doc_status: str | None = Query(None, alias="status"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    project: Project = Depends(get_owned_project),
    db: AsyncSession = Depends(get_db),
) -> ProjectDocumentListResponse:
    items, total = await service.list_documents(
        db, project.id, source_type=source_type, status=doc_status, limit=limit, offset=offset
    )
    return ProjectDocumentListResponse(
        items=[ProjectDocumentRead.from_model(d) for d in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@project_documents_router.post("/search", response_model=SearchResponse)
async def search_documents(
    payload: SearchRequest,
    project: Project = Depends(get_owned_project),
    db: AsyncSession = Depends(get_db),
    gateway: LLMGateway = Depends(get_llm_gateway),
) -> SearchResponse:
    """Retrieval only — no LLM answer generation, no caching. Returns
    ranked chunks with every retriever's raw score/rank attached
    (see RetrievedChunkRead) so retrieval quality can be inspected and
    tuned independently of the answer-generation step /ask adds on top.
    Mode dispatch delegates to rag_service.retrieve_chunks — the same
    function /ask uses internally — so "hybrid"/"vector"/"keyword"
    can never mean something subtly different between the two routes.
    """
    filters = RetrievalFilters(source_types=payload.source_types, document_ids=payload.document_ids)
    top_k = payload.top_k or settings.retrieval_top_k

    results = await rag_service.retrieve_chunks(
        db, gateway, project.id, payload.query, mode=payload.mode, top_k=top_k, filters=filters
    )

    return SearchResponse(
        query=payload.query,
        mode=payload.mode,
        results=[RetrievedChunkRead.from_retrieved(r) for r in results],
    )


@project_documents_router.post(
    "/ask",
    response_model=AskResponse,
    dependencies=[llm_rate_limit("document_ask", times=30, seconds=3600)],
)
async def ask_documents(
    payload: AskRequest,
    project: Project = Depends(get_owned_project),
    db: AsyncSession = Depends(get_db),
    gateway: LLMGateway = Depends(get_llm_gateway),
    redis: Redis = Depends(get_redis),
) -> AskResponse:
    """Full RAG: retrieve, build context, build prompt, generate an
    answer via Ollama, and return it with the sources it was grounded
    in. See rag_service.answer_question for the caching/hallucination-
    prevention behavior (empty retrieval short-circuits before any LLM
    call — see its docstring)."""
    filters = RetrievalFilters(source_types=payload.source_types, document_ids=payload.document_ids)
    result = await rag_service.answer_question(
        db,
        gateway,
        redis,
        project_id=project.id,
        question=payload.question,
        mode=payload.mode,
        top_k=payload.top_k,
        filters=filters,
        use_cache=payload.use_cache,
    )
    return AskResponse.from_answer(result)


@project_documents_router.get("/{document_id}", response_model=ProjectDocumentRead)
async def get_document(
    document: ProjectDocument = Depends(get_project_document),
) -> ProjectDocumentRead:
    return ProjectDocumentRead.from_model(document)


@project_documents_router.get(
    "/{document_id}/chunks", response_model=ProjectDocumentChunkListResponse
)
async def list_document_chunks(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    document: ProjectDocument = Depends(get_project_document),
    db: AsyncSession = Depends(get_db),
) -> ProjectDocumentChunkListResponse:
    items, total = await service.list_chunks(db, document.id, limit, offset)
    return ProjectDocumentChunkListResponse(
        items=[ProjectDocumentChunkRead.from_model(c) for c in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@project_documents_router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document: ProjectDocument = Depends(get_project_document),
    db: AsyncSession = Depends(get_db),
) -> None:
    await service.delete_document(db, document)
