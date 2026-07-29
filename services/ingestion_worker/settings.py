from pydantic_settings import BaseSettings, SettingsConfigDict


class WorkerConfig(BaseSettings):
    """Deliberately separate from apps/api's Settings class, even though
    several fields overlap. This worker is the one piece of the system
    scoped for independent extraction (ARCHITECTURE.md Section 1) — it
    should never import from apps/api, or extraction stops being "change
    the deployment target" and becomes "untangle a shared module first".
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    redis_url: str
    database_url: str


config = WorkerConfig()
