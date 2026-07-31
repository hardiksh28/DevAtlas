# DevAtlas — Production Deployment (Step 13)

Companion to [ARCHITECTURE.md](./ARCHITECTURE.md). That document covers the
application's module boundaries; this one covers what runs it in production.

## 1. Deployment architecture

Single-host Docker Compose, fronted by nginx — not Kubernetes, not managed
container services. DevAtlas is a modular monolith by design (ARCHITECTURE.md
§1); its deployment topology should match that until there's a concrete
reason not to.

```
Internet
   │  :80/:443
   ▼
 nginx  ── TLS termination, gzip, rate limiting, security headers
   │  (docker network, unencrypted — trusted internal hop)
   ├─→ web (Next.js standalone server, :3000)
   └─→ api (FastAPI/uvicorn, :8000)
             ├─→ postgres (pgvector) ── persistent volume
             ├─→ redis                ── cache + rate limits + arq queue
             ├─→ minio / real S3      ── ingested documents
             └─→ ollama               ── local LLM inference
 worker (arq) ── consumes the same redis queue, writes to postgres + storage
 prometheus  ── scrapes api:8000/metrics, localhost-only
 certbot     ── renews TLS certs into a shared volume nginx reads
 backup      ── daily pg_dump → gzip → S3, sidecar container
```

Two Compose files layer on top of the shared `docker-compose.yml` base:
- `docker-compose.override.yml` — dev-only (source bind-mounts, uvicorn
  `--reload`, and the local MinIO service standing in for real S3). Auto-merged
  by plain `docker compose up`; irrelevant in prod — the base file's `api`/
  `worker` services have no dependency on MinIO, so the production command
  below never starts or waits on it.
- `docker-compose.prod.yml` — additive prod-only services (nginx, certbot,
  prometheus, backup). Run explicitly:
  `docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d`.

**CI/CD:** `.github/workflows/ci.yml` (unchanged) lints/type-checks/tests
every PR. `.github/workflows/cd.yml` builds and pushes the three service
images (`api`, `web`, `worker`) to GHCR on every push to `main` and on
`v*.*.*` tags, tagged by both `latest` and short SHA. It assumes `main` is
branch-protected on CI's checks — it does not re-run tests itself. Deploying
a new image to the host is `docker compose pull && docker compose -f ... up
-d` (a manual or `workflow_run`-triggered SSH step); which one depends on
where the host actually lives, so it isn't guessed at here.

## 2. Scalability

The monolith's own module boundaries already say where the first scaling
pressure will land (ARCHITECTURE.md §1): the ingestion/embedding worker.
It's already queue-based and stateless per-job, so it scales horizontally
today with zero code changes — `docker compose up --scale worker=3`. The
`api` service is equally stateless (JWT auth, no in-process session state)
and scales the same way behind nginx's existing `proxy_pass`.

What does *not* scale by adding replicas: Postgres and Redis, both
single-instance here. That's an intentional V1 boundary, not an oversight —
read replicas, Redis Cluster, or a managed Postgres (RDS/Cloud SQL) are the
next steps, and none of them change application code, only the connection
string and infra. Not built now because there's no load data yet to size
them against.

## 3. Security

- **Transport:** TLS 1.2+ via nginx + Let's Encrypt (certbot), HSTS, HTTP→HTTPS
  redirect. Internal docker-network traffic (nginx→api/web) is plaintext by
  design — it never leaves the host's network namespace.
- **Secrets:** `.env` (gitignored) is the single source for all credentials;
  `Settings._require_strong_secret_in_production` (apps/api/app/core/config.py)
  fails startup if `API_SECRET_KEY` is short — a weak JWT signing key can't
  quietly reach production.
