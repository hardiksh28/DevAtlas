# DevAtlas — Launch Readiness Audit

**Date:** 2026-07-30
**Scope:** apps/web, apps/api, services/ingestion_worker, packages/*, infra/*, .github/workflows/*
**Method:** four parallel read-only audits (frontend, backend, infra/deployment, ingestion worker + packages), each verifying claims in `ARCHITECTURE.md`/`DEPLOYMENT.md` against actual code rather than trusting the docs.

**Headline:** this codebase is unusually disciplined for a pre-launch SaaS — consistent design tokens, real IDOR protection, tested SSRF defense-in-depth, Argon2id done correctly, N+1 avoidance applied deliberately throughout. The gaps below are real but narrow: a handful of P0/P1 items blocked launch, everything else is hardening or documented tech debt.

**Update, same pass:** all 5 P0 blockers and all 9 actionable P1 items below are now fixed and
verified (lint/typecheck/tests green on every changed package). Item #14 is a product-scope
decision, not a code fix, and is carried forward as-is. Findings are left in place rather than
deleted so the "what was wrong and why" reasoning stays attached to the fix.

Severity key: **P0** = must fix before launch (security/data-loss risk or contradicts a documented production claim) · **P1** = should fix before launch (real but contained blast radius) · **P2** = fix soon after launch · **P3** = tracked tech debt / future improvement.

---

## P0 — Blockers

| # | Area | Finding | Fix | Status |
|---|---|---|---|---|
| 1 | Backend security | `POST /v1/llm-gateway/generate` (`apps/api/app/modules/llm_gateway/router.py`) has no auth dependency and is unconditionally mounted in `main.py` in every environment. Docstring says "local verification only" but nothing enforces that — an unauthenticated caller gets a free, unmetered LLM proxy. | Require `Depends(get_current_user)`, or don't mount the route when `settings.environment == "production"`. | ✅ Fixed — both: route now requires `get_current_user`, and `main.py` only includes the router when `not settings.is_production`. |
| 2 | Backend security | Cost & Abuse Control module (`modules/cost_control/router.py`) is an empty stub — zero enforcement of the `usage_ledger` anywhere in the codebase. Every LLM-backed route (mentoring, code review, curriculum narration, `/documents/ask`) has no per-user budget or rate limit. | Minimum viable: a per-user/day request-count or token-count cap in Redis before launch; full cost-unit ledger can follow. | ✅ Fixed — `cost_control/limits.py`'s `llm_rate_limit` (per-user, Redis fixed-window, fails open) wired onto mentor chat, code review submission, milestone content generation, and document Q&A. See `API.md`. |
| 3 | Infra/prod | The documented production stack ("production uses real S3 instead of MinIO") doesn't hold up: `docker-compose.yml` has `api`/`worker` hard-depend on `minio: condition: service_healthy`, and `docker-compose.prod.yml` never overrides it — MinIO with root credentials ships on public ports (`9000`/`9001`) in every deployment, including prod. | Make `api`/`worker`'s MinIO dependency conditional (profile or override in `docker-compose.prod.yml` that removes it), or bind MinIO to `127.0.0.1` and rotate to non-root creds if it's staying. | ✅ Fixed — MinIO + its `api`/`worker` dependency moved entirely into `docker-compose.override.yml` (dev-only), bound to `127.0.0.1`. The prod command no longer starts or waits on it at all. |
| 4 | Ingestion worker | Retry-exhaustion leaves rows stuck forever: once arq's `max_tries` is exhausted, nothing transitions the `ingestion_jobs`/`project_documents` row to `failed`. Combined with finding below, a rate-limited GitHub/website fetch permanently wedges a job with no user-visible failure and no alerting. | Add a terminal on-give-up hook (arq `on_job_failure` or a wrapping try/except around the retryable call) that marks the row `failed` with a reason. | ✅ Fixed — each job function now checks `ctx["job_try"]` against its named max-tries constant on the last allowed attempt and records a terminal `failed` status instead of letting arq silently give up. |
| 5 | Ingestion worker | 429/403 responses from GitHub/crawled sites are misclassified as `PermanentIngestionError` (`pipeline/fetch.py`) instead of triggering backoff — a normal rate-limit response kills the job outright. | Special-case 403/429 into `RetryableIngestionError` with backoff (respect `Retry-After` if present). | ✅ Fixed — `safe_get` now raises `RetryableIngestionError` for 403/429 specifically, ahead of the generic `>=400` branch. |

## P1 — Fix before launch

| # | Area | Finding | Fix | Status |
|---|---|---|---|---|
| 6 | Frontend | No `error.tsx`/`global-error.tsx` anywhere under `apps/web/src/app` — any render exception falls through to Next's default unbranded error screen. | Add a root `error.tsx` (and one for the workspace route) with on-brand recovery UI + reset(). | ✅ Fixed — `app/error.tsx` (reuses `ErrorState`) and `app/global-error.tsx` (self-contained, for root-layout failures) added. |
| 7 | Frontend | The in-browser workspace (`components/workspace/*`, Monaco/panels/terminal) has zero responsive breakpoints — unusable on a phone, no stacked/drawer fallback the way `AppShell.tsx` has for its sidebar. | Either gate the workspace route behind a "use a larger screen" notice on small viewports, or ship a real responsive layout — flagging as a product decision, not purely technical. | ✅ Fixed (gating chosen) — the workspace route now checks a `min-width: 1024px` media query client-side and shows a "needs a larger screen" notice below it, so `WorkspaceShell` (and Monaco's bundle/data fetching) never mounts on mobile. A full responsive redesign remains open if the product wants workspace-on-mobile later. |
| 8 | Infra/CI | `cd.yml` pushes images to GHCR on every push to `main`/tags with no dependency on `ci.yml` passing — only "assumes main is branch-protected," which is unverifiable from the repo. | Add `workflow_run` gating on ci.yml success, or verify + document branch protection is actually configured on GitHub. | ✅ Fixed — `cd.yml` now triggers on `workflow_run` of CI (main pushes only proceed if `conclusion == 'success'`); tag pushes keep their own direct trigger since they're a deliberate post-CI release action. |
| 9 | Infra/security | `/metrics` is reachable through the public nginx vhost (no `location /metrics { deny all; }`), contradicting the "Prometheus scrape is localhost-only" framing — the same endpoint is also internet-facing. | Add an explicit deny/allow block for `/metrics` in `infra/nginx/templates/default.conf.template`. | ✅ Fixed — `location /metrics { deny all; }` added to the API server block. |
| 10 | Infra/reliability | `web` service uses plain `depends_on: - api` (no `condition: service_healthy`), inconsistent with every other service's correct health-gated startup. | Switch to `condition: service_healthy` once `api`'s healthcheck is confirmed reliable at cold start. | ✅ Fixed — `web` now depends on `api: condition: service_healthy` (api's Dockerfile already ships a `HEALTHCHECK`). |
| 11 | Infra/build | Root `.dockerignore` doesn't exclude `apps/api`/`services/ingestion_worker` from the `web` image's build context, bloating every web build with unrelated Python source. | Add those paths (and their lockfiles/tests) to `.dockerignore`. | ✅ Fixed — `apps/api`, `services`, `packages/schemas`, `packages/taxonomy-data`, `packages/object_storage`, and Python cache dirs added. |
| 12 | Ingestion worker | PDF parsing (`pipeline/parsers/pdf.py`) has no page-count or decompressed-size ceiling — only compressed upload size is bounded, so a crafted small PDF can expand into a large in-memory document. | Cap page count and/or extracted text length, fail the doc past the ceiling rather than the whole worker. | ✅ Fixed — `parse_pdf` now takes required `max_pages`/`max_extracted_chars`, checked before/during extraction, raising `PermanentIngestionError` past either ceiling. Configurable via `WorkerConfig`. |
| 13 | Ingestion worker | CPU-bound parsing/chunking (pypdf, BeautifulSoup, chunking) runs synchronously on the event loop with no `asyncio.to_thread` offload — a large PDF/HTML page stalls the entire worker process, including other concurrent jobs. | Wrap the parse/chunk calls in `asyncio.to_thread` the same way `LocalObjectStorage` already offloads I/O. | ✅ Fixed — PDF parsing, HTML-to-markdown conversion, and chunking are all now offloaded via `asyncio.to_thread` in `worker.py`. |
| 14 | Backend accessibility of test | Five architecture-doc modules (`repository_integration`, `effort_evaluation`, `stack_tiers`, `cost_control`, `lessons`) are empty stub routers — expected per the architecture doc's own phasing, but confirm the actual launch scope doesn't imply "hints are effort-gated" when the Effort Evaluator isn't built yet (product-facing claim risk, not a code bug). | Product decision: adjust launch copy/scope, or fast-follow the Effort Evaluator. | ⏳ Not a code fix — carried into `RELEASE_CHECKLIST.md`'s "known gaps" section as a launch-copy/scope decision for the team. |

## P2 — Fix soon after launch

- CORS `allow_methods`/`allow_headers` wildcarded on top of an explicit origin allow-list (`apps/api/app/main.py`) — tighten to actual verb/header set.
- Ollama HTTP client (`llm_gateway/providers/ollama_provider.py`) has no request timeout — a hung backend hangs the request indefinitely.
- No CI vulnerability scanning/SBOM for the three pushed images (Trivy/Grype step).
- No pytest coverage gate in CI (`--cov` + threshold).
- Backup container (`infra/docker/backup/Dockerfile`) runs as root, unlike every other container in the stack, while holding the most sensitive combined credentials.
- No resource limits (`mem_limit`/`cpus`) on any compose service — `ollama` in particular can exhaust host resources with no ceiling.
- Floating `:latest` tags on 5 base images (ollama, minio, minio/mc, certbot, prometheus).
- `apps/web/Dockerfile`'s `pnpm install --frozen-lockfile || pnpm install` fallback can silently build from a drifted lockfile that CI never tested.
- No route-level `loading.tsx` anywhere in `apps/web` — pages rely on client `isLoading` flags instead of Suspense streaming (blank flash on slow first paint).
- Missing Open Graph/Twitter card metadata and `robots.txt`/`sitemap.xml` on the public landing page.
- `DiagramsPanel.tsx` form controls (select/textarea) lack label associations, unlike every other form in the app.
- No skip-link to main content in `AppShell.tsx`.
- Ingestion worker: no concurrency limiter around Ollama embed calls (arq default `max_jobs=10`, uncapped) — a large repo ingest can fire up to 10 simultaneous embed batches at one instance.
- Ingestion worker test coverage gap: `discover_github_documents`, `discover_website_documents`, `process_document`, and the github/website parsers' size/count ceilings have no dedicated tests — exactly where the audited security claims live.
- `nginx` `default.conf.template` duplicates identical header blocks across two server blocks with no shared `include` snippet.

## P3 — Tech debt / recommended future improvements

- **Effort & Evidence Evaluator, Stack Support Tier Manager, Repository Integration (write access), Lessons module** — documented stubs per `ARCHITECTURE.md`'s own phasing; the mentoring/review "hint ladder" currently runs as a prompt/response contract, not an enforced state machine gated by real evidence. This is the single largest gap between the architecture document's differentiator claim and what's shipped.
- Heavy `# type: ignore[attr-defined]` usage across every module's `schemas.py` `from_model` adapters (dozens of instances) — consistent pattern, but the largest lint-suppression surface in the codebase; worth a real fix (typed `Mapped[...]` columns) once there's time.
- No dedicated FK index on `messages.milestone_id`/`code_reviews.milestone_id` — fine at current query patterns, revisit if a future feature filters by milestone across conversations.
- `workspace/router.py`'s `/tree` endpoint returns the whole file tree unpaginated, relying on the `max_workspace_files_per_project=300` ceiling rather than true pagination.
- No cumulative per-project storage/document-count quota across sequential (non-concurrent) ingestion jobs — only concurrent-job count is capped today.
- Automated restore-drill tooling for backups doesn't exist (manual runbook only) — acceptable per DEPLOYMENT.md's own reasoning, revisit once real user data exists.
- Dedicated vector DB, Kubernetes, multi-region — all correctly deferred per `ARCHITECTURE.md`'s existing "Scalability & Growth Path" section; no new recommendation beyond what's already documented there.

---

## Positive findings worth preserving (don't "fix" these by accident)

- SSRF defense-in-depth in the ingestion worker (`pipeline/fetch.py`) is real, tested, and handles DNS rebinding correctly per-redirect-hop.
- Argon2id password hashing with `needs_rehash` upgrade path, opaque/hashed/rotated refresh tokens, enumeration-safe auth responses.
- IDOR protection via a consistent `get_owned_project` → 404-not-403 pattern across every module.
- `selectinload`/`joinedload` used deliberately, not accidentally, everywhere N+1 risk exists.
- Frontend empty-state and API-error-surfacing patterns (`EmptyState`, `parseErrorMessage`, `role="alert"`) are applied consistently across every page — a genuine strength, not a gap.
- File upload validation checks magic bytes, not just extension, and blocks loopback/`.local`/`.internal` hosts pre-fetch.

---

## Recommended fix order

1. ~~P0 #1–#5 (security/production-correctness blockers)~~ — done, this pass.
2. ~~P1 #6–#13~~ — done, this pass. P1 #14 is a scope decision, carried to `RELEASE_CHECKLIST.md`.
3. P2 — first post-launch sprint.
4. P3 — tracked, revisit at the triggers already named in `ARCHITECTURE.md`'s Scalability & Growth Path section.

## Verification notes

Every fix above was linted (`ruff`), type-checked (`mypy`/`tsc`), and run against its existing
test suite (`pytest`, `next lint`) after the change — all green except one pre-existing,
unrelated failure: `apps/api/tests/test_auth_router.py::TestPasswordReset::test_full_reset_cycle`
fails under the local SQLite test fallback (fails identically in isolation, on code untouched by
this pass) — this matches `README.md`'s own documented caveat that the SQLite fallback "can't
exercise CITEXT/INET," which is why CI runs the full suite against real Postgres. Not fixed here
since it's outside this audit's scope and isn't reproducible against the real dialect.
