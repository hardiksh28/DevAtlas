"""Chunking stage — splits cleaned text into retrieval-sized pieces.

Why chunking matters (docs/architecture/ingestion-engine-v1.md Section 5
has the full explanation): a whole document is both too large to embed
as one meaningful vector (embedding models compress semantics into a
fixed-size vector — cram a 20-page guide into one and the vector
represents "the average of everything," useful for nothing specific)
and too large to feed an LLM as retrieved context. Chunks need to be
small enough to be topically coherent and large enough to keep the
surrounding context that makes a sentence meaningful — this module's
whole job is picking that boundary well: on heading/paragraph edges,
never mid-code-block, with enough overlap that an idea split across a
chunk boundary isn't lost to either side.

Two entry points, not three: `chunk_markdown_like` handles both
markdown files and website pages, because parsers/website.py converts
HTML into the same heading-prefixed, fenced-code-block plain text that
markdown already is — one heading-aware chunker serves both. PDFs get
`chunk_pdf_pages` instead, because PDF text extraction has no reliable
heading structure to key off of; page boundaries are the section unit
there.

Token counts everywhere are `len(text) // 4` — a documented, deliberate
approximation (English averages ~4 chars/token across common tokenizers)
rather than a real tokenizer dependency. Nothing downstream needs exact
counts yet (no embedding model is wired up in this pass — see
"Explicitly deferred" in the architecture doc); swap in the real
tokenizer for whatever embedding model is chosen when that ships,
behind this same function signature.
"""

import re
from dataclasses import dataclass, field

_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")
_FENCE_RE = re.compile(r"^```")

_CHARS_PER_TOKEN = 4


def approx_token_count(text: str) -> int:
    return max(1, len(text) // _CHARS_PER_TOKEN)


@dataclass
class ChunkDraft:
    content: str
    heading_path: list[str]
    token_count: int
    char_count: int
    chunk_metadata: dict = field(default_factory=dict)


@dataclass
class _Block:
    kind: str  # "heading" | "paragraph" | "code"
    text: str
    level: int | None = None


def _split_into_blocks(text: str) -> list[_Block]:
    blocks: list[_Block] = []
    paragraph_lines: list[str] = []
    code_lines: list[str] = []
    in_code = False

    def flush_paragraph() -> None:
        if paragraph_lines:
            joined = "\n".join(paragraph_lines).strip()
            if joined:
                blocks.append(_Block(kind="paragraph", text=joined))
            paragraph_lines.clear()

    for line in text.split("\n"):
        if _FENCE_RE.match(line.strip()):
            if in_code:
                code_lines.append(line)
                blocks.append(_Block(kind="code", text="\n".join(code_lines)))
                code_lines.clear()
                in_code = False
            else:
                flush_paragraph()
                in_code = True
                code_lines.append(line)
            continue

        if in_code:
            code_lines.append(line)
            continue

        heading_match = _HEADING_RE.match(line)
        if heading_match:
            flush_paragraph()
            blocks.append(_Block(kind="heading", text=heading_match.group(2).strip(), level=len(heading_match.group(1))))
            continue

        if line.strip() == "":
            flush_paragraph()
        else:
            paragraph_lines.append(line)

    flush_paragraph()
    if code_lines:  # unterminated fence — still emit what we have
        blocks.append(_Block(kind="code", text="\n".join(code_lines)))

    return blocks


def _split_oversized_code_block(text: str, target_tokens: int) -> list[str]:
    """A single fenced code block bigger than the target chunk size is
    split on line boundaries (never mid-line). `text` includes its own
    ```-fence lines (see _split_into_blocks) — those are stripped
    before splitting and NOT included in the returned pieces, since the
    caller wraps each piece in its own fresh pair of fences; keeping
    the original fences here would double them up."""
    lines = text.split("\n")
    if lines and lines[0].strip().startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].strip().startswith("```"):
        lines = lines[:-1]

    pieces: list[str] = []
    current: list[str] = []
    current_tokens = 0
    for line in lines:
        line_tokens = approx_token_count(line)
        if current and current_tokens + line_tokens > target_tokens:
            pieces.append("\n".join(current))
            current = []
            current_tokens = 0
        current.append(line)
        current_tokens += line_tokens
    if current:
        pieces.append("\n".join(current))
    return pieces


def _split_oversized_paragraph(text: str, target_tokens: int) -> list[str]:
    """A single paragraph bigger than the target chunk size — a long,
    unbroken block of prose with no internal line breaks to split on
    (unlike code, which is split by line above) — is split on word
    boundaries instead."""
    words = text.split(" ")
    pieces: list[str] = []
    current: list[str] = []
    current_tokens = 0
    for word in words:
        word_tokens = approx_token_count(word) + 1  # +1 approximates the joining space
        if current and current_tokens + word_tokens > target_tokens:
            pieces.append(" ".join(current))
            current = []
            current_tokens = 0
        current.append(word)
        current_tokens += word_tokens
    if current:
        pieces.append(" ".join(current))
    return pieces


