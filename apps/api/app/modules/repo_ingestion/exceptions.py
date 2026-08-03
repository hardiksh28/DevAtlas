"""Repository Ingestion Engine — domain exceptions.

Mirrors knowledge/exceptions.py exactly: service.py raises these, never
a bare HTTPException; main.py registers one handler per base class.
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class RepoIngestionError(Exception):
    """Base for every repository-ingestion-domain error."""

    def __init__(self, message: str, error_code: str) -> None:
        super().__init__(message)
        self.message = message
        self.error_code = error_code


class InvalidRepositoryUrlError(RepoIngestionError):
    def __init__(self, message: str) -> None:
        super().__init__(message, "invalid_repository_url")


class RepositoryNotFoundError(RepoIngestionError):
    """Raised for both a genuinely missing repo and a private one — V1
    only supports public repositories, same reasoning as the
    Documentation Ingestion Engine's identical GitHub-repo constraint."""

    def __init__(self, owner: str, repo: str) -> None:
        super().__init__(
            f"GitHub repo not found or inaccessible: {owner}/{repo}", "repository_not_found"
        )


class RepositoryTooLargeError(RepoIngestionError):
    def __init__(self, max_bytes: int) -> None:
        super().__init__(
            f"Repository exceeds the {max_bytes}-byte size limit.", "repository_too_large"
        )


class RepositoryTreeTruncatedError(RepoIngestionError):
    def __init__(self) -> None:
        super().__init__(
            "This repository's file tree is too large to list in one request.",
            "repository_tree_truncated",
        )


class TooManyFilesError(RepoIngestionError):
    def __init__(self, limit: int) -> None:
        super().__init__(
            f"Repository has more than {limit} files, over the ingestion limit.",
            "repository_too_many_files",
        )


class RepositoryConnectionNotFoundError(RepoIngestionError):
    def __init__(self) -> None:
        super().__init__(
            "This project has no connected repository yet.", "repository_connection_not_found"
        )


class RepositoryUpstreamError(RepoIngestionError):
    """GitHub was reachable but returned something this pass can't
    recover from mid-request (rate limited, transient 5xx). Surfaced as
    a 502 — the caller's request was fine, GitHub wasn't."""

    def __init__(self, message: str) -> None:
        super().__init__(message, "repository_upstream_error")


_STATUS_CODES: dict[type[RepoIngestionError], int] = {
    InvalidRepositoryUrlError: 422,
    RepositoryNotFoundError: 404,
    RepositoryTooLargeError: 422,
    RepositoryTreeTruncatedError: 422,
    TooManyFilesError: 422,
    RepositoryConnectionNotFoundError: 404,
    RepositoryUpstreamError: 502,
}


async def _handle_repo_ingestion_error(request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, RepoIngestionError)
    status_code = _STATUS_CODES.get(type(exc), 400)
    return JSONResponse(
        status_code=status_code,
        content={"detail": exc.message, "error_code": exc.error_code},
    )


def register_repo_ingestion_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(RepoIngestionError, _handle_repo_ingestion_error)
