"""add auth & identity tables (users, github identities, sessions, tokens)

Revision ID: 202607291200
Revises: 202607290001
Create Date: 2026-07-29

Implements docs/architecture/database-schema-v1.md's `users` table plus
the auth-module scaffold's `github_identities`/`oauth_tokens`, and adds
the tables the email/password login flow needs on top: `sessions`
(refresh-token store for the JWT access/refresh hybrid — see
app/modules/auth/security.py), `password_reset_tokens`, and
`email_verification_tokens`.

`users`/`github_identities`/`oauth_tokens` didn't exist in any prior
migration — the auth module's models.py was scaffolded ahead of its own
migration — so this is a straight CREATE TABLE for all six tables rather
than an ALTER of something already deployed.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "202607291200"
down_revision: str | None = "202607290001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # CITEXT: case-insensitive text so `Foo@x.com` and `foo@x.com`
    # collide at the DB level instead of relying on every call site to
    # .lower() first (docs/architecture/database-schema-v1.md).
    op.execute("CREATE EXTENSION IF NOT EXISTS citext")

    # Shared trigger function backing every table's `updated_at` column
    # — "Maintained by a shared BEFORE UPDATE trigger, not app code"
    # (database-schema-v1.md's cross-cutting conventions): a trigger
    # can't be forgotten the way an ORM-level onupdate= can be bypassed
    # by a raw UPDATE or a bulk `UPDATE ... SET` statement.
    op.execute(
        """
        CREATE OR REPLACE FUNCTION set_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = now();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql
        """
    )

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", postgresql.CITEXT(), nullable=False),
        sa.Column("email_verified_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("password_hash", sa.String(), nullable=True),
        sa.Column("password_updated_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("display_name", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="active"),
        sa.Column(
            "failed_login_attempts", sa.SmallInteger(), nullable=False, server_default="0"
        ),
        sa.Column("locked_until", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.CheckConstraint(
            "failed_login_attempts >= 0", name="ck_users_failed_login_attempts_nonneg"
        ),
        sa.CheckConstraint("status IN ('active', 'disabled', 'deleted')", name="ck_users_status"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.execute(
        "CREATE TRIGGER trg_users_set_updated_at BEFORE UPDATE ON users "
        "FOR EACH ROW EXECUTE FUNCTION set_updated_at()"
    )

    op.create_table(
        "github_identities",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=False,
            unique=True,
        ),
        sa.Column("github_user_id", sa.Integer(), nullable=False, unique=True),
        sa.Column("github_login", sa.String(length=255), nullable=False),
    )
    op.create_index("ix_github_identities_github_user_id", "github_identities", ["github_user_id"])

    op.create_table(
        "oauth_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=False,
            unique=True,
        ),
        sa.Column("encrypted_access_token", sa.LargeBinary(), nullable=False),
        sa.Column(
            "created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )

    op.create_table(
        "sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("refresh_token_hash", sa.String(), nullable=False, unique=True),
        sa.Column("user_agent", sa.String(), nullable=True),
        sa.Column("ip_address", postgresql.INET(), nullable=True),
        sa.Column(
            "created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "last_seen_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column("expires_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.CheckConstraint("expires_at > created_at", name="ck_sessions_expires_after_created"),
    )
    op.create_index("ix_sessions_user_id", "sessions", ["user_id"])

    op.create_table(
        "password_reset_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("token_hash", sa.String(), nullable=False, unique=True),
        sa.Column(
            "created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column("expires_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("consumed_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("requested_ip", postgresql.INET(), nullable=True),
        sa.CheckConstraint(
            "expires_at > created_at", name="ck_password_reset_expires_after_created"
        ),
    )
    # Partial index: only unconsumed tokens are ever looked up by
    # user_id (the "invalidate my prior reset tokens" step) — the
    # overwhelming majority of rows are dead weight within the hour.
    op.execute(
        "CREATE INDEX ix_password_reset_tokens_user_id_unconsumed "
        "ON password_reset_tokens (user_id) WHERE consumed_at IS NULL"
    )

    op.create_table(
        "email_verification_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("token_hash", sa.String(), nullable=False, unique=True),
        sa.Column("email", postgresql.CITEXT(), nullable=False),
        sa.Column(
            "created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column("expires_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("consumed_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.CheckConstraint(
            "expires_at > created_at", name="ck_email_verification_expires_after_created"
        ),
    )
    op.execute(
        "CREATE INDEX ix_email_verification_tokens_user_id_unconsumed "
        "ON email_verification_tokens (user_id) WHERE consumed_at IS NULL"
    )


def downgrade() -> None:
    op.drop_table("email_verification_tokens")
    op.drop_table("password_reset_tokens")
    op.drop_table("sessions")
    op.drop_table("oauth_tokens")
    op.drop_table("github_identities")
    op.execute("DROP TRIGGER IF EXISTS trg_users_set_updated_at ON users")
    op.drop_table("users")
    op.execute("DROP FUNCTION IF EXISTS set_updated_at")
    op.execute("DROP EXTENSION IF EXISTS citext")
