from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from sqlalchemy import text

from app.core.config import get_settings
from app.core.database import engine
from app.core.logging import configure_logging
from app.core.redis import redis_client
from app.modules.auth.exceptions import register_auth_exception_handlers
from app.modules.auth.router import router as auth_router
from app.modules.code_review.exceptions import register_code_review_exception_handlers
from app.modules.code_review.router import review_router
from app.modules.code_review.router import router as code_review_router
from app.modules.cost_control.exceptions import register_cost_control_exception_handlers
from app.modules.cost_control.router import router as cost_control_router
from app.modules.curriculum.exceptions import register_curriculum_exception_handlers
from app.modules.curriculum.router import roadmap_router
from app.modules.curriculum.router import router as curriculum_router
from app.modules.effort_evaluation.router import router as effort_evaluation_router
from app.modules.knowledge.exceptions import register_knowledge_exception_handlers
from app.modules.knowledge.router import project_documents_router
from app.modules.knowledge.router import router as knowledge_router
from app.modules.lessons.router import router as lessons_router
from app.modules.llm_gateway.router import router as llm_gateway_router
from app.modules.mentoring.exceptions import register_mentoring_exception_handlers
from app.modules.mentoring.router import mentor_router
from app.modules.mentoring.router import router as mentoring_router
from app.modules.progress_tracking.exceptions import register_progress_tracking_exception_handlers
from app.modules.progress_tracking.router import progress_router, quiz_router
from app.modules.progress_tracking.router import router as progress_tracking_router
from app.modules.projects.exceptions import register_project_exception_handlers
from app.modules.projects.router import dashboard_router as projects_dashboard_router
from app.modules.projects.router import router as projects_router
from app.modules.repository_integration.router import router as repository_integration_router
from app.modules.stack_tiers.router import router as stack_tiers_router
from app.modules.taxonomy.exceptions import register_taxonomy_exception_handlers
from app.modules.taxonomy.router import router as taxonomy_router
from app.modules.visuals.exceptions import register_visual_exception_handlers
from app.modules.visuals.router import router as visuals_router
from app.modules.workspace.exceptions import register_workspace_exception_handlers
from app.modules.workspace.router import router as workspace_router
from app.modules.workspace.router import workspace_files_router

settings = get_settings()
configure_logging(json_output=settings.is_production)

app = FastAPI(
    title="DevAtlas API",
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

# Exposes GET /metrics for Prometheus to scrape (request count/latency by
# route+status). docs_url is already hidden in production above; /metrics
# has no sensitive data (route templates + counts, not payloads) so it's
# left open here — put it behind the reverse proxy/network policy in
# infra/nginx if it shouldn't be public.
Instrumentator().instrument(app).expose(app)

register_auth_exception_handlers(app)
register_project_exception_handlers(app)
register_knowledge_exception_handlers(app)
register_taxonomy_exception_handlers(app)
register_curriculum_exception_handlers(app)
register_mentoring_exception_handlers(app)
register_code_review_exception_handlers(app)
register_visual_exception_handlers(app)
register_workspace_exception_handlers(app)
register_progress_tracking_exception_handlers(app)
register_cost_control_exception_handlers(app)


@app.get("/health")
async def health() -> dict[str, str]:
    """Liveness probe — no DB/Redis/LLM calls, so it stays fast and cheap
    for container orchestrators to poll frequently."""
    return {"status": "ok", "environment": settings.environment}


@app.get("/health/ready")
async def health_ready() -> dict[str, str]:
    """Readiness probe: confirms Postgres and Redis are actually reachable,
    unlike /health above. Use this one for load-balancer/orchestrator
    "is it safe to route traffic here yet" checks, not for high-frequency
    liveness polling."""
    async with engine.connect() as conn:
        await conn.execute(text("SELECT 1"))
    await redis_client.ping()
    return {"status": "ok"}


# Each module owns its own router; main.py only wires them together — it
# is deliberately kept free of business logic per the architecture doc's
# "single choke point" pattern applied to routing.
for module_router in (
    auth_router,
    projects_router,
    projects_dashboard_router,
    repository_integration_router,
    curriculum_router,
    roadmap_router,
    taxonomy_router,
    lessons_router,
    mentoring_router,
    mentor_router,
    effort_evaluation_router,
    code_review_router,
    review_router,
    visuals_router,
    progress_tracking_router,
    quiz_router,
    progress_router,
    knowledge_router,
    project_documents_router,
    workspace_router,
    workspace_files_router,
    stack_tiers_router,
    cost_control_router,
):
    app.include_router(module_router)

# Debug-only route for exercising the LLM gateway directly over HTTP
# (confirming Ollama is reachable). Authenticated (see router.py), but
# still excluded entirely in production so it's never live traffic there.
if not settings.is_production:
    app.include_router(llm_gateway_router)
