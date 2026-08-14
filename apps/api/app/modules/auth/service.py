"""Auth & Identity — service layer.

All business logic lives here, not in router.py. Routes only translate
HTTP <-> these functions; that split is what lets this module stay
callable from a future non-HTTP caller (a CLI, a background job, a test)
without dragging FastAPI along, and it's the same "thin router, real
logic in the module" shape the rest of the app already follows.

Every public function here either returns the thing the caller asked
for or raises one of app.modules.auth.exceptions — never `None` for a
failure case, never a bare HTTPException (that translation happens once,
centrally, via the exception handlers registered in main.py).
"""

import asyncio
import logging
import uuid
from collections.abc import Awaitable
from datetime import UTC, datetime, timedelta

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.modules.auth.email import (
    get_email_sender,
    send_email_verification_email,
    send_password_reset_email,
)
from app.modules.auth.exceptions import (
    AccountDisabledError,
    AccountLockedError,
    EmailAlreadyRegisteredError,
    InvalidCredentialsError,
    InvalidOrExpiredTokenError,
)
from app.modules.auth.models import EmailVerificationToken, PasswordResetToken, Session, User
from app.modules.auth.security import (
    generate_opaque_token,
    hash_opaque_token,
    hash_password,
    needs_rehash,
    verify_password,
)

settings = get_settings()
logger = logging.getLogger("app.auth.service")


def _now() -> datetime:
    return datetime.now(UTC)


async def _send_email_best_effort(send: Awaitable[None], *, context: str) -> None:
    """Delivery is fire-and-forget from every caller's perspective — a
    provider outage, bad recipient, or (with a sandbox Resend sender) a
    non-verified-domain rejection must never turn into a request failure.
    Two reasons that matters more than the obvious "don't break the UX":
    request_password_reset's whole enumeration-safety guarantee (see its
    docstring) depends on the response looking identical whether the
    email exists or not — an uncaught send failure would make a
    *registered* email's request 500 while an unregistered one silently
    200s, which is exactly the timing/behavior oracle that function
    exists to avoid. For registration, the alternative is worse in a
    different way: the user row is already committed by the time the
    email is sent, so a raised exception here would 500 an operation
    that, from the database's perspective, already succeeded.
    """
    try:
        await send
    except Exception:
        logger.exception("Transactional email send failed (%s) — continuing without it.", context)


# A real Argon2id hash of a fixed, unrelated string — verified against
# on every login attempt for an email that doesn't exist, so "no such
# user" and "wrong password" cost the same wall-clock time. Without
# this, an attacker can enumerate registered emails purely by timing
# (the real-user path always pays for one Argon2 verify; the
# no-such-user path would otherwise return instantly).
_DUMMY_PASSWORD_HASH = hash_password("timing-attack-mitigation-constant")


async def _get_user_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def _create_email_verification_token(db: AsyncSession, user: User) -> str:
    raw_token, token_hash = generate_opaque_token()
    expires_at = _now() + timedelta(hours=settings.email_verification_token_ttl_hours)
    db.add(
        EmailVerificationToken(
            user_id=user.id, token_hash=token_hash, email=user.email, expires_at=expires_at
        )
    )
    return raw_token


# --- Registration & email verification ---


async def register_user(db: AsyncSession, email: str, password: str, display_name: str) -> User:
    if await _get_user_by_email(db, email) is not None:
        raise EmailAlreadyRegisteredError()

    user = User(
        email=email,
        password_hash=await asyncio.to_thread(hash_password, password),
        password_updated_at=_now(),
        display_name=display_name,
    )
    db.add(user)
    await db.flush()  # assigns user.id, needed by the verification token FK below

    raw_token = await _create_email_verification_token(db, user)
    await db.commit()
    await db.refresh(user)

    await _send_email_best_effort(
        send_email_verification_email(get_email_sender(), user.email, raw_token),
        context="verification email on register",
    )
    return user


