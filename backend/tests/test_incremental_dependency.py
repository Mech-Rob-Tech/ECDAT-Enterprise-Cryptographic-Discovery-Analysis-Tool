"""Deterministic unit tests for incremental dependency planning."""

from analysis.incremental_dependency import (
    FileChange,
    IncrementalDependencyPlanner,
)


def test_build_plan_classifies_changes_deterministically():
    planner = IncrementalDependencyPlanner()

    plan = planner.build_plan(
        [
            FileChange("z.py", "modified"),
            FileChange("a.py", "added"),
            FileChange("m.py", "unchanged"),
            FileChange("b.py", "deleted"),
        ]
    )

    assert plan.unchanged == ("m.py",)
    assert plan.added == ("a.py",)
    assert plan.modified == ("z.py",)
    assert plan.deleted == ("b.py",)

    assert plan.changed_paths == (
        "a.py",
        "b.py",
        "z.py",
    )

    assert plan.affected_paths == (
        "a.py",
        "b.py",
        "z.py",
    )


def test_empty_changes_produce_empty_plan():
    plan = IncrementalDependencyPlanner().build_plan([])

    assert plan.unchanged == ()
    assert plan.added == ()
    assert plan.modified == ()
    assert plan.deleted == ()
    assert plan.affected_paths == ()
    assert plan.changed_paths == ()


def test_duplicate_paths_are_deterministic():
    planner = IncrementalDependencyPlanner()

    plan = planner.build_plan(
        [
            FileChange("crypto.py", "modified"),
            FileChange("crypto.py", "modified"),
        ]
    )

    assert plan.modified == ("crypto.py",)
    assert plan.changed_paths == ("crypto.py",)


def test_unchanged_files_are_not_reprocessed():
    plan = IncrementalDependencyPlanner().build_plan(
        [
            FileChange("crypto.py", "unchanged"),
            FileChange("service.py", "modified"),
        ]
    )

    assert plan.unchanged == ("crypto.py",)
    assert plan.affected_paths == ("service.py",)


def test_added_modified_and_deleted_are_all_affected():
    plan = IncrementalDependencyPlanner().build_plan(
        [
            FileChange("new.py", "added"),
            FileChange("changed.py", "modified"),
            FileChange("removed.py", "deleted"),
        ]
    )

    assert plan.affected_paths == (
        "changed.py",
        "new.py",
        "removed.py",
    )


def test_invalid_change_type_is_rejected():
    planner = IncrementalDependencyPlanner()

    try:
        planner.build_plan(
            [FileChange("crypto.py", "renamed")]
        )
    except ValueError as exc:
        assert "unsupported change type" in str(exc)
    else:
        raise AssertionError(
            "Expected invalid change type to raise ValueError"
        )


def test_empty_path_is_rejected():
    planner = IncrementalDependencyPlanner()

    try:
        planner.build_plan(
            [FileChange("", "modified")]
        )
    except ValueError as exc:
        assert "path must not be empty" in str(exc)
    else:
        raise AssertionError(
            "Expected empty path to raise ValueError"
        )


def test_changed_paths_resolve_to_observed_dependency_nodes():
    from model.dependency import Dependency

    planner = IncrementalDependencyPlanner()

    dependencies = [
        Dependency(
            dependency_id="dep-a",
            source_node_id="component:service.py",
            target_node_id="library:cryptography",
            relationship_type="COMPONENT_USES_LIBRARY",
            confidence="high",
            directness="direct",
            evidence_ids=[],
            source_reference="service.py:12",
            source_type="repository_dependency_discovery",
            record_version=1,
        ),
        Dependency(
            dependency_id="dep-b",
            source_node_id="component:other.py",
            target_node_id="library:requests",
            relationship_type="COMPONENT_USES_LIBRARY",
            confidence="medium",
            directness="direct",
            evidence_ids=[],
            source_reference="other.py:4",
            source_type="repository_dependency_discovery",
            record_version=1,
        ),
    ]

    affected = planner.affected_dependency_nodes(
        [
            FileChange("service.py", "modified"),
            FileChange("other.py", "unchanged"),
        ],
        dependencies,
    )

    assert affected == ("component:service.py",)


def test_deleted_file_can_mark_observed_dependency_node_affected():
    from model.dependency import Dependency

    planner = IncrementalDependencyPlanner()

    dependency = Dependency(
        dependency_id="dep-deleted",
        source_node_id="component:legacy.py",
        target_node_id="library:openssl",
        relationship_type="COMPONENT_USES_LIBRARY",
        confidence="high",
        directness="direct",
        evidence_ids=[],
        source_reference="legacy.py:8",
        source_type="repository_dependency_discovery",
        record_version=1,
    )

    affected = planner.affected_dependency_nodes(
        [FileChange("legacy.py", "deleted")],
        [dependency],
    )

    assert affected == ("component:legacy.py",)


def test_unrelated_dependency_observations_are_not_affected():
    from model.dependency import Dependency

    planner = IncrementalDependencyPlanner()

    dependency = Dependency(
        dependency_id="dep-unrelated",
        source_node_id="component:unrelated.py",
        target_node_id="library:tls",
        relationship_type="COMPONENT_USES_LIBRARY",
        confidence="high",
        directness="direct",
        evidence_ids=[],
        source_reference="unrelated.py:2",
        source_type="repository_dependency_discovery",
        record_version=1,
    )

    affected = planner.affected_dependency_nodes(
        [FileChange("service.py", "modified")],
        [dependency],
    )

    assert affected == ()


