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
