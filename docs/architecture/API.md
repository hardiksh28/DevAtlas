# DevAtlas API — Reference

This is the cross-cutting reference (auth, errors, pagination, rate limits) that doesn't fit
in any single endpoint's schema. For exact request/response shapes, use the live interactive
docs — this file intentionally doesn't duplicate them, since a hand-maintained copy of every
schema goes stale the moment a `schemas.py` changes and FastAPI's own generation doesn't.

- **Interactive docs (Swagger UI):** `GET /docs` — enabled outside production only
  (`app/main.py`; `docs_url=None` when `ENVIRONMENT=production`).
- **Raw OpenAPI schema:** `GET /openapi.json` — same availability.
- **Module responsibilities / data flow / why each module exists:**
  [`ARCHITECTURE.md`](./ARCHITECTURE.md).

## Auth

Cookie-based (httpOnly `access_token`/`refresh_token`, set by `/v1/auth/login` and
`/v1/auth/register`) is the primary model for the web client; an `Authorization: Bearer
<token>` header also works for non-browser clients (tests, scripts, future integrations) — see
[`auth-api-v1.md`](./auth-api-v1.md) for the full token/cookie contract and error codes.
Every project-scoped route additionally checks resource ownership via `get_owned_project`,
which 404s (never 403) on a project the caller doesn't own, so existence is never leaked
through the status code.

## Route map

Route groups, by prefix (tag shown alongside — see `/docs` for the full endpoint list within
each):

| Prefix | Tag |
|---|---|
| `/v1/auth` | Auth & Identity |
| `/v1/projects`, `/v1/dashboard` | Project Workspace |
| `/v1/projects/{project_id}/workspace` | Interactive Learning Workspace |
| `/v1/projects/{project_id}/documents` | Documentation Ingestion (Knowledge System) |
| `/v1/projects/{project_id}/roadmap` | Curriculum Engine — Roadmap |
| `/v1/projects/{project_id}/mentor` | Mentoring — Conversational Mentor |
| `/v1/projects/{project_id}/reviews` | Code Review Engine — Reviews |
| `/v1/projects/{project_id}/diagrams` | Visual Learning Engine |
| `/v1/projects/{project_id}/progress` | Progress & Weakness Tracking — Quiz |
| `/v1/progress` | Progress & Weakness Tracking |
| `/v1/taxonomy` | Taxonomy & Concept Graph |
| `/v1/knowledge`, `/v1/curriculum`, `/v1/mentoring`, `/v1/code-review`, `/v1/lessons`, `/v1/stack-tiers`, `/v1/repository-integration`, `/v1/effort-evaluation`, `/v1/cost-control` | Pre-existing stub routers for modules not yet built out (see ARCHITECTURE.md's phasing) |
| `/v1/llm-gateway` | Debug-only gateway passthrough — authenticated, and not mounted at all when `ENVIRONMENT=production` (see `app/main.py`) |
| `/health`, `/health/ready`, `/metrics` | Liveness / readiness / Prometheus — see `DEPLOYMENT.md` |

## Error shape

Every module raises its own typed exception hierarchy, caught by exactly one registered
handler per module (`register_*_exception_handlers` in each module's `exceptions.py`). Every
error response has the same shape regardless of which module raised it:

```json
{ "detail": "human-readable message", "error_code": "machine_readable_code" }
```

A `429` additionally carries a `Retry-After` header (seconds).

## Pagination

List endpoints take `limit`/`offset` query params, capped server-side (`le=100` or similar —
see the specific endpoint's schema in `/docs`). There is no cursor-based pagination.

## Rate limiting

Two independent limiters, both Redis-backed fixed-window counters, both **fail open** (an
unreachable Redis must never take a route down entirely):

- **Per-IP, on auth routes** (`app/modules/auth/rate_limit.py`) — guards
  register/login/forgot-password/etc. against credential-spraying and inbox-spam abuse, not
  tied to a logged-in user.
- **Per-user, on LLM-backed routes** (`app/modules/cost_control/limits.py`) — guards mentor
  chat, code review submission, milestone content generation, and document Q&A against
  unbounded per-account model spend. Add `dependencies=[llm_rate_limit("<op>", times=N,
  seconds=S)]` to any new route that calls the LLM Gateway; see the existing call sites in
  `mentoring/router.py`, `code_review/router.py`, `curriculum/router.py`, and
  `knowledge/router.py` for the pattern. This is a coarse stopgap, not the full
  operation-weighted cost ledger ARCHITECTURE.md's Cost & Abuse Control module describes —
  see [`LAUNCH_READINESS_AUDIT.md`](./LAUNCH_READINESS_AUDIT.md) P0 #2 for why it exists and
  what's still deferred.