def test_dependency_delta_classifies_added_removed_modified_and_unchanged():
    from model.dependency import Dependency
    from analysis.incremental_dependency import build_dependency_delta

    previous = [
        Dependency(
            dependency_id="dep-a",
            source_node_id="component:a.py",
            target_node_id="library:crypto",
            relationship_type="COMPONENT_USES_LIBRARY",
            confidence="high",
            directness="direct",
            source_type="repository",
            source_reference="a.py:1",
            record_version=1,
        ),
        Dependency(
            dependency_id="dep-b",
            source_node_id="component:b.py",
            target_node_id="library:tls",
            relationship_type="COMPONENT_USES_LIBRARY",
            confidence="high",
            directness="direct",
            source_type="repository",
            source_reference="b.py:1",
            record_version=1,
        ),
        Dependency(
            dependency_id="dep-c",
            source_node_id="component:c.py",
            target_node_id="library:openssl",
            relationship_type="COMPONENT_USES_LIBRARY",
            confidence="high",
            directness="direct",
            source_type="repository",
            source_reference="c.py:1",
            record_version=1,
        ),
    ]

    current = [
        previous[0],
        Dependency(
            dependency_id="dep-b",
            source_node_id="component:b.py",
            target_node_id="library:openssl",
            relationship_type="COMPONENT_USES_LIBRARY",
            confidence="high",
            directness="direct",
            source_type="repository",
            source_reference="b.py:1",
            record_version=1,
        ),
        Dependency(
            dependency_id="dep-d",
            source_node_id="component:d.py",
            target_node_id="library:crypto",
            relationship_type="COMPONENT_USES_LIBRARY",
            confidence="high",
            directness="direct",
            source_type="repository",
            source_reference="d.py:1",
            record_version=1,
        ),
    ]

    delta = build_dependency_delta(
        previous,
        current,
        ["component:b.py", "component:d.py"],
    )

    assert delta.added == ("dep-d",)
    assert delta.removed == ("dep-c",)
    assert delta.modified == ("dep-b",)
    assert delta.unchanged_count == 1

    assert delta.affected_nodes == (
        "component:b.py",
        "component:d.py",
    )

    assert delta.recompute_nodes == (
        "component:b.py",
        "component:d.py",
    )

    assert delta.preserved_nodes == (
        "component:a.py",
    )


def test_dependency_delta_is_deterministic():
    from model.dependency import Dependency
    from analysis.incremental_dependency import build_dependency_delta

    dependency = Dependency(
        dependency_id="dep-z",
        source_node_id="component:z.py",
        target_node_id="library:crypto",
        relationship_type="COMPONENT_USES_LIBRARY",
        confidence="high",
        directness="direct",
        source_type="repository",
        source_reference="z.py:1",
        record_version=1,
    )

    first = build_dependency_delta(
        [dependency],
        [dependency],
        ["component:z.py"],
    )

    second = build_dependency_delta(
        [dependency],
        [dependency],
        ["component:z.py"],
    )

    assert first == second


def test_dependency_detector_classifies_added_removed_modified_and_unchanged():
    from model.dependency import Dependency
    from analysis.incremental_dependency import DependencyDetector

    def dep(
        dependency_id,
        target,
        *,
        evidence_ids=None,
        source_reference="service.py:1",
    ):
        return Dependency(
            dependency_id=dependency_id,
            source_node_id="component:service.py",
            target_node_id=target,
            relationship_type="COMPONENT_USES_LIBRARY",
            confidence="high",
            directness="direct",
            evidence_ids=list(evidence_ids or []),
            source_type="repository",
            source_reference=source_reference,
            record_version=1,
        )

    previous = [
        dep("dep-unchanged", "library:tls"),
        dep("dep-modified", "library:crypto"),
        dep("dep-removed", "library:openssl"),
    ]

    current = [
        dep("dep-unchanged", "library:tls"),
        dep("dep-modified", "library:pqc"),
        dep("dep-added", "library:kyber"),
    ]

    changes = DependencyDetector().detect(
        previous,
        current,
    )

    assert [
        (item.dependency_id, item.change_type)
        for item in changes
    ] == [
        ("dep-added", "added"),
        ("dep-modified", "modified"),
        ("dep-removed", "removed"),
        ("dep-unchanged", "unchanged"),
    ]


def test_dependency_detector_reports_exact_changed_fields():
    from model.dependency import Dependency
    from analysis.incremental_dependency import DependencyDetector

    previous = Dependency(
        dependency_id="dep-1",
        source_node_id="component:a.py",
        target_node_id="library:crypto",
        relationship_type="COMPONENT_USES_LIBRARY",
        confidence="high",
        directness="direct",
        protocol="TLS",
        source_type="repository",
        source_reference="a.py:10",
        record_version=1,
    )

    current = Dependency(
        dependency_id="dep-1",
        source_node_id="component:a.py",
        target_node_id="library:pqc",
        relationship_type="COMPONENT_USES_LIBRARY",
        confidence="high",
        directness="direct",
        protocol="TLS",
        source_type="repository",
        source_reference="a.py:10",
        record_version=1,
    )

    change = DependencyDetector().detect(
        [previous],
        [current],
    )[0]

    assert change.change_type == "modified"
    assert change.changed_fields == ("target_node_id",)
    assert change.affected_source_node == "component:a.py"
    assert change.affected_target_node == "library:pqc"


def test_dependency_detector_preserves_evidence_deterministically():
    from model.dependency import Dependency
    from analysis.incremental_dependency import DependencyDetector

    dependency = Dependency(
        dependency_id="dep-evidence",
        source_node_id="component:a.py",
        target_node_id="library:crypto",
        relationship_type="COMPONENT_USES_LIBRARY",
        confidence="high",
        directness="direct",
        evidence_ids=["e3", "e1", "e2", "e1"],
        source_type="repository",
        source_reference="a.py:10",
        record_version=1,
    )

    change = DependencyDetector().detect(
        [],
        [dependency],
    )[0]

    assert change.change_type == "added"
    assert change.evidence_ids == ("e1", "e2", "e3")
    assert change.affected_source_node == "component:a.py"
    assert change.affected_target_node == "library:crypto"


def test_dependency_detector_is_deterministic():
    from model.dependency import Dependency
    from analysis.incremental_dependency import DependencyDetector

    dependency = Dependency(
        dependency_id="dep-z",
        source_node_id="component:z.py",
        target_node_id="library:crypto",
        relationship_type="COMPONENT_USES_LIBRARY",
        confidence="high",
        directness="direct",
        source_type="repository",
        source_reference="z.py:1",
        record_version=1,
    )

    detector = DependencyDetector()

    first = detector.detect(
        [dependency],
        [dependency],
    )

    second = detector.detect(
        [dependency],
        [dependency],
    )

    assert first == second


