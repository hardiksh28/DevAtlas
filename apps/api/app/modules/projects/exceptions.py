"""Project Workspace — domain exceptions.

Mirrors auth/exceptions.py exactly: service.py raises these, never a
bare HTTPException; main.py registers one handler per base class.
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class ProjectError(Exception):
    """Base for every project-domain error."""

    def __init__(self, message: str, error_code: str) -> None:
        super().__init__(message)
        self.message = message
        self.error_code = error_code


class ProjectNotFoundError(ProjectError):
    """Raised both when a project truly doesn't exist and when it
    exists but belongs to a different owner (or is already
    soft-deleted) — identical response either way. Distinguishing
    "not yours" from "doesn't exist" would let a caller enumerate
    other users' project IDs by status code alone, the same
    enumeration-safety reasoning auth's InvalidCredentialsError and
    InvalidOrExpiredTokenError already apply to logins and tokens.
    """

    def __init__(self) -> None:
        super().__init__("Project not found.", "project_not_found")


class InvalidProjectStateError(ProjectError):
    """Raised when a lifecycle transition doesn't make sense from the
    project's current state — e.g. archiving an already-deleted
    project."""

    def __init__(self, message: str) -> None:
        super().__init__(message, "invalid_project_state")


class ProjectLimitExceededError(ProjectError):
    """Raised when an owner is at `settings.max_active_projects_per_owner`
    — a plain ceiling, not a full quota system (see config.py), but
    without it project creation has no cost/abuse control at all,
    unlike every LLM-backed operation elsewhere in the app."""

    def __init__(self, limit: int) -> None:
        super().__init__(
            f"You've reached the limit of {limit} active projects. Archive or delete one to create another.",
            "project_limit_exceeded",
        )


_STATUS_CODES: dict[type[ProjectError], int] = {
    ProjectNotFoundError: 404,
    InvalidProjectStateError: 409,
    ProjectLimitExceededError: 422,
}


async def _handle_project_error(request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, ProjectError)
    status_code = _STATUS_CODES.get(type(exc), 400)
    return JSONResponse(
        status_code=status_code,
        content={"detail": exc.message, "error_code": exc.error_code},
    )


def register_project_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(ProjectError, _handle_project_error)
