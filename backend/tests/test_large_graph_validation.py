"""3C.9 — Deterministic large-graph validation baseline."""

from backend.analysis.dependency_engine import DependencyEngine
from backend.analysis.incremental_dependency import (
    AffectedNodePropagator,
    DependencyChange,
)
from backend.model.dependency import Dependency


def dep(dep_id, source, target):
    return Dependency(
        dependency_id=dep_id,
        source_node_id=source,
        target_node_id=target,
        relationship_type="depends_on",
        evidence_ids=(),
    )


def change(dependency):
    return DependencyChange(
        dependency_id=dependency.dependency_id,
        change_type="modified",
        previous_dependency=dependency,
        current_dependency=dependency,
        changed_fields=("confidence",),
        affected_source_node=dependency.source_node_id,
        affected_target_node=dependency.target_node_id,
        evidence_ids=(),
    )


def make_chain(size):
    return [
        dep(f"d{i}", f"n{i}", f"n{i + 1}")
        for i in range(size - 1)
    ]


def make_star(size):
    return [
        dep(f"d{i}", "root", f"n{i}")
        for i in range(size)
    ]


def make_tree(size):
    dependencies = []

    for i in range(1, size):
        parent = (i - 1) // 2
        dependencies.append(
            dep(
                f"d{i}",
                f"n{parent}",
                f"n{i}",
            )
        )

    return dependencies


def make_cycle(size):
    return [
        dep(
            f"d{i}",
            f"n{i}",
            f"n{(i + 1) % size}",
        )
        for i in range(size)
    ]


def test_chain_100():
    dependencies = make_chain(100)
    engine = DependencyEngine(dependencies)

    assert len(engine.dependencies) == 99
    assert engine.paths("n0")


def test_chain_1000():
    dependencies = make_chain(1000)
    engine = DependencyEngine(dependencies)

    assert len(engine.dependencies) == 999
    assert engine.paths("n0")


def test_star_1000():
    dependencies = make_star(1000)
    engine = DependencyEngine(dependencies)

    assert len(engine.dependencies) == 1000
    assert len(engine.direct_dependencies("root")) == 1000


def test_tree_1000():
    dependencies = make_tree(1000)
    engine = DependencyEngine(dependencies)

    assert len(engine.dependencies) == 999
    assert engine.paths("n0")


def test_cycle_1000_is_cycle_safe():
    dependencies = make_cycle(1000)
    engine = DependencyEngine(dependencies)

    paths = engine.paths("n0")

    assert paths
    assert all(
        len(path.node_ids) <= 1000
        for path in paths
    )


def test_large_chain_propagation_is_deterministic():
    dependencies = make_chain(1000)

    target = dependencies[-1]

    first = AffectedNodePropagator(dependencies).propagate(
        [change(target)]
    )

    second = AffectedNodePropagator(dependencies).propagate(
        [change(target)]
    )

    assert first == second


def test_large_graph_dependency_order_is_deterministic():
    dependencies = make_chain(1000)

    first = DependencyEngine(dependencies)
    second = DependencyEngine(list(reversed(dependencies)))

    assert first.dependencies == second.dependencies
