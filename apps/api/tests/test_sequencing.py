"""Unit tests for app.modules.curriculum.sequencing — pure, DB-free.

Mirrors the RAG engine's `reciprocal_rank_fusion` test style: every
input is a plain dataclass constructed in the test itself, no database
or LLM involved anywhere in this file.
"""

import pytest

from app.modules.curriculum.sequencing import (
    ConceptNode,
    CycleDetectedError,
    ExistingMilestone,
    diff_milestones,
    select_concepts_for_level,
    topological_order,
)


def _node(cid: str, severity: str) -> ConceptNode:
    return ConceptNode(id=cid, severity=severity)


class TestTopologicalOrder:
    def test_orders_prerequisites_before_dependents(self):
        concepts = [_node("b", "foundational"), _node("a", "foundational")]
        edges = {"b": ["a"]}  # b requires a

        order = topological_order(concepts, edges)

        assert order.index("a") < order.index("b")

    def test_ties_broken_by_severity_then_id(self):
        # No edges at all — everything is "available" simultaneously;
        # tie-break must be deterministic (severity rank, then id).
        concepts = [_node("z", "advanced"), _node("a", "foundational"), _node("m", "intermediate")]

        order = topological_order(concepts, {})

        assert order == ["a", "m", "z"]

    def test_same_input_always_produces_same_output(self):
        concepts = [_node("c", "advanced"), _node("a", "foundational"), _node("b", "intermediate")]
        edges = {"c": ["b"], "b": ["a"]}

        first = topological_order(concepts, edges)
        second = topological_order(list(reversed(concepts)), edges)

        assert first == second == ["a", "b", "c"]

    def test_cycle_raises(self):
        concepts = [_node("a", "foundational"), _node("b", "foundational")]
        edges = {"a": ["b"], "b": ["a"]}

        with pytest.raises(CycleDetectedError):
            topological_order(concepts, edges)

    def test_unknown_prerequisite_ids_are_ignored(self):
        # An edge referencing a concept outside this stack's set (e.g. a
        # cross-stack reference) doesn't block ordering — it's just not
        # a constraint sequencing can see.
        concepts = [_node("a", "foundational")]
        edges = {"a": ["not_in_this_stack"]}

        assert topological_order(concepts, edges) == ["a"]


class TestSelectConceptsForLevel:
    def _setup(self):
        # Two independent branches off a shared foundational concept:
        # foo.intermediate_thing (skippable for advanced — nothing
        # advanced depends on it) and foo.advanced_thing (depends
        # directly on foo.basics, not on foo.intermediate_thing) — this
        # is what makes "advanced skips foo.intermediate_thing but still
        # pulls in foo.basics" an actual test of the prerequisite safety
        # net, rather than everything being required transitively anyway.
        concepts = {
            "foo.basics": _node("foo.basics", "foundational"),
            "foo.intermediate_thing": _node("foo.intermediate_thing", "intermediate"),
            "foo.advanced_thing": _node("foo.advanced_thing", "advanced"),
        }
        edges = {
            "foo.intermediate_thing": ["foo.basics"],
            "foo.advanced_thing": ["foo.basics"],
        }
        ordered = ["foo.basics", "foo.intermediate_thing", "foo.advanced_thing"]
        return ordered, concepts, edges

    def test_beginner_gets_everything_at_or_above_foundational(self):
        ordered, concepts, edges = self._setup()
        selected = select_concepts_for_level(ordered, concepts, edges, "beginner")
        assert selected == ordered

    def test_advanced_skips_foundational_unless_required(self):
        ordered, concepts, edges = self._setup()
        selected = select_concepts_for_level(ordered, concepts, edges, "advanced")
        # foo.basics is a transitive prerequisite of foo.advanced_thing,
        # so it must still be included even though it's below the
        # "advanced" floor — the prerequisite safety net. foo.intermediate_thing
        # is genuinely skippable: nothing selected requires it.
        assert selected == ["foo.basics", "foo.advanced_thing"]

    def test_intermediate_includes_intermediate_and_its_prerequisites(self):
        ordered, concepts, edges = self._setup()
        selected = select_concepts_for_level(ordered, concepts, edges, "intermediate")
        assert selected == ordered  # both branches qualify at the intermediate floor

    def test_relative_order_preserved(self):
        ordered = ["a", "b", "c"]
        concepts = {cid: _node(cid, "advanced") for cid in ordered}
        selected = select_concepts_for_level(ordered, concepts, {}, "advanced")
        assert selected == ["a", "b", "c"]


class TestDiffMilestones:
    def test_fresh_roadmap_creates_all_new(self):
        plan = diff_milestones([], ["a", "b"])
        assert [e.concept_id for e in plan.entries] == ["a", "b"]
        assert all(e.existing_id is None for e in plan.entries)
        assert plan.dropped_ids == []

    def test_completed_milestone_is_preserved_and_not_dropped(self):
        existing = [ExistingMilestone(id="m1", concept_id="a", status="completed")]
        # Regenerating without "a" in the new selection (e.g. stack
        # changed) must still keep the completed milestone.
        plan = diff_milestones(existing, ["b"])

        concept_ids = [e.concept_id for e in plan.entries]
        assert "a" in concept_ids
        assert "b" in concept_ids
        assert plan.dropped_ids == []

    def test_never_started_milestone_dropped_if_no_longer_selected(self):
        existing = [ExistingMilestone(id="m1", concept_id="a", status="available")]
        plan = diff_milestones(existing, ["b"])

        assert [e.concept_id for e in plan.entries] == ["b"]
        assert plan.dropped_ids == ["m1"]

    def test_in_progress_milestone_kept_and_reused(self):
        existing = [ExistingMilestone(id="m1", concept_id="a", status="in_progress")]
        plan = diff_milestones(existing, ["a", "b"])

        entry_a = next(e for e in plan.entries if e.concept_id == "a")
        assert entry_a.existing_id == "m1"
        assert plan.dropped_ids == []

    def test_new_concept_inserted_without_disturbing_existing_ids(self):
        existing = [
            ExistingMilestone(id="m1", concept_id="a", status="completed"),
            ExistingMilestone(id="m2", concept_id="b", status="available"),
        ]
        # "c" is newly selected, inserted between a and b per the new
        # topological order.
        plan = diff_milestones(existing, ["a", "c", "b"])

        by_concept = {e.concept_id: e.existing_id for e in plan.entries}
        assert by_concept["a"] == "m1"
        assert by_concept["b"] == "m2"
        assert by_concept["c"] is None
        assert plan.dropped_ids == []