def test_dependency_detector_distinguishes_evidence_invalidation():
    from model.dependency import Dependency
    from analysis.incremental_dependency import DependencyDetector

    previous = Dependency(
        dependency_id="dep-invalidated",
        source_node_id="component:service.py",
        target_node_id="library:crypto",
        relationship_type="COMPONENT_USES_LIBRARY",
        confidence="high",
        directness="direct",
        evidence_ids=["e-old"],
        source_type="repository",
        source_reference="service.py:10",
        record_version=1,
    )

    current = Dependency(
        dependency_id="dep-invalidated",
        source_node_id="component:service.py",
        target_node_id="library:crypto",
        relationship_type="COMPONENT_USES_LIBRARY",
        confidence="high",
        directness="direct",
        evidence_ids=["e-new"],
        source_type="repository",
        source_reference="service.py:11",
        record_version=1,
    )

    change = DependencyDetector().detect(
        [previous],
        [current],
    )[0]

    assert change.change_type == "invalidated"
    assert change.changed_fields == (
        "source_reference",
    )
    assert change.affected_source_node == "component:service.py"
    assert change.affected_target_node == "library:crypto"
    assert change.evidence_ids == ("e-new",)


def test_affected_node_propagation_traverses_reverse_dependency_direction():
    from model.dependency import Dependency
    from analysis.incremental_dependency import (
        AffectedNodePropagator,
        DependencyChange,
    )

    dependencies = [
        Dependency(
            dependency_id="dep-ab",
            source_node_id="component:a",
            target_node_id="library:b",
            relationship_type="COMPONENT_USES_LIBRARY",
            confidence="high",
            source_type="repository",
            evidence_ids=["e-ab"],
        ),
        Dependency(
            dependency_id="dep-bc",
            source_node_id="library:b",
            target_node_id="library:c",
            relationship_type="LIBRARY_USES_LIBRARY",
            confidence="high",
            source_type="repository",
            evidence_ids=["e-bc"],
        ),
    ]

    change = DependencyChange(
        dependency_id="dep-bc",
        change_type="modified",
        previous_dependency=dependencies[1],
        current_dependency=dependencies[1],
        changed_fields=("target_node_id",),
        affected_source_node="library:b",
        affected_target_node="library:c",
        evidence_ids=("e-bc",),
    )

    result = AffectedNodePropagator(dependencies).propagate([change])

    assert [item.node_id for item in result.affected_nodes] == [
        "library:b",
        "component:a",
    ]

    assert result.affected_nodes[0].depth == 1
    assert result.affected_nodes[1].depth == 2


def test_affected_node_propagation_is_cycle_safe_and_deterministic():
    from model.dependency import Dependency
    from analysis.incremental_dependency import (
        AffectedNodePropagator,
        DependencyChange,
    )

    dependencies = [
        Dependency(
            dependency_id="ab",
            source_node_id="a",
            target_node_id="b",
            relationship_type="SERVICE_DEPENDS_ON_SERVICE",
            source_type="test",
        ),
        Dependency(
            dependency_id="bc",
            source_node_id="b",
            target_node_id="c",
            relationship_type="SERVICE_DEPENDS_ON_SERVICE",
            source_type="test",
        ),
        Dependency(
            dependency_id="ca",
            source_node_id="c",
            target_node_id="a",
            relationship_type="SERVICE_DEPENDS_ON_SERVICE",
            source_type="test",
        ),
    ]

    change = DependencyChange(
        dependency_id="bc",
        change_type="modified",
        previous_dependency=dependencies[1],
        current_dependency=dependencies[1],
        changed_fields=("target_node_id",),
        affected_source_node="b",
        affected_target_node="c",
        evidence_ids=(),
    )

    propagator = AffectedNodePropagator(dependencies)

    first = propagator.propagate([change])
    second = propagator.propagate([change])

    assert first == second
    assert [item.node_id for item in first.affected_nodes] == [
        "a",
        "b",
    ]


def test_affected_node_propagation_preserves_multiple_paths_and_evidence():
    from model.dependency import Dependency
    from analysis.incremental_dependency import (
        AffectedNodePropagator,
        DependencyChange,
    )

    dependencies = [
        Dependency(
            dependency_id="ab",
            source_node_id="a",
            target_node_id="b",
            relationship_type="SERVICE_DEPENDS_ON_SERVICE",
            source_type="test",
            evidence_ids=["e-ab"],
        ),
        Dependency(
            dependency_id="ac",
            source_node_id="a",
            target_node_id="c",
            relationship_type="SERVICE_DEPENDS_ON_SERVICE",
            source_type="test",
            evidence_ids=["e-ac"],
        ),
        Dependency(
            dependency_id="bc",
            source_node_id="b",
            target_node_id="c",
            relationship_type="SERVICE_DEPENDS_ON_SERVICE",
            source_type="test",
            evidence_ids=["e-bc"],
        ),
    ]

    change = DependencyChange(
        dependency_id="bc",
        change_type="modified",
        previous_dependency=dependencies[2],
        current_dependency=dependencies[2],
        changed_fields=("target_node_id",),
        affected_source_node="b",
        affected_target_node="c",
        evidence_ids=("e-bc",),
    )

    result = AffectedNodePropagator(dependencies).propagate([change])

    a = next(
        item
        for item in result.affected_nodes
        if item.node_id == "a"
    )

    assert len(a.paths) == 2
    assert set(a.origin_dependency_ids) == {"bc"}
    assert set(
        evidence_id
        for path in a.paths
        for evidence_id in path.evidence_ids
    ) == {"e-ab", "e-bc"}


