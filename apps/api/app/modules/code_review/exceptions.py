"""Code Review Engine — domain exceptions. Mirrors mentoring/exceptions.py."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class CodeReviewError(Exception):
    """Base for every code-review-domain error."""

    def __init__(self, message: str, error_code: str) -> None:
        super().__init__(message)
        self.message = message
        self.error_code = error_code


class ReviewNotFoundError(CodeReviewError):
    def __init__(self) -> None:
        super().__init__("Review not found.", "review_not_found")


class ReviewGenerationError(CodeReviewError):
    """Raised when the LLM Gateway fails outright, or returns
    unparseable content twice in a row (see content_builder.py) — a
    caller-visible 503, mirroring MentorReplyGenerationError."""

    def __init__(self, message: str) -> None:
        super().__init__(message, "review_generation_unavailable")


_STATUS_CODES: dict[type[CodeReviewError], int] = {
    ReviewNotFoundError: 404,
    ReviewGenerationError: 503,
}


async def _handle_code_review_error(request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, CodeReviewError)
    status_code = _STATUS_CODES.get(type(exc), 400)
    return JSONResponse(
        status_code=status_code,
        content={"detail": exc.message, "error_code": exc.error_code},
    )


def register_code_review_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(CodeReviewError, _handle_code_review_error)
