"""Unit tests for app.modules.auth.security.

Deliberately DB-free — everything in security.py is a pure function
(hashing, JWT encode/decode, random token generation), so these run
without Postgres/docker-compose and are exactly the tests CI's
`uv run pytest` job actually exercises today.
"""

import uuid
from datetime import UTC, datetime, timedelta

import jwt
import pytest

from app.core.config import get_settings
from app.modules.auth.security import (
    InvalidAccessTokenError,
    create_access_token,
    decode_access_token,
    generate_opaque_token,
    hash_opaque_token,
    hash_password,
    needs_rehash,
    verify_password,
)

settings = get_settings()


class TestPasswordHashing:
    def test_verify_accepts_correct_password(self) -> None:
        hashed = hash_password("correct horse battery staple")
        assert verify_password("correct horse battery staple", hashed)

    def test_verify_rejects_wrong_password(self) -> None:
        hashed = hash_password("correct horse battery staple")
        assert not verify_password("wrong password", hashed)

    def test_same_password_hashes_differently_each_time(self) -> None:
        # Argon2 embeds a random salt per hash — two hashes of the same
        # password must never be byte-identical, or a leaked hash table
        # would reveal which users share a password.
        first = hash_password("same-password")
        second = hash_password("same-password")
        assert first != second
        assert verify_password("same-password", first)
        assert verify_password("same-password", second)

    def test_freshly_hashed_password_does_not_need_rehash(self) -> None:
        assert needs_rehash(hash_password("whatever")) is False


class TestAccessTokens:
    def test_round_trip(self) -> None:
        user_id = uuid.uuid4()
        token, expires_in = create_access_token(user_id)
        assert expires_in == settings.access_token_ttl_minutes * 60
        assert decode_access_token(token) == user_id

    def test_rejects_expired_token(self) -> None:
        user_id = uuid.uuid4()
        now = datetime.now(UTC)
        expired_payload = {
            "sub": str(user_id),
            "type": "access",
            "iat": now - timedelta(minutes=20),
            "exp": now - timedelta(minutes=5),
        }
        expired_token = jwt.encode(
            expired_payload, settings.api_secret_key, algorithm=settings.jwt_algorithm
        )
        with pytest.raises(InvalidAccessTokenError):
            decode_access_token(expired_token)

    def test_rejects_tampered_signature(self) -> None:
        token, _ = create_access_token(uuid.uuid4())
        tampered = token[:-1] + ("A" if token[-1] != "A" else "B")
        with pytest.raises(InvalidAccessTokenError):
            decode_access_token(tampered)

    def test_rejects_wrong_token_type(self) -> None:
        # A JWT signed with the right secret but the wrong `type` claim
        # would otherwise let a refresh/reset flow's token (if it were
        # ever a JWT) be replayed as an access token.
        now = datetime.now(UTC)
        payload = {
            "sub": str(uuid.uuid4()),
            "type": "refresh",
            "iat": now,
            "exp": now + timedelta(minutes=5),
        }
        wrong_type_token = jwt.encode(
            payload, settings.api_secret_key, algorithm=settings.jwt_algorithm
        )
        with pytest.raises(InvalidAccessTokenError):
            decode_access_token(wrong_type_token)

    def test_rejects_malformed_token(self) -> None:
        with pytest.raises(InvalidAccessTokenError):
            decode_access_token("not-a-jwt-at-all")


class TestOpaqueTokens:
    def test_hash_matches_independently_computed_hash(self) -> None:
        raw_token, token_hash = generate_opaque_token()
        assert hash_opaque_token(raw_token) == token_hash

    def test_tokens_are_unique(self) -> None:
        raw_tokens = {generate_opaque_token()[0] for _ in range(100)}
        assert len(raw_tokens) == 100

    def test_hash_is_sha256_hex(self) -> None:
        _, token_hash = generate_opaque_token()
        assert len(token_hash) == 64
        int(token_hash, 16)  # raises ValueError if not valid hex
