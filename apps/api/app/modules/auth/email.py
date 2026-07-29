"""Auth & Identity — transactional email.

One interface (`EmailSender`), swappable implementation. No production
email provider (SES/Postmark/Resend) is wired in yet — no such
credentials exist in this repo's env vars today — so the only concrete
implementation is a console sender that logs the link. Swapping in a
real provider later means writing one more class and changing
`get_email_sender`'s branch; nothing above this module needs to change.
"""

import logging
from abc import ABC, abstractmethod
from urllib.parse import urlencode

from app.core.config import get_settings

logger = logging.getLogger("app.auth.email")
settings = get_settings()


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


def get_email_sender() -> EmailSender:
    # A real provider branch (e.g. `if settings.email_provider ==
    # "resend": return ResendEmailSender(...)`) goes here once one is
    # actually configured. Until then, every environment gets the
    # console sender — including production, which is a deliberate,
    # visible gap rather than a silent one: it shows up immediately as
    # "reset emails aren't arriving" instead of failing open in a way
    # that's hard to notice.
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
