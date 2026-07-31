"""Documentation Ingestion Engine — request/response schemas.

Every route in router.py takes and returns one of these — never a bare
dict — matching every other module's convention (see projects/schemas.py).
File uploads are the one route that takes multipart form fields instead
of a JSON body (FastAPI's `File`/`Form`, wired directly in router.py),
so there's no matching *Create schema for it here.
"""

import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

_URL_MAX_LENGTH = 2048
_QUERY_MAX_LENGTH = 2000

RetrievalMode = Literal["hybrid", "vector", "keyword"]


class GithubRepoIngestRequest(BaseModel):
    repo_url: str = Field(..., min_length=1, max_length=_URL_MAX_LENGTH)
    ref: str | None = Field(None, max_length=255, description="Branch, tag, or commit SHA.")

    @field_validator("repo_url")
    @classmethod
    def _not_blank(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("repo_url cannot be blank")
        return stripped


class WebsiteIngestRequest(BaseModel):
    url: str = Field(..., min_length=1, max_length=_URL_MAX_LENGTH)
    max_pages: int | None = Field(None, ge=1, le=2000)
    max_depth: int | None = Field(None, ge=0, le=10)

    @field_validator("url")
    @classmethod
    def _not_blank(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("url cannot be blank")
        return stripped


class IngestionJobRead(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    source_type: str
    source_input: dict[str, Any]
    status: str
    error_code: str | None
    error_message: str | None
    documents_discovered: int
    documents_succeeded: int
    documents_failed: int
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class IngestionJobListResponse(BaseModel):
    items: list[IngestionJobRead]
    total: int
    limit: int
    offset: int


class ProjectDocumentRead(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    ingestion_job_id: uuid.UUID
    source_type: str
    source_path: str
    source_url: str | None
    title: str | None
    checksum: str
    mime_type: str
    byte_size: int
    status: str
    error_code: str | None
    error_message: str | None
    chunk_count: int
    metadata: dict[str, Any]
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_model(cls, document: "object") -> "ProjectDocumentRead":
        # Explicit adapter, not from_attributes, because the response
        # field is named `metadata` (the natural API name) while the
        # column is `doc_metadata` (SQLAlchemy's Base reserves the plain
        # `metadata` attribute name for table metadata — see models.py).
        return cls(
            id=document.id,  # type: ignore[attr-defined]
            project_id=document.project_id,  # type: ignore[attr-defined]
            ingestion_job_id=document.ingestion_job_id,  # type: ignore[attr-defined]
            source_type=document.source_type,  # type: ignore[attr-defined]
            source_path=document.source_path,  # type: ignore[attr-defined]
            source_url=document.source_url,  # type: ignore[attr-defined]
            title=document.title,  # type: ignore[attr-defined]
            checksum=document.checksum,  # type: ignore[attr-defined]
            mime_type=document.mime_type,  # type: ignore[attr-defined]
            byte_size=document.byte_size,  # type: ignore[attr-defined]
            status=document.status,  # type: ignore[attr-defined]
            error_code=document.error_code,  # type: ignore[attr-defined]
            error_message=document.error_message,  # type: ignore[attr-defined]
            chunk_count=document.chunk_count,  # type: ignore[attr-defined]
            metadata=document.doc_metadata,  # type: ignore[attr-defined]
            created_at=document.created_at,  # type: ignore[attr-defined]
            updated_at=document.updated_at,  # type: ignore[attr-defined]
        )


class ProjectDocumentListResponse(BaseModel):
    items: list[ProjectDocumentRead]
    total: int
    limit: int
    offset: int


class UploadIngestResponse(BaseModel):
    """Uploads are the one source type where the document is known the
    instant the request lands — this returns both, so the client
    doesn't need a second round-trip just to get the document id it
    already implicitly created."""

    job: IngestionJobRead
    document: ProjectDocumentRead


class ProjectDocumentChunkRead(BaseModel):
    id: uuid.UUID
    document_id: uuid.UUID
    chunk_index: int
    content: str
    token_count: int
    char_count: int
    heading_path: list[str]
    metadata: dict[str, Any]
    embedding_status: str
    created_at: datetime

    @classmethod
    def from_model(cls, chunk: "object") -> "ProjectDocumentChunkRead":
        return cls(
            id=chunk.id,  # type: ignore[attr-defined]
            document_id=chunk.document_id,  # type: ignore[attr-defined]
            chunk_index=chunk.chunk_index,  # type: ignore[attr-defined]
            content=chunk.content,  # type: ignore[attr-defined]
            token_count=chunk.token_count,  # type: ignore[attr-defined]
            char_count=chunk.char_count,  # type: ignore[attr-defined]
            heading_path=chunk.heading_path,  # type: ignore[attr-defined]
            metadata=chunk.chunk_metadata,  # type: ignore[attr-defined]
            embedding_status=chunk.embedding_status,  # type: ignore[attr-defined]
            created_at=chunk.created_at,  # type: ignore[attr-defined]
        )


class ProjectDocumentChunkListResponse(BaseModel):
    items: list[ProjectDocumentChunkRead]
    total: int
    limit: int
    offset: int


# --- RAG Knowledge Engine (docs/architecture/rag-engine-v1.md) ---


class _RetrievalRequestMixin(BaseModel):
    """Shared shape between /search and /ask — same retrieval knobs,
    different final step (return chunks vs. generate an answer from
    them)."""

    mode: RetrievalMode = "hybrid"
    top_k: int | None = Field(None, ge=1, le=50)
    source_types: list[str] | None = Field(None, max_length=4)
    document_ids: list[uuid.UUID] | None = Field(None, max_length=100)


class SearchRequest(_RetrievalRequestMixin):
    query: str = Field(..., min_length=1, max_length=_QUERY_MAX_LENGTH)

    @field_validator("query")
    @classmethod
    def _not_blank(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("query cannot be blank")
        return stripped


class RetrievedChunkRead(BaseModel):
    chunk_id: uuid.UUID
    document_id: uuid.UUID
    title: str | None
    source_type: str
    source_path: str
    heading_path: list[str]
    content: str
    score: float
    vector_score: float | None
    keyword_score: float | None
    vector_rank: int | None
    keyword_rank: int | None

    @classmethod
    def from_retrieved(cls, chunk: "object") -> "RetrievedChunkRead":
        # Duck-typed against retrieval_service.RetrievedChunk, same
        # "object" + type:ignore convention as ProjectDocumentRead.from_model
        # above — schemas.py doesn't import service-layer modules.
        return cls(
            chunk_id=chunk.chunk_id,  # type: ignore[attr-defined]
            document_id=chunk.document_id,  # type: ignore[attr-defined]
            title=chunk.title,  # type: ignore[attr-defined]
            source_type=chunk.source_type,  # type: ignore[attr-defined]
            source_path=chunk.source_path,  # type: ignore[attr-defined]
            heading_path=chunk.heading_path,  # type: ignore[attr-defined]
            content=chunk.content,  # type: ignore[attr-defined]
            score=chunk.score,  # type: ignore[attr-defined]
            vector_score=chunk.vector_score,  # type: ignore[attr-defined]
            keyword_score=chunk.keyword_score,  # type: ignore[attr-defined]
            vector_rank=chunk.vector_rank,  # type: ignore[attr-defined]
            keyword_rank=chunk.keyword_rank,  # type: ignore[attr-defined]
        )


class SearchResponse(BaseModel):
    query: str
    mode: RetrievalMode
    results: list[RetrievedChunkRead]


class AskRequest(_RetrievalRequestMixin):
    question: str = Field(..., min_length=1, max_length=_QUERY_MAX_LENGTH)
    use_cache: bool = True

    @field_validator("question")
    @classmethod
    def _not_blank(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("question cannot be blank")
        return stripped


class AskSourceRead(BaseModel):
    index: int
    chunk_id: uuid.UUID
    document_id: uuid.UUID
    title: str | None
    source_type: str
    source_path: str
    heading_path: list[str]
    score: float

    @classmethod
    def from_context_source(cls, source: "object") -> "AskSourceRead":
        return cls(
            index=source.index,  # type: ignore[attr-defined]
            chunk_id=source.chunk_id,  # type: ignore[attr-defined]
            document_id=source.document_id,  # type: ignore[attr-defined]
            title=source.title,  # type: ignore[attr-defined]
            source_type=source.source_type,  # type: ignore[attr-defined]
            source_path=source.source_path,  # type: ignore[attr-defined]
            heading_path=source.heading_path,  # type: ignore[attr-defined]
            score=source.score,  # type: ignore[attr-defined]
        )


class AskResponse(BaseModel):
    answer: str
    sources: list[AskSourceRead]
    chunks_retrieved: int
    context_tokens: int
    truncated: bool
    cached: bool
    retrieval_mode: RetrievalMode

    @classmethod
    def from_answer(cls, result: "object") -> "AskResponse":
        return cls(
            answer=result.answer,  # type: ignore[attr-defined]
            sources=[
                AskSourceRead.from_context_source(s)
                for s in result.sources  # type: ignore[attr-defined]
            ],
            chunks_retrieved=result.chunks_retrieved,  # type: ignore[attr-defined]
            context_tokens=result.context_tokens,  # type: ignore[attr-defined]
            truncated=result.truncated,  # type: ignore[attr-defined]
            cached=result.cached,  # type: ignore[attr-defined]
            retrieval_mode=result.retrieval_mode,  # type: ignore[attr-defined]
        )
