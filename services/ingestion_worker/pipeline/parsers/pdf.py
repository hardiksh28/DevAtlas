"""PDF parsing — per-page text extraction via pypdf.

Page-level granularity (not whole-document) is deliberate: it's what
lets chunking.chunk_pdf_pages attach a real `page_number` to every
chunk, and what lets cleaning.strip_repeated_boilerplate detect running
headers/footers by comparing pages against each other.
"""

import io
import logging
from typing import Any

from pypdf import PdfReader
from pypdf.errors import PdfReadError

from pipeline.errors import PermanentIngestionError

logger = logging.getLogger(__name__)


def parse_pdf(
    raw_bytes: bytes, *, max_pages: int, max_extracted_chars: int
) -> tuple[list[str], dict[str, Any]]:
    """Returns (pages_text, doc_metadata). Raises pypdf.errors.PdfReadError
    on a corrupt file — worker.py catches this and records it as a
    PermanentIngestionError, since a malformed PDF will never parse no
    matter how many times it's retried.

    `max_pages`/`max_extracted_chars` bound a "PDF bomb" — only the
    *compressed* upload size is checked before this point
    (INGESTION_MAX_UPLOAD_BYTES); a small file can still decompress into
    an enormous page count or amount of text, and this is the one place
    that actually does the (potentially expensive) extraction, so it's
    the right place to cap it rather than the caller. Raises
    PermanentIngestionError past either ceiling — retrying changes
    nothing about a document's own page count or text volume.
    """
    reader = PdfReader(io.BytesIO(raw_bytes))

    if len(reader.pages) > max_pages:
        raise PermanentIngestionError(
            f"PDF has {len(reader.pages)} pages, exceeding the {max_pages}-page limit.",
            error_code="pdf_too_many_pages",
        )

    if reader.is_encrypted:
        # Some "encrypted" PDFs are only permission-restricted with no
        # real password — an empty-password decrypt handles those; a
        # genuinely password-protected file still fails to parse below,
        # which is correct (there's no password to try it with).
        try:
            reader.decrypt("")
        except Exception:
            logger.debug("PDF empty-password decrypt failed; continuing with encrypted reader")

    pages: list[str] = []
    extracted_chars = 0
    for page in reader.pages:
        text = page.extract_text() or ""
        extracted_chars += len(text)
        if extracted_chars > max_extracted_chars:
            raise PermanentIngestionError(
                f"PDF's extracted text exceeded the {max_extracted_chars}-character limit.",
                error_code="pdf_extracted_text_too_large",
            )
        pages.append(text)

    doc_metadata: dict[str, Any] = {"page_count": len(reader.pages)}
    info = reader.metadata
    if info is not None and info.title:
        doc_metadata["pdf_title"] = str(info.title)

    return pages, doc_metadata


__all__ = ["PdfReadError", "parse_pdf"]
