"""Deterministic incremental dependency-processing primitives."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, Mapping, Tuple

from backend.model.dependency import Dependency


@dataclass(frozen=True)
class FileChange:
    """One repository file change."""

    path: str
    change_type: str
    previous_fingerprint: str | None = None
    current_fingerprint: str | None = None


@dataclass(frozen=True)
class IncrementalDependencyPlan:
    """Deterministic plan for incremental dependency processing."""

    unchanged: Tuple[str, ...]
    added: Tuple[str, ...]
    modified: Tuple[str, ...]
    deleted: Tuple[str, ...]
    affected_paths: Tuple[str, ...]

    @property
    def changed_paths(self) -> Tuple[str, ...]:
        return tuple(
            sorted(
                set(self.added)
                | set(self.modified)
                | set(self.deleted)
            )
        )


class IncrementalDependencyPlanner:
    """Build deterministic dependency-processing plans."""

    _VALID_TYPES = frozenset(
        {"added", "modified", "deleted", "unchanged"}
    )

    def build_plan(
        self,
        changes: Iterable[FileChange],
    ) -> IncrementalDependencyPlan:
        normalized: Dict[str, FileChange] = {}

        for change in changes:
            path = change.path.strip()

            if not path:
                raise ValueError(
                    "file change path must not be empty"
                )

            if change.change_type not in self._VALID_TYPES:
                raise ValueError(
                    "unsupported change type: "
                    f"{change.change_type}"
                )

            normalized[path] = FileChange(
                path=path,
                change_type=change.change_type,
                previous_fingerprint=change.previous_fingerprint,
                current_fingerprint=change.current_fingerprint,
            )

        unchanged = tuple(
            sorted(
                path
                for path, change in normalized.items()
                if change.change_type == "unchanged"
            )
        )

        added = tuple(
            sorted(
                path
                for path, change in normalized.items()
                if change.change_type == "added"
            )
        )

        modified = tuple(
            sorted(
                path
                for path, change in normalized.items()
                if change.change_type == "modified"
            )
        )

        deleted = tuple(
            sorted(
                path
                for path, change in normalized.items()
                if change.change_type == "deleted"
            )
        )

        affected_paths = tuple(
            sorted(
                set(added)
                | set(modified)
                | set(deleted)
            )
        )

        return IncrementalDependencyPlan(
            unchanged=unchanged,
            added=added,
            modified=modified,
            deleted=deleted,
            affected_paths=affected_paths,
        )

    def affected_dependency_nodes(
        self,
        changes: Iterable[FileChange],
        dependencies: Iterable[object],
    ) -> Tuple[str, ...]:
        """Resolve changed repository paths to observed dependency nodes.

        Only direct repository observations are considered. Transitive graph
        propagation belongs to DependencyEngine.
        """
        plan = self.build_plan(changes)
        affected_paths = set(plan.affected_paths)

        nodes = set()

        for dependency in dependencies:
            source_reference = getattr(
                dependency,
                "source_reference",
                None,
            )

            if not source_reference:
                continue

            source_path = str(source_reference).split(
                ":",
                1,
            )[0]

            if source_path in affected_paths:
                nodes.add(
                    dependency.source_node_id
                )

        return tuple(sorted(nodes))



@dataclass(frozen=True)
class DependencyChange:
    """Deterministic classification of one dependency observation."""

    dependency_id: str
    change_type: str
    previous_dependency: object | None
    current_dependency: object | None
    changed_fields: Tuple[str, ...]
    affected_source_node: str | None
    affected_target_node: str | None
    evidence_ids: Tuple[str, ...]


class DependencyDetector:
    """Detect deterministic changes between dependency observations.

    This layer performs observation comparison only. It does not propagate
    impact and does not decide recomputation policy.
    """

    _FIELD_NAMES = (
        "source_node_id",
        "target_node_id",
        "relationship_type",
        "confidence",
        "directness",
        "protocol",
        "purpose",
        "effective_from",
        "effective_until",
        "observed_at",
        "source_type",
        "source_reference",
        "record_version",
    )

    def detect(
        self,
        previous_dependencies: Iterable[object],
        current_dependencies: Iterable[object],
    ) -> Tuple[DependencyChange, ...]:
        previous = {
            getattr(item, "dependency_id"): item
            for item in previous_dependencies
        }
        current = {
            getattr(item, "dependency_id"): item
            for item in current_dependencies
        }

        changes = []

        for dependency_id in sorted(
            set(previous) | set(current)
        ):
            old = previous.get(dependency_id)
            new = current.get(dependency_id)

            if old is None:
                changes.append(
                    self._change(
                        dependency_id,
                        "added",
                        None,
                        new,
                        (),
                    )
                )
                continue

            if new is None:
                changes.append(
                    self._change(
                        dependency_id,
                        "removed",
                        old,
                        None,
                        (),
                    )
                )
                continue

            changed_fields = tuple(
                field
                for field in self._FIELD_NAMES
                if getattr(old, field, None)
                != getattr(new, field, None)
            )

            if changed_fields:
                change_type = (
                    "invalidated"
                    if self._is_invalidated(old, new, changed_fields)
                    else "modified"
                )
            else:
                change_type = "unchanged"

            changes.append(
                self._change(
                    dependency_id,
                    change_type,
                    old,
                    new,
                    changed_fields,
                )
            )

        return tuple(changes)

    @staticmethod
    def _is_invalidated(
        previous: object,
        current: object,
        changed_fields: Tuple[str, ...],
    ) -> bool:
        """Evidence invalidation is distinct from structural modification."""

        if not changed_fields:
            return False

        source_changed = (
            "source_reference" in changed_fields
            or "source_type" in changed_fields
        )

        previous_evidence = tuple(
            sorted(
                set(
                    getattr(
                        previous,
                        "evidence_ids",
                        (),
                    )
                    or ()
                )
            )
        )

        current_evidence = tuple(
            sorted(
                set(
                    getattr(
                        current,
                        "evidence_ids",
                        (),
                    )
                    or ()
                )
            )
        )

        evidence_changed = (
            previous_evidence != current_evidence
        )

        return source_changed and evidence_changed

    @staticmethod
    def _change(
        dependency_id: str,
        change_type: str,
        previous: object | None,
        current: object | None,
        changed_fields: Tuple[str, ...],
    ) -> DependencyChange:
        item = current or previous

        return DependencyChange(
            dependency_id=dependency_id,
            change_type=change_type,
            previous_dependency=previous,
            current_dependency=current,
            changed_fields=changed_fields,
            affected_source_node=(
                getattr(item, "source_node_id", None)
                if item is not None
                else None
            ),
            affected_target_node=(
                getattr(item, "target_node_id", None)
                if item is not None
                else None
            ),
            evidence_ids=tuple(
                sorted(
                    set(
                        getattr(
                            item,
                            "evidence_ids",
                            (),
                        )
                        or ()
                    )
                )
            ),
        )


@dataclass(frozen=True)
class DependencyDelta:
    """Semantic difference between two dependency states."""

    added: Tuple[str, ...]
    removed: Tuple[str, ...]
    modified: Tuple[str, ...]
    unchanged_count: int

    affected_nodes: Tuple[str, ...]
    recompute_nodes: Tuple[str, ...]
    preserved_nodes: Tuple[str, ...]


def build_dependency_delta(
    previous_dependencies: Iterable[object],
    current_dependencies: Iterable[object],
    affected_nodes: Iterable[str],
) -> DependencyDelta:
    """Build a deterministic dependency-state delta.

    Dependency identity is based on dependency_id. A dependency with the
    same identity but different structural fields is considered modified.
    """

    def fingerprint(dependency: object) -> Tuple[object, ...]:
        return (
            getattr(dependency, "source_node_id", None),
            getattr(dependency, "target_node_id", None),
            getattr(dependency, "relationship_type", None),
            getattr(dependency, "confidence", None),
            getattr(dependency, "directness", None),
            getattr(dependency, "protocol", None),
            getattr(dependency, "purpose", None),
            getattr(dependency, "effective_from", None),
            getattr(dependency, "effective_until", None),
            getattr(dependency, "source_type", None),
            getattr(dependency, "source_reference", None),
            getattr(dependency, "record_version", None),
        )

    previous = {
        getattr(item, "dependency_id"): fingerprint(item)
        for item in previous_dependencies
    }

    current = {
        getattr(item, "dependency_id"): fingerprint(item)
        for item in current_dependencies
    }

    previous_ids = set(previous)
    current_ids = set(current)

    added = tuple(sorted(current_ids - previous_ids))
    removed = tuple(sorted(previous_ids - current_ids))

    modified = tuple(
        sorted(
            dependency_id
            for dependency_id in previous_ids & current_ids
            if previous[dependency_id] != current[dependency_id]
        )
    )

    unchanged_count = sum(
        1
        for dependency_id in previous_ids & current_ids
        if previous[dependency_id] == current[dependency_id]
    )

    affected = tuple(sorted(set(affected_nodes)))

    recompute = set(affected)

    current_changed_dependency_ids = (
        set(added)
        | set(modified)
    )

    for dependency in current_dependencies:
        dependency_id = getattr(
            dependency,
            "dependency_id",
            None,
        )

        if dependency_id in current_changed_dependency_ids:
            recompute.add(
                getattr(dependency, "source_node_id")
            )

    recompute_nodes = tuple(sorted(recompute))

    preserved_nodes = tuple(
        sorted(
            set(
                getattr(item, "source_node_id")
                for item in current_dependencies
            )
            - set(recompute_nodes)
        )
    )

    return DependencyDelta(
        added=added,
        removed=removed,
        modified=modified,
        unchanged_count=unchanged_count,
        affected_nodes=affected,
        recompute_nodes=recompute_nodes,
        preserved_nodes=preserved_nodes,
    )


@dataclass(frozen=True)
class PropagationPath:
    """One deterministic causal path from a dependency change to a node."""

    origin_dependency_id: str
    node_ids: Tuple[str, ...]
    dependency_ids: Tuple[str, ...]
    evidence_ids: Tuple[str, ...]


@dataclass(frozen=True)
class AffectedNode:
    """One node reached by deterministic dependency propagation."""

    node_id: str
    depth: int
    origin_dependency_ids: Tuple[str, ...]
    paths: Tuple[PropagationPath, ...]


@dataclass(frozen=True)
class PropagationResult:
    """Deterministic affected-node propagation result."""

    affected_nodes: Tuple[AffectedNode, ...]
    paths: Tuple[PropagationPath, ...]
    suspensions: Tuple[ConditionalImpactSuspension, ...] = ()


@dataclass(frozen=True)
class ConditionalImpactResult:
    """Deterministic result of evaluating dependency conditions."""

    dependency_id: str
    decision: str
    matched_conditions: Tuple[Tuple[str, str], ...]
    blocking_conditions: Tuple[Tuple[str, str], ...]
    unresolved_conditions: Tuple[Tuple[str, str], ...]


@dataclass(frozen=True)
class ConditionalImpactSuspension:
    """Immutable record for an unresolved conditional dependency."""

    dependency_id: str
    unresolved_conditions: Tuple[Tuple[str, str], ...]
    matched_conditions: Tuple[Tuple[str, str], ...]
    evidence_ids: Tuple[str, ...]


class ConditionalImpactEvaluator:
    """Evaluate explicit dependency conditions against structural context.

    Conditions use exact key/value equality and deterministic AND semantics.

    Decision semantics:

    ACTIVE:
        Every condition is present and matches.

    BLOCKED:
        At least one condition is present but does not match.

    UNRESOLVED:
        No condition is blocked, but at least one required condition is
        missing from the supplied context.

    The evaluator is intentionally data-blind. It only examines the supplied
    condition and context metadata.
    """

    ACTIVE = "ACTIVE"
    BLOCKED = "BLOCKED"
    UNRESOLVED = "UNRESOLVED"

    def evaluate(
        self,
        dependency_id: str,
        conditions: Tuple[Tuple[str, str], ...],
        context: dict[str, str],
    ) -> ConditionalImpactResult:
        normalized_conditions = tuple(
            sorted(
                (str(key), str(value))
                for key, value in conditions
            )
        )

        normalized_context = {
            str(key): str(value)
            for key, value in context.items()
        }

        matched = []
        blocking = []
        unresolved = []

        for key, expected_value in normalized_conditions:
            actual_value = normalized_context.get(key)

            if actual_value is None:
                unresolved.append((key, expected_value))
            elif actual_value == expected_value:
                matched.append((key, expected_value))
            else:
                blocking.append((key, expected_value))

        if blocking:
            decision = self.BLOCKED
        elif unresolved:
            decision = self.UNRESOLVED
        else:
            decision = self.ACTIVE

        return ConditionalImpactResult(
            dependency_id=str(dependency_id),
            decision=decision,
            matched_conditions=tuple(matched),
            blocking_conditions=tuple(blocking),
            unresolved_conditions=tuple(unresolved),
        )


class AffectedNodePropagator:
    """Propagate dependency changes through observed reverse dependencies.

    Propagation answers only the structural question:
    "Which dependants are reachable from these changed dependency targets?"

    Governance, conditional predicates, and recomputation policy belong to
    later stages.
    """

    def __init__(self, dependencies: Iterable[object]) -> None:
        from analysis.dependency_engine import DependencyEngine

        self._dependencies = tuple(
            sorted(
                dependencies,
                key=lambda item: (
                    item.source_node_id,
                    item.target_node_id,
                    item.relationship_type,
                    item.dependency_id,
                ),
            )
        )
        self._engine = DependencyEngine(self._dependencies)

    def propagate(
        self,
        changes: Iterable[DependencyChange],
        *,
        max_depth: int | None = None,
        conditions_by_dependency: dict[
            str, Tuple[Tuple[str, str], ...]
        ] | None = None,
        context: dict[str, str] | None = None,
    ) -> PropagationResult:
        if max_depth is not None and max_depth < 1:
            return PropagationResult((), (), ())

        conditions_by_dependency = conditions_by_dependency or {}
        context = context or {}

        conditional_evaluator = ConditionalImpactEvaluator()
        suspensions = []

        queue = []

        for change in changes:
            origin = (
                change.affected_target_node
                or change.affected_source_node
            )

            if not origin:
                continue

            queue.append(
                (
                    origin,
                    origin,
                    change.dependency_id,
                    change.change_type,
                    tuple(change.evidence_ids),
                    0,
                    (origin,),
                    (),
                )
            )

        queue.sort(
            key=lambda item: (
                item[1],
                item[2],
            )
        )

        paths = []

        while queue:
            (
                current_node,
                origin_node,
                origin_dependency_id,
                change_type,
                evidence_ids,
                depth,
                node_ids,
                dependency_ids,
            ) = queue.pop(0)

            if max_depth is not None and depth >= max_depth:
                continue

            for dependency in self._engine.dependants(current_node):
                conditions = conditions_by_dependency.get(
                    dependency.dependency_id,
                    (),
                )

                impact = conditional_evaluator.evaluate(
                    dependency_id=dependency.dependency_id,
                    conditions=conditions,
                    context=context,
                )

                if impact.decision == ConditionalImpactEvaluator.BLOCKED:
                    continue

                if impact.decision == ConditionalImpactEvaluator.UNRESOLVED:
                    suspensions.append(
                        ConditionalImpactSuspension(
                            dependency_id=dependency.dependency_id,
                            unresolved_conditions=impact.unresolved_conditions,
                            matched_conditions=impact.matched_conditions,
                            evidence_ids=tuple(
                                sorted(set(dependency.evidence_ids))
                            ),
                        )
                    )
                    continue

                next_node = dependency.source_node_id

                if next_node in node_ids:
                    continue

                next_depth = depth + 1
                next_dependency_ids = (
                    dependency_ids
                    + (dependency.dependency_id,)
                )

                path = PropagationPath(
                    origin_dependency_id=origin_dependency_id,
                    node_ids=node_ids + (next_node,),
                    dependency_ids=next_dependency_ids,
                    evidence_ids=tuple(
                        sorted(
                            set(evidence_ids)
                            | (
                                set(dependency.evidence_ids)
                                if depth > 0
                                else set()
                            )
                        )
                    ),
                )

                paths.append(path)

                queue.append(
                    (
                        next_node,
                        origin_node,
                        origin_dependency_id,
                        change_type,
                        path.evidence_ids,
                        next_depth,
                        path.node_ids,
                        path.dependency_ids,
                    )
                )

            queue.sort(
                key=lambda item: (
                    item[5],
                    item[1],
                    item[2],
                    item[0],
                    item[6],
                    item[7],
                )
            )

        unique_paths = tuple(
            sorted(
                {
                    (
                        path.origin_dependency_id,
                        path.node_ids,
                        path.dependency_ids,
                        path.evidence_ids,
                    ): path
                    for path in paths
                }.values(),
                key=lambda path: (
                    path.node_ids[-1],
                    len(path.dependency_ids),
                    path.node_ids,
                    path.dependency_ids,
                    path.origin_dependency_id,
                ),
            )
        )

        grouped = {}

        for path in unique_paths:
            node_id = path.node_ids[-1]
            grouped.setdefault(node_id, []).append(path)

        affected_nodes = []

        affected_node_ids = set(grouped)

        def has_cycle() -> bool:
            """Detect cycles in the complete observed dependency graph."""
            visiting = set()
            visited = set()

            def visit(node_id: str) -> bool:
                if node_id in visiting:
                    return True

                if node_id in visited:
                    return False

                visiting.add(node_id)

                for dependency in self._engine.direct_dependencies(
                    node_id
                ):
                    if visit(dependency.target_node_id):
                        return True

                visiting.remove(node_id)
                visited.add(node_id)
                return False

            all_node_ids = sorted(
                {
                    dependency.source_node_id
                    for dependency in self._dependencies
                }
                | {
                    dependency.target_node_id
                    for dependency in self._dependencies
                }
            )

            return any(
                visit(node_id)
                for node_id in all_node_ids
                if node_id not in visited
            )

        cycle_present = has_cycle()

        if cycle_present:
            ordered_nodes = sorted(affected_node_ids)
        else:
            ordered_nodes = sorted(
                affected_node_ids,
                key=lambda node_id: (
                    min(
                        len(path.dependency_ids)
                        for path in grouped[node_id]
                    ),
                    node_id,
                ),
            )

        for node_id in ordered_nodes:
            node_paths = tuple(
                sorted(
                    grouped[node_id],
                    key=lambda path: (
                        len(path.dependency_ids),
                        path.origin_dependency_id,
                        path.node_ids,
                        path.dependency_ids,
                    ),
                )
            )

            affected_nodes.append(
                AffectedNode(
                    node_id=node_id,
                    depth=min(
                        len(path.dependency_ids)
                        for path in node_paths
                    ),
                    origin_dependency_ids=tuple(
                        sorted(
                            {
                                path.origin_dependency_id
                                for path in node_paths
                            }
                        )
                    ),
                    paths=node_paths,
                )
            )

        return PropagationResult(
            affected_nodes=tuple(affected_nodes),
            paths=unique_paths,
            suspensions=tuple(
                sorted(
                    set(suspensions),
                    key=lambda suspension: (
                        suspension.dependency_id,
                        suspension.unresolved_conditions,
                        suspension.matched_conditions,
                        suspension.evidence_ids,
                    ),
                )
            ),
        )

# ---------------------------------------------------------------------------
# 3C.5 — Affected Subgraph
# ---------------------------------------------------------------------------
#
# This layer is intentionally a projection/materialization step.
#
# It consumes PropagationResult produced by 3C.3/3C.4 and does NOT:
#   - perform traversal
#   - evaluate conditional impact
#   - recompute dependencies
#   - decide recompute/preserve
#   - calculate structural digests
#   - mutate dependency state
#
# Those responsibilities belong to other stages.
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class AffectedSubgraph:
    """
    Deterministic analytical projection of an affected dependency region.

    The subgraph is derived from an already-computed PropagationResult.

    dependency_ids:
        Dependency observations actually traversed by propagation.

    boundary_dependency_ids:
        Known dependency observations having exactly one endpoint inside
        the affected node set. Boundary edges are retained separately so
        they cannot be mistaken for propagated/internal edges.

    suspended_dependency_ids:
        Dependencies whose propagation was suspended by the conditional
        impact layer, e.g. UNRESOLVED conditions.

    This model is descriptive only. It does not make recomputation,
    preservation, risk, or migration decisions.
    """

    root_node_ids: tuple[str, ...]
    affected_nodes: tuple["AffectedNode", ...]
    dependency_ids: tuple[str, ...]
    boundary_dependency_ids: tuple[str, ...]
    suspended_dependency_ids: tuple[str, ...] = ()
    evidence_ids: tuple[str, ...] = ()
    max_depth: int = 0

    def __post_init__(self) -> None:
        if tuple(sorted(set(self.root_node_ids))) != self.root_node_ids:
            raise ValueError("root_node_ids must be sorted and unique")

        affected_ids = tuple(node.node_id for node in self.affected_nodes)

        if len(set(affected_ids)) != len(affected_ids):
            raise ValueError("affected_nodes must contain unique node IDs")

        if affected_ids != tuple(
            sorted(affected_ids, key=lambda node_id: node_id)
        ):
            raise ValueError("affected_nodes must be sorted by node_id")

        for value_name, values in (
            ("dependency_ids", self.dependency_ids),
            ("boundary_dependency_ids", self.boundary_dependency_ids),
            ("suspended_dependency_ids", self.suspended_dependency_ids),
            ("evidence_ids", self.evidence_ids),
        ):
            if tuple(sorted(set(values))) != values:
                raise ValueError(
                    f"{value_name} must be sorted and unique"
                )

        # A dependency may legitimately be both:
        #   1. represented/traversed by propagation, and
        #   2. a boundary edge crossing the affected-node set.
        #
        # Therefore dependency_ids and boundary_dependency_ids are NOT
        # mutually exclusive sets.

        if not set(self.root_node_ids).issubset(set(affected_ids)):
            raise ValueError(
                "root_node_ids must be a subset of affected node IDs"
            )

        if not set(self.suspended_dependency_ids).issubset(
            set(self.boundary_dependency_ids)
        ):
            raise ValueError(
                "suspended dependencies must be boundary dependencies"
            )

        if self.max_depth < 0:
            raise ValueError("max_depth must be >= 0")

        observed_max_depth = max(
            (node.depth for node in self.affected_nodes),
            default=0,
        )

        if self.max_depth != observed_max_depth:
            raise ValueError(
                "max_depth must equal the maximum affected-node depth"
            )

    @property
    def node_ids(self) -> tuple[str, ...]:
        """Canonical affected node IDs."""
        return tuple(node.node_id for node in self.affected_nodes)

    @property
    def node_count(self) -> int:
        return len(self.affected_nodes)

    @property
    def dependency_count(self) -> int:
        return len(self.dependency_ids)

    @property
    def boundary_count(self) -> int:
        return len(self.boundary_dependency_ids)

    @property
    def evidence_count(self) -> int:
        return len(self.evidence_ids)


def build_affected_subgraph(
    propagation: "PropagationResult",
    dependencies: Iterable[Dependency],
) -> AffectedSubgraph:
    """
    Materialize an AffectedSubgraph from an existing PropagationResult.

    The function performs no graph traversal.

    `dependencies` is the dependency observation universe available to the
    caller. For historical/removed-edge analysis, callers may provide the
    union of the relevant previous and current dependency observations.

    Determinism:
        - nodes are sorted by node_id
        - dependency IDs are sorted lexicographically
        - evidence IDs are sorted lexicographically
        - roots are sorted lexicographically
        - boundary edges are sorted lexicographically
    """

    affected_nodes = tuple(
        sorted(
            propagation.affected_nodes,
            key=lambda node: node.node_id,
        )
    )

    node_ids = {
        node.node_id
        for node in affected_nodes
    }

    root_node_ids = {
        path.node_ids[0]
        for path in propagation.paths
        if path.node_ids
    }

    dependency_ids = {
        dependency_id
        for path in propagation.paths
        for dependency_id in path.dependency_ids
    }

    evidence_ids = {
        evidence_id
        for path in propagation.paths
        for evidence_id in path.evidence_ids
    }

    dependency_map: Mapping[str, Dependency] = {
        dependency.dependency_id: dependency
        for dependency in dependencies
    }

    boundary_dependency_ids: set[str] = set()

    for dependency in dependency_map.values():
        source_inside = dependency.source_node_id in node_ids
        target_inside = dependency.target_node_id in node_ids

        # Exactly one endpoint is inside the affected region.
        if source_inside ^ target_inside:
            boundary_dependency_ids.add(
                dependency.dependency_id
            )

    suspended_dependency_ids = {
        suspension.dependency_id
        for suspension in propagation.suspensions
    }

    # Suspensions represent propagation boundaries. If the corresponding
    # dependency is available in the supplied observation universe, it must
    # be represented as a boundary edge.
    boundary_dependency_ids.update(
        suspended_dependency_ids
        & set(dependency_map)
    )

    max_depth = max(
        (node.depth for node in affected_nodes),
        default=0,
    )

    return AffectedSubgraph(
        root_node_ids=tuple(sorted(root_node_ids)),
        affected_nodes=affected_nodes,
        dependency_ids=tuple(sorted(dependency_ids)),
        boundary_dependency_ids=tuple(
            sorted(boundary_dependency_ids)
        ),
        suspended_dependency_ids=tuple(
            sorted(
                suspended_dependency_ids
                & boundary_dependency_ids
            )
        ),
        evidence_ids=tuple(sorted(evidence_ids)),
        max_depth=max_depth,
    )
