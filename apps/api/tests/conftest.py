"""Shared pytest fixtures for API tests.

The auth integration tests need a real relational database — CITEXT's
case-insensitive uniqueness is part of the behavior under test, not an
implementation detail — but this repo's DB is Postgres-only and this
environment doesn't always have Docker/Postgres available. Two paths,
in priority order:

1. If TEST_DATABASE_URL is set (CI's `api` job sets this against a real
   Postgres service container — see .github/workflows/ci.yml), use it
   as-is: full fidelity, exactly the production dialect.
2. Otherwise fall back to an in-memory SQLite engine, with CITEXT/INET
   compiled down to portable equivalents (VARCHAR COLLATE NOCASE / plain
   VARCHAR) via SQLAlchemy's `@compiles` hook. This is test-only — it
   never touches the production models, only how *this process*
   compiles two Postgres-specific types against a non-Postgres engine —
   and it's what makes `uv run pytest` work without any local services.
"""

import os
from collections.abc import AsyncGenerator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from redis.exceptions import ConnectionError as RedisConnectionError
from sqlalchemy import text
from sqlalchemy.dialects.postgresql import CITEXT, INET
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401 — registers auth models on Base.metadata
from app.core.database import Base, get_db
from app.core.redis import get_redis

TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL")
_USING_SQLITE = not TEST_DATABASE_URL or TEST_DATABASE_URL.startswith("sqlite")

if _USING_SQLITE:
    TEST_DATABASE_URL = TEST_DATABASE_URL or "sqlite+aiosqlite://"

    @compiles(CITEXT, "sqlite")
    def _compile_citext_sqlite(element, compiler, **kw) -> str:
        return "VARCHAR COLLATE NOCASE"

    @compiles(INET, "sqlite")
    def _compile_inet_sqlite(element, compiler, **kw) -> str:
        return "VARCHAR"


def _make_engine() -> AsyncEngine:
    if _USING_SQLITE:
        # StaticPool so every checked-out connection shares the same
        # in-memory database — plain sqlite+aiosqlite:// would otherwise
        # hand out a fresh, empty :memory: database per connection.
        return create_async_engine(
            TEST_DATABASE_URL,
            poolclass=StaticPool,
            connect_args={"check_same_thread": False},
        )
    return create_async_engine(TEST_DATABASE_URL)


@pytest_asyncio.fixture
async def engine() -> AsyncGenerator[AsyncEngine, None]:
    eng = _make_engine()
    async with eng.begin() as conn:
        if not _USING_SQLITE:
            # CITEXT is an extension, not a built-in type — the
            # production migration enables it once per database
            # (see alembic/versions/202607291200_*), but a CI-provisioned
            # Postgres service container starts without it.
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS citext"))
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    await eng.dispose()


@pytest_asyncio.fixture
async def db_session(engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    """A single session for service-layer tests that call service.py
    functions directly (no HTTP layer involved)."""
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session


class FakeRedis:
    """In-memory stand-in for redis.asyncio.Redis, implementing just
    the three calls rate_limit.py makes. Lets router tests exercise
    real rate-limiting behavior without a Redis server."""

    def __init__(self) -> None:
        self._counters: dict[str, int] = {}

    async def incr(self, key: str) -> int:
        self._counters[key] = self._counters.get(key, 0) + 1
        return self._counters[key]

    async def expire(self, key: str, seconds: int) -> None:
        return None

    async def ttl(self, key: str) -> int:
        return 60


class FailingRedis:
    """Simulates Redis being unreachable — every call raises, so tests
    can confirm the rate limiter fails open instead of taking auth down."""

    async def incr(self, key: str) -> int:
        raise RedisConnectionError("simulated redis outage")

    async def expire(self, key: str, seconds: int) -> None:
        raise RedisConnectionError("simulated redis outage")

    async def ttl(self, key: str) -> int:
        raise RedisConnectionError("simulated redis outage")


@pytest_asyncio.fixture
async def client(engine: AsyncEngine) -> AsyncGenerator[AsyncClient, None]:
    """An httpx client driving the real FastAPI app in-process (ASGI
    transport, no network), with the DB and Redis dependencies swapped
    for test doubles bound to this test's isolated schema."""
    from app.main import app as fastapi_app

    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        async with session_factory() as session:
            yield session

    fake_redis = FakeRedis()

    async def override_get_redis() -> FakeRedis:
        return fake_redis

    fastapi_app.dependency_overrides[get_db] = override_get_db
    fastapi_app.dependency_overrides[get_redis] = override_get_redis
    try:
        transport = ASGITransport(app=fastapi_app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac
    finally:
        fastapi_app.dependency_overrides.clear()