def test_affected_node_propagation_respects_max_depth():
    from model.dependency import Dependency
    from analysis.incremental_dependency import (
        AffectedNodePropagator,
        DependencyChange,
    )

    dependencies = [
        Dependency(
            dependency_id="ab",
            source_node_id="a",
            target_node_id="b",
            relationship_type="SERVICE_DEPENDS_ON_SERVICE",
            source_type="test",
        ),
        Dependency(
            dependency_id="bc",
            source_node_id="b",
            target_node_id="c",
            relationship_type="SERVICE_DEPENDS_ON_SERVICE",
            source_type="test",
        ),
    ]

    change = DependencyChange(
        dependency_id="bc",
        change_type="modified",
        previous_dependency=dependencies[1],
        current_dependency=dependencies[1],
        changed_fields=("target_node_id",),
        affected_source_node="b",
        affected_target_node="c",
        evidence_ids=(),
    )

    result = AffectedNodePropagator(dependencies).propagate(
        [change],
        max_depth=1,
    )

    assert tuple(
        item.node_id
        for item in result.affected_nodes
    ) == ("b",)


# ---------------------------------------------------------------------------
# 3C.4 — Conditional Impact
# ---------------------------------------------------------------------------

def test_conditional_impact_unconditional_dependency_is_active():
    from backend.analysis.incremental_dependency import (
        ConditionalImpactEvaluator,
    )

    evaluator = ConditionalImpactEvaluator()

    result = evaluator.evaluate(
        dependency_id="dep-ab",
        conditions=(),
        context={},
    )

    assert result.decision == "ACTIVE"
    assert result.matched_conditions == ()
    assert result.blocking_conditions == ()
    assert result.unresolved_conditions == ()


def test_conditional_impact_matching_condition_is_active():
    from backend.analysis.incremental_dependency import (
        ConditionalImpactEvaluator,
    )

    evaluator = ConditionalImpactEvaluator()

    result = evaluator.evaluate(
        dependency_id="dep-ab",
        conditions=(
            ("environment", "production"),
        ),
        context={
            "environment": "production",
        },
    )

    assert result.decision == "ACTIVE"
    assert result.matched_conditions == (
        ("environment", "production"),
    )
    assert result.blocking_conditions == ()
    assert result.unresolved_conditions == ()


def test_conditional_impact_failing_condition_is_blocked():
    from backend.analysis.incremental_dependency import (
        ConditionalImpactEvaluator,
    )

    evaluator = ConditionalImpactEvaluator()

    result = evaluator.evaluate(
        dependency_id="dep-ab",
        conditions=(
            ("environment", "production"),
        ),
        context={
            "environment": "development",
        },
    )

    assert result.decision == "BLOCKED"
    assert result.matched_conditions == ()
    assert result.blocking_conditions == (
        ("environment", "production"),
    )
    assert result.unresolved_conditions == ()


def test_conditional_impact_missing_context_is_unresolved():
    from backend.analysis.incremental_dependency import (
        ConditionalImpactEvaluator,
    )

    evaluator = ConditionalImpactEvaluator()

    result = evaluator.evaluate(
        dependency_id="dep-ab",
        conditions=(
            ("jurisdiction", "IN"),
        ),
        context={
            "environment": "production",
        },
    )

    assert result.decision == "UNRESOLVED"
    assert result.matched_conditions == ()
    assert result.blocking_conditions == ()
    assert result.unresolved_conditions == (
        ("jurisdiction", "IN"),
    )


def test_conditional_impact_multiple_conditions_use_and_semantics():
    from backend.analysis.incremental_dependency import (
        ConditionalImpactEvaluator,
    )

    evaluator = ConditionalImpactEvaluator()

    result = evaluator.evaluate(
        dependency_id="dep-ab",
        conditions=(
            ("environment", "production"),
            ("jurisdiction", "IN"),
            ("security_tier", "restricted"),
        ),
        context={
            "environment": "production",
            "jurisdiction": "IN",
            "security_tier": "restricted",
        },
    )

    assert result.decision == "ACTIVE"
    assert result.matched_conditions == (
        ("environment", "production"),
        ("jurisdiction", "IN"),
        ("security_tier", "restricted"),
    )


def test_conditional_impact_missing_condition_does_not_become_blocked():
    from backend.analysis.incremental_dependency import (
        ConditionalImpactEvaluator,
    )

    evaluator = ConditionalImpactEvaluator()

    result = evaluator.evaluate(
        dependency_id="dep-ab",
        conditions=(
            ("environment", "production"),
            ("jurisdiction", "IN"),
        ),
        context={
            "environment": "production",
        },
    )

    assert result.decision == "UNRESOLVED"
    assert result.matched_conditions == (
        ("environment", "production"),
    )
    assert result.blocking_conditions == ()
    assert result.unresolved_conditions == (
        ("jurisdiction", "IN"),
    )


def test_conditional_impact_blocked_and_unresolved_are_distinct():
    from backend.analysis.incremental_dependency import (
        ConditionalImpactEvaluator,
    )

    evaluator = ConditionalImpactEvaluator()

    blocked = evaluator.evaluate(
        dependency_id="dep-blocked",
        conditions=(("environment", "production"),),
        context={"environment": "development"},
    )

    unresolved = evaluator.evaluate(
        dependency_id="dep-unresolved",
        conditions=(("jurisdiction", "IN"),),
        context={"environment": "production"},
    )

    assert blocked.decision == "BLOCKED"
    assert unresolved.decision == "UNRESOLVED"
    assert blocked.blocking_conditions
    assert not blocked.unresolved_conditions
    assert unresolved.unresolved_conditions
    assert not unresolved.blocking_conditions


def test_conditional_impact_result_is_deterministic():
    from backend.analysis.incremental_dependency import (
        ConditionalImpactEvaluator,
    )

    evaluator = ConditionalImpactEvaluator()

    result_a = evaluator.evaluate(
        dependency_id="dep-ab",
        conditions=(
            ("security_tier", "restricted"),
            ("environment", "production"),
            ("jurisdiction", "IN"),
        ),
        context={
            "jurisdiction": "IN",
            "environment": "production",
            "security_tier": "restricted",
        },
    )

    result_b = evaluator.evaluate(
        dependency_id="dep-ab",
        conditions=(
            ("jurisdiction", "IN"),
            ("security_tier", "restricted"),
            ("environment", "production"),
        ),
        context={
            "security_tier": "restricted",
            "jurisdiction": "IN",
            "environment": "production",
        },
    )

    assert result_a == result_b


