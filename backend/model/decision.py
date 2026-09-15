"""Canonical decision-layer models for ECDAT v0.8."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


DECISION_REVIEW = "REVIEW"
DECISION_PRIORITIZE = "PRIORITIZE"
DECISION_ACTION = "ACTION"


@dataclass(frozen=True)
class DecisionPolicy:
    """Immutable rule definition used by the decision engine."""

    policy_id: str
    version: str
    minimum_exposure_score: int = 3
    minimum_consequence_score: int = 3
    action_rule: str = (
        "ACTION when exposure or consequence is CRITICAL, "
        "or both are HIGH, or MOSCA indicates an AT_RISK "
        "high/critical condition."
    )
    priority_rule: str = (
        "PRIORITIZE when either exposure or consequence is HIGH, "
        "or when quantum/MOSCA pressure is HIGH."
    )
    review_rule: str = (
        "REVIEW when no higher-priority decision rule applies."
    )


@dataclass(frozen=True)
class DecisionRecord:
    """Deterministic decision for one canonical artifact."""

    decision_id: str
    artifact_id: str
    application_id: Optional[str]
    decision: str
    policy_id: str
    policy_version: str

    exposure_level: str
    consequence_level: str
    security_risk: Optional[str]
    quantum_risk: Optional[str]
    mosca_risk: Optional[str]
    mosca_status: Optional[str]

    rationale: str
    evidence_ids: List[str] = field(default_factory=list)
    dependency_ids: List[str] = field(default_factory=list)
    business_context_ids: List[str] = field(default_factory=list)
    recommendation_ids: List[str] = field(default_factory=list)
    migration_option_ids: List[str] = field(default_factory=list)

    blockers: List[str] = field(default_factory=list)
    confidence: str = "medium"

    provenance: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ActionVector:
    """Executable projection of an ECDAT decision."""

    action: str
    priority: str
    artifact_id: str
    application_id: Optional[str]
    decision_id: str

    target: Optional[str] = None
    migration_option_id: Optional[str] = None

    prerequisites: List[str] = field(default_factory=list)
    blockers: List[str] = field(default_factory=list)
    evidence_ids: List[str] = field(default_factory=list)

    verification_required: bool = False
    rationale: str = ""
    provenance: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class IntelligenceSnapshot:
    """Compact deterministic payload for the Workbench decision view."""

    decision: DecisionRecord
    action: ActionVector
