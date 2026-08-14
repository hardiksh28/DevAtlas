"""Auth & Identity — router.

Thin HTTP layer only: every handler below extracts what it needs from
the request, calls exactly one service.py function, and shapes the
result into a schemas.py response. No business logic, no direct model
queries beyond what `Depends(get_current_user)` already does — see
service.py for the actual rules (lockout thresholds, token TTLs,
enumeration-safe responses, etc.).

Cookie contract (browser clients):
- `access_token` — httpOnly, short-lived JWT, sent on every request
  (Path=/). Also returned in the response body for non-browser callers.
- `refresh_token` — httpOnly, opaque, long-lived, scoped to Path=/v1/auth
  only (it's never needed outside the refresh/logout routes, so it's
  never sent anywhere else).
"""

from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db
from app.modules.auth import service
from app.modules.auth.dependencies import (
    ACCESS_TOKEN_COOKIE_NAME,
    REFRESH_TOKEN_COOKIE_NAME,
    get_current_user,
)
from app.modules.auth.exceptions import NotAuthenticatedError
from app.modules.auth.models import User
from app.modules.auth.rate_limit import rate_limit
from app.modules.auth.schemas import (
    AccessTokenResponse,
    ForgotPasswordRequest,
    LoginRequest,
    MessageResponse,
    RegisterRequest,
    ResendVerificationRequest,
    ResetPasswordRequest,
    UpdateCompanionRequest,
    UserRead,
    VerifyEmailRequest,
)
from app.modules.auth.security import create_access_token

router = APIRouter(prefix="/v1/auth", tags=["Auth & Identity"])
settings = get_settings()

_REFRESH_COOKIE_PATH = f"{router.prefix}"


def _client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


def _set_auth_cookies(response: Response, access_token: str, expires_in: int, refresh_token: str) -> None:
    response.set_cookie(
        key=ACCESS_TOKEN_COOKIE_NAME,
        value=access_token,
        max_age=expires_in,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        domain=settings.cookie_domain,
        path="/",
    )
    response.set_cookie(
        key=REFRESH_TOKEN_COOKIE_NAME,
        value=refresh_token,
        max_age=settings.refresh_token_ttl_days * 24 * 60 * 60,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        domain=settings.cookie_domain,
        path=_REFRESH_COOKIE_PATH,
    )


def _clear_auth_cookies(response: Response) -> None:
    response.delete_cookie(
        ACCESS_TOKEN_COOKIE_NAME, domain=settings.cookie_domain, path="/"
    )
    response.delete_cookie(
        REFRESH_TOKEN_COOKIE_NAME, domain=settings.cookie_domain, path=_REFRESH_COOKIE_PATH
    )


async def _issue_tokens_response(
    response: Response, db: AsyncSession, request: Request, user: User
) -> AccessTokenResponse:
    access_token, expires_in = create_access_token(user.id)
    refresh_token, _ = await service.create_session(
        db, user, request.headers.get("user-agent"), _client_ip(request)
    )
    _set_auth_cookies(response, access_token, expires_in, refresh_token)
    return AccessTokenResponse(
        access_token=access_token,
        expires_in=expires_in,
        user=UserRead.from_model(user),
    )


