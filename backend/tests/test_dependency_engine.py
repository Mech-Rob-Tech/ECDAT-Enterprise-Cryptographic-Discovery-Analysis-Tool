from analysis.dependency_engine import (
    DependencyEngine,
    dependencies_from_relationships,
)
from model.dependency import Dependency


def make_dependency(
    source: str,
    target: str,
    dependency_id: str,
    *,
    evidence_ids=None,
    protocol=None,
):
    return Dependency(
        dependency_id=dependency_id,
        source_node_id=source,
        target_node_id=target,
        relationship_type="SERVICE_DEPENDS_ON_SERVICE",
        confidence="high",
        evidence_ids=list(evidence_ids or []),
        protocol=protocol,
        source_type="test",
    )


def test_closure_separates_direct_and_indirect_dependencies():
    engine = DependencyEngine(
        [
            make_dependency("artifact:x25519", "component:tls", "d1", evidence_ids=["e1"], protocol="TLS"),
            make_dependency("component:tls", "service:gateway", "d2", evidence_ids=["e2"]),
            make_dependency("service:gateway", "service:partner", "d3", evidence_ids=["e3"]),
        ]
    )

    closure = engine.closure(
        "artifact:x25519",
        external_node_ids={"service:partner"},
    )

    assert closure.direct_dependencies == ("component:tls",)
    assert closure.indirect_dependencies == ("service:gateway", "service:partner")
    assert closure.external_dependencies == ("service:partner",)
    assert closure.affected_protocols == ("TLS",)
    assert closure.closure_depth == 3
    assert closure.path_count == 3
    assert closure.evidence_coverage == 1.0


def test_paths_are_deterministic_and_cycle_safe():
    engine = DependencyEngine(
        [
            make_dependency("a", "b", "ab"),
            make_dependency("b", "c", "bc"),
            make_dependency("c", "a", "ca"),
        ]
    )

    paths = engine.paths("a")

    assert [(item.node_ids, item.dependency_ids) for item in paths] == [
        (("a", "b"), ("ab",)),
        (("a", "b", "c"), ("ab", "bc")),
    ]


def test_migration_precedence_places_dependencies_first():
    engine = DependencyEngine(
        [
            make_dependency("application", "gateway", "ag"),
            make_dependency("gateway", "crypto-library", "gc"),
        ]
    )

    assert engine.migration_precedence("application") == (
        ("crypto-library",),
        ("gateway",),
        ("application",),
    )


def test_missing_evidence_reduces_coverage():
    engine = DependencyEngine(
        [
            make_dependency("a", "b", "ab", evidence_ids=["e1"]),
            make_dependency("b", "c", "bc"),
        ]
    )

    assert engine.closure("a").evidence_coverage == 0.0


def test_generic_topology_relationships_are_not_promoted_to_dependencies():
    relationships = [
        {
            "relationship_id": "a|contains|b",
            "source_id": "a",
            "target_id": "b",
            "relationship_type": "contains",
            "confidence": "high",
        },
        {
            "relationship_id": "b|uses|c",
            "source_id": "b",
            "target_id": "c",
            "relationship_type": "uses",
            "confidence": "high",
        },
        {
            "relationship_id": "b|USES_LIBRARY|c",
            "source_id": "b",
            "target_id": "c",
            "relationship_type": "USES_LIBRARY",
            "confidence": "high",
            "evidence_ids": ["e1"],
        },
    ]

    dependencies = dependencies_from_relationships(relationships, scan_id="scan:1")

    assert len(dependencies) == 1
    assert dependencies[0].relationship_type == "USES_LIBRARY"
    assert dependencies[0].scan_id == "scan:1"
    assert dependencies[0].evidence_ids == ["e1"]
