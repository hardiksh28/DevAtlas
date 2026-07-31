"""Shared shapes for the Documentation Ingestion Engine
(docs/architecture/ingestion-engine-v1.md) — the one place apps/api and
services/ingestion_worker agree on the closed sets of valid source-type
and status strings. Both sides store these as plain TEXT + CHECK
constraint columns (database-schema-v1.md's "why TEXT not native ENUM"
convention) — these enums exist so the *Python-side* values can't drift
out of sync with each other, not to change how they're stored.
"""

from enum import StrEnum


class SourceType(StrEnum):
    MARKDOWN_FILE = "markdown_file"
    PDF_FILE = "pdf_file"
    GITHUB_REPO = "github_repo"
    WEBSITE = "website"


class IngestionJobStatus(StrEnum):
    """Lifecycle of one user-submitted ingestion request. `DISCOVERING`
    only applies to github_repo/website (enumerating files/pages before
    any document exists to process); upload jobs skip straight from
    QUEUED to PROCESSING since the API already knows the one document.
    """

    QUEUED = "queued"
    DISCOVERING = "discovering"
    PROCESSING = "processing"
    COMPLETED = "completed"
    COMPLETED_WITH_ERRORS = "completed_with_errors"
    FAILED = "failed"


class DocumentStatus(StrEnum):
    """Lifecycle of one document through Validation → Parsing → Cleaning
    → Chunking → Metadata Extraction → Embedding Queue (see the
    architecture doc's pipeline diagram) → Database Storage."""

    PENDING = "pending"
    VALIDATING = "validating"
    PARSING = "parsing"
    CLEANING = "cleaning"
    CHUNKING = "chunking"
    EXTRACTING_METADATA = "extracting_metadata"
    QUEUED_FOR_EMBEDDING = "queued_for_embedding"
    COMPLETED = "completed"
    FAILED = "failed"


class ChunkEmbeddingStatus(StrEnum):
    """Deliberately separate from DocumentStatus — a document can finish
    the whole ingestion pipeline (COMPLETED, or QUEUED_FOR_EMBEDDING)
    while its chunks' embeddings are still PENDING; embedding generation
    is explicitly out of scope for this pass (see ingestion-engine-v1.md
    "Explicitly deferred") and is tracked per-chunk so a future embedding
    worker can query "all PENDING chunks" directly without re-deriving
    that set from document status.
    """

    PENDING = "pending"
    QUEUED = "queued"
    COMPLETED = "completed"
    SKIPPED = "skipped"
    FAILED = "failed"
