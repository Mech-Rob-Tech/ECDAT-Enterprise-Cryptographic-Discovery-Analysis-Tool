from backend.analysis.incremental_dependency import (
    AffectedNode,
    AffectedSubgraph,
    PropagationPath,
    PropagationResult,
    ConditionalImpactSuspension,
    build_affected_subgraph,
)
from backend.model.dependency import Dependency


def make_dependency(
    dependency_id: str,
    source: str,
    target: str,
    evidence_ids=(),
) -> Dependency:
    return Dependency(
        dependency_id=dependency_id,
        source_node_id=source,
        target_node_id=target,
        relationship_type="depends_on",
        evidence_ids=list(evidence_ids),
        source_type="test",
        source_reference=f"{source}:1",
    )


def make_propagation(
    affected_nodes,
    paths,
    suspensions=(),
) -> PropagationResult:
    return PropagationResult(
        affected_nodes=tuple(affected_nodes),
        paths=tuple(paths),
        suspensions=tuple(suspensions),
    )


def test_empty_propagation_produces_empty_subgraph():
    result = make_propagation([], [])

    subgraph = build_affected_subgraph(
        result,
        [],
    )

    assert subgraph.root_node_ids == ()
    assert subgraph.node_ids == ()
    assert subgraph.dependency_ids == ()
    assert subgraph.boundary_dependency_ids == ()
    assert subgraph.suspended_dependency_ids == ()
    assert subgraph.evidence_ids == ()
    assert subgraph.max_depth == 0


def test_affected_subgraph_materializes_propagated_region():
    path = PropagationPath(
        origin_dependency_id="dep-ab",
        node_ids=("b", "a"),
        dependency_ids=("dep-ab",),
        evidence_ids=("ev-ab",),
    )

    affected_nodes = (
        AffectedNode(
            node_id="a",
            depth=1,
            origin_dependency_ids=("dep-ab",),
            paths=(path,),
        ),
        AffectedNode(
            node_id="b",
            depth=0,
            origin_dependency_ids=("dep-ab",),
            paths=(path,),
        ),
    )

    result = make_propagation(
        affected_nodes,
        (path,),
    )

    dependencies = [
        make_dependency(
            "dep-ab",
            "a",
            "b",
            ("ev-ab",),
        ),
    ]

    subgraph = build_affected_subgraph(
        result,
        dependencies,
    )

    assert subgraph.root_node_ids == ("b",)
    assert subgraph.node_ids == ("a", "b")
    assert subgraph.dependency_ids == ("dep-ab",)
    assert subgraph.boundary_dependency_ids == ()
    assert subgraph.evidence_ids == ("ev-ab",)
    assert subgraph.max_depth == 1


def test_boundary_dependencies_are_not_internal_dependencies():
    path = PropagationPath(
        origin_dependency_id="dep-ab",
        node_ids=("b", "a"),
        dependency_ids=("dep-ab",),
        evidence_ids=("ev-ab",),
    )

    affected_nodes = (
        AffectedNode(
            node_id="a",
            depth=1,
            origin_dependency_ids=("dep-ab",),
            paths=(path,),
        ),
        AffectedNode(
            node_id="b",
            depth=0,
            origin_dependency_ids=("dep-ab",),
            paths=(path,),
        ),
    )

    result = make_propagation(
        affected_nodes,
        (path,),
    )

    dependencies = [
        make_dependency("dep-ab", "a", "b"),
        make_dependency("dep-ca", "c", "a"),
        make_dependency("dep-bd", "b", "d"),
    ]

    subgraph = build_affected_subgraph(
        result,
        dependencies,
    )

    assert subgraph.dependency_ids == ("dep-ab",)
    assert subgraph.boundary_dependency_ids == (
        "dep-bd",
        "dep-ca",
    )


