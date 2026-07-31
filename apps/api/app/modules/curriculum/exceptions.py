"""Curriculum Engine — domain exceptions.

Mirrors knowledge/exceptions.py exactly: service.py raises these, never
a bare HTTPException; main.py registers one handler for the base class.
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class CurriculumError(Exception):
    """Base for every curriculum-domain error."""

    def __init__(self, message: str, error_code: str) -> None:
        super().__init__(message)
        self.message = message
        self.error_code = error_code


class RoadmapNotFoundError(CurriculumError):
    def __init__(self) -> None:
        super().__init__("This project has no roadmap yet.", "roadmap_not_found")


class MilestoneNotFoundError(CurriculumError):
    def __init__(self) -> None:
        super().__init__("Milestone not found.", "milestone_not_found")


class InvalidMilestoneTransitionError(CurriculumError):
    def __init__(self, current_status: str, requested_status: str) -> None:
        super().__init__(
            f"Cannot move a '{current_status}' milestone to '{requested_status}'.",
            "invalid_milestone_transition",
        )


class ContentGenerationError(CurriculumError):
    """Raised when the LLM Gateway fails outright, or returns
    unparseable content twice in a row (see content_builder.py) — a
    caller-visible 503, distinct from every other error here: it means
    the narration step is unavailable, not that the request was invalid.
    """

    def __init__(self, message: str) -> None:
        super().__init__(message, "content_generation_unavailable")


_STATUS_CODES: dict[type[CurriculumError], int] = {
    RoadmapNotFoundError: 404,
    MilestoneNotFoundError: 404,
    InvalidMilestoneTransitionError: 409,
    ContentGenerationError: 503,
}


async def _handle_curriculum_error(request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, CurriculumError)
    status_code = _STATUS_CODES.get(type(exc), 400)
    return JSONResponse(
        status_code=status_code,
        content={"detail": exc.message, "error_code": exc.error_code},
    )


def register_curriculum_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(CurriculumError, _handle_curriculum_error)