@router.post(
    "/register",
    response_model=AccessTokenResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[rate_limit("register", times=5, seconds=60)],
)
async def register(
    payload: RegisterRequest,
    response: Response,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> AccessTokenResponse:
    """Creates the account, sends a verification email, and logs the
    user in immediately — email verification is informational (reflected
    in `UserRead.email_verified`), not a gate on using the product, so
    there's no reason to make the user wait for it."""
    user = await service.register_user(db, payload.email, payload.password, payload.display_name)
    return await _issue_tokens_response(response, db, request, user)


@router.post(
    "/login",
    response_model=AccessTokenResponse,
    dependencies=[rate_limit("login", times=10, seconds=60)],
)
async def login(
    payload: LoginRequest,
    response: Response,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> AccessTokenResponse:
    user = await service.authenticate_user(db, payload.email, payload.password)
    return await _issue_tokens_response(response, db, request, user)


@router.post("/refresh", response_model=AccessTokenResponse)
async def refresh(
    response: Response,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> AccessTokenResponse:
    raw_refresh_token = request.cookies.get(REFRESH_TOKEN_COOKIE_NAME)
    if not raw_refresh_token:
        raise NotAuthenticatedError()

    new_refresh_token, user = await service.rotate_refresh_token(
        db, raw_refresh_token, request.headers.get("user-agent"), _client_ip(request)
    )
    access_token, expires_in = create_access_token(user.id)
    _set_auth_cookies(response, access_token, expires_in, new_refresh_token)
    return AccessTokenResponse(
        access_token=access_token,
        expires_in=expires_in,
        user=UserRead.from_model(user),
    )


@router.post("/logout", response_model=MessageResponse)
async def logout(
    response: Response,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    raw_refresh_token = request.cookies.get(REFRESH_TOKEN_COOKIE_NAME)
    if raw_refresh_token:
        await service.revoke_session(db, raw_refresh_token)
    _clear_auth_cookies(response)
    return MessageResponse(message="Logged out.")


@router.post("/logout-all", response_model=MessageResponse)
async def logout_all(
    response: Response,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MessageResponse:
    await service.revoke_all_sessions(db, current_user)
    _clear_auth_cookies(response)
    return MessageResponse(message="Logged out of all sessions.")


@router.get("/me", response_model=UserRead)
async def me(current_user: User = Depends(get_current_user)) -> UserRead:
    return UserRead.from_model(current_user)


@router.patch("/me/companion", response_model=UserRead)
async def update_companion(
    payload: UpdateCompanionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserRead:
    user = await service.update_companion(
        db, current_user, payload.companion_name, payload.companion_avatar
    )
    return UserRead.from_model(user)


@router.post(
    "/forgot-password",
    response_model=MessageResponse,
    dependencies=[rate_limit("forgot_password", times=5, seconds=60)],
)
async def forgot_password(
    payload: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)
) -> MessageResponse:
    await service.request_password_reset(db, payload.email)
    # Same message whether or not the email is registered — see
    # service.request_password_reset for why.
    return MessageResponse(
        message="If an account with that email exists, a password reset link has been sent."
    )


@router.post(
    "/reset-password",
    response_model=MessageResponse,
    dependencies=[rate_limit("reset_password", times=10, seconds=60)],
)
async def reset_password_route(
    payload: ResetPasswordRequest, db: AsyncSession = Depends(get_db)
) -> MessageResponse:
    await service.reset_password(db, payload.token, payload.password)
    return MessageResponse(message="Password has been reset. Please log in again.")


@router.post(
    "/verify-email",
    response_model=UserRead,
    dependencies=[rate_limit("verify_email", times=10, seconds=60)],
)
async def verify_email_route(
    payload: VerifyEmailRequest, db: AsyncSession = Depends(get_db)
) -> UserRead:
    user = await service.verify_email(db, payload.token)
    return UserRead.from_model(user)


@router.post(
    "/resend-verification",
    response_model=MessageResponse,
    dependencies=[rate_limit("resend_verification", times=5, seconds=60)],
)
async def resend_verification(
    payload: ResendVerificationRequest, db: AsyncSession = Depends(get_db)
) -> MessageResponse:
    # Deliberately does NOT require being logged in (a user who can't log
    # in because an old session expired should still be able to ask for a
    # fresh verification link) and deliberately does NOT reveal whether
    # the email exists, matching forgot-password's enumeration-safe shape.
    user = await service.get_user_by_email(db, payload.email)
    if user is not None:
        await service.resend_verification_email(db, user)
    return MessageResponse(message="If an account with that email exists, a verification email has been sent.")
