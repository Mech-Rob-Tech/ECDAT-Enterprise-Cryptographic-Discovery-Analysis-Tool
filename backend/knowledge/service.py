from __future__ import annotations

from typing import Optional

from knowledge.registry import get_registry
from knowledge.resolver import resolve_algorithm
from knowledge.schema import KnowledgeRegistry, KnowledgeResolution


class KnowledgeService:
    """
    Application-facing service boundary.

    Consumers should depend on this interface instead of importing
    registry internals.
    """

    def __init__(
        self,
        registry: Optional[KnowledgeRegistry] = None,
    ):
        self.registry = registry or get_registry()

    @property
    def version(self) -> str:
        return self.registry.manifest.knowledge_version

    @property
    def integrity_hash(self) -> str:
        return self.registry.manifest.registry_hash

    def resolve(
        self,
        query: str,
        purpose: Optional[str] = None,
        as_of: Optional[str] = None,
        target_type: Optional[str] = None,
        target_name: Optional[str] = None,
        target_version: Optional[str] = None,
    ) -> KnowledgeResolution:
        return resolve_algorithm(
            registry=self.registry,
            query=query,
            purpose=purpose,
            as_of=as_of,
            target_type=target_type,
            target_name=target_name,
            target_version=target_version,
        )

    def algorithms(self):
        return self.registry.algorithms

    def standards(self):
        return self.registry.standards

    def migrations(self):
        return self.registry.migrations

    def compatibility(self):
        return self.registry.compatibility

    def conflicts(self):
        return self.registry.conflicts
