"""Repository Ingestion Engine — models.

One `RepositoryConnection` row per project, filling in the
`repository_connections` FK slot `projects/models.py`'s `Project`
docstring reserved. 1:1 with `Project` (same shape as `ProjectSettings`)
— a project has one connected codebase in V1; re-ingesting replaces the
row in place rather than accumulating history, since nothing yet reads
"what did this look like last time."

Deliberately scoped to structural metadata only (language, framework,
package manager, file/folder counts) — no file content, no parsing of
individual source files beyond the handful of manifests this pass reads.
See docs/architecture/ingestion-engine-v1.md for the separate
Documentation Ingestion Engine, which this module does not replace or
depend on: that one chunks docs for RAG; this one profiles a codebase's
shape for the modules that need to know what stack a project is in
(Stack Support Tier Manager, Code Review Engine) before any of them
exist yet to consume it.
"""

import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from sqlalchemy.types import JSON

from app.core.database import Base

# JSONB on Postgres, plain JSON elsewhere — same reasoning as every
# other module's catch-all metadata column (see knowledge/models.py).
_JSONB_OR_JSON = JSON().with_variant(JSONB(), "postgresql")


class RepositoryConnection(Base):
    """The result of the last successful ingestion for a project's
    connected GitHub repository. `project_id` is unique, not a plain FK
    index — see the module docstring for why this is 1:1, not
    one-to-many, in V1."""

    __tablename__ = "repository_connections"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), unique=True
    )

    repo_url: Mapped[str] = mapped_column(String(2048))
    owner: Mapped[str] = mapped_column(String(255))
    name: Mapped[str] = mapped_column(String(255))
    default_branch: Mapped[str] = mapped_column(String(255))

    primary_language: Mapped[str | None] = mapped_column(String(100), default=None)
    framework: Mapped[str | None] = mapped_column(String(100), default=None)
    package_manager: Mapped[str | None] = mapped_column(String(20), default=None)

    total_files: Mapped[int] = mapped_column(Integer, server_default="0")
    total_folders: Mapped[int] = mapped_column(Integer, server_default="0")

    # Catch-all for anything worth keeping that doesn't earn its own
    # column yet: which manifest files were found, the raw dependency
    # list read from package.json. Promote a key to a real column only
    # once something needs to filter/index on it (ProjectSettings'
    # same rule).
    repo_metadata: Mapped[dict] = mapped_column(_JSONB_OR_JSON, server_default="{}")

    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now())