def test_conditional_impact_blocked_edge_does_not_propagate():
    from backend.analysis.incremental_dependency import (
        ConditionalImpactEvaluator,
    )

    evaluator = ConditionalImpactEvaluator()

    result = evaluator.evaluate(
        dependency_id="dep-bc",
        conditions=(("environment", "production"),),
        context={"environment": "development"},
    )

    assert result.decision == "BLOCKED"

    # A BLOCKED dependency is known to be inapplicable.
    assert result.decision != "ACTIVE"


def test_conditional_impact_unresolved_edge_does_not_propagate_now():
    from backend.analysis.incremental_dependency import (
        ConditionalImpactEvaluator,
    )

    evaluator = ConditionalImpactEvaluator()

    result = evaluator.evaluate(
        dependency_id="dep-bc",
        conditions=(("jurisdiction", "IN"),),
        context={"environment": "production"},
    )

    assert result.decision == "UNRESOLVED"

    # UNRESOLVED is not permission to propagate.
    assert result.decision != "ACTIVE"


def test_conditional_impact_unresolved_state_retains_required_condition():
    from backend.analysis.incremental_dependency import (
        ConditionalImpactEvaluator,
    )

    evaluator = ConditionalImpactEvaluator()

    result = evaluator.evaluate(
        dependency_id="dep-bc",
        conditions=(
            ("environment", "production"),
            ("jurisdiction", "IN"),
        ),
        context={"environment": "production"},
    )

    assert result.decision == "UNRESOLVED"
    assert result.unresolved_conditions == (
        ("jurisdiction", "IN"),
    )


def test_conditional_impact_unresolved_becomes_active_when_context_arrives():
    from backend.analysis.incremental_dependency import (
        ConditionalImpactEvaluator,
    )

    evaluator = ConditionalImpactEvaluator()

    unresolved = evaluator.evaluate(
        dependency_id="dep-bc",
        conditions=(("jurisdiction", "IN"),),
        context={},
    )

    resolved = evaluator.evaluate(
        dependency_id="dep-bc",
        conditions=(("jurisdiction", "IN"),),
        context={"jurisdiction": "IN"},
    )

    assert unresolved.decision == "UNRESOLVED"
    assert resolved.decision == "ACTIVE"
    assert unresolved.dependency_id == resolved.dependency_id


def test_conditional_impact_propagation_active_edge_reaches_dependants():
    from backend.analysis.dependency_engine import DependencyEngine
    from backend.analysis.incremental_dependency import (
        AffectedNodePropagator,
        ConditionalImpactEvaluator,
        DependencyChange,
    )
    from backend.model.dependency import Dependency

    dependencies = (
        Dependency(
            dependency_id="dep-ab",
            source_node_id="a",
            target_node_id="b",
            relationship_type="depends_on",
            evidence_ids=("e-ab",),
        ),
        Dependency(
            dependency_id="dep-bc",
            source_node_id="b",
            target_node_id="c",
            relationship_type="depends_on",
            evidence_ids=("e-bc",),
        ),
    )

    change = DependencyChange(
        dependency_id="dep-bc",
        change_type="modified",
        previous_dependency=dependencies[1],
        current_dependency=dependencies[1],
        changed_fields=("confidence",),
        affected_source_node="b",
        affected_target_node="c",
        evidence_ids=("e-bc",),
    )

    impact = ConditionalImpactEvaluator().evaluate(
        dependency_id="dep-bc",
        conditions=(("environment", "production"),),
        context={"environment": "production"},
    )

    assert impact.decision == "ACTIVE"

    result = AffectedNodePropagator(
        dependencies,
    ).propagate(
        (change,),
    )

    assert [node.node_id for node in result.affected_nodes] == [
        "b",
        "a",
    ]


def test_conditional_impact_blocked_edge_is_not_used_for_propagation():
    from backend.analysis.incremental_dependency import (
        ConditionalImpactEvaluator,
    )

    impact = ConditionalImpactEvaluator().evaluate(
        dependency_id="dep-bc",
        conditions=(("environment", "production"),),
        context={"environment": "development"},
    )

    assert impact.decision == "BLOCKED"

    # The conditional layer explicitly denies traversal.
    assert impact.decision != "ACTIVE"


def test_conditional_impact_unresolved_edge_is_not_used_for_propagation():
    from backend.analysis.incremental_dependency import (
        ConditionalImpactEvaluator,
    )

    impact = ConditionalImpactEvaluator().evaluate(
        dependency_id="dep-bc",
        conditions=(("jurisdiction", "IN"),),
        context={},
    )

    assert impact.decision == "UNRESOLVED"

    # Unknown is not equivalent to permission to propagate.
    assert impact.decision != "ACTIVE"


def test_conditional_impact_unresolved_edge_can_be_re_evaluated():
    from backend.analysis.incremental_dependency import (
        ConditionalImpactEvaluator,
    )

    evaluator = ConditionalImpactEvaluator()

    suspended = evaluator.evaluate(
        dependency_id="dep-bc",
        conditions=(("jurisdiction", "IN"),),
        context={},
    )

    resumed = evaluator.evaluate(
        dependency_id="dep-bc",
        conditions=(("jurisdiction", "IN"),),
        context={"jurisdiction": "IN"},
    )

    assert suspended.decision == "UNRESOLVED"
    assert suspended.unresolved_conditions == (
        ("jurisdiction", "IN"),
    )

    assert resumed.decision == "ACTIVE"
    assert resumed.unresolved_conditions == ()
    assert resumed.matched_conditions == (
        ("jurisdiction", "IN"),
    )


