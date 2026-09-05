from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class ScanDiff:
    from_scan_id: str
    to_scan_id: str

    added_artifact_ids: List[str] = field(default_factory=list)
    removed_artifact_ids: List[str] = field(default_factory=list)
    changed_artifact_ids: List[str] = field(default_factory=list)

    risk_increased: List[Dict[str, Any]] = field(default_factory=list)
    risk_decreased: List[Dict[str, Any]] = field(default_factory=list)

    mosca_changed: List[Dict[str, Any]] = field(default_factory=list)

    relationship_changed: List[Dict[str, Any]] = field(default_factory=list)
    recommendation_changed: List[Dict[str, Any]] = field(default_factory=list)
    migration_changed: List[Dict[str, Any]] = field(default_factory=list)

    business_context_changed: List[Dict[str, Any]] = field(default_factory=list)

    evidence_relocated: List[Dict[str, Any]] = field(default_factory=list)
    evidence_changed: List[Dict[str, Any]] = field(default_factory=list)

    summary: Dict[str, Any] = field(default_factory=dict)
    methodology: Dict[str, Any] = field(default_factory=dict)
