"""Shared async Redis client.

Mirrors app/core/database.py's shape: one module-level client, created
lazily by redis-py itself (Redis.from_url doesn't open a connection
until the first command), so importing this module never requires
Redis to actually be reachable — the same reason `create_async_engine`
in database.py doesn't require Postgres to be up at import time.
"""

from redis.asyncio import Redis

from app.core.config import get_settings

settings = get_settings()

redis_client = Redis.from_url(settings.redis_url, decode_responses=True)


async def get_redis() -> Redis:
    return redis_client
