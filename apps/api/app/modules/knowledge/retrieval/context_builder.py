"""Context Builder — assembles retrieved chunks into a single,
token-budgeted context block for the prompt, with a numbered citation
per chunk.

docs/architecture/rag-engine-v1.md Section 6 ("Token Optimization")
covers why `max_tokens` here is deliberately well under the model's real
context window rather than equal to it, and why chunks are included or
excluded *whole* — never truncated mid-chunk, which would hand the model
a half-sentence and no way to tell it was cut off.
"""

from dataclasses import dataclass
from typing import Any

from app.modules.knowledge.retrieval.retrieval_service import RetrievedChunk

# Same `chars // 4` heuristic as services/ingestion_worker/pipeline/chunking.py's
# approx_token_count — duplicated, not imported, because apps/api and the
# ingestion worker are separate deployable services with no dependency
# edge between them (see that module's docstring for the ingestion side
# of this same reasoning). Kept identical on purpose: a chunk's
# token_count as stored at ingestion time and its token_count as
# measured here at retrieval time should agree.
_CHARS_PER_TOKEN = 4


def _approx_token_count(text: str) -> int:
    return max(1, len(text) // _CHARS_PER_TOKEN)


@dataclass
class ContextSource:
    """One chunk as it appears in the assembled context — the citation
    index is what lets the prompt say "[2]" and the API response show
    the caller exactly which chunk that citation points to."""

    index: int
    chunk_id: Any
    document_id: Any
    title: str | None
    source_type: str
    source_path: str
    heading_path: list[str]
    score: float


@dataclass
class BuiltContext:
    text: str
    sources: list[ContextSource]
    total_tokens: int
    # True when one or more retrieved chunks were left out to stay
    # within max_tokens — surfaced to the API caller rather than
    # silently dropped, since it changes how much to trust "the answer
    # didn't mention X."
    truncated: bool


def _format_chunk(index: int, chunk: RetrievedChunk) -> str:
    label = chunk.title or chunk.source_path
    breadcrumb = " > ".join(chunk.heading_path) if chunk.heading_path else None
    header = f"[{index}] {label}"
    if breadcrumb:
        header += f" — {breadcrumb}"
    page_number = chunk.chunk_metadata.get("page_number")
    if page_number is not None:
        header += f" (page {page_number})"
    return f"{header}\n{chunk.content}"


def build_context(chunks: list[RetrievedChunk], *, max_tokens: int) -> BuiltContext:
    """Chunks are assumed already ranked best-first (hybrid_search's
    output) — this function only decides *how many* fit the budget, not
    their order. A chunk is included whole or not at all; the first
    chunk that would exceed the budget stops inclusion entirely
    (chunks after it are lower-ranked anyway, so there's no value in
    skipping one and trying the next)."""
    blocks: list[str] = []
    sources: list[ContextSource] = []
    total_tokens = 0
    truncated = False

    for i, chunk in enumerate(chunks, start=1):
        block = _format_chunk(i, chunk)
        block_tokens = _approx_token_count(block)
        # `blocks and ...` — the top-ranked chunk is always included
        # even if it alone exceeds max_tokens (a badly-undersized budget
        # shouldn't produce a completely empty context); every chunk
        # after the first is genuinely optional.
        if blocks and total_tokens + block_tokens > max_tokens:
            truncated = True
            break

        blocks.append(block)
        total_tokens += block_tokens
        sources.append(
            ContextSource(
                index=i,
                chunk_id=chunk.chunk_id,
                document_id=chunk.document_id,
                title=chunk.title,
                source_type=chunk.source_type,
                source_path=chunk.source_path,
                heading_path=chunk.heading_path,
                score=chunk.score,
            )
        )

    return BuiltContext(
        text="\n\n".join(blocks),
        sources=sources,
        total_tokens=total_tokens,
        truncated=truncated,
    )
