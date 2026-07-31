"""Knowledge System / Documentation Ingestion Engine / RAG Knowledge
Engine — domain exceptions.

Mirrors projects/exceptions.py exactly: service.py raises these, never a
bare HTTPException; main.py registers one handler per base class.
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class KnowledgeError(Exception):
    """Base for every ingestion-domain error."""

    def __init__(self, message: str, error_code: str) -> None:
        super().__init__(message)
        self.message = message
        self.error_code = error_code


class UnsupportedSourceError(KnowledgeError):
    """Raised when an uploaded file's extension/content-type isn't one
    of the supported source types, or fails a cheap sanity check (e.g.
    a PDF upload whose bytes don't start with the PDF magic number)."""

    def __init__(self, message: str) -> None:
        super().__init__(message, "unsupported_source")


class UploadTooLargeError(KnowledgeError):
    def __init__(self, max_bytes: int) -> None:
        super().__init__(f"Upload exceeds the {max_bytes}-byte limit.", "upload_too_large")


class InvalidSourceUrlError(KnowledgeError):
    """Raised by the API's cheap, request-path URL shape/SSRF checks
    (see validation.py) — malformed URL, wrong scheme, or a hostname the
    API refuses to ever contact. The worker performs the expensive,
    thorough version of this same check (DNS resolution, redirect-chain
    re-validation) before it ever fetches — see
    docs/architecture/ingestion-engine-v1.md Section 6."""

    def __init__(self, message: str) -> None:
        super().__init__(message, "invalid_source_url")


class IngestionJobLimitExceededError(KnowledgeError):
    def __init__(self, limit: int) -> None:
        super().__init__(
            f"This project has reached the limit of {limit} active ingestion jobs. "
            "Wait for one to finish before starting another.",
            "ingestion_job_limit_exceeded",
        )


class IngestionJobNotFoundError(KnowledgeError):
    def __init__(self) -> None:
        super().__init__("Ingestion job not found.", "ingestion_job_not_found")


class ProjectDocumentNotFoundError(KnowledgeError):
    def __init__(self) -> None:
        super().__init__("Document not found.", "document_not_found")


class RetrievalServiceUnavailableError(KnowledgeError):
    """Raised when the LLM Gateway itself fails during retrieval/answer
    generation (Ollama unreachable, embedding call timed out) — a
    caller-visible 503, distinct from every other error in this module:
    it means the search/answer infrastructure is down, not that the
    caller's request was invalid."""

    def __init__(self, message: str) -> None:
        super().__init__(message, "retrieval_service_unavailable")


_STATUS_CODES: dict[type[KnowledgeError], int] = {
    UnsupportedSourceError: 422,
    UploadTooLargeError: 413,
    InvalidSourceUrlError: 422,
    IngestionJobLimitExceededError: 422,
    IngestionJobNotFoundError: 404,
    ProjectDocumentNotFoundError: 404,
    RetrievalServiceUnavailableError: 503,
}


async def _handle_knowledge_error(request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, KnowledgeError)
    status_code = _STATUS_CODES.get(type(exc), 400)
    return JSONResponse(
        status_code=status_code,
        content={"detail": exc.message, "error_code": exc.error_code},
    )


def register_knowledge_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(KnowledgeError, _handle_knowledge_error)
