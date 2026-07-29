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
