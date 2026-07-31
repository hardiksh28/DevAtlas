"""Tests for app.modules.taxonomy.service — YAML parsing/validation
(pure) and DB reads/sync (integration, against db_session)."""

from pathlib import Path

import pytest

from app.modules.taxonomy.exceptions import StackNotFoundError, TaxonomyValidationError
from app.modules.taxonomy.service import (
    get_concepts_for_stack,
    get_prerequisite_edges,
    list_stacks,
    load_concepts_from_yaml,
    sync_concepts_for_stack,
)

_TAXONOMY_DATA_DIR = Path(__file__).resolve().parents[3] / "packages" / "taxonomy-data" / "concepts"


def _write_yaml(tmp_path: Path, content: str) -> Path:
    path = tmp_path / "test-stack.yaml"
    path.write_text(content)
    return path


class TestLoadConceptsFromYaml:
    def test_loads_the_real_curated_python_basics_file(self):
        parsed = load_concepts_from_yaml(_TAXONOMY_DATA_DIR / "example-python-basics.yaml")
        assert parsed.stack == "python"
        ids = {c.id for c in parsed.concepts}
        assert "python.variables_and_types" in ids
        assert "python.async_await" in ids

    def test_dangling_prerequisite_reference_raises(self, tmp_path):
        path = _write_yaml(
            tmp_path,
            """
stack: test
stack_version: "1"
concepts:
  - id: test.a
    severity: foundational
    prerequisites: [test.does_not_exist]
""",
        )
        with pytest.raises(TaxonomyValidationError):
            load_concepts_from_yaml(path)

    def test_cycle_raises(self, tmp_path):
        path = _write_yaml(
            tmp_path,
            """
stack: test
stack_version: "1"
concepts:
  - id: test.a
    severity: foundational
    prerequisites: [test.b]
  - id: test.b
    severity: foundational
    prerequisites: [test.a]
""",
        )
        with pytest.raises(TaxonomyValidationError):
            load_concepts_from_yaml(path)

    def test_unknown_severity_raises(self, tmp_path):
        path = _write_yaml(
            tmp_path,
            """
stack: test
stack_version: "1"
concepts:
  - id: test.a
    severity: nonsense
    prerequisites: []
""",
        )
        with pytest.raises(TaxonomyValidationError):
            load_concepts_from_yaml(path)


class TestSyncAndReads:
    async def test_sync_then_read_round_trips(self, db_session, tmp_path):
        path = _write_yaml(
            tmp_path,
            """
stack: test
stack_version: "1"
concepts:
  - id: test.a
    severity: foundational
    prerequisites: []
    mastery_criteria: ["knows a"]
  - id: test.b
    severity: intermediate
    prerequisites: [test.a]
""",
        )
        parsed = load_concepts_from_yaml(path)
        await sync_concepts_for_stack(db_session, parsed)

        concepts = await get_concepts_for_stack(db_session, "test", "1")
        assert {c.id for c in concepts} == {"test.a", "test.b"}

        edges = await get_prerequisite_edges(db_session, ["test.a", "test.b"])
        assert edges["test.b"] == ["test.a"]
        assert edges["test.a"] == []

    async def test_sync_is_idempotent(self, db_session, tmp_path):
        path = _write_yaml(
            tmp_path,
            """
stack: test
stack_version: "1"
concepts:
  - id: test.a
    severity: foundational
    prerequisites: []
""",
        )
        parsed = load_concepts_from_yaml(path)
        await sync_concepts_for_stack(db_session, parsed)
        await sync_concepts_for_stack(db_session, parsed)  # re-run, should converge not duplicate

        concepts = await get_concepts_for_stack(db_session, "test", "1")
        assert len(concepts) == 1

    async def test_unknown_stack_raises_not_found(self, db_session):
        with pytest.raises(StackNotFoundError):
            await get_concepts_for_stack(db_session, "nonexistent", "1")

    async def test_list_stacks_reflects_synced_content(self, db_session, tmp_path):
        path = _write_yaml(
            tmp_path,
            """
stack: test
stack_version: "1"
concepts:
  - id: test.a
    severity: foundational
    prerequisites: []
  - id: test.b
    severity: intermediate
    prerequisites: []
""",
        )
        await sync_concepts_for_stack(db_session, load_concepts_from_yaml(path))

        stacks = await list_stacks(db_session)

        assert ("test", "1", 2) in stacks
