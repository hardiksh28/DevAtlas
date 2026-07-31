"""Mentoring Engine — domain exceptions. Mirrors curriculum/exceptions.py."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class MentoringError(Exception):
    """Base for every mentoring-domain error."""

    def __init__(self, message: str, error_code: str) -> None:
        super().__init__(message)
        self.message = message
        self.error_code = error_code


class MentorReplyGenerationError(MentoringError):
    """Raised when the LLM Gateway fails outright, or returns
    unparseable content twice in a row (see content_builder.py) — a
    caller-visible 503, mirroring curriculum's ContentGenerationError."""

    def __init__(self, message: str) -> None:
        super().__init__(message, "mentor_reply_unavailable")


_STATUS_CODES: dict[type[MentoringError], int] = {
    MentorReplyGenerationError: 503,
}


async def _handle_mentoring_error(request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, MentoringError)
    status_code = _STATUS_CODES.get(type(exc), 400)
    return JSONResponse(
        status_code=status_code,
        content={"detail": exc.message, "error_code": exc.error_code},
    )


def register_mentoring_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(MentoringError, _handle_mentoring_error)
