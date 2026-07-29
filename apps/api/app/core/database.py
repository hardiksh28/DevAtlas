from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from typing import ClassVar

from sqlalchemy import DateTime
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.types import TypeDecorator

from app.core.config import get_settings

settings = get_settings()

engine = create_async_engine(settings.database_url, pool_pre_ping=True)
async_session_factory = async_sessionmaker(engine, expire_on_commit=False)


class UTCDateTime(TypeDecorator):
    """A `datetime` column that's guaranteed timezone-aware coming back
    out of the ORM, regardless of what the underlying driver hands
    back. Every stored timestamp in this app (token/session expiry,
    account lockout) is compared against `datetime.now(UTC)` somewhere
    — a driver that silently returns a naive value would make that
    comparison raise TypeError instead of doing the comparison. Postgres
    columns are TIMESTAMPTZ (see the auth migration) and asyncpg already
    returns aware values for those; this only has to compensate for
    dialects that don't preserve tzinfo (e.g. SQLite, used in tests).
    """

    impl = DateTime(timezone=True)
    cache_ok = True

    def process_result_value(self, value: datetime | None, dialect: object) -> datetime | None:
        if value is not None and value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value


class Base(DeclarativeBase):
    """Shared declarative base — every module's models inherit from this
    so Alembic's autogenerate can discover them from a single metadata
    object (see alembic/env.py)."""

    type_annotation_map: ClassVar[dict[type, type]] = {datetime: UTCDateTime}


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency: yields a session, guarantees it's closed even
    if the request handler raises."""
    async with async_session_factory() as session:
        yield session
