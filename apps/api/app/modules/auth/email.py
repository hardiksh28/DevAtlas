"""Auth & Identity — transactional email.

One interface (`EmailSender`), swappable implementation. `ConsoleEmailSender`
logs the link instead of sending it (dev/test default, and the safe
fallback if "resend" is selected without an API key). `ResendEmailSender`
calls Resend's HTTP API directly via the app's existing `httpx` dependency
— no new SDK needed for one POST endpoint. Adding a second provider later
means one more class and one more branch in `get_email_sender`; nothing
above this module needs to change.
"""

import logging
from abc import ABC, abstractmethod
from urllib.parse import urlencode

import httpx

from app.core.config import get_settings

logger = logging.getLogger("app.auth.email")
settings = get_settings()

RESEND_API_URL = "https://api.resend.com/emails"


class EmailSender(ABC):
    @abstractmethod
    async def send(self, to: str, subject: str, body: str) -> None: ...


class ConsoleEmailSender(EmailSender):
    """Dev/test default: logs the email instead of sending it. This is
    deliberately not gated behind `if not settings.is_production` inside
    the send path — the *factory* (`get_email_sender`) is where that
    decision belongs, so this class stays a pure, always-safe no-op
    sender usable in tests too."""

    async def send(self, to: str, subject: str, body: str) -> None:
        logger.info("EMAIL to=%s subject=%r\n%s", to, subject, body)


class ResendEmailSender(EmailSender):
    """Sends via Resend's REST API (https://resend.com/docs/api-reference/emails/send-email).

    Deliberately fails loud rather than swallowing errors: an auth
    endpoint that reports "email sent" when it wasn't (e.g. an expired
    API key) is worse than one that surfaces a 500, because the user has
    no other way to discover their reset/verification link never arrived.
    """

    def __init__(self, api_key: str, from_address: str) -> None:
        self._api_key = api_key
        self._from_address = from_address

    async def send(self, to: str, subject: str, body: str) -> None:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                RESEND_API_URL,
                headers={"Authorization": f"Bearer {self._api_key}"},
                json={
                    "from": self._from_address,
                    "to": [to],
                    "subject": subject,
                    # Callers build `body` as plain text (see the
                    # send_*_email helpers below) — wrapping in <pre>
                    # preserves the line breaks without needing a
                    # separate HTML template per email.
                    "html": f"<pre style='font-family: inherit; white-space: pre-wrap'>{body}</pre>",
                    "text": body,
                },
            )
            response.raise_for_status()


def get_email_sender() -> EmailSender:
    if settings.email_provider == "resend":
        if settings.resend_api_key:
            return ResendEmailSender(settings.resend_api_key, settings.email_from_address)
        # Misconfigured deploy (provider selected, no key) — fall back to
        # console but log loudly so "reset emails aren't arriving" has an
        # obvious cause in the logs instead of a silent 401 from Resend.
        logger.warning(
            "EMAIL_PROVIDER=resend but RESEND_API_KEY is unset — falling back to "
            "ConsoleEmailSender. Transactional emails will only appear in logs."
        )
    return ConsoleEmailSender()


def build_password_reset_link(raw_token: str) -> str:
    query = urlencode({"token": raw_token})
    return f"{settings.frontend_url}/reset-password?{query}"


def build_email_verification_link(raw_token: str) -> str:
    query = urlencode({"token": raw_token})
    return f"{settings.frontend_url}/verify-email?{query}"


async def send_password_reset_email(sender: EmailSender, to: str, raw_token: str) -> None:
    link = build_password_reset_link(raw_token)
    await sender.send(
        to=to,
        subject="Reset your password",
        body=(
            f"We received a request to reset your password.\n\n"
            f"Reset it here (expires in {settings.password_reset_token_ttl_minutes} minutes):\n"
            f"{link}\n\n"
            f"If you didn't request this, you can safely ignore this email."
        ),
    )


async def send_email_verification_email(sender: EmailSender, to: str, raw_token: str) -> None:
    link = build_email_verification_link(raw_token)
    await sender.send(
        to=to,
        subject="Verify your email",
        body=(
            f"Confirm your email address to finish setting up your account "
            f"(expires in {settings.email_verification_token_ttl_hours} hours):\n"
            f"{link}"
        ),
    )
