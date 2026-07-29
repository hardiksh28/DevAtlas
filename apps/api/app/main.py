from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.modules.auth.exceptions import register_auth_exception_handlers
from app.modules.auth.router import router as auth_router
from app.modules.code_review.router import router as code_review_router
from app.modules.cost_control.router import router as cost_control_router
from app.modules.curriculum.router import router as curriculum_router
from app.modules.effort_evaluation.router import router as effort_evaluation_router
from app.modules.knowledge.router import router as knowledge_router
from app.modules.lessons.router import router as lessons_router
from app.modules.llm_gateway.router import router as llm_gateway_router
from app.modules.mentoring.router import router as mentoring_router
from app.modules.progress_tracking.router import router as progress_tracking_router
from app.modules.repository_integration.router import router as repository_integration_router
from app.modules.stack_tiers.router import router as stack_tiers_router
from app.modules.taxonomy.router import router as taxonomy_router

settings = get_settings()

app = FastAPI(
    title="AI Engineering Workspace API",
    version="0.1.0",
    docs_url="/docs" if not settings.is_production else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_auth_exception_handlers(app)


@app.get("/health")
async def health() -> dict[str, str]:
    """Liveness probe — no DB/Redis/LLM calls, so it stays fast and cheap
    for container orchestrators to poll frequently."""
    return {"status": "ok", "environment": settings.environment}


# Each module owns its own router; main.py only wires them together — it
# is deliberately kept free of business logic per the architecture doc's
# "single choke point" pattern applied to routing.
for module_router in (
    auth_router,
    repository_integration_router,
    curriculum_router,
    taxonomy_router,
    lessons_router,
    mentoring_router,
    effort_evaluation_router,
    code_review_router,
    progress_tracking_router,
    knowledge_router,
    stack_tiers_router,
    llm_gateway_router,
    cost_control_router,
):
    app.include_router(module_router)
