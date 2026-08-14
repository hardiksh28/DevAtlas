"""Build Plan — domain exceptions.

Mirrors curriculum/exceptions.py exactly: service.py raises these,
never a bare HTTPException; main.py registers one handler for the base
class.
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class BuildPlanError(Exception):
    """Base for every build-plan-domain error."""

    def __init__(self, message: str, error_code: str) -> None:
        super().__init__(message)
        self.message = message
        self.error_code = error_code


class BuildPlanNotFoundError(BuildPlanError):
    def __init__(self) -> None:
        super().__init__("This project has no build plan yet.", "build_plan_not_found")


class StepNotFoundError(BuildPlanError):
    def __init__(self) -> None:
        super().__init__("Build plan step not found.", "build_plan_step_not_found")


class ProjectDescriptionMissingError(BuildPlanError):
    def __init__(self) -> None:
        super().__init__(
            "Add a project description before generating a build plan — the plan is "
            "generated from it.",
            "project_description_missing",
        )


class InvalidStepTransitionError(BuildPlanError):
    def __init__(self, current_status: str, requested_status: str) -> None:
        super().__init__(
            f"Cannot move a '{current_status}' step to '{requested_status}'.",
            "invalid_step_transition",
        )


class PlanGenerationError(BuildPlanError):
    """Raised when the LLM Gateway fails outright, or returns
    unparseable content twice in a row (see content_builder.py) — a
    caller-visible 503, distinct from every other error here: it means
    the generation step is unavailable, not that the request was
    invalid."""

    def __init__(self, message: str) -> None:
        super().__init__(message, "plan_generation_unavailable")


_STATUS_CODES: dict[type[BuildPlanError], int] = {
    BuildPlanNotFoundError: 404,
    StepNotFoundError: 404,
    ProjectDescriptionMissingError: 422,
    InvalidStepTransitionError: 409,
    PlanGenerationError: 503,
}


async def _handle_build_plan_error(request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, BuildPlanError)
    status_code = _STATUS_CODES.get(type(exc), 400)
    return JSONResponse(
        status_code=status_code,
        content={"detail": exc.message, "error_code": exc.error_code},
    )


def register_build_plan_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(BuildPlanError, _handle_build_plan_error)
