"""Auth & Identity — per-IP rate limiting for the abuse-prone routes.

`AccountLockedError` (service.py) only slows down guessing against one
*known* account; nothing stopped an attacker from spraying credential
guesses across many accounts, or hammering forgot-password/register/
resend-verification to spam another person's inbox or fill the users
table. This is a coarse, IP-scoped fixed-window counter to close that
gap — it's not meant to replace account lockout, only to sit in front
of it.

Backed by Redis (already a first-class dependency of this app, see
app/core/redis.py) so the counters are shared across every API process
instead of being reset per-worker. Fails open on any Redis error: a
rate limiter that's unreachable must never be able to take the login
page down, and a temporarily-unlimited window is a far smaller risk
than authentication becoming unavailable.
"""

import logging

from fastapi import Depends, Request
from fastapi.params import Depends as DependsType
from redis.asyncio import Redis
from redis.exceptions import RedisError

from app.core.redis import get_redis
from app.modules.auth.exceptions import RateLimitExceededError

logger = logging.getLogger("app.auth.rate_limit")


def _client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


def rate_limit(key_prefix: str, times: int, seconds: int) -> DependsType:
    """Returns a route dependency enforcing `times` requests per
    `seconds` per client IP. `key_prefix` namespaces the counter per
    route, e.g. spamming /forgot-password doesn't burn /login's
    separate budget."""

    async def _dependency(request: Request, redis: Redis = Depends(get_redis)) -> None:
        key = f"auth_rl:{key_prefix}:{_client_ip(request)}"
        try:
            count = await redis.incr(key)
            if count == 1:
                await redis.expire(key, seconds)
        except RedisError:
            logger.warning("rate limiter backend unavailable, failing open for %r", key_prefix)
            return

        if count > times:
            ttl = await redis.ttl(key)
            raise RateLimitExceededError(retry_after=ttl if ttl > 0 else seconds)

    return Depends(_dependency)
