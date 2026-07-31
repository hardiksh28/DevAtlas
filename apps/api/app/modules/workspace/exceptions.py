"""Interactive Learning Workspace — domain exceptions. Mirrors
curriculum/exceptions.py and mentoring/exceptions.py exactly.
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class WorkspaceError(Exception):
    """Base for every workspace-domain error."""

    def __init__(self, message: str, error_code: str) -> None:
        super().__init__(message)
        self.message = message
        self.error_code = error_code


class WorkspaceFileNotFoundError(WorkspaceError):
    def __init__(self) -> None:
        super().__init__("File not found.", "workspace_file_not_found")


class PathAlreadyExistsError(WorkspaceError):
    def __init__(self, path: str) -> None:
        super().__init__(f"A file already exists at '{path}'.", "workspace_path_already_exists")


class ContentConflictError(WorkspaceError):
    """Raised when a save's `expected_content_hash` doesn't match the
    currently stored hash — the file changed (elsewhere) since the
    client last read it. See docs/architecture/interactive-workspace-v1.md's
    file synchronization section for why this is last-write-wins-with-
    a-warning rather than a merge."""

    def __init__(self) -> None:
        super().__init__(
            "This file changed since you last loaded it.", "workspace_content_conflict"
        )


class FileTooLargeError(WorkspaceError):
    def __init__(self, max_bytes: int) -> None:
        super().__init__(
            f"File content cannot exceed {max_bytes} bytes.", "workspace_file_too_large"
        )


class FileLimitExceededError(WorkspaceError):
    def __init__(self, max_files: int) -> None:
        super().__init__(
            f"This project already has the maximum of {max_files} workspace files.",
            "workspace_file_limit_exceeded",
        )


_STATUS_CODES: dict[type[WorkspaceError], int] = {
    WorkspaceFileNotFoundError: 404,
    PathAlreadyExistsError: 409,
    ContentConflictError: 409,
    FileTooLargeError: 413,
    FileLimitExceededError: 400,
}


async def _handle_workspace_error(request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, WorkspaceError)
    status_code = _STATUS_CODES.get(type(exc), 400)
    return JSONResponse(
        status_code=status_code,
        content={"detail": exc.message, "error_code": exc.error_code},
    )


def register_workspace_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(WorkspaceError, _handle_workspace_error)
