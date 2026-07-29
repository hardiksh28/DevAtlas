"""Auth & Identity — FastAPI dependencies.

`get_current_user` is the one thing every other module will eventually
import from this module (`Depends(get_current_user)` on any route that
needs an authenticated caller) — it's the actual enforcement point, not
just documentation of intent. Everything it needs to validate a request
is either the request's cookies or the database; deliberately no
framework-crossing imports the other direction (auth never imports from
a feature module).
"""

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.auth.exceptions import AccountDisabledError, NotAuthenticatedError
from app.modules.auth.models import User
from app.modules.auth.security import InvalidAccessTokenError, decode_access_token

ACCESS_TOKEN_COOKIE_NAME = "access_token"
REFRESH_TOKEN_COOKIE_NAME = "refresh_token"


def _extract_access_token(request: Request) -> str:
    # Cookie first (the browser client's path); Authorization header as
    # a fallback for non-browser callers (mobile, CLI, server-to-server,
    # tests) that don't carry a cookie jar.
    token = request.cookies.get(ACCESS_TOKEN_COOKIE_NAME)
    if token:
        return token

    authorization = request.headers.get("Authorization")
    if authorization and authorization.lower().startswith("bearer "):
        return authorization[len("bearer ") :]

    raise NotAuthenticatedError()


async def get_current_user(request: Request, db: AsyncSession = Depends(get_db)) -> User:
    token = _extract_access_token(request)
    try:
        user_id = decode_access_token(token)
    except InvalidAccessTokenError as exc:
        raise NotAuthenticatedError() from exc

    user = await db.get(User, user_id)
    if user is None:
        raise NotAuthenticatedError()
    if user.status != "active":
        raise AccountDisabledError()

    return user
