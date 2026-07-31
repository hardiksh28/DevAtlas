# Build context is the monorepo root (not apps/api) so the uv workspace's
# packages/schemas and packages/object_storage resolve. See
# docker-compose.yml.

# --- Builder: resolve deps with uv into a project-local venv ---
FROM python:3.12-slim AS builder
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy PYTHONDONTWRITEBYTECODE=1
WORKDIR /app
RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock ./
COPY apps/api/pyproject.toml apps/api/pyproject.toml
COPY packages/schemas/pyproject.toml packages/schemas/pyproject.toml
COPY packages/object_storage/pyproject.toml packages/object_storage/pyproject.toml
RUN uv sync --package api --no-install-workspace --no-dev

COPY apps/api apps/api
COPY packages/schemas packages/schemas
COPY packages/object_storage packages/object_storage
RUN uv sync --package api --no-dev

# --- Runtime: slim image, non-root user, no build toolchain ---
FROM python:3.12-slim AS runtime
WORKDIR /app
RUN addgroup --system app && adduser --system --ingroup app app
COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/apps/api/. /app/
ENV PATH="/app/.venv/bin:$PATH" PYTHONUNBUFFERED=1
USER app
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8000/health', timeout=2).status == 200 else 1)"
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
