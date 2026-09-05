from __future__ import annotations

from typing import Optional

from knowledge.freshness import (
    registry_freshness,
)
from knowledge.registry import get_registry
from knowledge.resolver import resolve_algorithm
from knowledge.schema import (
    KnowledgeRegistry,
    KnowledgeResolution,
)
from knowledge.temporal import (
    snapshot_state,
)


class KnowledgeService:
    """
    Stable application-facing boundary for ECDAT knowledge.

    Consumers should not depend on registry implementation details.
    """

    def __init__(
        self,
        registry: Optional[KnowledgeRegistry] = None,
    ):
        self.registry = (
            registry or get_registry()
        )

    @property
    def version(self) -> str:
        return (
            self.registry.manifest
            .knowledge_version
        )

    @property
    def integrity_hash(self) -> str:
        return (
            self.registry.manifest
            .registry_hash
        )

    def snapshot(self) -> dict:
        return {
            "knowledge_version": self.version,
            "knowledge_hash": self.integrity_hash,
            "generated_at": (
                self.registry.manifest
                .generated_at
            ),
        }

    def freshness(
        self,
        *,
        max_age_days: int = 180,
        as_of: Optional[str] = None,
    ) -> dict:
        return registry_freshness(
            self.registry.provenance,
            max_age_days=max_age_days,
            as_of=as_of,
        )

    def snapshot_state(
        self,
        knowledge_version: Optional[str],
        knowledge_hash: Optional[str],
    ) -> str:
        return snapshot_state(
            snapshot_version=knowledge_version,
            snapshot_hash=knowledge_hash,
            current_version=self.version,
            current_hash=self.integrity_hash,
        )

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
