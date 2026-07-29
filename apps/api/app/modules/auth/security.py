"""Auth & Identity — cryptographic primitives.

Three distinct concerns live here, each with a different threat model:

1. Password hashing (Argon2id) — one-way, slow-by-design, for credentials
   a human chose and might reuse elsewhere.
2. JWT access tokens — fast to verify (no DB hit), short-lived, signed
   (not encrypted) so their claims are trusted only because the
   signature is checked, never because they "look right."
3. Opaque tokens (refresh / password-reset / email-verification) — high
   entropy random strings; only their SHA-256 hash is ever persisted, so
   a leaked database row can't be replayed as a real token.

Nothing here talks to the database or FastAPI — that separation is what
lets these functions be unit-tested without a running Postgres.
"""

import hashlib
import secrets
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from app.core.config import get_settings

settings = get_settings()

# Argon2id (the library's default) with the library's own tuned default
# cost parameters — deliberately not hand-tuned here. Argon2's authors'
# defaults already target ~ms-scale verification on typical hardware;
# hand-picking custom cost parameters without benchmarking the actual
# deploy target is more likely to weaken this than improve it.
_password_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    """Returns the full Argon2id-encoded string (algorithm, salt, and
    cost parameters embedded) — safe to store directly in
    `users.password_hash`."""
    return _password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """Constant-time-by-construction (argon2-cffi handles this) — never
    replace with a manual `==` comparison of hashes."""
    try:
        return _password_hasher.verify(password_hash, password)
    except VerifyMismatchError:
        return False


def needs_rehash(password_hash: str) -> bool:
    """True if this hash was created with older/weaker cost parameters
    than the library's current defaults — call after a successful
    `verify_password` and re-hash+save if so, so cost parameters
    upgrade gradually as users log in rather than requiring a bulk
    migration."""
    return _password_hasher.check_needs_rehash(password_hash)


# --- JWT access tokens ---

_ACCESS_TOKEN_TYPE = "access"


def create_access_token(user_id: uuid.UUID) -> tuple[str, int]:
    """Returns (token, expires_in_seconds). The claim set is
    deliberately minimal — just enough to identify the user and let the
    verifier reject wrong-typed/expired/tampered tokens; anything the
    request handler needs beyond `sub` should be loaded fresh from the
    database, not trusted from the token, since a token issued 10
    minutes ago can't reflect a role change that happened 1 minute ago.
    """
    now = datetime.now(UTC)
    expires_delta = timedelta(minutes=settings.access_token_ttl_minutes)
    payload = {
        "sub": str(user_id),
        "type": _ACCESS_TOKEN_TYPE,
        "iat": now,
        "exp": now + expires_delta,
    }
    token = jwt.encode(payload, settings.api_secret_key, algorithm=settings.jwt_algorithm)
    return token, int(expires_delta.total_seconds())


class InvalidAccessTokenError(Exception):
    """Raised for any reason a token can't be trusted — expired, bad
    signature, wrong `type` claim, malformed. Deliberately one error
    type: the caller (the auth dependency) always responds 401 either
    way, and collapsing the reasons avoids leaking which specific check
    failed to a client that might be probing for one."""


def decode_access_token(token: str) -> uuid.UUID:
    """Returns the authenticated user's id, or raises
    InvalidAccessTokenError."""
    try:
        payload: dict[str, Any] = jwt.decode(
            token, settings.api_secret_key, algorithms=[settings.jwt_algorithm]
        )
    except jwt.PyJWTError as exc:
        raise InvalidAccessTokenError("token is expired, malformed, or has a bad signature") from exc

    if payload.get("type") != _ACCESS_TOKEN_TYPE:
        # Rejects a refresh/reset/verification token being replayed as
        # an access token — those are opaque strings, not JWTs, so this
        # only matters if someone hand-crafts a JWT with the right
        # signing key but the wrong `type`.
        raise InvalidAccessTokenError("wrong token type")

    try:
        return uuid.UUID(payload["sub"])
    except (KeyError, ValueError) as exc:
        raise InvalidAccessTokenError("missing or malformed subject claim") from exc


# --- Opaque tokens (refresh / password-reset / email-verification) ---


def generate_opaque_token() -> tuple[str, str]:
    """Returns (raw_token, token_hash). The raw token is what's sent to
    the client (cookie, or emailed link) and never stored; the hash is
    what's persisted and looked up on the next request. SHA-256 (not
    Argon2) is correct here — unlike a password, this token already has
    256 bits of entropy from `secrets.token_urlsafe`, so a fast hash
    can't be brute-forced the way a human-chosen password could be.
    """
    raw_token = secrets.token_urlsafe(32)
    return raw_token, hash_opaque_token(raw_token)


def hash_opaque_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
