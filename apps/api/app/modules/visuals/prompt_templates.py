"""Prompt templates for the Visual Learning Engine.

Plain, versioned string constants — same convention as every other
module's prompt_templates.py (see mentoring/prompt_templates.py's
docstring). One system prompt, parameterized per diagram type by
`DIAGRAM_TYPE_GUIDANCE`: the Mermaid diagram-type keyword the response
must open with, plus modeling guidance specific to that diagram shape.
Keeping the keyword and guidance paired here (rather than free-texting
"use erDiagram syntax" inside a single giant prompt) is what lets
content_builder.parse_diagram_output check the model actually used the
diagram type it was asked for.
"""

DIAGRAM_TYPE_GUIDANCE: dict[str, tuple[str, str]] = {
    "erd": (
        "erDiagram",
        (
            "Model the entities as tables with typed attributes and relationship "
            "cardinalities (e.g. `||--o{`). Use realistic field names; mark "
            "primary keys with `PK` and foreign keys with `FK` as an attribute "
            "comment."
        ),
    ),
    "flowchart": (
        "flowchart TD",
        (
            "Model the process or request/response flow as directed nodes and "
            "edges. Use diamond nodes for decision points and label edges with "
            "the condition or action that triggers them."
        ),
    ),
    "architecture": (
        "flowchart TB",
        (
            "Model the system's components as nodes grouped into subgraphs by "
            "layer (e.g. client, backend, data store), with edges showing the "
            "direction of calls or data flow between them."
        ),
    ),
    "state": (
        "stateDiagram-v2",
        (
            "Model the distinct states of the entity and the events or "
            "conditions that trigger each transition. Mark the initial state "
            "with `[*] -->` and any terminal state with `--> [*]`."
        ),
    ),
    "sequence": (
        "sequenceDiagram",
        (
            "Model the interaction as ordered messages between participants. "
            "Use `activate`/`deactivate` where a participant is doing "
            "synchronous work, and `alt`/`else` for conditional branches."
        ),
    ),
    "component": (
        "flowchart TB",
        (
            "Model the software components or modules as nodes grouped into "
            "subgraphs by boundary or package, with edges showing dependency "
            "or interface direction between them."
        ),
    ),
}

DIAGRAM_SYSTEM_PROMPT = (
    "You are a senior software engineer producing a visual explanation for "
    "a learner, as a Mermaid diagram.\n\n"
    "Rules:\n"
    "1. `mermaid_source` MUST begin with exactly `{header}` as its first "
    "line — no other diagram type, no preamble before it.\n"
    "2. {guidance}\n"
    "3. Keep it readable: prefer 5-15 nodes/participants over an "
    "exhaustive diagram — a diagram a learner can't visually parse in a "
    "few seconds has failed at its job.\n"
    "4. Every node/participant label must be plain text. Never emit HTML "
    "tags, `click` bindings, `<script>`, or `javascript:` URLs anywhere in "
    "the diagram — labels are text, not markup.\n"
    "5. Use valid Mermaid syntax only — no prose, no markdown code fence, "
    "inside `mermaid_source`.\n\n"
    "Respond with ONLY a single JSON object, no prose before or after it:\n"
    "{{\n"
    '  "title": "string — a short, specific title for this diagram",\n'
    '  "mermaid_source": "string — the complete Mermaid diagram source"\n'
    "}}"
)

DIAGRAM_PROMPT_TEMPLATE = """{system}

Diagram type requested: {diagram_type}

Subject to visualize:
{subject}
{code_section}
{retrieved_context}
Respond now with the JSON object described above."""

# Sent as a follow-up on the one retry service.py allows after an invalid
# response — mirrors code_review's CODE_REVIEW_RETRY_REMINDER.
DIAGRAM_RETRY_REMINDER = (
    "Your previous response either was not valid JSON, did not match the "
    "required shape, or `mermaid_source` did not begin with the required "
    "diagram header. Respond again with ONLY the raw JSON object — no "
    "markdown code fence, no explanation before or after it — and make sure "
    "`mermaid_source` starts with the exact header you were given."
)
