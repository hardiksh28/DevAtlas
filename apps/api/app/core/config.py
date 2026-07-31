from functools import lru_cache
from typing import Literal

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Single source of truth for runtime configuration.

    Every field maps 1:1 to a variable in .env.example — if you add an env
    var, add it here too, or it silently won't be validated at startup.
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: str = "development"
    api_secret_key: str

    database_url: str
    redis_url: str

    ollama_base_url: str = "http://ollama:11434"
    ollama_model: str = "llama3.1:8b"
    llm_provider: str = "ollama"
    # Embedding-capable model, separate from `ollama_model` (a chat/
    # generation model) — Ollama treats these as different model
    # families entirely, not a mode flag on one model. 768-dim,
    # matching schemas.EMBEDDING_DIMENSIONS (see that module's docstring
    # for why the two must never disagree).
    ollama_embedding_model: str = "nomic-embed-text"

    github_oauth_client_id: str | None = None
    github_oauth_client_secret: str | None = None
    github_app_id: str | None = None
    github_app_private_key_path: str | None = None

    next_public_api_url: str = "http://localhost:8000"

    # --- CORS ---
    # Explicit allow-list rather than derived from next_public_api_url
    # (that's the *API's* own URL, not the web app's origin — deriving
    # one from the other by string-replacing "8000" with "3000" only
    # ever worked by coincidence in local dev and silently allows the
    # wrong origins, or none of the right ones, anywhere else).
    # Comma-separated so it's a single plain env var like the rest of
    # this file, e.g. "https://app.example.com,https://staging.example.com".
    cors_origins_raw: str = Field("http://localhost:3000", alias="CORS_ORIGINS")

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins_raw.split(",") if origin.strip()]

    # --- Auth: JWT access tokens ---
    # HS256 with api_secret_key (single shared secret, matching the rest
    # of the app's "one secret" pattern) rather than a dedicated RS256
    # keypair — V1 has one API process signing and verifying its own
    # tokens, so asymmetric keys would add key-management overhead with
    # no actual benefit yet. Revisit if a second service ever needs to
    # verify tokens without the ability to mint them.
    jwt_algorithm: str = "HS256"
    access_token_ttl_minutes: int = 15

    # --- Auth: refresh tokens (opaque, hashed, stored in `sessions`) ---
    # Deliberately long-lived relative to the access token — the access
    # token is what's checked on every request, so it can be short-lived
    # without forcing the user to re-login; the refresh token is what
    # actually gets revoked on logout (see docs/architecture/database-schema-v1.md).
    refresh_token_ttl_days: int = 30

    # --- Auth: one-time tokens ---
    password_reset_token_ttl_minutes: int = 60
    email_verification_token_ttl_hours: int = 24

    # --- Auth: account lockout ---
    max_failed_login_attempts: int = 5
    lockout_duration_minutes: int = 15

    # --- Auth: cookies ---
    # Cookie `Domain` is left unset (host-only) by default — dev has web
    # and api on different ports of `localhost`, which are the same
    # *site* (registrable domain ignores port) so a host-only cookie is
    # still sent. In production, set this to the shared parent domain
    # (e.g. ".example.com") if web/api live on different subdomains.
    cookie_domain: str | None = None

    # --- Auth: links embedded in transactional emails ---
    frontend_url: str = "http://localhost:3000"

    # --- Project Workspace ---
    # Guards against unbounded storage growth from a single authenticated
    # account (each project is a real row plus a 1:1 settings row) —
    # there's no per-operation cost ledger for plain CRUD the way LLM
    # calls have one (see ARCHITECTURE.md's Cost & Abuse Control module),
    # so this is a simple ceiling rather than a full quota system.
    max_active_projects_per_owner: int = 200

    # --- Documentation Ingestion Engine (docs/architecture/ingestion-engine-v1.md) ---
    # "local" writes to a directory on disk (dev/tests, no MinIO/S3
    # needed); "s3" is the only backend used in any real deployment,
    # and also what local dev talks to via docker-compose's `minio`
    # service — only object_storage_endpoint_url differs.
    object_storage_backend: Literal["local", "s3"] = "local"
    object_storage_bucket: str = "devatlas-documents"
    object_storage_region: str = "us-east-1"
    object_storage_endpoint_url: str | None = None
    object_storage_access_key_id: str | None = None
    object_storage_secret_access_key: str | None = None
    # Only read when object_storage_backend == "local".
    object_storage_local_path: str = "./.data/object_storage"

    # Simple ceilings, same "plain ceiling, not a full quota system"
    # reasoning as max_active_projects_per_owner — ingestion has no
    # per-operation cost ledger yet either.
    max_active_ingestion_jobs_per_project: int = 20
    ingestion_max_upload_bytes: int = 25 * 1024 * 1024  # 25 MB
    ingestion_max_website_pages: int = 200
    ingestion_max_website_crawl_depth: int = 3
    ingestion_max_github_files: int = 500
    ingestion_max_github_repo_bytes: int = 200 * 1024 * 1024  # 200 MB
    # Optional — raises the GitHub API's unauthenticated 60 req/hour
    # rate limit for repo-tree listing. Never required (V1 only reads
    # public repos), never used for raw.githubusercontent.com fetches
    # (those aren't rate-limited by the API quota).
    github_api_token: str | None = None

    # --- RAG Knowledge Engine (docs/architecture/rag-engine-v1.md) ---
    # Candidates pulled from each retriever *before* fusion — wider than
    # the final result count so Reciprocal Rank Fusion (Section 5 of
    # that doc) has enough of each ranked list to actually combine.
    retrieval_vector_candidates: int = 20
    retrieval_keyword_candidates: int = 20
    # Final, post-fusion chunk count handed to the context builder.
    retrieval_top_k: int = 8
    # Reciprocal Rank Fusion's smoothing constant — standard default
    # from the original RRF paper; larger values flatten the influence
    # of rank position (rank 1 vs rank 10 matters less), smaller values
    # sharpen it. Not something worth exposing as a per-request knob.
    retrieval_rrf_k: int = 60
    # Context builder's token budget — see rag-engine-v1.md Section 6
    # (Token Optimization) for why this is well under the model's real
    # context window, not equal to it.
    context_max_tokens: int = 3000
    # Answer-cache TTL (Section 9, Caching Strategy). Short enough that
    # a newly-ingested document shows up in answers within one cache
    # lifetime without any invalidation hook on ingestion completion.
    retrieval_cache_ttl_seconds: int = 300

    # --- Taxonomy & Concept Graph Service ---
    # Where scripts/seed_taxonomy.py reads curated concept YAML from —
    # a path, not a URL, since this is authored content checked into the
    # monorepo, never fetched at runtime.
    taxonomy_data_dir: str = "../../packages/taxonomy-data/concepts"

    # --- Curriculum Engine (docs/architecture/curriculum-engine-v1.md) ---
    # Per-concept time estimate by severity, summed into a roadmap's
    # estimated_total_minutes — a simple heuristic, not measured data,
    # deliberately adjustable without a code change if it turns out to
    # be off in practice.
    curriculum_minutes_foundational: int = 30
    curriculum_minutes_intermediate: int = 60
    curriculum_minutes_advanced: int = 90

    # --- Interactive Learning Workspace (docs/architecture/interactive-workspace-v1.md) ---
    # Same "simple ceiling, not a full quota system" reasoning as
    # max_active_projects_per_owner — plain file CRUD has no per-
    # operation cost ledger to bound it another way.
    max_workspace_files_per_project: int = 300
    workspace_file_max_bytes: int = 256 * 1024  # 256 KB — generous for source files

    # --- Mentoring Engine (docs/architecture/mentor-engine-v1.md) ---
    # Context-window cap by plain message count, not a token budget —
    # see that doc's "Context window management" section for why a
    # count cap is the right-sized version for conversation turns.
    mentor_recent_message_limit: int = 20
    # Once the uncompacted tail exceeds this many messages, everything
    # except the last few turns is folded into `conversations.summary`.
    mentor_summary_trigger_messages: int = 20

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def cookie_secure(self) -> bool:
        # `Secure` cookies are dropped by browsers over plain HTTP, which
        # is exactly the local dev transport — deriving this from
        # `environment` means dev keeps working over http:// without a
        # separate flag someone has to remember to flip before deploying.
        return self.is_production

    @property
    def cookie_samesite(self) -> Literal["lax", "strict", "none"]:
        return "lax"

    @model_validator(mode="after")
    def _require_strong_secret_in_production(self) -> "Settings":
        # api_secret_key doubles as the JWT HMAC signing key
        # (app/modules/auth/security.py) — RFC 7518 §3.2 recommends at
        # least 32 bytes for HS256, and a short/guessable key there is a
        # direct path to forging access tokens. Dev's "local-dev-secret"
        # is well below that and is fine for dev; failing fast here means
        # a weak key can't quietly ship to production instead of being
        # caught at the first deploy.
        if self.is_production and len(self.api_secret_key) < 32:
            raise ValueError(
                "api_secret_key must be at least 32 characters in production "
                "(it signs JWTs — a short key is forgeable)"
            )
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