def test_conditional_impact_unresolved_result_can_form_suspension():
    from backend.analysis.incremental_dependency import (
        ConditionalImpactEvaluator,
        ConditionalImpactSuspension,
    )

    evaluator = ConditionalImpactEvaluator()

    result = evaluator.evaluate(
        dependency_id="dep-bc",
        conditions=(
            ("environment", "production"),
            ("jurisdiction", "IN"),
        ),
        context={
            "environment": "production",
        },
    )

    suspension = ConditionalImpactSuspension(
        dependency_id=result.dependency_id,
        unresolved_conditions=result.unresolved_conditions,
        matched_conditions=result.matched_conditions,
        evidence_ids=("e-bc",),
    )

    assert suspension.dependency_id == "dep-bc"
    assert suspension.unresolved_conditions == (
        ("jurisdiction", "IN"),
    )
    assert suspension.matched_conditions == (
        ("environment", "production"),
    )
    assert suspension.evidence_ids == ("e-bc",)


def test_conditional_propagation_active_crosses_edge():
    from backend.analysis.incremental_dependency import (
        AffectedNodePropagator,
        DependencyChange,
    )
    from backend.model.dependency import Dependency

    dependencies = (
        Dependency(
            dependency_id="dep-ab",
            source_node_id="a",
            target_node_id="b",
            relationship_type="depends_on",
            evidence_ids=("e-ab",),
        ),
        Dependency(
            dependency_id="dep-bc",
            source_node_id="b",
            target_node_id="c",
            relationship_type="depends_on",
            evidence_ids=("e-bc",),
        ),
    )

    change = DependencyChange(
        dependency_id="dep-bc",
        change_type="modified",
        previous_dependency=dependencies[1],
        current_dependency=dependencies[1],
        changed_fields=("confidence",),
        affected_source_node="b",
        affected_target_node="c",
        evidence_ids=("e-bc",),
    )

    result = AffectedNodePropagator(dependencies).propagate(
        (change,),
        conditions_by_dependency={
            "dep-bc": (("environment", "production"),),
        },
        context={
            "environment": "production",
        },
    )

    assert [node.node_id for node in result.affected_nodes] == [
        "b",
        "a",
    ]
    assert result.suspensions == ()


def test_conditional_propagation_blocked_cuts_edge():
    from backend.analysis.incremental_dependency import (
        AffectedNodePropagator,
        DependencyChange,
    )
    from backend.model.dependency import Dependency

    dependencies = (
        Dependency(
            dependency_id="dep-ab",
            source_node_id="a",
            target_node_id="b",
            relationship_type="depends_on",
            evidence_ids=("e-ab",),
        ),
        Dependency(
            dependency_id="dep-bc",
            source_node_id="b",
            target_node_id="c",
            relationship_type="depends_on",
            evidence_ids=("e-bc",),
        ),
    )

    change = DependencyChange(
        dependency_id="dep-bc",
        change_type="modified",
        previous_dependency=dependencies[1],
        current_dependency=dependencies[1],
        changed_fields=("confidence",),
        affected_source_node="b",
        affected_target_node="c",
        evidence_ids=("e-bc",),
    )

    result = AffectedNodePropagator(dependencies).propagate(
        (change,),
        conditions_by_dependency={
            "dep-bc": (("environment", "production"),),
        },
        context={
            "environment": "development",
        },
    )

    assert result.affected_nodes == ()
    assert result.paths == ()
    assert result.suspensions == ()


def test_conditional_propagation_unresolved_suspends_edge():
    from backend.analysis.incremental_dependency import (
        AffectedNodePropagator,
        ConditionalImpactSuspension,
        DependencyChange,
    )
    from backend.model.dependency import Dependency

    dependencies = (
        Dependency(
            dependency_id="dep-ab",
            source_node_id="a",
            target_node_id="b",
            relationship_type="depends_on",
            evidence_ids=("e-ab",),
        ),
        Dependency(
            dependency_id="dep-bc",
            source_node_id="b",
            target_node_id="c",
            relationship_type="depends_on",
            evidence_ids=("e-bc",),
        ),
    )

    change = DependencyChange(
        dependency_id="dep-bc",
        change_type="modified",
        previous_dependency=dependencies[1],
        current_dependency=dependencies[1],
        changed_fields=("confidence",),
        affected_source_node="b",
        affected_target_node="c",
        evidence_ids=("e-bc",),
    )

    result = AffectedNodePropagator(dependencies).propagate(
        (change,),
        conditions_by_dependency={
            "dep-bc": (("jurisdiction", "IN"),),
        },
        context={},
    )

    assert result.affected_nodes == ()
    assert result.paths == ()

    assert result.suspensions == (
        ConditionalImpactSuspension(
            dependency_id="dep-bc",
            unresolved_conditions=(
                ("jurisdiction", "IN"),
            ),
            matched_conditions=(),
            evidence_ids=("e-bc",),
        ),
    )


def test_dependency_delta_accepts_one_shot_dependency_iterators():
    from model.dependency import Dependency
    from analysis.incremental_dependency import build_dependency_delta

    previous = [
        Dependency(
            dependency_id="dep-a",
            source_node_id="component:a.py",
            target_node_id="library:crypto",
            relationship_type="COMPONENT_USES_LIBRARY",
            confidence="high",
            directness="direct",
            source_type="repository",
            source_reference="a.py:1",
            record_version=1,
        ),
    ]

    current = [
        Dependency(
            dependency_id="dep-a",
            source_node_id="component:a.py",
            target_node_id="library:tls",
            relationship_type="COMPONENT_USES_LIBRARY",
            confidence="high",
            directness="direct",
            source_type="repository",
            source_reference="a.py:1",
            record_version=1,
        ),
    ]

    delta = build_dependency_delta(
        iter(previous),
        iter(current),
        (),
    )

    assert delta.added == ()
    assert delta.removed == ()
    assert delta.modified == ("dep-a",)
    assert delta.unchanged_count == 0
    assert delta.recompute_nodes == ("component:a.py",)
    assert delta.preserved_nodes == ()


