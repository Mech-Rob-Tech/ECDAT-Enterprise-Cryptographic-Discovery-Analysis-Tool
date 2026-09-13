"""3C.10 — Large-scale deterministic dependency stress validation."""

from __future__ import annotations

import gc
import time
import tracemalloc

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


def measure_chain(size):
    gc.collect()
    tracemalloc.start()

    start = time.perf_counter()

    dependencies = make_chain(size)
    engine = DependencyEngine(dependencies)

    construction_time = time.perf_counter() - start

    target = dependencies[-1]

    start = time.perf_counter()

    first = AffectedNodePropagator(
        dependencies
    ).propagate([change(target)])

    propagation_time = time.perf_counter() - start

    peak_memory = tracemalloc.get_traced_memory()[1]

    tracemalloc.stop()

    return {
        "size": size,
        "edges": len(engine.dependencies),
        "affected_nodes": len(first.affected_nodes),
        "construction_seconds": construction_time,
        "propagation_seconds": propagation_time,
        "peak_bytes": peak_memory,
    }


def test_chain_10000():
    result = measure_chain(10_000)

    assert result["edges"] == 9_999
    assert result["affected_nodes"] > 0

    print("\n3C.10 RESULT")
    print(result)
