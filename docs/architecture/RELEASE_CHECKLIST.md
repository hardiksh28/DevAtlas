# DevAtlas — Release Checklist

Run through this before the first production deploy, and before any release that touches
infra, auth, or the LLM Gateway. Companion to [`DEPLOYMENT.md`](./DEPLOYMENT.md) (how it's
deployed) and [`LAUNCH_READINESS_AUDIT.md`](./LAUNCH_READINESS_AUDIT.md) (what was found and
fixed to get here).

## Before the first production deploy

- [ ] All P0 items in `LAUNCH_READINESS_AUDIT.md` are fixed (they are, as of this pass —
      re-check if this file has drifted since).
- [ ] `.env` on the production host has real values, not the placeholders in `.env.example`:
  - [ ] `API_SECRET_KEY` — long, random, unique to this environment (startup fails if it's
        weak — `Settings._require_strong_secret_in_production`, `app/core/config.py`).
  - [ ] `OBJECT_STORAGE_*` point at real S3 (or another managed provider), **not** MinIO —
        the production compose command (`-f docker-compose.yml -f docker-compose.prod.yml`)
        no longer starts MinIO at all (fixed per P0 #3), so this is now enforced by topology,
        not just convention.
  - [ ] `API_DOMAIN`, `WEB_DOMAIN`, `CERTBOT_EMAIL` set for the SSL bootstrap.
  - [ ] `POSTGRES_*` credentials are production-grade, not the dev defaults.
- [ ] Host firewall allows only inbound 80/443 from the internet — Postgres/Redis/Ollama's
      ports in `docker-compose.yml` are for local dev convenience and are not meant to be
      internet-reachable in production (see `DEPLOYMENT.md` §3).
- [ ] Branch protection on `main` actually requires `ci.yml`'s checks to pass — `cd.yml` now
      also gates on this via `workflow_run` (fixed per P1 #8), but both should agree.
- [ ] SSL bootstrap performed once per domain (`DEPLOYMENT.md` §5's certbot `certonly` step),
      then `443` blocks restored in `infra/nginx/templates/default.conf.template`.
- [ ] `docker compose -f docker-compose.yml -f docker-compose.prod.yml run --rm api uv run
      alembic upgrade head` run before first traffic.
- [ ] `GET /health` and `GET /health/ready` both return 200 for `api`; `apps/web`'s
      `GET /api/health` returns 200.
- [ ] `backup` service is running and its first `pg_dump` has actually landed in the S3
      bucket — don't assume, check.
- [ ] Prometheus (`127.0.0.1:9090` on the host) is scraping `api:8000/metrics` — reachable
      only internally, and no longer reachable through the public nginx vhost (fixed per
      P1 #9).

## Every release

- [ ] CI green on the commit being deployed (enforced automatically now, but confirm).
- [ ] No new LLM-backed route shipped without a `llm_rate_limit(...)` dependency (see
      [`API.md`](./API.md)'s Rate limiting section) — this is the one convention most likely
      to be forgotten on a new feature, since nothing fails loudly if it's skipped.
- [ ] No new compose service exposes a port without a `127.0.0.1:` prefix unless it's meant
      to be public (only `nginx` should bind `80`/`443` to all interfaces).
- [ ] Any new required env var is added to the relevant `.env.example` (root, `apps/api`,
      `services/ingestion_worker`) with a placeholder, not left undocumented.
- [ ] Migrations, if any, are backward-compatible with the currently-running image for the
      duration of the rolling restart (add-column-nullable-then-backfill, not
      drop-column-in-the-same-release).
- [ ] Smoke test the golden path manually once: register → connect nothing needed → create a
      project → generate a roadmap → open the workspace → send one mentor message → submit
      one code review.

## Known gaps to carry into the next planning cycle

See `LAUNCH_READINESS_AUDIT.md`'s P2/P3 sections for the full list. The two worth flagging
explicitly at release time because they're product-facing, not just technical debt:

- The Effort & Evidence Evaluator isn't built — the mentor/review "hint ladder" is currently a
  prompt/response contract, not an enforced gate. Launch copy should describe what's actually
  shipped, not the full effort-gated vision in `ARCHITECTURE.md`.
- Cost & Abuse Control is a coarse per-user rate limiter (a stopgap, see `API.md`), not the
  full operation-weighted budget ledger — fine for an initial launch's traffic volume, revisit
  once there's real usage data to size real budgets against.
