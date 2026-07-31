# Contributing to DevAtlas

## Setup

Follow [`README.md`](README.md)'s "First-time setup" section. You'll need Docker,
Node 20+/pnpm, and [uv](https://docs.astral.sh/uv/).

## Project shape

DevAtlas is a modular monolith (see [`docs/architecture/ARCHITECTURE.md`](docs/architecture/ARCHITECTURE.md)
for the full reasoning) — one FastAPI app (`apps/api`) with strict per-feature module
boundaries under `apps/api/app/modules/`. Every module with real routes follows the same
shape:

```
modules/<name>/
  router.py       # thin HTTP layer only — extracts input, calls service.py, shapes output
  service.py      # all business logic
  models.py       # SQLAlchemy models
  schemas.py      # Pydantic request/response shapes + from_model() adapters
  exceptions.py   # typed errors + one registered exception handler for the module
```

Match this shape for any new module rather than inventing a new one — a reviewer should be
able to find "the logic" in the same place every time.

Other things worth knowing before you touch code:

- **LLM Orchestration Gateway is the only thing that ever calls the model provider.**
  Feature modules call `get_llm_gateway()`, never a provider SDK directly.
- **Two authorization boundaries never merge:** `Auth & Identity` (login) and
  `Repository Integration` (GitHub App, repo read access) are deliberately separate — don't
  let one module hold the other's tokens.
- Every project-scoped route depends on `get_owned_project` (404s on a project the caller
  doesn't own — never 403, so existence isn't leaked). Reuse it; don't hand-roll ownership
  checks.
- `services/ingestion_worker` never imports from `apps/api`, even where fields overlap
  (`WorkerConfig` vs. `Settings`) — it's the one component scoped for independent
  extraction later, and an import would quietly undo that.

## Before opening a PR

```bash
pnpm --filter web lint && pnpm --filter web typecheck && pnpm --filter web build
cd apps/api && uv run ruff check . && uv run mypy app --ignore-missing-imports && uv run pytest
cd services/ingestion_worker && uv run ruff check . && uv run pytest
```

CI (`.github/workflows/ci.yml`) runs all of the above on every PR — `.github/workflows/cd.yml`
only builds/pushes images once CI has actually passed on `main` (see
[`docs/architecture/DEPLOYMENT.md`](docs/architecture/DEPLOYMENT.md)), so a red CI run blocks
release, not just review.

A few conventions the test suites and linters enforce that are easy to miss by reading one
file in isolation:

- New Alembic migrations: `docker compose exec api uv run alembic revision --autogenerate -m "..."`
  (run inside the container — see README's "Database migrations" section for why).
- New LLM-backed routes should go through `app.modules.cost_control.limits.llm_rate_limit`
  (per-user budget) the same way the existing mentoring/code-review/curriculum/knowledge
  routes do — an LLM-backed route with no budget is exactly the gap
  [`docs/architecture/LAUNCH_READINESS_AUDIT.md`](docs/architecture/LAUNCH_READINESS_AUDIT.md)
  flagged as a launch blocker.
- Broad `except Exception` is allowed only at a documented LLM-output-parsing boundary
  (converting a provider/validation failure into a domain error) — narrow it to the specific
  exception type everywhere else.

## Commit / PR conventions

- Small, focused PRs over large ones — this codebase's module boundaries make that easy to
  do without breaking anything else.
- Write the commit message around *why*, not a restatement of the diff.
- If a change cuts a deliberate corner (a hardcoded ceiling, a stopgap rate limit, a stub),
  say so in a code comment naming the ceiling and what would trigger revisiting it — see
  the "Explicitly deferred" sections throughout `docs/architecture/*.md` for the existing
  style.
