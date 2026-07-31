"""Interactive Learning Workspace — models.

Two tables. Deliberately no `is_directory` row and no folder concept
anywhere in the schema — `path` is the only source of truth for
structure, the same way git/GitHub's own tree view works: a folder
exists exactly when a file lives under it, and disappears the moment
the last one is removed or renamed out. See
docs/architecture/interactive-workspace-v1.md.

`WorkspaceFile.content` lives directly in a Postgres `TEXT` column, not
the ObjectStorage/MinIO abstraction the Ingestion Engine uses for
uploaded documents — code files here are KB-sized and rewritten on
every autosave; round-tripping every keystroke through MinIO adds
latency and a second failure mode for no benefit at this size.
"""

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from sqlalchemy.types import JSON

from app.core.database import Base

_JSONB_OR_JSON = JSON().with_variant(JSONB(), "postgresql")


class WorkspaceFile(Base):
    __tablename__ = "workspace_files"
    __table_args__ = (
        UniqueConstraint("project_id", "path", name="uq_workspace_files_project_path"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))
    # POSIX-style relative path, e.g. "src/index.html" — validated in
    # schemas.py (no leading slash, no "." / ".." segments), matching
    # the `projects.name` precedent of keeping shape validation in
    # Pydantic rather than a DB CHECK.
    path: Mapped[str] = mapped_column(String(500))
    content: Mapped[str] = mapped_column(server_default="")
    # sha256 hex digest of `content`, recomputed server-side on every
    # write — the client only ever supplies it back as an optimistic-
    # concurrency precondition (see service.update_file_content), never
    # as a value to persist verbatim.
    content_hash: Mapped[str | None] = mapped_column(String(64), default=None)
    size_bytes: Mapped[int] = mapped_column(server_default="0")

    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now())


class WorkspaceLayout(Base):
    """1:1 with Project — same shape as `ProjectSettings`. Unlike that
    table, this one is created lazily on first read/write rather than
    transactionally alongside the project (mirrors mentoring's
    `get_or_create_conversation` idiom): most projects won't have their
    workspace opened the moment they're created, so there's no reason
    to write this row eagerly.
    """

    __tablename__ = "workspace_layouts"
    __table_args__ = (
        CheckConstraint(
            "right_rail_tab IN ('lesson', 'chat', 'diagrams')",
            name="ck_workspace_layouts_right_rail_tab",
        ),
        CheckConstraint(
            "bottom_panel_tab IN ('terminal', 'preview')",
            name="ck_workspace_layouts_bottom_panel_tab",
        ),
    )

    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), primary_key=True
    )
    # Ordered list of workspace_files.id, stored as strings (JSONB array
    # elements can't carry a real FK) — service.delete_file() prunes
    # this list explicitly whenever a referenced file is removed.
    open_tabs: Mapped[list] = mapped_column(_JSONB_OR_JSON, server_default="[]")
    # A real FK column (unlike open_tabs) so deleting the active file
    # auto-clears this via ON DELETE SET NULL, same pattern as
    # Message.milestone_id.
    active_tab_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("workspace_files.id", ondelete="SET NULL"), default=None
    )
    panel_sizes: Mapped[dict] = mapped_column(_JSONB_OR_JSON, server_default="{}")
    bottom_panel_visible: Mapped[bool] = mapped_column(server_default="false")
    right_rail_tab: Mapped[str] = mapped_column(String(20), server_default="lesson")
    bottom_panel_tab: Mapped[str] = mapped_column(String(20), server_default="terminal")
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now())