async def verify_email(db: AsyncSession, raw_token: str) -> User:
    token_hash = hash_opaque_token(raw_token)
    result = await db.execute(
        select(EmailVerificationToken).where(EmailVerificationToken.token_hash == token_hash)
    )
    token_row = result.scalar_one_or_none()
    if token_row is None or token_row.consumed_at is not None or token_row.expires_at <= _now():
        raise InvalidOrExpiredTokenError()

    user = await db.get(User, token_row.user_id)
    if user is None:
        raise InvalidOrExpiredTokenError()

    # Only flips email_verified_at if the token's target email still
    # matches the user's *current* email — guards the race where a user
    # requests verification, then changes their email again before
    # clicking the (now stale) link.
    if user.email == token_row.email:
        user.email_verified_at = _now()
    token_row.consumed_at = _now()

    await db.commit()
    await db.refresh(user)
    return user


async def resend_verification_email(db: AsyncSession, user: User) -> None:
    if user.email_verified_at is not None:
        return  # already verified — nothing to resend, not an error

    await db.execute(
        update(EmailVerificationToken)
        .where(
            EmailVerificationToken.user_id == user.id,
            EmailVerificationToken.consumed_at.is_(None),
        )
        .values(consumed_at=_now())
    )
    raw_token = await _create_email_verification_token(db, user)
    await db.commit()
    await _send_email_best_effort(
        send_email_verification_email(get_email_sender(), user.email, raw_token),
        context="verification email on resend",
    )


# --- Login & lockout ---


async def authenticate_user(db: AsyncSession, email: str, password: str) -> User:
    # Argon2 verification/hashing is deliberately slow, CPU-bound work —
    # run it in a worker thread so it doesn't block the event loop (and
    # every other in-flight request on this process) for the ~100ms it
    # takes, the same reason it's offloaded everywhere else in this file.
    user = await _get_user_by_email(db, email)
    if user is None:
        await asyncio.to_thread(verify_password, password, _DUMMY_PASSWORD_HASH)  # timing parity, see above
        raise InvalidCredentialsError()

    if user.status != "active":
        raise AccountDisabledError()
    if user.is_locked:
        raise AccountLockedError()

    if user.password_hash is None or not await asyncio.to_thread(
        verify_password, password, user.password_hash
    ):
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= settings.max_failed_login_attempts:
            user.locked_until = _now() + timedelta(minutes=settings.lockout_duration_minutes)
        await db.commit()
        raise InvalidCredentialsError()

    if user.failed_login_attempts > 0 or user.locked_until is not None:
        user.failed_login_attempts = 0
        user.locked_until = None

    if await asyncio.to_thread(needs_rehash, user.password_hash):
        # Argon2's tuned defaults changed (library upgrade) since this
        # user's password was last hashed — upgrade it opportunistically
        # now that we have the plaintext, instead of a bulk migration.
        user.password_hash = await asyncio.to_thread(hash_password, password)

    await db.commit()
    await db.refresh(user)
    return user


# --- Sessions (refresh-token store) ---


