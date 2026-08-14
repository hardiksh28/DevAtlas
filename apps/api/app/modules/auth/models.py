import uuid
from datetime import UTC, datetime

from sqlalchemy import CheckConstraint, ForeignKey, Index, LargeBinary, SmallInteger, String
from sqlalchemy.dialects.postgresql import CITEXT, INET, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base


class User(Base):
    """The platform's own identity — primary key everywhere else in the
    system points here, never at a GitHub user ID directly. This is what
    lets a second login method be added later (ARCHITECTURE.md, Auth &
    Identity) without an identity migration.

    Email/password is that second login method (see
    docs/architecture/database-schema-v1.md) — it coexists with GitHub
    OAuth rather than replacing it; `password_hash` is nullable so a
    GitHub-only user is still a valid row.
    """

    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("failed_login_attempts >= 0", name="ck_users_failed_login_attempts_nonneg"),
        CheckConstraint("status IN ('active', 'disabled', 'deleted')", name="ck_users_status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # CITEXT gives case-insensitive uniqueness/comparison at the DB level
    # (Foo@x.com and foo@x.com are the same account) instead of relying
    # on every call site remembering to .lower() first.
    email: Mapped[str] = mapped_column(CITEXT, unique=True, index=True)
    email_verified_at: Mapped[datetime | None] = mapped_column(default=None)

    # Full Argon2id-encoded string (algorithm, salt, cost params all
    # embedded in the encoding) — NULL for users who only ever used
    # GitHub OAuth.
    password_hash: Mapped[str | None] = mapped_column(String, default=None)
    password_updated_at: Mapped[datetime | None] = mapped_column(default=None)

    display_name: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(20), server_default="active")

    # The user's named, customized mentor persona (see schemas.COMPANION_AVATARS
    # for the closed set `companion_avatar` is validated against). Both
    # nullable — a user who hasn't been through the naming flow yet still
    # gets a mentor, just with a generic default in the UI.
    companion_name: Mapped[str | None] = mapped_column(String(50), default=None)
    companion_avatar: Mapped[str | None] = mapped_column(String(30), default=None)

    failed_login_attempts: Mapped[int] = mapped_column(SmallInteger, server_default="0")
    locked_until: Mapped[datetime | None] = mapped_column(default=None)

    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    # Maintained by a DB trigger (set_updated_at(), attached in the
    # migration), not onupdate= here — a trigger can't be bypassed by a
    # raw UPDATE or a bulk `update(User)...` statement the way an
    # ORM-level default can (see database-schema-v1.md's cross-cutting
    # conventions).
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now())

    github_identity: Mapped["GithubIdentity"] = relationship(back_populates="user", uselist=False)
    sessions: Mapped[list["Session"]] = relationship(back_populates="user", cascade="all, delete-orphan")

    @property
    def is_locked(self) -> bool:
        return self.locked_until is not None and self.locked_until > datetime.now(UTC)


class GithubIdentity(Base):
    """Linked identity, 1:1 with User for V1 (see ARCHITECTURE.md Section
    7). Kept as its own table — not columns on User — so a second
    provider never requires touching the users table's shape."""

    __tablename__ = "github_identities"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), unique=True)
    github_user_id: Mapped[int] = mapped_column(unique=True, index=True)
    github_login: Mapped[str] = mapped_column(String(255))

    user: Mapped["User"] = relationship(back_populates="github_identity")


class OAuthToken(Base):
    """Login-only tokens (read:user, user:email) — deliberately separate
    from repository_integration's tokens, which are read-only repo-access
    tokens tied to a GitHub App install. Never the same table, never the
    same trust boundary (ARCHITECTURE.md Section 7)."""

    __tablename__ = "oauth_tokens"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), unique=True)
    # Encrypted at rest (application-level encryption, not plaintext) —
    # never store OAuth tokens as plain text columns.
    encrypted_access_token: Mapped[bytes] = mapped_column(LargeBinary)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class Session(Base):
    """Refresh-token store backing the JWT access/refresh hybrid: the
    access token is a short-lived, self-contained JWT checked on every
    request (no DB hit); this table holds the long-lived *refresh*
    token's hash, which is what actually makes "logout" and "logout
    everywhere" instant and real instead of "wait for the JWT to expire."

    Only a hash of the raw refresh token is ever stored — identical
    reasoning to password hashing: if this table leaks, a hash is
    useless to an attacker, a raw token is an instant account takeover.
    """

    __tablename__ = "sessions"
    __table_args__ = (
        CheckConstraint("expires_at > created_at", name="ck_sessions_expires_after_created"),
        Index("ix_sessions_user_id", "user_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    refresh_token_hash: Mapped[str] = mapped_column(String, unique=True)
    user_agent: Mapped[str | None] = mapped_column(String, default=None)
    ip_address: Mapped[str | None] = mapped_column(INET, default=None)

    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    last_seen_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())
    expires_at: Mapped[datetime] = mapped_column()
    revoked_at: Mapped[datetime | None] = mapped_column(default=None)

    user: Mapped["User"] = relationship(back_populates="sessions")


class PasswordResetToken(Base):
    """One-time, short-lived, hashed token issued for "forgot password";
    consumed exactly once to authorize a new password. Only the hash is
    stored — the raw token exists only in the emailed link."""

    __tablename__ = "password_reset_tokens"
    __table_args__ = (
        CheckConstraint("expires_at > created_at", name="ck_password_reset_expires_after_created"),
        Index(
            "ix_password_reset_tokens_user_id_unconsumed",
            "user_id",
            postgresql_where="consumed_at IS NULL",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    token_hash: Mapped[str] = mapped_column(String, unique=True)

    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    expires_at: Mapped[datetime] = mapped_column()
    consumed_at: Mapped[datetime | None] = mapped_column(default=None)
    requested_ip: Mapped[str | None] = mapped_column(INET, default=None)


class EmailVerificationToken(Base):
    """Structurally identical to PasswordResetToken, different job:
    proves the user controls an email address (at signup, and later for
    email-change flows). Successful verification sets
    `users.email_verified_at`.

    `email` is stored on the token (not read off `users.email`) so a
    future "change your email" flow can verify a new, not-yet-committed
    address without ambiguity about which email is being proven.
    """

    __tablename__ = "email_verification_tokens"
    __table_args__ = (
        CheckConstraint("expires_at > created_at", name="ck_email_verification_expires_after_created"),
        Index(
            "ix_email_verification_tokens_user_id_unconsumed",
            "user_id",
            postgresql_where="consumed_at IS NULL",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    token_hash: Mapped[str] = mapped_column(String, unique=True)
    email: Mapped[str] = mapped_column(CITEXT)

    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    expires_at: Mapped[datetime] = mapped_column()
    consumed_at: Mapped[datetime | None] = mapped_column(default=None)
