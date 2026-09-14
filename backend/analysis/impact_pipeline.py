"""Dynamic scan-to-impact orchestration for ECDAT.

This module connects existing deterministic analytical primitives:

    previous scan
        ↓
    dependency change detection
        ↓
    dependency delta
        ↓
    structural propagation
        ↓
    impact attribution

It does not discover dependencies and does not make migration decisions.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping

from analysis.dependency_service import DependencyService
from analysis.incremental_dependency import (
    DependencyDetector,
    DependencyChange,
    DependencyDelta,
    AffectedNodePropagator,
    build_dependency_delta,
)
from analysis.impact_attribution import (
    ImpactAssessment,
    ImpactAttributionEngine,
)


@dataclass(frozen=True)
class DynamicImpactResult:
    """Complete deterministic result of comparing two scan states."""

    dependency_changes: tuple[DependencyChange, ...]
    dependency_delta: DependencyDelta
    propagation_result: object
    impact_assessment: ImpactAssessment

    @property
    def changed_dependency_ids(self) -> tuple[str, ...]:
        return tuple(
            change.dependency_id
            for change in self.dependency_changes
            if change.change_type != "unchanged"
        )


def _field(scan: object, name: str, default: object = ()) -> object:
    if isinstance(scan, Mapping):
        return scan.get(name, default)
    return getattr(scan, name, default)


def _dependencies(scan: object) -> tuple[object, ...]:
    """Return canonical Dependency objects from a scan state.

    Historical scan states are persisted as JSON dictionaries.
    Analytical engines operate on the canonical Dependency domain
    model, so reconstruction happens at this boundary.
    """
    records = tuple(
        _field(scan, "dependencies", ()) or ()
    )

    if not records:
        return ()

    if all(
        not isinstance(record, Mapping)
        for record in records
    ):
        return records

    service = DependencyService.from_dicts(
        list(records)
    )

    return service.list_dependencies()


def _business_contexts(scan: object) -> tuple[object, ...]:
    return tuple(_field(scan, "business_contexts", ()) or ())


def _evidence_ids(scan: object) -> tuple[str, ...]:
    evidence = _field(scan, "evidence", ()) or ()

    ids = []

    for item in evidence:
        if isinstance(item, Mapping):
            value = item.get("evidence_id")
        else:
            value = getattr(item, "evidence_id", None)

        if value is not None:
            ids.append(str(value))

    return tuple(sorted(set(ids)))


def assess_scan_change(
    previous_scan: object,
    current_scan: object,
    *,
    max_depth: int | None = None,
    conditions_by_dependency: dict[
        str, tuple[tuple[str, str], ...]
    ] | None = None,
    context: dict[str, str] | None = None,
) -> DynamicImpactResult:
    """Compare two real ECDAT scan states and attribute downstream impact.

    The caller supplies only the previous and current scan state.
    Dependency changes are detected automatically.
    """

    previous_dependencies = _dependencies(previous_scan)
    current_dependencies = _dependencies(current_scan)

    detector = DependencyDetector()

    changes = detector.detect(
        previous_dependencies,
        current_dependencies,
    )

    changed = tuple(
        change
        for change in changes
        if change.change_type != "unchanged"
    )

    affected_nodes = tuple(
        sorted(
            {
                node_id
                for change in changed
                for node_id in (
                    change.affected_target_node,
                    change.affected_source_node,
                )
                if node_id
            }
        )
    )

    delta = build_dependency_delta(
        previous_dependencies,
        current_dependencies,
        affected_nodes,
    )

    propagator = AffectedNodePropagator(
        current_dependencies
    )

    propagation = propagator.propagate(
        changed,
        max_depth=max_depth,
        conditions_by_dependency=conditions_by_dependency,
        context=context,
    )

    roots = tuple(
        sorted(
            {
                (
                    change.affected_target_node
                    or change.affected_source_node
                )
                for change in changed
                if (
                    change.affected_target_node
                    or change.affected_source_node
                )
            }
        )
    )

    current_evidence_ids = _evidence_ids(current_scan)

    assessment = ImpactAttributionEngine().assess(
        propagation,
        _business_contexts(current_scan),
        root_node_ids=roots,
        context_evidence_ids=current_evidence_ids,
    )

    return DynamicImpactResult(
        dependency_changes=changes,
        dependency_delta=delta,
        propagation_result=propagation,
        impact_assessment=assessment,
    )
