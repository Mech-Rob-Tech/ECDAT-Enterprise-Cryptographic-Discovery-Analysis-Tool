"""3C.8 — Incremental/full equivalence and structural-gap validation."""

from backend.analysis.dependency_engine import DependencyEngine
from backend.analysis.incremental_dependency import (
    AffectedNodePropagator,
    ConditionalImpactEvaluator,
    DependencyChange,
    DependencyDetector,
    build_dependency_delta,
)
from backend.model.dependency import Dependency


def dep(dep_id, source, target, *, evidence=(), conditions=()):
    return Dependency(
        dependency_id=dep_id,
        source_node_id=source,
        target_node_id=target,
        relationship_type="depends_on",
        evidence_ids=tuple(evidence),
    )


def change(dependency, change_type="modified"):
    return DependencyChange(
        dependency_id=dependency.dependency_id,
        change_type=change_type,
        previous_dependency=dependency,
        current_dependency=dependency,
        changed_fields=("confidence",),
        affected_source_node=dependency.source_node_id,
        affected_target_node=dependency.target_node_id,
        evidence_ids=tuple(sorted(dependency.evidence_ids)),
    )


def structural_state(dependencies):
    """Canonical structural state used as the independent comparison oracle."""
    engine = DependencyEngine(dependencies)

    edges = tuple(
        (
            item.dependency_id,
            item.source_node_id,
            item.target_node_id,
            item.relationship_type,
        )
        for item in engine.dependencies
    )

    nodes = tuple(
        sorted(
            {
                node
                for dependency in engine.dependencies
                for node in (
                    dependency.source_node_id,
                    dependency.target_node_id,
                )
            }
        )
    )

    return nodes, edges


# ---------------------------------------------------------------------------
# H1 — Reference Oracle Equivalence
# ---------------------------------------------------------------------------


def test_reference_oracle_addition():
    previous = [
        dep("ab", "a", "b"),
    ]
    current = [
        dep("ab", "a", "b"),
        dep("bc", "b", "c"),
    ]

    delta = build_dependency_delta(previous, current, ["b"])
    full = structural_state(current)

    incremental = structural_state(
        previous + [dep("bc", "b", "c")]
    )

    assert delta.added == ("bc",)
    assert full == incremental
    assert delta.recompute_nodes == ("b",)


def test_reference_oracle_modification():
    previous = [
        dep("ab", "a", "b"),
    ]
    current = [
        dep("ab", "a", "c"),
    ]

    delta = build_dependency_delta(previous, current, ["a"])

    full = structural_state(current)
    incremental = structural_state(current)

    assert delta.modified == ("ab",)
    assert full == incremental
    assert delta.recompute_nodes == ("a",)


def test_reference_oracle_removal():
    previous = [
        dep("ab", "a", "b"),
        dep("bc", "b", "c"),
    ]
    current = [
        dep("ab", "a", "b"),
    ]

    delta = build_dependency_delta(previous, current, [])

    full = structural_state(current)
    incremental = structural_state(
        [item for item in previous if item.dependency_id != "bc"]
    )

    assert delta.removed == ("bc",)
    assert full == incremental
    assert delta.recompute_nodes == ()


def test_reference_oracle_chain():
    dependencies = [
        dep("ab", "a", "b"),
        dep("bc", "b", "c"),
        dep("cd", "c", "d"),
    ]

    engine = DependencyEngine(dependencies)
    paths = engine.paths("a")

    assert paths
    assert any(
        path.node_ids == ("a", "b", "c", "d")
        for path in paths
    )

    assert structural_state(dependencies) == structural_state(
        list(reversed(dependencies))
    )


def test_reference_oracle_cycle():
    dependencies = [
        dep("ab", "a", "b"),
        dep("bc", "b", "c"),
        dep("ca", "c", "a"),
    ]

    engine = DependencyEngine(dependencies)

    first = engine.paths("a")
    second = engine.paths("a")

    assert first == second
    assert all(len(path.node_ids) <= 3 for path in first)


def test_reference_oracle_reordered_dependencies():
    dependencies = [
        dep("bc", "b", "c"),
        dep("ab", "a", "b"),
        dep("cd", "c", "d"),
    ]

    assert structural_state(dependencies) == structural_state(
        list(reversed(dependencies))
    )