def test_suspended_dependency_is_retained_as_boundary():
    path = PropagationPath(
        origin_dependency_id="dep-ab",
        node_ids=("b",),
        dependency_ids=("dep-ab",),
        evidence_ids=("ev-ab",),
    )

    suspension = ConditionalImpactSuspension(
        dependency_id="dep-bc",
        unresolved_conditions=("environment",),
        matched_conditions=(),
        evidence_ids=("ev-bc",),
    )

    affected_nodes = (
        AffectedNode(
            node_id="b",
            depth=0,
            origin_dependency_ids=("dep-ab",),
            paths=(path,),
        ),
    )

    result = make_propagation(
        affected_nodes,
        (path,),
        (suspension,),
    )

    dependencies = [
        make_dependency("dep-ab", "b", "a"),
        make_dependency("dep-bc", "b", "c"),
    ]

    subgraph = build_affected_subgraph(
        result,
        dependencies,
    )

    assert subgraph.boundary_dependency_ids == (
        "dep-ab",
        "dep-bc",
    )
    assert subgraph.suspended_dependency_ids == (
        "dep-bc",
    )


def test_determinism_is_independent_of_input_order():
    path_1 = PropagationPath(
        origin_dependency_id="dep-1",
        node_ids=("b", "a"),
        dependency_ids=("dep-1",),
        evidence_ids=("ev-1",),
    )

    path_2 = PropagationPath(
        origin_dependency_id="dep-2",
        node_ids=("c", "b", "a"),
        dependency_ids=("dep-2",),
        evidence_ids=("ev-2",),
    )

    affected_nodes = (
        AffectedNode(
            node_id="c",
            depth=2,
            origin_dependency_ids=("dep-2",),
            paths=(path_2,),
        ),
        AffectedNode(
            node_id="a",
            depth=0,
            origin_dependency_ids=("dep-1",),
            paths=(path_1,),
        ),
        AffectedNode(
            node_id="b",
            depth=1,
            origin_dependency_ids=("dep-1", "dep-2"),
            paths=(path_1, path_2),
        ),
    )

    result_a = make_propagation(
        affected_nodes,
        (path_2, path_1),
    )

    result_b = make_propagation(
        tuple(reversed(affected_nodes)),
        (path_1, path_2),
    )

    dependencies = [
        make_dependency("dep-2", "b", "c", ("ev-2",)),
        make_dependency("dep-1", "a", "b", ("ev-1",)),
    ]

    subgraph_a = build_affected_subgraph(
        result_a,
        dependencies,
    )

    subgraph_b = build_affected_subgraph(
        result_b,
        reversed(dependencies),
    )

    assert subgraph_a == subgraph_b


def test_removed_dependency_can_remain_in_propagation_projection():
    """
    The projection may retain a dependency ID carried by the propagation
    result even when that dependency is absent from the current dependency
    observation universe.

    This matters for later delta/recompute analysis.
    """

    path = PropagationPath(
        origin_dependency_id="removed-dep",
        node_ids=("b", "a"),
        dependency_ids=("removed-dep",),
        evidence_ids=("old-evidence",),
    )

    affected_nodes = (
        AffectedNode(
            node_id="a",
            depth=1,
            origin_dependency_ids=("removed-dep",),
            paths=(path,),
        ),
        AffectedNode(
            node_id="b",
            depth=0,
            origin_dependency_ids=("removed-dep",),
            paths=(path,),
        ),
    )

    result = make_propagation(
        affected_nodes,
        (path,),
    )

    subgraph = build_affected_subgraph(
        result,
        [],
    )

    assert subgraph.dependency_ids == ("removed-dep",)
    assert subgraph.evidence_ids == ("old-evidence",)


def test_counts_are_structural_and_deterministic():
    path = PropagationPath(
        origin_dependency_id="dep-ab",
        node_ids=("b", "a"),
        dependency_ids=("dep-ab",),
        evidence_ids=("ev-ab",),
    )

    result = make_propagation(
        (
            AffectedNode(
                node_id="a",
                depth=1,
                origin_dependency_ids=("dep-ab",),
                paths=(path,),
            ),
            AffectedNode(
                node_id="b",
                depth=0,
                origin_dependency_ids=("dep-ab",),
                paths=(path,),
            ),
        ),
        (path,),
    )

    subgraph = build_affected_subgraph(
        result,
        [
            make_dependency("dep-ab", "a", "b"),
            make_dependency("dep-ca", "c", "a"),
        ],
    )

    assert subgraph.node_count == 2
    assert subgraph.dependency_count == 1
    assert subgraph.boundary_count == 1
    assert subgraph.evidence_count == 1
