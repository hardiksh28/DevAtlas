# DevAtlas

An AI mentor that teaches by guiding, not generating. See [`docs/architecture/ARCHITECTURE.md`](docs/architecture/ARCHITECTURE.md) for the full system design — module boundaries, data flow, and the reasoning behind every stack choice below.

## Stack

| Layer | Choice |
|---|---|
| Frontend | Next.js (App Router), TypeScript, Tailwind CSS, Zustand, React Query |
| Backend | FastAPI, SQLAlchemy (async), Alembic |
| Database | PostgreSQL, `pgvector`, Redis |
| AI | Ollama (local inference), LangGraph (orchestration) |
| Infra | Docker, Docker Compose, GitHub Actions |

## Prerequisites

- Docker + Docker Compose
- Node.js 20+ and [pnpm](https://pnpm.io) (`corepack enable` will provide it)
- [uv](https://docs.astral.sh/uv/) for local (non-Docker) Python work
- ~8GB free disk for the Ollama model

## First-time setup

```bash
cp .env.example .env          # edit values if you're not using the defaults
pnpm install                  # installs apps/web + packages/ui
docker compose build
docker compose up -d postgres redis ollama
docker compose run --rm api uv run alembic upgrade head
docker compose up -d
```

The `ollama` container pulls `OLLAMA_MODEL` (default `llama3.1:8b`) on first boot — that alone can take several minutes depending on your connection; watch it with `docker compose logs -f ollama`.

## Running it

| Service | URL |
|---|---|
| Web | http://localhost:3000 |
| API | http://localhost:8000 (docs at `/docs`) |
| Ollama | http://localhost:11434 |
| Postgres | `localhost:5432` |
| Redis | `localhost:6379` |

Day-to-day frontend development is faster outside Docker (instant HMR):

```bash
docker compose up -d postgres redis ollama api worker
cp apps/web/.env.example apps/web/.env.local
pnpm --filter web dev
```

Running `apps/api` or `services/ingestion_worker` directly on the host (rather than in Docker) needs its own `.env`, copied from that directory's own `.env.example` — `pydantic-settings` resolves `.env` relative to the process's working directory, so the repo-root `.env` isn't picked up automatically, and the hostnames differ anyway (`postgres`/`redis`/`ollama` only resolve inside the Docker network; host processes need `localhost`):

```bash
cp apps/api/.env.example apps/api/.env
cp services/ingestion_worker/.env.example services/ingestion_worker/.env
```

Both `apps/api` and `services/ingestion_worker` are members of one **uv workspace** (root `pyproject.toml`) sharing a single `.venv`. Running plain `uv sync` from inside just one of them resyncs the shared venv to *only* that member's dependencies — which silently uninstalls what the other member needs. Use `uv sync --all-packages` from the repo root instead.

## Database migrations

```bash
# after changing a model in apps/api/app/modules/*/models.py:
docker compose exec api uv run alembic revision --autogenerate -m "describe the change"
docker compose exec api uv run alembic upgrade head
```

Migrations run inside the `api` container so they use the exact same dependency versions as the running app — running Alembic from your host risks a local Python/driver mismatch producing a migration that looks fine locally and fails in CI.

## Auth

Email/password auth (register/login/logout/forgot-reset-password/email-verification) is implemented — see [`docs/architecture/auth-api-v1.md`](docs/architecture/auth-api-v1.md) for the token model, cookie contract, and error codes. Reset/verification emails aren't actually sent yet (`apps/api/app/modules/auth/email.py`'s `ConsoleEmailSender` logs the link instead) since no email provider is configured — swap that module's factory once one is.

## Repository layout

```
apps/
  web/                 Next.js client
  api/                 FastAPI application (modular monolith — see modules/)
services/
  ingestion_worker/    arq background worker — corpus ingestion + freshness re-crawl
packages/
  schemas/             Shared Pydantic models (uv workspace)
  taxonomy-data/        Curated concept-taxonomy content
  ui/                  Shared React components (pnpm workspace)
infra/
  docker/              Non-Dockerfile infra assets (e.g. the Ollama entrypoint)
docs/
  architecture/        ARCHITECTURE.md and future ADRs
  decisions/           One file per significant decision, dated
```

## Tests & linting

```bash
pnpm --filter web lint && pnpm --filter web typecheck
cd apps/api && uv run ruff check . && uv run mypy app --ignore-missing-imports && uv run pytest
```

CI (`.github/workflows/ci.yml`) runs all of the above on every PR.
