"""Auth & Identity — domain exceptions.

The service layer (service.py) raises these; it never raises HTTPException
directly, and it never returns a sentinel/None for a failure case. Keeping
FastAPI/HTTP concerns out of the service layer means the same functions
stay callable from a future non-HTTP caller (a CLI, a background job)
without dragging framework imports along.

main.py registers one exception handler per class here, mapping each to
an HTTP status — see `register_auth_exception_handlers`.
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class AuthError(Exception):
    """Base for every auth-domain error."""

    def __init__(self, message: str, error_code: str) -> None:
        super().__init__(message)
        self.message = message
        self.error_code = error_code


class EmailAlreadyRegisteredError(AuthError):
    def __init__(self) -> None:
        super().__init__("An account with this email already exists.", "email_already_registered")


class InvalidCredentialsError(AuthError):
    """Deliberately identical whether the email doesn't exist or the
    password is wrong — distinguishing the two in the response is a
    textbook account-enumeration leak."""

    def __init__(self) -> None:
        super().__init__("Incorrect email or password.", "invalid_credentials")


class AccountLockedError(AuthError):
    def __init__(self) -> None:
        super().__init__(
            "This account is temporarily locked due to repeated failed login attempts.",
            "account_locked",
        )


class AccountDisabledError(AuthError):
    def __init__(self) -> None:
        super().__init__("This account has been disabled.", "account_disabled")


class InvalidOrExpiredTokenError(AuthError):
    """Shared by password-reset, email-verification, and refresh-token
    validation — same reasoning as InvalidCredentialsError: "expired" vs
    "never existed" vs "already used" isn't information a client needs,
    and handing it out for free helps an attacker enumerate valid
    tokens."""

    def __init__(self) -> None:
        super().__init__("This token is invalid or has expired.", "invalid_or_expired_token")


class NotAuthenticatedError(AuthError):
    def __init__(self) -> None:
        super().__init__("Authentication required.", "not_authenticated")


class RateLimitExceededError(AuthError):
    """Raised by rate_limit.py's dependency once an IP exceeds the
    budget for a given route. `retry_after` (seconds) becomes the
    response's Retry-After header so a well-behaved client knows when
    to try again instead of immediately re-requesting."""

    def __init__(self, retry_after: int) -> None:
        super().__init__("Too many requests. Please try again later.", "rate_limited")
        self.retry_after = retry_after


# --- FastAPI wiring ---
#
# One handler, registered once against the AuthError base class.
# Starlette's exception middleware walks a raised exception's MRO to
# find the most specific registered handler, so every subclass above
# is caught by this single registration — adding a new AuthError
# subclass later only means adding one line to _STATUS_CODES, not a new
# handler.

_STATUS_CODES: dict[type[AuthError], int] = {
    EmailAlreadyRegisteredError: 409,
    InvalidCredentialsError: 401,
    AccountLockedError: 423,  # Locked
    AccountDisabledError: 403,
    InvalidOrExpiredTokenError: 400,
    NotAuthenticatedError: 401,
    RateLimitExceededError: 429,
}


async def _handle_auth_error(request: Request, exc: Exception) -> JSONResponse:
    # Starlette's registered-handler signature is (Request, Exception) —
    # narrowed back to AuthError here since add_exception_handler(AuthError, ...)
    # below guarantees this handler is only ever invoked for AuthError
    # (and subclass) instances.
    assert isinstance(exc, AuthError)
    status_code = _STATUS_CODES.get(type(exc), 400)
    headers: dict[str, str] | None = None
    if status_code == 401:
        headers = {"WWW-Authenticate": "Bearer"}
    elif isinstance(exc, RateLimitExceededError):
        headers = {"Retry-After": str(exc.retry_after)}
    return JSONResponse(
        status_code=status_code,
        content={"detail": exc.message, "error_code": exc.error_code},
        headers=headers,
    )


def register_auth_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AuthError, _handle_auth_error)