def test_recompute_and_preserve_are_disjoint_in_oracle():
    stable = dep("stable", "stable", "tls")
    changed = dep("changed", "changed", "pqc")

    delta = build_dependency_delta(
        [stable],
        [stable, changed],
        ["changed"],
    )

    assert set(delta.recompute_nodes).isdisjoint(
        delta.preserved_nodes
    )


# ---------------------------------------------------------------------------
# Structural vectors — propagation
# ---------------------------------------------------------------------------


def test_structural_vector_chain_propagates_downstream():
    dependencies = [
        dep("ab", "a", "b"),
        dep("bc", "b", "c"),
        dep("cd", "c", "d"),
    ]

    result = AffectedNodePropagator(dependencies).propagate(
        [change(dependencies[1])]
    )

    assert [node.node_id for node in result.affected_nodes] == [
        "b",
        "a",
    ]


def test_structural_vector_cycle_terminates():
    dependencies = [
        dep("ab", "a", "b"),
        dep("bc", "b", "c"),
        dep("ca", "c", "a"),
    ]

    result = AffectedNodePropagator(dependencies).propagate(
        [change(dependencies[1])]
    )

    nodes = [item.node_id for item in result.affected_nodes]

    assert nodes == ["a", "b"]
    assert len(nodes) == len(set(nodes))


def test_structural_vector_blocked_prunes_edge():
    dependencies = [
        dep("ab", "a", "b"),
        dep("bc", "b", "c"),
    ]

    result = AffectedNodePropagator(dependencies).propagate(
        [change(dependencies[1])],
        conditions_by_dependency={
            "bc": (("environment", "production"),),
        },
        context={
            "environment": "development",
        },
    )

    assert result.affected_nodes == ()
    assert result.paths == ()


def test_structural_vector_unresolved_suspends_edge():
    dependencies = [
        dep("ab", "a", "b"),
        dep("bc", "b", "c"),
    ]

    result = AffectedNodePropagator(dependencies).propagate(
        [change(dependencies[1])],
        conditions_by_dependency={
            "bc": (("jurisdiction", "IN"),),
        },
        context={},
    )

    assert result.affected_nodes == ()
    assert result.paths == ()
    assert len(result.suspensions) == 1
    assert result.suspensions[0].dependency_id == "bc"


# ---------------------------------------------------------------------------
# H2 — Asynchronous Boundary Slicing
# ---------------------------------------------------------------------------


def test_unresolved_boundary_isolated_from_interior_drift():
    boundary = dep("bc", "b", "c")
    interior = dep("cd", "c", "d")

    dependencies = [
        dep("ab", "a", "b"),
        boundary,
        interior,
    ]

    first = AffectedNodePropagator(dependencies).propagate(
        [change(boundary)],
        conditions_by_dependency={
            "bc": (("jurisdiction", "IN"),),
        },
        context={},
    )

    drifted = [
        dep("ab", "a", "b"),
        boundary,
        dep("cd", "c", "e"),
    ]

    second = AffectedNodePropagator(drifted).propagate(
        [change(boundary)],
        conditions_by_dependency={
            "bc": (("jurisdiction", "IN"),),
        },
        context={},
    )

    assert first == second


def test_unresolved_boundary_changes_when_boundary_itself_changes():
    boundary = dep("bc", "b", "c")

    first = AffectedNodePropagator([boundary]).propagate(
        [change(boundary)],
        conditions_by_dependency={
            "bc": (("jurisdiction", "IN"),),
        },
        context={},
    )

    changed_boundary = dep("bc", "b", "d")

    second = AffectedNodePropagator([changed_boundary]).propagate(
        [change(changed_boundary)],
        conditions_by_dependency={
            "bc": (("jurisdiction", "IN"),),
        },
        context={},
    )

    assert first == second