def test_dependency_delta_recompute_and_preserve_are_disjoint():
    from model.dependency import Dependency
    from analysis.incremental_dependency import build_dependency_delta

    def dep(dependency_id, source, target):
        return Dependency(
            dependency_id=dependency_id,
            source_node_id=source,
            target_node_id=target,
            relationship_type="COMPONENT_USES_LIBRARY",
            confidence="high",
            directness="direct",
            source_type="repository",
            source_reference=f"{source.split(':', 1)[-1]}:1",
            record_version=1,
        )

    previous = [
        dep("dep-a", "component:a.py", "library:tls"),
        dep("dep-b", "component:b.py", "library:tls"),
        dep("dep-c", "component:c.py", "library:tls"),
    ]

    current = [
        dep("dep-a", "component:a.py", "library:tls"),
        dep("dep-b", "component:b.py", "library:crypto"),
        dep("dep-c", "component:c.py", "library:tls"),
    ]

    delta = build_dependency_delta(
        previous,
        current,
        ["component:b.py"],
    )

    assert delta.recompute_nodes == ("component:b.py",)
    assert delta.preserved_nodes == (
        "component:a.py",
        "component:c.py",
    )

    assert set(delta.recompute_nodes).isdisjoint(
        set(delta.preserved_nodes)
    )


def test_removed_dependency_does_not_automatically_recompute_source():
    from model.dependency import Dependency
    from analysis.incremental_dependency import build_dependency_delta

    dependency = Dependency(
        dependency_id="dep-removed",
        source_node_id="component:a.py",
        target_node_id="library:openssl",
        relationship_type="COMPONENT_USES_LIBRARY",
        confidence="high",
        directness="direct",
        source_type="repository",
        source_reference="a.py:1",
        record_version=1,
    )

    delta = build_dependency_delta(
        [dependency],
        [],
        [],
    )

    assert delta.removed == ("dep-removed",)
    assert delta.recompute_nodes == ()
    assert delta.preserved_nodes == ()


def test_added_dependency_recomputes_current_source_node():
    from model.dependency import Dependency
    from analysis.incremental_dependency import build_dependency_delta

    dependency = Dependency(
        dependency_id="dep-added",
        source_node_id="component:a.py",
        target_node_id="library:openssl",
        relationship_type="COMPONENT_USES_LIBRARY",
        confidence="high",
        directness="direct",
        source_type="repository",
        source_reference="a.py:1",
        record_version=1,
    )

    delta = build_dependency_delta(
        [],
        [dependency],
        [],
    )

    assert delta.added == ("dep-added",)
    assert delta.recompute_nodes == ("component:a.py",)
    assert delta.preserved_nodes == ()


def test_modified_dependency_recomputes_current_source_node():
    from model.dependency import Dependency
    from analysis.incremental_dependency import build_dependency_delta

    previous = Dependency(
        dependency_id="dep-modified",
        source_node_id="component:a.py",
        target_node_id="library:openssl",
        relationship_type="COMPONENT_USES_LIBRARY",
        confidence="high",
        directness="direct",
        source_type="repository",
        source_reference="a.py:1",
        record_version=1,
    )

    current = Dependency(
        dependency_id="dep-modified",
        source_node_id="component:a.py",
        target_node_id="library:pqc",
        relationship_type="COMPONENT_USES_LIBRARY",
        confidence="high",
        directness="direct",
        source_type="repository",
        source_reference="a.py:1",
        record_version=1,
    )

    delta = build_dependency_delta(
        [previous],
        [current],
        [],
    )

    assert delta.modified == ("dep-modified",)
    assert delta.recompute_nodes == ("component:a.py",)
    assert delta.preserved_nodes == ()


def test_affected_node_can_require_recompute_without_current_dependency():
    from analysis.incremental_dependency import build_dependency_delta

    delta = build_dependency_delta(
        [],
        [],
        ["component:changed.py"],
    )

    assert delta.affected_nodes == ("component:changed.py",)
    assert delta.recompute_nodes == ("component:changed.py",)
    assert delta.preserved_nodes == ()


def test_unaffected_current_source_is_preserved():
    from model.dependency import Dependency
    from analysis.incremental_dependency import build_dependency_delta

    dependency = Dependency(
        dependency_id="dep-stable",
        source_node_id="component:stable.py",
        target_node_id="library:tls",
        relationship_type="COMPONENT_USES_LIBRARY",
        confidence="high",
        directness="direct",
        source_type="repository",
        source_reference="stable.py:1",
        record_version=1,
    )

    delta = build_dependency_delta(
        [dependency],
        [dependency],
        [],
    )

    assert delta.recompute_nodes == ()
    assert delta.preserved_nodes == ("component:stable.py",)


def test_recompute_and_preserve_order_is_deterministic():
    from model.dependency import Dependency
    from analysis.incremental_dependency import build_dependency_delta

    dependencies = [
        Dependency(
            dependency_id="dep-z",
            source_node_id="component:z.py",
            target_node_id="library:tls",
            relationship_type="COMPONENT_USES_LIBRARY",
            confidence="high",
            directness="direct",
            source_type="repository",
            source_reference="z.py:1",
            record_version=1,
        ),
        Dependency(
            dependency_id="dep-a",
            source_node_id="component:a.py",
            target_node_id="library:tls",
            relationship_type="COMPONENT_USES_LIBRARY",
            confidence="high",
            directness="direct",
            source_type="repository",
            source_reference="a.py:1",
            record_version=1,
        ),
    ]

    first = build_dependency_delta(
        dependencies,
        dependencies,
        ["component:z.py"],
    )

    second = build_dependency_delta(
        list(reversed(dependencies)),
        list(reversed(dependencies)),
        ["component:z.py"],
    )

    assert first.recompute_nodes == ("component:z.py",)
    assert first.preserved_nodes == ("component:a.py",)

    assert first == second