- **Containers:** every image already ran as non-root before this step
  (Dockerfiles' `USER app`/`USER nextjs`); this step adds `.dockerignore` per
  build context so `.env`, `.venv`, and `__pycache__` never end up baked into
  a layer.
- **Network exposure:** only nginx binds `80`/`443` publicly. Postgres/Redis/
  MinIO/Ollama ports in `docker-compose.yml` are for local dev convenience —
  in production, put the host behind a security group/firewall that only
  allows inbound 80/443 from the internet (compose's port-list merge
  semantics make surgically removing them via an override file more fragile
  than a firewall rule, so that's the boundary, not the compose file).
- **Rate limiting:** nginx `limit_req` (20 r/s, burst 40) on the API server
  block — a first line of defense in front of the app's own
  Cost & Abuse Control module (ARCHITECTURE.md §1).

## 4. Observability

- **Logging:** stdlib `logging`, JSON-formatted lines to stdout when
  `ENVIRONMENT=production` (`app/core/logging.py`, mirrored in
  `services/ingestion_worker/worker.py`), plain text otherwise. Shipping/
  rotation is deliberately not this app's job — stdout is captured by
  Docker's log driver, and whatever aggregator reads it (CloudWatch, Loki,
  etc.) owns retention. No log-shipping code was written here; that's the
  container runtime's native job, not the app's.
- **Metrics:** `GET /metrics` on the API (prometheus-fastapi-instrumentator —
  one line of instrumentation, not a hand-rolled counter registry), scraped
  by the `prometheus` service in `docker-compose.prod.yml`. Bound to
  `127.0.0.1:9090` only. No Grafana dashboards shipped — add one when
  there's an actual on-call rotation to serve; a JSON dashboard file nobody
  looks at yet is exactly the kind of scaffolding this step avoids.
- **Health checks:** two-tier, matching standard liveness/readiness
  semantics:
  - `GET /health` — liveness, no I/O, always fast (existing).
  - `GET /health/ready` — readiness, pings Postgres + Redis; a load
    balancer/orchestrator should gate traffic on this one, not `/health`.
  - `apps/web`'s `GET /api/health` — same liveness shape for the Next.js
    container.
  - The worker has no HTTP surface, so its Docker `HEALTHCHECK` uses arq's
    own `--check` flag, which reads the health-check key arq already writes
    to Redis (`health_check_interval = 30` in `WorkerSettings`) — no custom
    health-check code needed.

## 5. Disaster recovery

- **Backups:** the `backup` service (`infra/docker/backup/`) runs a daily
  `pg_dump | gzip` and uploads to the same S3/MinIO bucket the app already
  uses for documents (`OBJECT_STORAGE_*` env vars — one bucket, one set of
  credentials, no new infra). Retention is a bucket **lifecycle rule**
  (e.g. expire objects under `backups/` after 30 days) configured on the
  bucket itself, not scripted deletion logic — S3 already does this
  natively, so nothing here duplicates it.
- **Restore:** `gunzip < backup.sql.gz | psql $DATABASE_URL` against a fresh
  Postgres instance. Not automated/tested by a script in this repo — a
  restore is rare and consequential enough that it should be a deliberate,
  read-the-runbook action, not a one-command black box.
- **RPO/RTO:** with a daily backup cadence, RPO is up to 24h of writes. If
  that's too coarse once real users exist, the next step is Postgres
  streaming WAL archiving (point-in-time recovery), not more frequent
  `pg_dump` runs — noted here, not built, since it's meaningfully more
  infra for a V1 with no production traffic yet.
- **SSL bootstrap** (one-time, manual — not scripted, since it only ever
  runs once per domain): start nginx with only the HTTP/ACME-challenge
  server block reachable (comment out the `443` blocks in
  `infra/nginx/templates/default.conf.template` for the very first boot),
  then run
  `docker compose run --rm certbot certonly --webroot -w /var/www/certbot -d $API_DOMAIN -d $WEB_DOMAIN --email $CERTBOT_EMAIL --agree-tos`,
  then restore the `443` blocks and restart nginx. After that, the
  `certbot` service's renewal loop keeps certs current with no further
  manual steps.

## What was skipped, and why

- **Kubernetes / managed container orchestration** — no traffic yet to
  justify it; Compose + a firewall covers a single-host production
  deployment completely. Revisit if horizontal scaling across multiple
  hosts is ever actually needed.
- **Grafana / dashboards-as-code** — Prometheus alone covers "is a metric
  being recorded"; dashboards are worth building once someone is actually
  watching them.
- **Automated restore-drill tooling** — a restore is rare enough that a
  documented manual procedure beats a script nobody has exercised.
- **Multi-region / multi-AZ** — no justification without real uptime SLAs.
