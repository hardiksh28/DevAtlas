"""Integration tests for app.modules.auth.router.

Drives the real FastAPI app end-to-end (ASGI transport, no network) —
cookie behavior, status codes, and the AuthError -> HTTP mapping in
exceptions.py are all things a service-layer test can't see, since they
only exist once the router and its dependencies are wired together.

The app never sends real email (see email.py's ConsoleEmailSender) — it
logs the reset/verification link instead, so these tests recover the
raw token by parsing that log line rather than mocking the sender.
"""

import logging
import re
from urllib.parse import parse_qs, urlparse

import pytest

EMAIL_LOGGER = "app.auth.email"


def _extract_token(caplog: pytest.LogCaptureFixture) -> str:
    # caplog accumulates records for the whole test, not just what's
    # logged inside a `with caplog.at_level(...)` block — a token-bearing
    # email logged earlier (e.g. the verify-email link sent at
    # registration) stays in caplog.records. The most recently logged
    # email is always the one relevant to the flow under test, so scan in
    # reverse rather than returning the first match.
    for record in reversed(caplog.records):
        if record.name == EMAIL_LOGGER:
            match = re.search(r"https?://\S+\?token=\S+", record.message)
            if match:
                query = urlparse(match.group(0)).query
                return parse_qs(query)["token"][0]
    raise AssertionError(f"no link found in {EMAIL_LOGGER} logs")


async def _register(client, email="user@example.com", password="hunter22222", display_name="User One"):
    return await client.post(
        "/v1/auth/register",
        json={"email": email, "password": password, "display_name": display_name},
    )


class TestRegister:
    async def test_register_sets_cookies_and_returns_user(self, client):
        resp = await _register(client, email="alice@example.com")
        assert resp.status_code == 201
        body = resp.json()
        assert body["user"]["email"] == "alice@example.com"
        assert body["user"]["email_verified"] is False
        assert "access_token" in resp.cookies
        assert "refresh_token" in resp.cookies

    async def test_register_rejects_weak_password(self, client):
        resp = await _register(client, password="short")
        assert resp.status_code == 422

    async def test_register_rejects_duplicate_email(self, client):
        await _register(client, email="dupe@example.com")
        resp = await _register(client, email="dupe@example.com")
        assert resp.status_code == 409
        assert resp.json()["error_code"] == "email_already_registered"

    async def test_register_rejects_blank_display_name(self, client):
        resp = await client.post(
            "/v1/auth/register",
            json={"email": "blank@example.com", "password": "hunter22222", "display_name": "   "},
        )
        assert resp.status_code == 422


class TestLogin:
    async def test_login_success(self, client):
        await _register(client, email="login@example.com", password="correct-password-1")
        resp = await client.post(
            "/v1/auth/login",
            json={"email": "login@example.com", "password": "correct-password-1"},
        )
        assert resp.status_code == 200
        assert "access_token" in resp.cookies

    async def test_login_wrong_password(self, client):
        await _register(client, email="wrongpw@example.com", password="correct-password-1")
        resp = await client.post(
            "/v1/auth/login",
            json={"email": "wrongpw@example.com", "password": "wrong-password"},
        )
        assert resp.status_code == 401
        assert resp.json()["error_code"] == "invalid_credentials"

    async def test_login_unknown_email_same_error_as_wrong_password(self, client):
        resp = await client.post(
            "/v1/auth/login",
            json={"email": "nobody@example.com", "password": "whatever123"},
        )
        assert resp.status_code == 401
        assert resp.json()["error_code"] == "invalid_credentials"


class TestMe:
    async def test_me_requires_auth(self, client):
        resp = await client.get("/v1/auth/me")
        assert resp.status_code == 401

    async def test_me_returns_current_user(self, client):
        await _register(client, email="me@example.com", password="correct-password-1")
        resp = await client.get("/v1/auth/me")
        assert resp.status_code == 200
        assert resp.json()["email"] == "me@example.com"


class TestRefreshAndLogout:
    async def test_refresh_rotates_tokens(self, client):
        register_resp = await _register(client, email="refresh@example.com")
        old_refresh = register_resp.cookies["refresh_token"]

        resp = await client.post("/v1/auth/refresh")
        assert resp.status_code == 200
        assert resp.cookies["refresh_token"] != old_refresh

    async def test_refresh_without_cookie_rejected(self, client):
        resp = await client.post("/v1/auth/refresh")
        assert resp.status_code == 401

    async def test_logout_revokes_session(self, client):
        await _register(client, email="logout@example.com")
        resp = await client.post("/v1/auth/logout")
        assert resp.status_code == 200

        # The refresh cookie was cleared client-side, but even if a
        # client replayed the old value, refresh must now fail.
        refresh_resp = await client.post("/v1/auth/refresh")
        assert refresh_resp.status_code == 401

    async def test_logout_all_requires_auth(self, client):
        resp = await client.post("/v1/auth/logout-all")
        assert resp.status_code == 401

    async def test_logout_all_revokes_session(self, client):
        await _register(client, email="logoutall@example.com")
        resp = await client.post("/v1/auth/logout-all")
        assert resp.status_code == 200

        refresh_resp = await client.post("/v1/auth/refresh")
        assert refresh_resp.status_code == 401


