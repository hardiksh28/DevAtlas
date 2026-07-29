"""Integration tests for app.modules.auth.service.

Unlike test_auth_security.py (pure functions, no DB), these exercise the
service layer against a real AsyncSession/schema — registration,
lockout, session rotation, and the two token-based flows all depend on
actual row state (uniqueness, expiry, consumed_at) that a mock can't
faithfully stand in for. See tests/conftest.py for how the backing
database is provided without requiring Docker/Postgres locally.
"""

from datetime import UTC, datetime, timedelta

import pytest
from argon2 import PasswordHasher
from sqlalchemy import select

from app.core.config import get_settings
from app.modules.auth import service
from app.modules.auth.exceptions import (
    AccountDisabledError,
    AccountLockedError,
    EmailAlreadyRegisteredError,
    InvalidCredentialsError,
    InvalidOrExpiredTokenError,
)
from app.modules.auth.models import EmailVerificationToken, PasswordResetToken, Session
from app.modules.auth.security import hash_opaque_token

settings = get_settings()


async def _register(db, email="user@example.com", password="hunter22222", display_name="User One"):
    return await service.register_user(db, email, password, display_name)


class TestRegisterUser:
    async def test_creates_user_with_hashed_password(self, db_session):
        user = await _register(db_session)
        assert user.id is not None
        assert user.password_hash is not None
        assert user.password_hash != "hunter22222"
        assert user.email_verified_at is None

    async def test_duplicate_email_rejected(self, db_session):
        await _register(db_session, email="dupe@example.com")
        with pytest.raises(EmailAlreadyRegisteredError):
            await _register(db_session, email="dupe@example.com")

    async def test_duplicate_email_case_insensitive(self, db_session):
        # CITEXT: "Foo@x.com" and "foo@x.com" are the same account.
        await _register(db_session, email="CaseTest@Example.com")
        with pytest.raises(EmailAlreadyRegisteredError):
            await _register(db_session, email="casetest@example.com")


class TestEmailVerification:
    async def test_invalid_token_rejected(self, db_session):
        with pytest.raises(InvalidOrExpiredTokenError):
            await service.verify_email(db_session, "not-a-real-token")

    async def test_expired_token_rejected(self, db_session):
        user = await _register(db_session, email="expired@example.com")
        raw_token = "expired-raw-token"
        # expires_at > created_at is a DB constraint, so an "already
        # expired" row needs created_at pushed back too, not just expires_at.
        db_session.add(
            EmailVerificationToken(
                user_id=user.id,
                token_hash=hash_opaque_token(raw_token),
                email=user.email,
                created_at=datetime.now(UTC) - timedelta(hours=2),
                expires_at=datetime.now(UTC) - timedelta(hours=1),
            )
        )
        await db_session.commit()

        with pytest.raises(InvalidOrExpiredTokenError):
            await service.verify_email(db_session, raw_token)

    async def test_already_consumed_token_rejected(self, db_session):
        user = await _register(db_session, email="consumed@example.com")
        raw_token = "consumed-raw-token"
        db_session.add(
            EmailVerificationToken(
                user_id=user.id,
                token_hash=hash_opaque_token(raw_token),
                email=user.email,
                expires_at=datetime.now(UTC) + timedelta(hours=1),
                consumed_at=datetime.now(UTC),
            )
        )
        await db_session.commit()

        with pytest.raises(InvalidOrExpiredTokenError):
            await service.verify_email(db_session, raw_token)

    async def test_valid_unconsumed_token_verifies(self, db_session):
        user = await _register(db_session, email="valid-verify@example.com")
        raw_token = "valid-raw-token"
        db_session.add(
            EmailVerificationToken(
                user_id=user.id,
                token_hash=hash_opaque_token(raw_token),
                email=user.email,
                expires_at=datetime.now(UTC) + timedelta(hours=1),
            )
        )
        await db_session.commit()

        verified_user = await service.verify_email(db_session, raw_token)
        assert verified_user.id == user.id
        assert verified_user.email_verified_at is not None

    async def test_stale_link_does_not_verify_changed_email(self, db_session):
        """If the user's email changed after the link was sent, the
        token should be consumed (so it can't be reused) but must NOT
        flip email_verified_at for the *new* email."""
        user = await _register(db_session, email="original@example.com")
        raw_token = "stale-raw-token"
        db_session.add(
            EmailVerificationToken(
                user_id=user.id,
                token_hash=hash_opaque_token(raw_token),
                email="original@example.com",
                expires_at=datetime.now(UTC) + timedelta(hours=1),
            )
        )
        user.email = "changed@example.com"
        await db_session.commit()

        result_user = await service.verify_email(db_session, raw_token)
        assert result_user.email_verified_at is None


