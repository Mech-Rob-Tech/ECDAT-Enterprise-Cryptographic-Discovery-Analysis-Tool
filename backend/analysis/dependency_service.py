"""Application service for ECDAT dependency intelligence.

This module provides the stable domain boundary between HTTP/API consumers
and the dependency graph engine. It contains no transport logic and does not
persist derived graph state.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, Sequence, Tuple

from analysis.dependency_engine import (
    DependencyClosure,
    DependencyEngine,
    DependencyPath,
)
from model.dependency import Dependency


@dataclass(frozen=True)
class DependencyNotFoundError(Exception):
    """Raised when a requested dependency does not exist."""

    dependency_id: str


class DependencyService:
    """Deterministic dependency-intelligence application service."""

    def __init__(
        self,
        dependencies: Sequence[Dependency],
    ) -> None:
        self._dependencies: Tuple[Dependency, ...] = tuple(
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

        self._by_id: Dict[str, Dependency] = {
            item.dependency_id: item
            for item in self._dependencies
        }

        self._engine = DependencyEngine(self._dependencies)

    def list_dependencies(
        self,
        *,
        source_node_id: Optional[str] = None,
        target_node_id: Optional[str] = None,
        relationship_type: Optional[str] = None,
    ) -> Tuple[Dependency, ...]:
        """Return deterministic observed dependency facts."""

        results = self._dependencies

        if source_node_id is not None:
            results = tuple(
                item
                for item in results
                if item.source_node_id == source_node_id
            )

        if target_node_id is not None:
            results = tuple(
                item
                for item in results
                if item.target_node_id == target_node_id
            )

        if relationship_type is not None:
            results = tuple(
                item
                for item in results
                if item.relationship_type == relationship_type
            )

        return results

    def get_dependency(
        self,
        dependency_id: str,
    ) -> Dependency:
        """Return one observed dependency by stable identifier."""

        dependency = self._by_id.get(dependency_id)

        if dependency is None:
            raise DependencyNotFoundError(dependency_id)

        return dependency

    def direct_dependencies(
        self,
        node_id: str,
    ) -> Tuple[Dependency, ...]:
        """Return directly observed outgoing dependencies."""

        return self._engine.direct_dependencies(node_id)

    def closure(
        self,
        node_id: str,
        *,
        external_node_ids: Sequence[str] = (),
    ) -> DependencyClosure:
        """Calculate deterministic dependency closure from a node."""

        return self._engine.closure(
            node_id,
            external_node_ids=external_node_ids,
        )

    def paths(
        self,
        source_node_id: str,
        target_node_id: str,
        *,
        max_depth: Optional[int] = None,
    ) -> Tuple[DependencyPath, ...]:
        """Return deterministic observed paths to a target node."""

        if max_depth is not None and max_depth < 1:
            return ()

        return tuple(
            path
            for path in self._engine.paths(
                source_node_id,
                max_depth=max_depth,
            )
            if path.node_ids[-1] == target_node_id
        )

    def migration_precedence(
        self,
        root_node_id: str,
    ) -> Tuple[Tuple[str, ...], ...]:
        """Calculate technical migration ordering constraints."""

        return self._engine.migration_precedence(root_node_id)
