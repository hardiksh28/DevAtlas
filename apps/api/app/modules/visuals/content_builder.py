"""Visual Learning Engine — LLM response parsing and security hardening.

Same defensive shape as code_review/content_builder.py (strip an
accidental code fence, parse JSON, validate against the Pydantic schema),
plus diagram-specific guards:

1. **Diagram-type grounding.** `mermaid_source` must actually open with the
   Mermaid keyword the prompt required (prompt_builder.diagram_header) —
   catches the model silently switching diagram types.
2. **Script/markup stripping.** Even though the frontend renders with
   Mermaid's default `strict` security level (HTML in labels is escaped,
   not executed — see MermaidDiagram.tsx), this is defense-in-depth for a
   value that started life as LLM output: `click` bindings are stripped
   outright (they can call an arbitrary page-defined JS function by name),
   and any literal `<script` or `javascript:` fails parsing so the one
   retry (service.py) gets a chance to produce something clean instead of
   silently shipping it.
3. **Size ceiling.** A diagram a learner can't visually parse has failed
   at its job (prompt_templates.py rule 3) — reject rather than truncate,
   since truncating Mermaid mid-statement produces invalid syntax anyway.
"""

import json
import re

from app.modules.visuals.prompt_builder import diagram_header
from app.modules.visuals.schemas import DiagramOutput

_CODE_FENCE_RE = re.compile(r"^```(?:json|mermaid)?\s*|\s*```$", re.MULTILINE)
_CLICK_LINE_RE = re.compile(r"^\s*click\s+\S+.*$", re.IGNORECASE | re.MULTILINE)
_UNSAFE_PATTERN_RE = re.compile(r"<script|javascript:", re.IGNORECASE)
_MAX_MERMAID_CHARS = 8000


class DiagramParseError(Exception):
    """Raised when the LLM's response isn't valid JSON, doesn't match
    DiagramOutput's shape, doesn't open with the required diagram header,
    or fails the security checks. Not a VisualError subclass — this module
    has no FastAPI/HTTP awareness; service.py decides whether to retry or
    translate this into DiagramGenerationError."""


def _strip_fence(text: str) -> str:
    return _CODE_FENCE_RE.sub("", text.strip()).strip()


def parse_diagram_output(raw: str, *, diagram_type: str) -> DiagramOutput:
    cleaned = _strip_fence(raw)
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise DiagramParseError(f"Response was not valid JSON: {exc}") from exc

    try:
        parsed = DiagramOutput.model_validate(data)
    except Exception as exc:  # pydantic.ValidationError, deliberately broad at the boundary
        raise DiagramParseError(f"Response JSON didn't match the expected shape: {exc}") from exc

    source = _strip_fence(parsed.mermaid_source)

    if _UNSAFE_PATTERN_RE.search(source):
        raise DiagramParseError("Response contained a disallowed script/markup pattern.")
    source = _CLICK_LINE_RE.sub("", source).strip()

    if len(source) > _MAX_MERMAID_CHARS:
        raise DiagramParseError(f"Diagram source exceeded {_MAX_MERMAID_CHARS} characters.")

    expected_header = diagram_header(diagram_type)
    first_line = next((line.strip() for line in source.splitlines() if line.strip()), "")
    if not first_line.lower().replace(" ", "").startswith(expected_header.lower().replace(" ", "")):
        raise DiagramParseError(
            f"mermaid_source did not start with the required '{expected_header}' header."
        )

    return DiagramOutput(title=parsed.title, mermaid_source=source)
