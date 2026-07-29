"""Auth & Identity — request/response schemas.

Every route in router.py takes and returns one of these — never a bare
dict — so FastAPI validates the request body and generates accurate
OpenAPI docs from a single source of truth.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator

# NIST 800-63B guidance (length over forced composition rules): require a
# reasonable minimum length, don't force "must contain a symbol" rules
# that push users toward predictable substitutions (`password!` isn't
# meaningfully stronger than `password`). Cap the max length too — an
# unbounded password lets someone submit a multi-megabyte string that's
# expensive for Argon2 to hash, a cheap denial-of-service lever.
_PASSWORD_MIN_LENGTH = 8
_PASSWORD_MAX_LENGTH = 128

# Opaque tokens (see security.py) are secrets.token_urlsafe(32), ~43
# chars — 512 is generous headroom for that while still rejecting an
# attacker handing this unauthenticated field an arbitrarily large body
# just to make the server do pointless SHA-256/DB-lookup work per byte.
_OPAQUE_TOKEN_MAX_LENGTH = 512


class _PasswordMixin(BaseModel):
    password: str = Field(..., min_length=_PASSWORD_MIN_LENGTH, max_length=_PASSWORD_MAX_LENGTH)

    @field_validator("password")
    @classmethod
    def _password_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("password cannot be blank")
        return value


class RegisterRequest(_PasswordMixin):
    email: EmailStr
    display_name: str = Field(..., min_length=1, max_length=255)

    @field_validator("display_name")
    @classmethod
    def _display_name_not_blank(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("display_name cannot be blank")
        return stripped


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1, max_length=_PASSWORD_MAX_LENGTH)


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(_PasswordMixin):
    token: str = Field(..., min_length=1, max_length=_OPAQUE_TOKEN_MAX_LENGTH)


class VerifyEmailRequest(BaseModel):
    token: str = Field(..., min_length=1, max_length=_OPAQUE_TOKEN_MAX_LENGTH)


class ResendVerificationRequest(BaseModel):
    email: EmailStr


class UserRead(BaseModel):
    id: uuid.UUID
    email: str
    display_name: str
    email_verified: bool
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}

    @classmethod
    def from_model(cls, user: "object") -> "UserRead":
        """Maps the ORM model's nullable `email_verified_at` timestamp
        onto the API's boolean `email_verified` — the API contract
        shouldn't leak *when* verification happened, only whether it
        did; `from_attributes` alone can't do that field rename+coerce,
        so this is an explicit adapter rather than a validator hook.
        """
        return cls(
            id=user.id,  # type: ignore[attr-defined]
            email=user.email,  # type: ignore[attr-defined]
            display_name=user.display_name,  # type: ignore[attr-defined]
            email_verified=user.email_verified_at is not None,  # type: ignore[attr-defined]
            status=user.status,  # type: ignore[attr-defined]
            created_at=user.created_at,  # type: ignore[attr-defined]
        )


class AccessTokenResponse(BaseModel):
    """Returned alongside the httpOnly cookies on login/refresh. The
    access token is duplicated into the response body (not just the
    cookie) for non-browser clients (mobile, CLI, tests) that can't rely
    on cookie jars — but the refresh token is never returned in a body,
    cookie-only, since it's the long-lived credential that actually
    matters if leaked."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserRead


class MessageResponse(BaseModel):
    message: str