class TestResendVerification:
    async def test_noop_if_already_verified(self, db_session):
        user = await _register(db_session, email="already@example.com")
        user.email_verified_at = datetime.now(UTC)
        await db_session.commit()

        await service.resend_verification_email(db_session, user)
        # No new token should be created.
        result = await db_session.execute(
            select(EmailVerificationToken).where(
                EmailVerificationToken.user_id == user.id,
                EmailVerificationToken.consumed_at.is_(None),
            )
        )
        assert len(result.scalars().all()) == 1  # only the original signup token

    async def test_invalidates_prior_unconsumed_tokens(self, db_session):
        user = await _register(db_session, email="resend@example.com")
        await service.resend_verification_email(db_session, user)

        result = await db_session.execute(
            select(EmailVerificationToken).where(
                EmailVerificationToken.user_id == user.id,
                EmailVerificationToken.consumed_at.is_(None),
            )
        )
        unconsumed = result.scalars().all()
        assert len(unconsumed) == 1  # the newly issued one only


class TestAuthenticateUser:
    async def test_success(self, db_session):
        await _register(db_session, email="login@example.com", password="correct-password-1")
        user = await service.authenticate_user(db_session, "login@example.com", "correct-password-1")
        assert user.email == "login@example.com"
        assert user.failed_login_attempts == 0

    async def test_login_is_case_insensitive_on_email(self, db_session):
        await _register(db_session, email="CaseLogin@Example.com", password="correct-password-1")
        user = await service.authenticate_user(
            db_session, "caselogin@example.com", "correct-password-1"
        )
        assert user is not None

    async def test_unknown_email_rejected(self, db_session):
        with pytest.raises(InvalidCredentialsError):
            await service.authenticate_user(db_session, "nobody@example.com", "whatever123")

    async def test_wrong_password_rejected_and_counted(self, db_session):
        await _register(db_session, email="wrongpw@example.com", password="correct-password-1")
        with pytest.raises(InvalidCredentialsError):
            await service.authenticate_user(db_session, "wrongpw@example.com", "wrong-password")

        user = await service.get_user_by_email(db_session, "wrongpw@example.com")
        assert user.failed_login_attempts == 1

    async def test_lockout_after_max_failed_attempts(self, db_session):
        await _register(db_session, email="lockout@example.com", password="correct-password-1")
        for _ in range(settings.max_failed_login_attempts):
            with pytest.raises(InvalidCredentialsError):
                await service.authenticate_user(db_session, "lockout@example.com", "wrong-password")

        user = await service.get_user_by_email(db_session, "lockout@example.com")
        assert user.is_locked

        with pytest.raises(AccountLockedError):
            await service.authenticate_user(db_session, "lockout@example.com", "correct-password-1")

    async def test_successful_login_resets_failed_attempts(self, db_session):
        await _register(db_session, email="reset-attempts@example.com", password="correct-password-1")
        with pytest.raises(InvalidCredentialsError):
            await service.authenticate_user(db_session, "reset-attempts@example.com", "wrong-password")

        user = await service.authenticate_user(
            db_session, "reset-attempts@example.com", "correct-password-1"
        )
        assert user.failed_login_attempts == 0
        assert user.locked_until is None

    async def test_disabled_account_rejected(self, db_session):
        user = await _register(db_session, email="disabled@example.com", password="correct-password-1")
        user.status = "disabled"
        await db_session.commit()

        with pytest.raises(AccountDisabledError):
            await service.authenticate_user(db_session, "disabled@example.com", "correct-password-1")

    async def test_stale_hash_is_rehashed_on_login(self, db_session):
        user = await _register(db_session, email="rehash@example.com", password="correct-password-1")
        weak_hasher = PasswordHasher(time_cost=1, memory_cost=8, parallelism=1)
        weak_hash = weak_hasher.hash("correct-password-1")
        user.password_hash = weak_hash
        await db_session.commit()

        await service.authenticate_user(db_session, "rehash@example.com", "correct-password-1")

        refreshed = await service.get_user_by_email(db_session, "rehash@example.com")
        assert refreshed.password_hash != weak_hash