async def create_session(
    db: AsyncSession, user: User, user_agent: str | None, ip_address: str | None
) -> tuple[str, Session]:
    raw_refresh_token, token_hash = generate_opaque_token()
    expires_at = _now() + timedelta(days=settings.refresh_token_ttl_days)
    session = Session(
        user_id=user.id,
        refresh_token_hash=token_hash,
        user_agent=user_agent,
        ip_address=ip_address,
        expires_at=expires_at,
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return raw_refresh_token, session


async def rotate_refresh_token(
    db: AsyncSession, raw_refresh_token: str, user_agent: str | None, ip_address: str | None
) -> tuple[str, User]:
    """Validates the presented refresh token and issues a new one in its
    place (same session row, new hash+expiry) — rotation-on-use means a
    stolen-but-not-yet-used refresh token is invalidated the moment the
    legitimate client refreshes, since the old hash stops matching
    anything."""
    token_hash = hash_opaque_token(raw_refresh_token)
    result = await db.execute(select(Session).where(Session.refresh_token_hash == token_hash))
    session = result.scalar_one_or_none()
    if session is None or session.revoked_at is not None or session.expires_at <= _now():
        raise InvalidOrExpiredTokenError()

    user = await db.get(User, session.user_id)
    if user is None or user.status != "active":
        raise InvalidOrExpiredTokenError()

    new_raw_token, new_hash = generate_opaque_token()
    session.refresh_token_hash = new_hash
    session.expires_at = _now() + timedelta(days=settings.refresh_token_ttl_days)
    if user_agent:
        session.user_agent = user_agent
    if ip_address:
        session.ip_address = ip_address

    await db.commit()
    return new_raw_token, user


async def revoke_session(db: AsyncSession, raw_refresh_token: str) -> None:
    """Logout. Idempotent by design — logging out with an already-
    revoked or unrecognized token is not an error; the end state
    (no valid session) is what the caller wants either way."""
    token_hash = hash_opaque_token(raw_refresh_token)
    result = await db.execute(select(Session).where(Session.refresh_token_hash == token_hash))
    session = result.scalar_one_or_none()
    if session is not None and session.revoked_at is None:
        session.revoked_at = _now()
        await db.commit()


async def revoke_all_sessions(db: AsyncSession, user: User) -> None:
    """"Log out everywhere" — the exact capability
    docs/architecture/database-schema-v1.md designed the `sessions`
    table around."""
    await db.execute(
        update(Session)
        .where(Session.user_id == user.id, Session.revoked_at.is_(None))
        .values(revoked_at=_now())
    )
    await db.commit()


# --- Password reset ---


async def request_password_reset(db: AsyncSession, email: str) -> None:
    """Always succeeds from the caller's perspective regardless of
    whether the email is registered — the router returns the same
    generic message either way. Branching the *response* on existence
    is a textbook account-enumeration leak."""
    user = await _get_user_by_email(db, email)
    if user is None or user.status != "active":
        return

    await db.execute(
        update(PasswordResetToken)
        .where(PasswordResetToken.user_id == user.id, PasswordResetToken.consumed_at.is_(None))
        .values(consumed_at=_now())
    )
    raw_token, token_hash = generate_opaque_token()
    expires_at = _now() + timedelta(minutes=settings.password_reset_token_ttl_minutes)
    db.add(PasswordResetToken(user_id=user.id, token_hash=token_hash, expires_at=expires_at))
    await db.commit()

    await _send_email_best_effort(
        send_password_reset_email(get_email_sender(), user.email, raw_token),
        context="password reset email",
    )


async def reset_password(db: AsyncSession, raw_token: str, new_password: str) -> None:
    token_hash = hash_opaque_token(raw_token)
    result = await db.execute(
        select(PasswordResetToken).where(PasswordResetToken.token_hash == token_hash)
    )
    token_row = result.scalar_one_or_none()
    if token_row is None or token_row.consumed_at is not None or token_row.expires_at <= _now():
        raise InvalidOrExpiredTokenError()

    user = await db.get(User, token_row.user_id)
    if user is None:
        raise InvalidOrExpiredTokenError()

    user.password_hash = await asyncio.to_thread(hash_password, new_password)
    user.password_updated_at = _now()
    user.failed_login_attempts = 0
    user.locked_until = None
    token_row.consumed_at = _now()

    # A password reset is the strongest signal available that the
    # account may have been compromised — revoke every existing session
    # so a stolen session cookie doesn't survive the very reset meant to
    # recover from it.
    await db.execute(
        update(Session)
        .where(Session.user_id == user.id, Session.revoked_at.is_(None))
        .values(revoked_at=_now())
    )
    await db.commit()


async def get_user_by_id(db: AsyncSession, user_id: uuid.UUID) -> User | None:
    return await db.get(User, user_id)


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    return await _get_user_by_email(db, email)