def chunk_markdown_like(
    text: str, *, target_tokens: int = 800, overlap_tokens: int = 100
) -> list[ChunkDraft]:
    blocks = _split_into_blocks(text)
    chunks: list[ChunkDraft] = []
    heading_stack: list[tuple[int, str]] = []
    current_parts: list[str] = []
    current_tokens = 0
    current_has_code = False
    chunk_start_heading_path: list[str] = []

    def flush_chunk(overlap_text: str = "") -> str:
        nonlocal current_parts, current_tokens, current_has_code
        if not current_parts:
            return ""
        content = "\n\n".join(current_parts).strip()
        if content:
            chunks.append(
                ChunkDraft(
                    content=content,
                    heading_path=list(chunk_start_heading_path),
                    token_count=approx_token_count(content),
                    char_count=len(content),
                    chunk_metadata={"is_code_heavy": current_has_code},
                )
            )
        tail = content[-overlap_tokens * _CHARS_PER_TOKEN :] if overlap_tokens > 0 else ""
        current_parts = [tail] if tail else []
        current_tokens = approx_token_count(tail) if tail else 0
        current_has_code = False
        return tail

    for block in blocks:
        if block.kind == "heading":
            assert block.level is not None
            while heading_stack and heading_stack[-1][0] >= block.level:
                heading_stack.pop()
            heading_stack.append((block.level, block.text))

            # Force a boundary at every heading (not just major
            # sections) so a chunk's recorded heading_path is never
            # wrong — without this, a small paragraph sitting right
            # before a subheading could stay unflushed until the
            # subheading's own content joins it, and the whole merged
            # chunk would then be mislabeled with the *later* heading's
            # path. Only flushes if there's already real content
            # buffered, so short leading sections don't each become
            # their own near-empty chunk.
            if current_tokens > 0:
                flush_chunk()
            chunk_start_heading_path = [title for _, title in heading_stack]
            continue

        block_text = block.text
        block_tokens = approx_token_count(block_text)
        is_code = block.kind == "code"

        if block_tokens > target_tokens:
            pieces = (
                _split_oversized_code_block(block_text, target_tokens)
                if is_code
                else _split_oversized_paragraph(block_text, target_tokens)
            )
            for piece in pieces:
                if current_tokens > 0:
                    flush_chunk()
                current_parts = [f"```\n{piece}\n```"] if is_code else [piece]
                current_tokens = approx_token_count(piece)
                current_has_code = is_code
                flush_chunk()
            continue

        if current_tokens > 0 and current_tokens + block_tokens > target_tokens:
            flush_chunk()

        if not current_parts:
            chunk_start_heading_path = [title for _, title in heading_stack]

        current_parts.append(block_text)
        current_tokens += block_tokens
        current_has_code = current_has_code or is_code

    flush_chunk()

    for index, chunk in enumerate(chunks):
        chunk.chunk_metadata["chunk_position"] = index

    return chunks


def chunk_pdf_pages(
    pages: list[str], *, target_tokens: int = 800, overlap_tokens: int = 100
) -> list[ChunkDraft]:
    """PDF text extraction has no reliable heading structure — the page
    is the section unit instead. Each page is packed into one or more
    chunks independently (a short page becomes one small chunk rather
    than being merged with its neighbor; simple, and good enough until
    page-merging is a demonstrated need)."""
    chunks: list[ChunkDraft] = []
    for page_number, page_text in enumerate(pages, start=1):
        paragraphs = [p.strip() for p in page_text.split("\n\n") if p.strip()]
        current_parts: list[str] = []
        current_tokens = 0

        def flush(parts: list[str], page_num: int = page_number) -> None:
            if not parts:
                return
            content = "\n\n".join(parts).strip()
            if content:
                chunks.append(
                    ChunkDraft(
                        content=content,
                        heading_path=[],
                        token_count=approx_token_count(content),
                        char_count=len(content),
                        chunk_metadata={"page_number": page_num},
                    )
                )

        for paragraph in paragraphs:
            paragraph_tokens = approx_token_count(paragraph)

            if paragraph_tokens > target_tokens:
                for piece in _split_oversized_paragraph(paragraph, target_tokens):
                    if current_tokens > 0:
                        flush(current_parts)
                    current_parts = [piece]
                    current_tokens = approx_token_count(piece)
                    flush(current_parts)
                current_parts = []
                current_tokens = 0
                continue

            if current_tokens > 0 and current_tokens + paragraph_tokens > target_tokens:
                flush(current_parts)
                tail = current_parts[-1][-overlap_tokens * _CHARS_PER_TOKEN :] if overlap_tokens > 0 else ""
                current_parts = [tail] if tail else []
                current_tokens = approx_token_count(tail) if tail else 0
            current_parts.append(paragraph)
            current_tokens += paragraph_tokens

        flush(current_parts)

    for index, chunk in enumerate(chunks):
        chunk.chunk_metadata["chunk_position"] = index

    return chunks
