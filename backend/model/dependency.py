from dataclasses import dataclass, field
from typing import List, Optional


@dataclass(frozen=True)
class Dependency:
    """Canonical observed dependency fact.

    Dependencies are observations, not transitive conclusions. Indirect
    relationships are derived by the dependency engine and retain the
    observed edge IDs that justify them.
    """

    dependency_id: str
    source_node_id: str
    target_node_id: str
    relationship_type: str
    confidence: str = "unknown"
    directness: str = "direct"
    evidence_ids: List[str] = field(default_factory=list)
    protocol: Optional[str] = None
    purpose: Optional[str] = None
    effective_from: Optional[str] = None
    effective_until: Optional[str] = None
    observed_at: Optional[str] = None
    scan_id: Optional[str] = None
    source_type: str = "unknown"
    source_reference: Optional[str] = None
    record_version: int = 1

    def __post_init__(self) -> None:
        if not self.dependency_id:
            raise ValueError("dependency_id is required")
        if not self.source_node_id:
            raise ValueError("source_node_id is required")
        if not self.target_node_id:
            raise ValueError("target_node_id is required")
        if not self.relationship_type:
            raise ValueError("relationship_type is required")
        if self.directness not in {"direct", "indirect"}:
            raise ValueError("directness must be direct or indirect")
        if self.record_version < 1:
            raise ValueError("record_version must be >= 1")
