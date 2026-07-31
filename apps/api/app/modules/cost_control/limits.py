"""Cost & Abuse Control — per-user rate limiting for LLM-backed routes.

The full operation-weighted budget ledger (ARCHITECTURE.md Section 3) is
not built yet. Until it is, every LLM-backed route (mentoring, code
review, curriculum narration, document Q&A) had *no* per-user ceiling at
all — a single account could drive unbounded model spend. This is the
minimum viable stopgap: a coarse, per-user fixed-window counter, same
mechanism as auth/rate_limit.py's per-IP limiter, just keyed by user_id
instead of client IP since these routes are already authenticated.

Fails open on any Redis error, for the same reason auth's limiter does:
an unreachable rate limiter must never be able to take a paid feature
down entirely.
"""

import logging

from fastapi import Depends
from fastapi.params import Depends as DependsType
from redis.asyncio import Redis
from redis.exceptions import RedisError

from app.core.redis import get_redis
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.models import User
from app.modules.cost_control.exceptions import UsageLimitExceededError

logger = logging.getLogger("app.cost_control.limits")


def llm_rate_limit(operation: str, times: int, seconds: int) -> DependsType:
    """Returns a route dependency enforcing `times` LLM-backed requests
    per `seconds` per user. `operation` namespaces the counter so, e.g.,
    spamming code review doesn't burn the mentor chat's separate budget."""

    async def _dependency(
        current_user: User = Depends(get_current_user),
        redis: Redis = Depends(get_redis),
    ) -> None:
        key = f"cost_rl:{operation}:{current_user.id}"
        try:
            count = await redis.incr(key)
            if count == 1:
                await redis.expire(key, seconds)
        except RedisError:
            logger.warning("usage limiter backend unavailable, failing open for %r", operation)
            return

        if count > times:
            ttl = await redis.ttl(key)
            raise UsageLimitExceededError(retry_after=ttl if ttl > 0 else seconds)

    return Depends(_dependency)
