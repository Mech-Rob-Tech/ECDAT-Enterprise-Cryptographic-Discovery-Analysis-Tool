"""Dependency repository contract for ECDAT v0.6."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional, Sequence, Tuple

from model.dependency import Dependency


class DependencyRepository(ABC):
    """Persistence contract for observed dependency facts."""

    @abstractmethod
    def list_dependencies(
        self,
        *,
        scan_version_id: Optional[str] = None,
        source_node_id: Optional[str] = None,
        target_node_id: Optional[str] = None,
        relationship_type: Optional[str] = None,
    ) -> Tuple[Dependency, ...]:
        """Return deterministic observed dependency facts."""

    @abstractmethod
    def get_dependency(
        self,
        dependency_id: str,
    ) -> Optional[Dependency]:
        """Return one dependency or None when it does not exist."""

    @abstractmethod
    def save_dependencies(
        self,
        dependencies: Sequence[Dependency],
        *,
        scan_version_id: str,
    ) -> None:
        """Persist observed dependency facts for one scan version."""

    @abstractmethod
    def delete_scan_version_dependencies(
        self,
        scan_version_id: str,
    ) -> None:
        """Delete dependency observations for one scan version."""