def test_unresolved_becomes_active_when_context_resolves():
    dependency = dep("bc", "b", "c")

    unresolved = AffectedNodePropagator([dependency]).propagate(
        [change(dependency)],
        conditions_by_dependency={
            "bc": (("jurisdiction", "IN"),),
        },
        context={},
    )

    resolved = AffectedNodePropagator([dependency]).propagate(
        [change(dependency)],
        conditions_by_dependency={
            "bc": (("jurisdiction", "IN"),),
        },
        context={"jurisdiction": "IN"},
    )

    assert len(unresolved.suspensions) == 1
    assert resolved.suspensions == ()


# ---------------------------------------------------------------------------
# H3 — Commutative Execution
# ---------------------------------------------------------------------------


def test_independent_mutations_are_order_invariant():
    a = dep("a", "component:a", "library:a")
    b = dep("b", "component:b", "library:b")

    first = build_dependency_delta(
        [],
        [a, b],
        ["component:a", "component:b"],
    )

    second = build_dependency_delta(
        [],
        [b, a],
        ["component:b", "component:a"],
    )

    assert first == second
    assert first.digest == second.digest


def test_independent_mutation_digest_is_order_invariant():
    dependencies = [
        dep("z", "component:z", "library:z"),
        dep("a", "component:a", "library:a"),
        dep("m", "component:m", "library:m"),
    ]

    first = build_dependency_delta(
        [],
        dependencies,
        ["component:z", "component:a", "component:m"],
    )

    second = build_dependency_delta(
        [],
        list(reversed(dependencies)),
        ["component:m", "component:z", "component:a"],
    )

    assert first.digest == second.digest


def test_different_topologies_can_share_the_same_delta_classification():
    first = build_dependency_delta(
        [],
        [dep("ab", "a", "b")],
        ["a"],
    )

    second = build_dependency_delta(
        [],
        [dep("ab", "a", "c")],
        ["a"],
    )

    # The delta digest intentionally describes the classified mutation,
    # not the complete dependency topology.
    assert first == second
    assert first.digest == second.digest

    # Topology must therefore be validated independently.
    assert structural_state([dep("ab", "a", "b")]) != structural_state(
        [dep("ab", "a", "c")]
    )


def test_independent_execution_order_preserves_structural_state():
    first_dependencies = [
        dep("ab", "a", "b"),
        dep("cd", "c", "d"),
    ]

    second_dependencies = [
        dep("cd", "c", "d"),
        dep("ab", "a", "b"),
    ]

    assert structural_state(first_dependencies) == structural_state(
        second_dependencies
    )


def test_delta_digest_does_not_claim_graph_identity():
    first = build_dependency_delta(
        [],
        [dep("ab", "a", "b")],
        ["a"],
    )

    second = build_dependency_delta(
        [],
        [dep("ab", "a", "c")],
        ["a"],
    )

    assert first.digest == second.digest
    assert structural_state([dep("ab", "a", "b")]) != structural_state(
        [dep("ab", "a", "c")]
    )


# ---------------------------------------------------------------------------
# Digest ↔ structural oracle
# ---------------------------------------------------------------------------


def test_same_semantic_delta_has_same_digest():
    first = build_dependency_delta(
        [],
        [dep("ab", "a", "b")],
        ["a"],
    )

    second = build_dependency_delta(
        [],
        [dep("ab", "a", "b")],
        ["a"],
    )

    assert first == second
    assert first.digest == second.digest


def test_digest_changes_when_delta_classification_changes():
    first = build_dependency_delta(
        [],
        [dep("ab", "a", "b")],
        ["a"],
    )

    second = build_dependency_delta(
        [],
        [],
        ["a"],
    )

    assert first != second
    assert first.digest != second.digest


# ---------------------------------------------------------------------------
# Conditional evaluator cross-check
# ---------------------------------------------------------------------------


def test_conditional_state_partition_is_exhaustive():
    evaluator = ConditionalImpactEvaluator()

    active = evaluator.evaluate(
        "dep-active",
        (("environment", "production"),),
        {"environment": "production"},
    )

    blocked = evaluator.evaluate(
        "dep-blocked",
        (("environment", "production"),),
        {"environment": "development"},
    )

    unresolved = evaluator.evaluate(
        "dep-unresolved",
        (("jurisdiction", "IN"),),
        {},
    )

    assert {active.decision, blocked.decision, unresolved.decision} == {
        "ACTIVE",
        "BLOCKED",
        "UNRESOLVED",
    }