class TestSessions:
    async def test_create_and_rotate(self, db_session):
        user = await _register(db_session, email="session@example.com")
        raw_refresh, session = await service.create_session(db_session, user, "pytest-agent", "127.0.0.1")
        assert session.user_id == user.id

        new_raw, rotated_user = await service.rotate_refresh_token(
            db_session, raw_refresh, "pytest-agent", "127.0.0.1"
        )
        assert rotated_user.id == user.id
        assert new_raw != raw_refresh

        # Old refresh token is no longer valid after rotation.
        with pytest.raises(InvalidOrExpiredTokenError):
            await service.rotate_refresh_token(db_session, raw_refresh, None, None)

    async def test_rotate_rejects_unknown_token(self, db_session):
        with pytest.raises(InvalidOrExpiredTokenError):
            await service.rotate_refresh_token(db_session, "no-such-token", None, None)

    async def test_rotate_rejects_expired_session(self, db_session):
        user = await _register(db_session, email="expiredsession@example.com")
        raw_refresh, token_hash = "expired-refresh-raw", hash_opaque_token("expired-refresh-raw")
        db_session.add(
            Session(
                user_id=user.id,
                refresh_token_hash=token_hash,
                created_at=datetime.now(UTC) - timedelta(days=2),
                expires_at=datetime.now(UTC) - timedelta(days=1),
            )
        )
        await db_session.commit()

        with pytest.raises(InvalidOrExpiredTokenError):
            await service.rotate_refresh_token(db_session, raw_refresh, None, None)

    async def test_revoke_session_is_idempotent(self, db_session):
        user = await _register(db_session, email="revoke@example.com")
        raw_refresh, _ = await service.create_session(db_session, user, None, None)

        await service.revoke_session(db_session, raw_refresh)
        # Second revoke of the same (already revoked) token must not raise.
        await service.revoke_session(db_session, raw_refresh)

        with pytest.raises(InvalidOrExpiredTokenError):
            await service.rotate_refresh_token(db_session, raw_refresh, None, None)

    async def test_revoke_session_unknown_token_is_noop(self, db_session):
        await service.revoke_session(db_session, "never-issued-token")  # must not raise

    async def test_revoke_all_sessions(self, db_session):
        user = await _register(db_session, email="revokeall@example.com")
        raw_a, _ = await service.create_session(db_session, user, None, None)
        raw_b, _ = await service.create_session(db_session, user, None, None)

        await service.revoke_all_sessions(db_session, user)

        with pytest.raises(InvalidOrExpiredTokenError):
            await service.rotate_refresh_token(db_session, raw_a, None, None)
        with pytest.raises(InvalidOrExpiredTokenError):
            await service.rotate_refresh_token(db_session, raw_b, None, None)


class TestPasswordReset:
    async def test_unknown_email_is_silent_noop(self, db_session):
        # Enumeration-safe: must not raise for an email that was never registered.
        await service.request_password_reset(db_session, "nobody@example.com")

    async def test_full_reset_cycle(self, db_session):
        user = await _register(db_session, email="forgot@example.com", password="original-password1")
        await service.request_password_reset(db_session, "forgot@example.com")

        result = await db_session.execute(
            select(PasswordResetToken).where(PasswordResetToken.user_id == user.id)
        )
        row = result.scalar_one()
        assert row.consumed_at is None

        # We can't recover the raw token from its hash, so drive the
        # rest of the flow through a token we control end-to-end.
        raw_token = "reset-raw-token"
        db_session.add(
            PasswordResetToken(
                user_id=user.id,
                token_hash=hash_opaque_token(raw_token),
                expires_at=datetime.now(UTC) + timedelta(minutes=30),
            )
        )
        await db_session.commit()

        await service.reset_password(db_session, raw_token, "new-password-99")

        # Old password no longer works, new one does.
        with pytest.raises(InvalidCredentialsError):
            await service.authenticate_user(db_session, "forgot@example.com", "original-password1")
        authed = await service.authenticate_user(db_session, "forgot@example.com", "new-password-99")
        assert authed.id == user.id

    async def test_reset_revokes_existing_sessions(self, db_session):
        user = await _register(db_session, email="resetrevoke@example.com", password="original-password1")
        raw_refresh, _ = await service.create_session(db_session, user, None, None)

        raw_token = "resetrevoke-raw-token"
        db_session.add(
            PasswordResetToken(
                user_id=user.id,
                token_hash=hash_opaque_token(raw_token),
                expires_at=datetime.now(UTC) + timedelta(minutes=30),
            )
        )
        await db_session.commit()

        await service.reset_password(db_session, raw_token, "new-password-99")

        with pytest.raises(InvalidOrExpiredTokenError):
            await service.rotate_refresh_token(db_session, raw_refresh, None, None)

    async def test_expired_reset_token_rejected(self, db_session):
        user = await _register(db_session, email="expiredreset@example.com")
        raw_token = "expiredreset-raw-token"
        db_session.add(
            PasswordResetToken(
                user_id=user.id,
                token_hash=hash_opaque_token(raw_token),
                created_at=datetime.now(UTC) - timedelta(hours=1),
                expires_at=datetime.now(UTC) - timedelta(minutes=1),
            )
        )
        await db_session.commit()

        with pytest.raises(InvalidOrExpiredTokenError):
            await service.reset_password(db_session, raw_token, "new-password-99")

    async def test_reset_clears_lockout_state(self, db_session):
        user = await _register(db_session, email="lockedreset@example.com", password="original-password1")
        user.failed_login_attempts = settings.max_failed_login_attempts
        user.locked_until = datetime.now(UTC) + timedelta(minutes=15)
        await db_session.commit()

        raw_token = "lockedreset-raw-token"
        db_session.add(
            PasswordResetToken(
                user_id=user.id,
                token_hash=hash_opaque_token(raw_token),
                expires_at=datetime.now(UTC) + timedelta(minutes=30),
            )
        )
        await db_session.commit()

        await service.reset_password(db_session, raw_token, "new-password-99")

        refreshed = await service.get_user_by_email(db_session, "lockedreset@example.com")
        assert refreshed.failed_login_attempts == 0
        assert refreshed.locked_until is None
