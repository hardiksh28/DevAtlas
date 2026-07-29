from typing import ClassVar

from arq import cron
from arq.connections import RedisSettings
from arq.cron import CronJob
from arq.typing import WorkerCoroutine

from settings import config


async def refresh_global_corpus(ctx: dict) -> None:
    """Freshness / re-crawl scheduler (ARCHITECTURE.md Section 2).

    Placeholder body: real implementation will diff each curated stack's
    docs against `global_documents.last_refreshed` and enqueue
    `ingest_document` jobs for anything stale. Left unimplemented here —
    there's no curated source list yet to crawl.
    """
    print("refresh_global_corpus: no-op (no curated sources configured yet)")


async def ingest_document(ctx: dict, document_url: str) -> None:
    """Global Corpus Ingestion Worker (ARCHITECTURE.md Section 2).

    Fetches one document, chunks it, generates embeddings, and writes to
    `global_documents` / `global_embeddings` (pgvector). Placeholder body
    — the chunking/embedding pipeline isn't built yet.
    """
    print(f"ingest_document: would ingest {document_url}")


class WorkerSettings:
    """arq reads this class by name (`arq worker.WorkerSettings`, see
    services/ingestion_worker/Dockerfile). `functions` is the closed set
    of jobs this worker can run — enqueueing anything not listed here
    fails loudly instead of silently doing nothing.
    """

    # ClassVar: arq reads these as class-level attributes, not per-instance
    # state — annotating them tells the type checker (and RUF012) that's
    # intentional rather than an accidentally-shared mutable default.
    functions: ClassVar[list[WorkerCoroutine]] = [ingest_document]
    cron_jobs: ClassVar[list[CronJob]] = [
        # Runs daily at 03:00 — cheap enough to be conservative by
        # default; tune per-stack once real release-velocity data exists.
        cron(refresh_global_corpus, hour=3, minute=0),
    ]
    redis_settings = RedisSettings.from_dsn(config.redis_url)
