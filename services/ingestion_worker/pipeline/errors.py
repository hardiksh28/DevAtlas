"""Error taxonomy for the ingestion pipeline (Validation → Parsing →
Cleaning → Chunking → Metadata Extraction). worker.py's job functions
branch on these two base classes to decide retry-vs-fail handling — see
docs/architecture/ingestion-engine-v1.md Section 6 (Error Handling).
"""


class IngestionError(Exception):
    def __init__(self, message: str, *, error_code: str) -> None:
        super().__init__(message)
        self.message = message
        self.error_code = error_code


class RetryableIngestionError(IngestionError):
    """Transient failure (network timeout, 5xx, connection reset). Left
    to propagate uncaught out of a job function so arq's own max_tries/
    backoff takes over — never caught-and-recorded as a final failure."""


class PermanentIngestionError(IngestionError):
    """Will never succeed no matter how many times it's retried (404,
    invalid URL, unsupported file, a hard size/count limit exceeded).
    Always caught by the job function itself and recorded as a failed
    status — never re-raised, so arq doesn't waste a retry on it."""
