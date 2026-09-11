from analysis.dependency_engine import DependencyClosure
from analysis.dependency_service import (
    DependencyNotFoundError,
    DependencyService,
)
from model.dependency import Dependency


def make_dependency(
    dependency_id,
    source,
    target,
    relationship="COMPONENT_USES_LIBRARY",
    confidence="high",
    evidence_ids=None,
    protocol=None,
):
    return Dependency(
        dependency_id=dependency_id,
        source_node_id=source,
        target_node_id=target,
        relationship_type=relationship,
        confidence=confidence,
        evidence_ids=evidence_ids or [],
        protocol=protocol,
    )


def test_list_dependencies_filters_deterministically():
    dependencies = [
        make_dependency("dep-2", "component-b", "library-x"),
        make_dependency("dep-1", "component-a", "library-x"),
        make_dependency(
            "dep-3",
            "component-a",
            "service-y",
            relationship="SERVICE_DEPENDS_ON_SERVICE",
        ),
    ]

    service = DependencyService(dependencies)

    result = service.list_dependencies(
        source_node_id="component-a",
    )

    assert [item.dependency_id for item in result] == [
        "dep-1",
        "dep-3",
    ]

    result = service.list_dependencies(
        target_node_id="library-x",
        relationship_type="COMPONENT_USES_LIBRARY",
    )

    assert [item.dependency_id for item in result] == [
        "dep-1",
        "dep-2",
    ]


def test_get_dependency_returns_observed_fact():
    dependency = make_dependency(
        "dep-1",
        "component-a",
        "library-x",
        evidence_ids=["evidence-1"],
    )

    service = DependencyService([dependency])

    result = service.get_dependency("dep-1")

    assert result == dependency
    assert result.evidence_ids == ["evidence-1"]


def test_get_dependency_raises_for_unknown_dependency():
    service = DependencyService([])

    try:
        service.get_dependency("missing")
    except DependencyNotFoundError as exc:
        assert exc.dependency_id == "missing"
    else:
        raise AssertionError("Expected DependencyNotFoundError")


def test_direct_dependencies_delegate_to_engine():
    dependencies = [
        make_dependency("dep-1", "component-a", "library-x"),
        make_dependency("dep-2", "component-a", "service-y"),
    ]

    service = DependencyService(dependencies)

    result = service.direct_dependencies("component-a")

    assert [item.dependency_id for item in result] == [
        "dep-1",
        "dep-2",
    ]


def test_closure_preserves_external_dependency_classification():
    dependencies = [
        make_dependency("dep-1", "component-a", "library-x"),
        make_dependency("dep-2", "library-x", "service-y"),
    ]

    service = DependencyService(dependencies)

    result = service.closure(
        "component-a",
        external_node_ids=["service-y"],
    )

    assert isinstance(result, DependencyClosure)
    assert result.root_node_id == "component-a"
    assert result.direct_dependencies == ("library-x",)
    assert result.indirect_dependencies == ("service-y",)
    assert result.external_dependencies == ("service-y",)
    assert result.closure_depth == 2


def test_paths_returns_only_paths_to_requested_target():
    dependencies = [
        make_dependency("dep-1", "component-a", "library-x"),
        make_dependency("dep-2", "component-a", "library-y"),
        make_dependency("dep-3", "library-x", "service-z"),
    ]

    service = DependencyService(dependencies)

    result = service.paths(
        "component-a",
        "service-z",
    )

    assert len(result) == 1
    assert result[0].node_ids == (
        "component-a",
        "library-x",
        "service-z",
    )
    assert result[0].dependency_ids == (
        "dep-1",
        "dep-3",
    )
    assert result[0].directness == "indirect"


def test_paths_respects_max_depth():
    dependencies = [
        make_dependency("dep-1", "component-a", "library-x"),
        make_dependency("dep-2", "library-x", "service-z"),
    ]

    service = DependencyService(dependencies)

    result = service.paths(
        "component-a",
        "service-z",
        max_depth=1,
    )

    assert result == ()


def test_migration_precedence_places_dependencies_before_dependants():
    dependencies = [
        make_dependency("dep-1", "application-a", "gateway-a"),
        make_dependency("dep-2", "gateway-a", "crypto-library"),
    ]

    service = DependencyService(dependencies)

    result = service.migration_precedence("application-a")

    assert result == (
        ("crypto-library",),
        ("gateway-a",),
        ("application-a",),
    )


def test_service_results_are_deterministic():
    dependencies = [
        make_dependency("dep-3", "a", "c"),
        make_dependency("dep-1", "a", "b"),
        make_dependency("dep-2", "b", "c"),
    ]

    service_one = DependencyService(dependencies)
    service_two = DependencyService(list(reversed(dependencies)))

    assert service_one.list_dependencies() == service_two.list_dependencies()
    assert service_one.closure("a") == service_two.closure("a")
    assert service_one.paths("a", "c") == service_two.paths("a", "c")
    assert service_one.migration_precedence("a") == (
        service_two.migration_precedence("a")
    )
