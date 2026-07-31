from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class WorkerConfig(BaseSettings):
    """Deliberately separate from apps/api's Settings class, even though
    several fields overlap. This worker is the one piece of the system
    scoped for independent extraction (ARCHITECTURE.md Section 1) — it
    should never import from apps/api, or extraction stops being "change
    the deployment target" and becomes "untangle a shared module first".
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Mirrors apps/api's Settings.environment — only used to pick a log
    # format (see worker.py's logging setup), nothing deeper.
    environment: str = "development"

    redis_url: str
    database_url: str

    # --- Object storage (raw fetched bytes: uploads are already stored
    # by apps/api at upload time; github_repo/website content is fetched
    # and stored here, for provenance and reprocessing) ---
    object_storage_backend: Literal["local", "s3"] = "local"
    object_storage_bucket: str = "devatlas-documents"
    object_storage_region: str = "us-east-1"
    object_storage_endpoint_url: str | None = None
    object_storage_access_key_id: str | None = None
    object_storage_secret_access_key: str | None = None
    object_storage_local_path: str = "./.data/object_storage"

    # --- Ingestion limits (mirrors apps/api's own ceilings on the
    # request-path side of these same numbers — see
    # apps/api/app/core/config.py. Duplicated rather than imported for
    # the same reason as everything else in this file: no dependency on
    # apps/api.) ---
    ingestion_max_website_pages: int = 200
    ingestion_max_website_crawl_depth: int = 3
    ingestion_max_github_files: int = 500
    ingestion_max_github_repo_bytes: int = 200 * 1024 * 1024  # 200 MB
    ingestion_max_fetch_bytes: int = 20 * 1024 * 1024  # per single file/page
    ingestion_fetch_timeout_seconds: float = 15.0
    github_api_token: str | None = None

    # A small *compressed* PDF can still decompress into an enormous page
    # count or text volume ("PDF bomb") — ingestion_max_fetch_bytes above
    # only bounds the upload itself, not what pypdf extracts from it.
    ingestion_max_pdf_pages: int = 2000
    ingestion_max_pdf_extracted_chars: int = 10_000_000  # ~10M chars (~10MB of text)

    # --- Chunking (docs/architecture/ingestion-engine-v1.md Section 5) ---
    chunk_target_tokens: int = 800
    chunk_overlap_tokens: int = 100

    # --- Embedding (docs/architecture/rag-engine-v1.md) ---
    # Mirrors apps/api/app/core/config.py's own Ollama fields — not
    # imported from there, same extraction-boundary reasoning as
    # everything else in this file. `ollama_embedding_model` must
    # produce EMBEDDING_DIMENSIONS-wide vectors (packages/schemas) —
    # changing it here without a matching migration/re-embed breaks
    # every existing project_embeddings row.
    ollama_base_url: str = "http://ollama:11434"
    ollama_embedding_model: str = "nomic-embed-text"
    embedding_fetch_timeout_seconds: float = 30.0
    # Chunks per Ollama /api/embed call — bounds request/response size
    # for documents with thousands of chunks rather than embedding the
    # whole document in one HTTP call.
    embedding_batch_size: int = 32


config = WorkerConfig()