class TestEmailVerification:
    async def test_verify_email_flow(self, client, caplog: pytest.LogCaptureFixture):
        with caplog.at_level(logging.INFO, logger=EMAIL_LOGGER):
            await _register(client, email="verifyme@example.com")
        token = _extract_token(caplog)

        resp = await client.post("/v1/auth/verify-email", json={"token": token})
        assert resp.status_code == 200
        assert resp.json()["email_verified"] is True

    async def test_verify_email_rejects_bad_token(self, client):
        resp = await client.post("/v1/auth/verify-email", json={"token": "not-a-real-token"})
        assert resp.status_code == 400
        assert resp.json()["error_code"] == "invalid_or_expired_token"

    async def test_resend_verification_is_enumeration_safe(self, client):
        registered = await client.post(
            "/v1/auth/resend-verification", json={"email": "resendtarget@example.com"}
        )
        unregistered = await client.post(
            "/v1/auth/resend-verification", json={"email": "nobody-at-all@example.com"}
        )
        assert registered.status_code == unregistered.status_code == 200
        assert registered.json() == unregistered.json()


class TestPasswordReset:
    async def test_forgot_password_is_enumeration_safe(self, client):
        await _register(client, email="hasaccount@example.com")
        registered = await client.post(
            "/v1/auth/forgot-password", json={"email": "hasaccount@example.com"}
        )
        unregistered = await client.post(
            "/v1/auth/forgot-password", json={"email": "nobody-at-all@example.com"}
        )
        assert registered.status_code == unregistered.status_code == 200
        assert registered.json() == unregistered.json()

    async def test_full_reset_cycle(self, client, caplog: pytest.LogCaptureFixture):
        await _register(client, email="resetflow@example.com", password="original-password1")

        with caplog.at_level(logging.INFO, logger=EMAIL_LOGGER):
            await client.post("/v1/auth/forgot-password", json={"email": "resetflow@example.com"})
        token = _extract_token(caplog)

        resp = await client.post(
            "/v1/auth/reset-password", json={"token": token, "password": "brand-new-password9"}
        )
        assert resp.status_code == 200

        old_login = await client.post(
            "/v1/auth/login",
            json={"email": "resetflow@example.com", "password": "original-password1"},
        )
        assert old_login.status_code == 401

        new_login = await client.post(
            "/v1/auth/login",
            json={"email": "resetflow@example.com", "password": "brand-new-password9"},
        )
        assert new_login.status_code == 200

    async def test_reset_password_rejects_bad_token(self, client):
        resp = await client.post(
            "/v1/auth/reset-password", json={"token": "not-a-real-token", "password": "whatever123"}
        )
        assert resp.status_code == 400
        assert resp.json()["error_code"] == "invalid_or_expired_token"


class TestRateLimiting:
    async def test_login_rate_limit_returns_429_with_retry_after(self, client):
        for _ in range(10):
            await client.post(
                "/v1/auth/login", json={"email": "ratelimit@example.com", "password": "wrong-password"}
            )

        resp = await client.post(
            "/v1/auth/login", json={"email": "ratelimit@example.com", "password": "wrong-password"}
        )
        assert resp.status_code == 429
        assert resp.json()["error_code"] == "rate_limited"
        assert "Retry-After" in resp.headers

    async def test_rate_limiter_fails_open_when_redis_unavailable(self, client):
        from app.core.redis import get_redis
        from app.main import app as fastapi_app
        from tests.conftest import FailingRedis

        async def override_get_redis() -> FailingRedis:
            return FailingRedis()

        # Overrides the client fixture's working FakeRedis for the rest
        # of this test only — the client fixture clears all overrides
        # during its own teardown regardless of what's set here.
        fastapi_app.dependency_overrides[get_redis] = override_get_redis

        for _ in range(15):
            resp = await client.post(
                "/v1/auth/login",
                json={"email": "failopen@example.com", "password": "wrong-password"},
            )
            # Redis is "down": every attempt must still be evaluated as
            # a normal login attempt (401), never blocked (429).
            assert resp.status_code == 401
