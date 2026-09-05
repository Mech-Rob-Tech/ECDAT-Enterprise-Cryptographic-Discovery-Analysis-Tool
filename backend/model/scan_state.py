from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ScanState:
    """
    Immutable analytical snapshot of an ECDAT scan.

    A historical scan must preserve enough canonical information
    to reproduce analytical comparisons without rescanning the
    original repository.
    """

    scan_id: str

    # Scan identity / metadata
    application_ids: List[str] = field(default_factory=list)
    generated_at: Optional[str] = None
    target: Optional[str] = None

    # Canonical inventory snapshot
    artifact_ids: List[str] = field(default_factory=list)
    canonical_artifacts: List[Dict[str, Any]] = field(default_factory=list)

    # Supporting canonical evidence/context
    evidence: List[Dict[str, Any]] = field(default_factory=list)
    business_contexts: List[Dict[str, Any]] = field(default_factory=list)

    # Graph snapshot
    relationships: List[Dict[str, Any]] = field(default_factory=list)

    # Analytical projections
    risk_landscape: Dict[str, Any] = field(default_factory=dict)

    # Original scan summary and metadata
    summary: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
