# Build context is the monorepo root (not services/ingestion_worker) so
# the uv workspace's packages/schemas and packages/object_storage resolve.
# See docker-compose.yml.

FROM python:3.12-slim AS builder
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy PYTHONDONTWRITEBYTECODE=1
WORKDIR /app
RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock ./
COPY services/ingestion_worker/pyproject.toml services/ingestion_worker/pyproject.toml
COPY packages/schemas/pyproject.toml packages/schemas/pyproject.toml
COPY packages/object_storage/pyproject.toml packages/object_storage/pyproject.toml
RUN uv sync --package ingestion-worker --no-install-workspace --no-dev

COPY services/ingestion_worker services/ingestion_worker
COPY packages/schemas packages/schemas
COPY packages/object_storage packages/object_storage
RUN uv sync --package ingestion-worker --no-dev

FROM python:3.12-slim AS runtime
WORKDIR /app
RUN addgroup --system app && adduser --system --ingroup app app
COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/services/ingestion_worker/. /app/
ENV PATH="/app/.venv/bin:$PATH" PYTHONUNBUFFERED=1
USER app
# arq's own --check flag reads the health-check key it writes to Redis
# (WorkerSettings.health_check_interval) — no separate HTTP endpoint needed.
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
  CMD arq worker.WorkerSettings --check
CMD ["arq", "worker.WorkerSettings"]
