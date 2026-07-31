"""Taxonomy & Concept Graph Service — domain exceptions.

Mirrors knowledge/exceptions.py exactly: service.py raises these, never
a bare HTTPException; main.py registers one handler for the base class.
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class TaxonomyError(Exception):
    """Base for every taxonomy-domain error."""

    def __init__(self, message: str, error_code: str) -> None:
        super().__init__(message)
        self.message = message
        self.error_code = error_code


class StackNotFoundError(TaxonomyError):
    """No curated concept taxonomy exists for this (stack, stack_version)
    pair — mirrors the Stack Support Tier Manager's 🔴 tier concept
    (ARCHITECTURE.md Section 3) rather than fabricating a taxonomy on
    the fly, which would violate "the LLM never modifies it directly."
    """

    def __init__(self, stack: str, stack_version: str) -> None:
        super().__init__(
            f"No curated taxonomy found for {stack} {stack_version}.", "stack_not_found"
        )


class TaxonomyValidationError(TaxonomyError):
    """Raised while parsing/validating a curated YAML file at seed time
    — a dangling prerequisite reference or a prerequisite cycle. Never
    raised at request time; a request only ever reads already-validated
    rows.
    """

    def __init__(self, message: str) -> None:
        super().__init__(message, "taxonomy_validation_error")


_STATUS_CODES: dict[type[TaxonomyError], int] = {
    StackNotFoundError: 404,
    TaxonomyValidationError: 500,
}


async def _handle_taxonomy_error(request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, TaxonomyError)
    status_code = _STATUS_CODES.get(type(exc), 400)
    return JSONResponse(
        status_code=status_code,
        content={"detail": exc.message, "error_code": exc.error_code},
    )


def register_taxonomy_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(TaxonomyError, _handle_taxonomy_error)