def test_dependency_delta_digest_is_deterministic():
    from analysis.incremental_dependency import DependencyDelta

    delta = DependencyDelta(
        added=("dep-b",),
        removed=("dep-c",),
        modified=("dep-a",),
        unchanged_count=2,
        affected_nodes=("component:a.py", "component:b.py"),
        recompute_nodes=("component:a.py",),
        preserved_nodes=("component:b.py",),
    )

    assert delta.digest == delta.digest
    assert len(delta.digest) == 64
    assert all(
        character in "0123456789abcdef"
        for character in delta.digest
    )


def test_dependency_delta_digest_matches_sha256_of_canonical_bytes():
    import hashlib

    from analysis.incremental_dependency import DependencyDelta

    delta = DependencyDelta(
        added=("dep-a",),
        removed=(),
        modified=("dep-b",),
        unchanged_count=1,
        affected_nodes=("component:a.py",),
        recompute_nodes=("component:a.py",),
        preserved_nodes=(),
    )

    expected = hashlib.sha256(delta.canonical_bytes()).hexdigest()

    assert delta.digest == expected


def test_dependency_delta_digest_is_invariant_to_equivalent_input_order():
    from analysis.incremental_dependency import DependencyDelta

    first = DependencyDelta(
        added=("dep-a", "dep-b"),
        removed=("dep-c",),
        modified=("dep-d",),
        unchanged_count=3,
        affected_nodes=("component:a.py", "component:b.py"),
        recompute_nodes=("component:a.py",),
        preserved_nodes=("component:b.py",),
    )

    second = DependencyDelta(
        added=("dep-a", "dep-b"),
        removed=("dep-c",),
        modified=("dep-d",),
        unchanged_count=3,
        affected_nodes=("component:a.py", "component:b.py"),
        recompute_nodes=("component:a.py",),
        preserved_nodes=("component:b.py",),
    )

    assert first.digest == second.digest
    assert first.canonical_bytes() == second.canonical_bytes()


def test_dependency_delta_digest_changes_when_added_changes():
    from analysis.incremental_dependency import DependencyDelta

    base = DependencyDelta(
        added=("dep-a",),
        removed=(),
        modified=(),
        unchanged_count=0,
        affected_nodes=(),
        recompute_nodes=(),
        preserved_nodes=(),
    )

    changed = DependencyDelta(
        added=("dep-a", "dep-b"),
        removed=(),
        modified=(),
        unchanged_count=0,
        affected_nodes=(),
        recompute_nodes=(),
        preserved_nodes=(),
    )

    assert base.digest != changed.digest


def test_dependency_delta_digest_changes_when_removed_changes():
    from analysis.incremental_dependency import DependencyDelta

    base = DependencyDelta(
        added=(),
        removed=("dep-a",),
        modified=(),
        unchanged_count=0,
        affected_nodes=(),
        recompute_nodes=(),
        preserved_nodes=(),
    )

    changed = DependencyDelta(
        added=(),
        removed=("dep-a", "dep-b"),
        modified=(),
        unchanged_count=0,
        affected_nodes=(),
        recompute_nodes=(),
        preserved_nodes=(),
    )

    assert base.digest != changed.digest


def test_dependency_delta_digest_changes_when_modified_changes():
    from analysis.incremental_dependency import DependencyDelta

    base = DependencyDelta(
        added=(),
        removed=(),
        modified=("dep-a",),
        unchanged_count=0,
        affected_nodes=(),
        recompute_nodes=(),
        preserved_nodes=(),
    )

    changed = DependencyDelta(
        added=(),
        removed=(),
        modified=("dep-a", "dep-b"),
        unchanged_count=0,
        affected_nodes=(),
        recompute_nodes=(),
        preserved_nodes=(),
    )

    assert base.digest != changed.digest


def test_dependency_delta_digest_changes_when_affected_nodes_change():
    from analysis.incremental_dependency import DependencyDelta

    base = DependencyDelta(
        added=(),
        removed=(),
        modified=(),
        unchanged_count=0,
        affected_nodes=("component:a.py",),
        recompute_nodes=(),
        preserved_nodes=(),
    )

    changed = DependencyDelta(
        added=(),
        removed=(),
        modified=(),
        unchanged_count=0,
        affected_nodes=("component:b.py",),
        recompute_nodes=(),
        preserved_nodes=(),
    )

    assert base.digest != changed.digest


def test_dependency_delta_digest_changes_when_recompute_or_preserve_changes():
    from analysis.incremental_dependency import DependencyDelta

    base = DependencyDelta(
        added=(),
        removed=(),
        modified=(),
        unchanged_count=1,
        affected_nodes=(),
        recompute_nodes=("component:a.py",),
        preserved_nodes=("component:b.py",),
    )

    recompute_changed = DependencyDelta(
        added=(),
        removed=(),
        modified=(),
        unchanged_count=1,
        affected_nodes=(),
        recompute_nodes=("component:b.py",),
        preserved_nodes=("component:a.py",),
    )

    assert base.digest != recompute_changed.digest


def test_dependency_delta_canonical_bytes_are_utf8_and_stable():
    from analysis.incremental_dependency import DependencyDelta

    delta = DependencyDelta(
        added=("dep-α",),
        removed=(),
        modified=(),
        unchanged_count=0,
        affected_nodes=("component:日本.py",),
        recompute_nodes=(),
        preserved_nodes=(),
    )

    canonical = delta.canonical_bytes()

    assert isinstance(canonical, bytes)
    assert canonical == delta.canonical_bytes()
    assert b"dep-" in canonical

def test_dependency_delta_canonicalization_distinguishes_structural_values():
    from analysis.incremental_dependency import DependencyDelta

    first = DependencyDelta(
        added=("a,b",),
        removed=(),
        modified=(),
        unchanged_count=0,
        affected_nodes=(),
        recompute_nodes=(),
        preserved_nodes=(),
    )

    second = DependencyDelta(
        added=("a", "b"),
        removed=(),
        modified=(),
        unchanged_count=0,
        affected_nodes=(),
        recompute_nodes=(),
        preserved_nodes=(),
    )

    assert first.canonical_bytes() != second.canonical_bytes()
    assert first.digest != second.digest
