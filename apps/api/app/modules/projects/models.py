import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from sqlalchemy.types import JSON

from app.core.database import Base

# JSONB on Postgres (native containment/indexing support), plain JSON
# elsewhere — this is what lets tests/conftest.py's SQLite fallback
# engine create this table at all; SQLAlchemy has no generic compiler
# for postgresql.JSONB against the SQLite dialect.
_JSONB_OR_JSON = JSON().with_variant(JSONB(), "postgresql")


class Project(Base):
    """The workspace shell — what `repository_connections`, `roadmaps`,
    and `milestones` (ARCHITECTURE.md Section 7, still out of scope)
    will attach to via FK later without this table needing to change
    shape when they do. See docs/architecture/project-workspace-v1.md.

    Single-owner, matching docs/architecture/database-schema-v1.md's
    original draft — team/collaboration is an explicitly later phase.
    """

    __tablename__ = "projects"
    __table_args__ = (
        CheckConstraint("status IN ('active', 'archived', 'deleted')", name="ck_projects_status"),
        Index("ix_projects_owner_status_updated", "owner_id", "status", "updated_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(String, default=None)
    status: Mapped[str] = mapped_column(String(20), server_default="active")

    # Distinct from `deleted_at` below — archiving is a fully reversible
    # "I'm done with this for now," never a step toward deletion (see
    # the architecture doc's "archive vs delete vs restore" section).
    archived_at: Mapped[datetime | None] = mapped_column(default=None)
    # Soft delete: set on DELETE, cleared on restore. Kept alongside
    # `status` (rather than status alone, unlike `users`) because this
    # module supports an actual restore flow, not just an "is this row
    # alive" flag — the timestamp is what a future retention/purge job
    # and a "recoverable for 30 days" UI would filter on.
    deleted_at: Mapped[datetime | None] = mapped_column(default=None)

    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    # Maintained by the shared set_updated_at() trigger (see the auth
    # migration), not onupdate= — same reasoning as every other table.
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now())

    # lazy="joined": every card/list render needs icon+color (see
    # ProjectRead.from_model), so this 1:1 relationship is always
    # pulled in via a single JOIN rather than a lazy per-row load —
    # the standard SQLAlchemy pattern for a to-one relationship that's
    # needed essentially every time its parent is, and what makes
    # `project.settings` safe to access without an explicit eager-load
    # option at every call site (avoiding async lazy-load pitfalls).
    settings: Mapped["ProjectSettings"] = relationship(
        back_populates="project",
        uselist=False,
        cascade="all, delete-orphan",
        lazy="joined",
        innerjoin=True,
    )
    recent_views: Mapped[list["RecentProject"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )


class ProjectSettings(Base):
    """1:1 with Project — same shape as auth's `user_preferences`:
    typed columns for the handful of settings read on every card/shell
    render (`icon`, `color`), one JSONB catch-all for everything else.
    Promote a `settings` key to a real column only once something
    needs to filter or index on it — don't pre-guess.
    """

    __tablename__ = "project_settings"
    __table_args__ = (
        CheckConstraint(
            "color IN ('slate', 'blue', 'green', 'amber', 'rose', 'violet')",
            name="ck_project_settings_color",
        ),
    )

    # PK **is** the FK — true 1:1, no surrogate id, identical to
    # user_preferences.user_id.
    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), primary_key=True
    )
    icon: Mapped[str] = mapped_column(String(16), server_default="📁")
    # Named accent from a closed palette, not free text — `color`
    # drives a Tailwind class lookup on the frontend, and a free-text
    # value that resolves to no class would fail silently there rather
    # than loudly here.
    color: Mapped[str] = mapped_column(String(20), server_default="slate")
    settings: Mapped[dict] = mapped_column(_JSONB_OR_JSON, server_default="{}")
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now())

    project: Mapped["Project"] = relationship(back_populates="settings")


class RecentProject(Base):
    """Per-(user, project) last-viewed marker powering the dashboard's
    "recent projects" rail — deliberately separate from
    `projects.updated_at` (which tracks *modification*, not *viewing*).
    Composite PK gives upsert-friendly dedupe for free: one row per
    pair regardless of view count, so this table's size is bounded by
    distinct projects viewed, never by view count (no reaper job
    needed, unlike sessions/`*_tokens`).
    """

    __tablename__ = "recent_projects"
    __table_args__ = (Index("ix_recent_projects_user_viewed", "user_id", "last_viewed_at"),)

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), primary_key=True
    )
    last_viewed_at: Mapped[datetime] = mapped_column(server_default=func.now())

    project: Mapped["Project"] = relationship(back_populates="recent_views")
