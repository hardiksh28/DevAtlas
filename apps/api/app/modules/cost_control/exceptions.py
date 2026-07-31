"""Cost & Abuse Control — exceptions.

Mirrors auth/exceptions.py's shape (one typed error, one handler,
registered once against the base class) so every module follows the
same convention.
"""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class CostControlError(Exception):
    def __init__(self, message: str, error_code: str) -> None:
        self.message = message
        self.error_code = error_code
        super().__init__(message)


class UsageLimitExceededError(CostControlError):
    """Raised by limits.py's dependency once a user exceeds the budget
    for a given LLM-backed operation. `retry_after` (seconds) becomes
    the response's Retry-After header."""

    def __init__(self, retry_after: int) -> None:
        super().__init__("Usage limit reached. Please try again later.", "usage_limit_exceeded")
        self.retry_after = retry_after


async def _handle_cost_control_error(request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, CostControlError)
    headers = None
    if isinstance(exc, UsageLimitExceededError):
        headers = {"Retry-After": str(exc.retry_after)}
    return JSONResponse(
        status_code=429,
        content={"detail": exc.message, "error_code": exc.error_code},
        headers=headers,
    )


def register_cost_control_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(CostControlError, _handle_cost_control_error)
