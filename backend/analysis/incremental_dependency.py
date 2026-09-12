"""Deterministic incremental dependency-processing primitives."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, Tuple


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
    ) -> PropagationResult:
        if max_depth is not None and max_depth < 1:
            return PropagationResult((), ())

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
        )
