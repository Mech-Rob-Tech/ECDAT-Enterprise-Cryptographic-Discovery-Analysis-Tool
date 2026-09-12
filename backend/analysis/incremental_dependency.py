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
