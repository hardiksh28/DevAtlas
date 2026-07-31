"""Enqueues jobs onto the same Redis-backed queue
services/ingestion_worker consumes (see services/ingestion_worker/worker.py's
WorkerSettings.functions for the closed set of job names this can call).

Uses arq's own client (`ArqRedis`/`create_pool`), not the plain redis-py
client in app/core/redis.py — arq owns its own job-serialization wire
format, and this is the one place apps/api needs to speak it.
"""

from arq import ArqRedis, create_pool
from arq.connections import RedisSettings

from app.core.config import get_settings

_pool: ArqRedis | None = None


async def get_queue() -> ArqRedis:
    """FastAPI dependency. A single cached pool per process — matches
    the "one shared client, created lazily" shape of
    database.py/redis.py rather than opening a new connection pool per
    request."""
    global _pool
    if _pool is None:
        settings = get_settings()
        _pool = await create_pool(RedisSettings.from_dsn(settings.redis_url))
    return _pool
