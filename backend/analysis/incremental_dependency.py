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
