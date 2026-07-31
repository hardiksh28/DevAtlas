"""Unit tests for app.modules.visuals.content_builder and prompt_builder —
pure, no DB/network involved."""

import json

import pytest

from app.modules.visuals.content_builder import DiagramParseError, parse_diagram_output
from app.modules.visuals.prompt_builder import build_diagram_prompt


def _payload(**overrides):
    payload = {
        "title": "JWT Auth Flow",
        "mermaid_source": "sequenceDiagram\n    Client->>Server: POST /login\n    Server-->>Client: JWT",
    }
    payload.update(overrides)
    return payload


class TestParseDiagramOutput:
    def test_parses_valid_json(self):
        parsed = parse_diagram_output(json.dumps(_payload()), diagram_type="sequence")
        assert parsed.title == "JWT Auth Flow"
        assert parsed.mermaid_source.startswith("sequenceDiagram")

    def test_strips_markdown_code_fence(self):
        fenced = f"```json\n{json.dumps(_payload())}\n```"
        parsed = parse_diagram_output(fenced, diagram_type="sequence")
        assert parsed.title == "JWT Auth Flow"

    def test_strips_nested_mermaid_fence_inside_source(self):
        payload = _payload(mermaid_source="```mermaid\nsequenceDiagram\n    A->>B: hi\n```")
        parsed = parse_diagram_output(json.dumps(payload), diagram_type="sequence")
        assert parsed.mermaid_source.startswith("sequenceDiagram")
        assert "```" not in parsed.mermaid_source

    def test_wrong_diagram_header_raises(self):
        payload = _payload(mermaid_source="erDiagram\n    USER ||--o{ ORDER : places")
        with pytest.raises(DiagramParseError):
            parse_diagram_output(json.dumps(payload), diagram_type="sequence")

    def test_strips_click_bindings(self):
        payload = _payload(
            mermaid_source=(
                "flowchart TD\n    A[Start] --> B[End]\n    click A call doSomething()"
            )
        )
        parsed = parse_diagram_output(json.dumps(payload), diagram_type="flowchart")
        assert "click" not in parsed.mermaid_source.lower()

    def test_rejects_script_tag(self):
        payload = _payload(
            mermaid_source="sequenceDiagram\n    Note over A: <script>alert(1)</script>"
        )
        with pytest.raises(DiagramParseError):
            parse_diagram_output(json.dumps(payload), diagram_type="sequence")

    def test_rejects_javascript_url(self):
        payload = _payload(
            mermaid_source='sequenceDiagram\n    Note over A: javascript:alert(1)'
        )
        with pytest.raises(DiagramParseError):
            parse_diagram_output(json.dumps(payload), diagram_type="sequence")

    def test_rejects_oversized_source(self):
        huge = "sequenceDiagram\n" + ("    A->>B: hi\n" * 1000)
        with pytest.raises(DiagramParseError):
            parse_diagram_output(json.dumps(_payload(mermaid_source=huge)), diagram_type="sequence")

    def test_invalid_json_raises(self):
        with pytest.raises(DiagramParseError):
            parse_diagram_output("not json at all", diagram_type="sequence")

    def test_missing_required_field_raises(self):
        with pytest.raises(DiagramParseError):
            parse_diagram_output(json.dumps({"title": "x"}), diagram_type="sequence")

    def test_erd_header_accepted_for_erd_type(self):
        payload = _payload(mermaid_source="erDiagram\n    USER ||--o{ ORDER : places")
        parsed = parse_diagram_output(json.dumps(payload), diagram_type="erd")
        assert parsed.mermaid_source.startswith("erDiagram")

    def test_flowchart_header_accepted_for_component_type(self):
        payload = _payload(mermaid_source="flowchart TB\n    subgraph API\n    end")
        parsed = parse_diagram_output(json.dumps(payload), diagram_type="component")
        assert parsed.mermaid_source.startswith("flowchart TB")


class TestBuildDiagramPrompt:
    def test_includes_subject_and_type(self):
        prompt = build_diagram_prompt(
            diagram_type="state", subject="Order lifecycle", code=None, retrieved_context=""
        )
        assert "state" in prompt
        assert "Order lifecycle" in prompt
        assert "stateDiagram-v2" in prompt

    def test_includes_code_and_context_when_present(self):
        prompt = build_diagram_prompt(
            diagram_type="architecture",
            subject="This service's layout",
            code="def f(): pass",
            retrieved_context="Uses a message queue.",
        )
        assert "def f(): pass" in prompt
        assert "Uses a message queue." in prompt
