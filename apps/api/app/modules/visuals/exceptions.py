"""Visual Learning Engine — domain exceptions. Mirrors code_review/exceptions.py."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class VisualError(Exception):
    """Base for every visual-learning-domain error."""

    def __init__(self, message: str, error_code: str) -> None:
        super().__init__(message)
        self.message = message
        self.error_code = error_code


class DiagramNotFoundError(VisualError):
    def __init__(self) -> None:
        super().__init__("Diagram not found.", "diagram_not_found")


class DiagramGenerationError(VisualError):
    """Raised when the LLM Gateway fails outright, or returns unparseable /
    unsafe content twice in a row (see content_builder.py) — a
    caller-visible 503, mirroring ReviewGenerationError."""

    def __init__(self, message: str) -> None:
        super().__init__(message, "diagram_generation_unavailable")


_STATUS_CODES: dict[type[VisualError], int] = {
    DiagramNotFoundError: 404,
    DiagramGenerationError: 503,
}


async def _handle_visual_error(request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, VisualError)
    status_code = _STATUS_CODES.get(type(exc), 400)
    return JSONResponse(
        status_code=status_code,
        content={"detail": exc.message, "error_code": exc.error_code},
    )


def register_visual_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(VisualError, _handle_visual_error)
