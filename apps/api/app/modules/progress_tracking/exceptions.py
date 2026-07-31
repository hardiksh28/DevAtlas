"""Progress & Weakness Tracking Service — domain exceptions. Mirrors
curriculum/exceptions.py exactly."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class ProgressTrackingError(Exception):
    """Base for every progress-tracking-domain error."""

    def __init__(self, message: str, error_code: str) -> None:
        super().__init__(message)
        self.message = message
        self.error_code = error_code


class MilestoneNotFoundError(ProgressTrackingError):
    def __init__(self) -> None:
        super().__init__("Milestone not found.", "milestone_not_found")


class QuizNotAvailableError(ProgressTrackingError):
    def __init__(self) -> None:
        super().__init__(
            "This milestone has no generated quiz yet.", "quiz_not_available"
        )


class QuizAnswerMismatchError(ProgressTrackingError):
    def __init__(self) -> None:
        super().__init__(
            "Submitted answers don't match the quiz's question count.", "quiz_answer_mismatch"
        )


_STATUS_CODES: dict[type[ProgressTrackingError], int] = {
    MilestoneNotFoundError: 404,
    QuizNotAvailableError: 409,
    QuizAnswerMismatchError: 422,
}


async def _handle_progress_tracking_error(request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, ProgressTrackingError)
    status_code = _STATUS_CODES.get(type(exc), 400)
    return JSONResponse(
        status_code=status_code,
        content={"detail": exc.message, "error_code": exc.error_code},
    )


def register_progress_tracking_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(ProgressTrackingError, _handle_progress_tracking_error)
