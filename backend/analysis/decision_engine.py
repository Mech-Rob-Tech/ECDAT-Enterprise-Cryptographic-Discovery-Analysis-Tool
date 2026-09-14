"""Deterministic decision engine for ECDAT v0.8.

This module consumes existing Risk Matrix / Risk Landscape outputs and
canonical migration/recommendation data. It deliberately does not create
a second risk model.
"""

from __future__ import annotations

from dataclasses import asdict
from typing import Any, Dict, Iterable, List, Optional

from model.canonical import stable_id
from model.decision import (
    ActionVector,
    DecisionPolicy,
    DecisionRecord,
    IntelligenceSnapshot,
    DECISION_ACTION,
    DECISION_PRIORITIZE,
    DECISION_REVIEW,
)
from analysis.risk_matrix import (
    RISK_SCORE,
    get_business_criticality,
    get_business_context,
    build_business_context_lookup,
    get_security_risk,
    get_quantum_risk,
    get_mosca_risk,
    get_mosca_status,
    get_artifact_application_id,
)


DEFAULT_POLICY = DecisionPolicy(
    policy_id="ecdAT-decision-policy",
    version="0.8",
)


def _get(value: Any, key: str, default: Any = None) -> Any:
    if value is None:
        return default
    if isinstance(value, dict):
        return value.get(key, default)
    return getattr(value, key, default)


def _ids(value: Any, key: str) -> List[str]:
    result = _get(value, key, []) or []
    if isinstance(result, (list, tuple, set)):
        return [str(item) for item in result if item is not None]
    return []


def _decision(
    exposure_levels: Iterable[Optional[str]],
    consequence: str,
    mosca_risk: Optional[str],
    mosca_status: Optional[str],
) -> str:
    levels = [level for level in exposure_levels if level]
    if (
        "CRITICAL" in levels
        or consequence == "CRITICAL"
        or ("HIGH" in levels and consequence == "HIGH")
        or (
            mosca_status == "AT_RISK"
            and mosca_risk in {"HIGH", "CRITICAL"}
        )
    ):
        return DECISION_ACTION

    if (
        "HIGH" in levels
        or consequence == "HIGH"
        or mosca_risk == "HIGH"
    ):
        return DECISION_PRIORITIZE

    return DECISION_REVIEW


def _priority(decision: str) -> str:
    return {
        DECISION_ACTION: "HIGH",
        DECISION_PRIORITIZE: "MEDIUM",
        DECISION_REVIEW: "LOW",
    }[decision]


def _best_migration(
    artifact: Any,
    migration_options: Optional[Iterable[Any]],
) -> Optional[Any]:
    ids = set(_ids(artifact, "migration_option_ids"))
    if not ids or migration_options is None:
        return None

    candidates = [
        option for option in migration_options
        if str(_get(option, "option_id")) in ids
    ]
    if not candidates:
        return None

    rank = {"high": 0, "medium": 1, "low": 2}
    return sorted(
        candidates,
        key=lambda item: (
            rank.get(str(_get(item, "confidence", "medium")).lower(), 1),
            str(_get(item, "option_id", "")),
        ),
    )[0]


def build_decision_record(
    artifact: Any,
    business_context: Any = None,
    migration_options: Optional[Iterable[Any]] = None,
    dependency_ids: Optional[Iterable[str]] = None,
    policy: DecisionPolicy = DEFAULT_POLICY,
) -> DecisionRecord:
    """Build one deterministic decision record from canonical inputs."""

    artifact_id = str(_get(artifact, "artifact_id", "unknown"))
    application_id = get_artifact_application_id(artifact)
    security = get_security_risk(artifact)
    quantum = get_quantum_risk(artifact)
    mosca = get_mosca_risk(artifact)
    mosca_status = get_mosca_status(artifact)
    consequence = get_business_criticality(
        artifact,
        business_context=business_context,
    )

    decision = _decision(
        (security, quantum),
        consequence,
        mosca,
        mosca_status,
    )

    evidence_ids = _ids(artifact, "evidence_ids")
    recommendation_ids = _ids(artifact, "recommendation_ids")
    migration_ids = _ids(artifact, "migration_option_ids")
    dependency_list = [str(item) for item in (dependency_ids or [])]

    context_id = _get(business_context, "business_context_id")
    context_ids = [str(context_id)] if context_id is not None else []

    reasons: List[str] = []
    if security in {"HIGH", "CRITICAL"}:
        reasons.append(f"security risk is {security}")
    if quantum in {"HIGH", "CRITICAL"}:
        reasons.append(f"quantum risk is {quantum}")
    if mosca_status == "AT_RISK":
        reasons.append(f"MOSCA is AT_RISK with {mosca or 'LOW'} risk")
    if consequence in {"HIGH", "CRITICAL"}:
        reasons.append(f"business consequence is {consequence}")
    if not reasons:
        reasons.append("no higher-priority analytical condition is present")

    rationale = f"{decision}: " + "; ".join(reasons) + "."

    confidence = "high" if evidence_ids else "medium"
    if business_context is not None:
        context_confidence = str(_get(business_context, "confidence", ""))
        if context_confidence:
            confidence = context_confidence.lower()

    provenance: Dict[str, Any] = {
        "source": "canonical-risk-matrix-risk-landscape",
        "policy_id": policy.policy_id,
        "policy_version": policy.version,
    }

    decision_id = stable_id(
        "decision",
        policy.version,
        artifact_id,
    )

    return DecisionRecord(
        decision_id=decision_id,
        artifact_id=artifact_id,
        application_id=application_id,
        decision=decision,
        policy_id=policy.policy_id,
        policy_version=policy.version,
        exposure_level=max(
            (security, quantum),
            key=lambda item: RISK_SCORE.get(item or "LOW", 1),
        ),
        consequence_level=consequence,
        security_risk=security,
        quantum_risk=quantum,
        mosca_risk=mosca,
        mosca_status=mosca_status,
        rationale=rationale,
        evidence_ids=evidence_ids,
        dependency_ids=dependency_list,
        business_context_ids=context_ids,
        recommendation_ids=recommendation_ids,
        migration_option_ids=migration_ids,
        blockers=[],
        confidence=confidence,
        provenance=provenance,
    )


def build_action_vector(
    artifact: Any,
    decision_record: DecisionRecord,
    migration_options: Optional[Iterable[Any]] = None,
) -> ActionVector:
    """Project a decision and existing migration option into an action."""

    option = _best_migration(artifact, migration_options)
    option_id = _get(option, "option_id") if option is not None else None
    target = _get(option, "target_algorithm", _get(option, "name")) if option is not None else None
    prerequisites = _ids(option, "prerequisites") if option is not None else []
    constraints = _ids(option, "constraints") if option is not None else []

    if decision_record.decision == DECISION_ACTION:
        action = "MIGRATE" if option is not None else "REMEDIATE"
    elif decision_record.decision == DECISION_PRIORITIZE:
        action = "PLAN_MIGRATION" if option is not None else "ASSESS"
    else:
        action = "MONITOR"

    return ActionVector(
        action=action,
        priority=_priority(decision_record.decision),
        artifact_id=decision_record.artifact_id,
        application_id=decision_record.application_id,
        decision_id=decision_record.decision_id,
        target=str(target) if target is not None else None,
        migration_option_id=str(option_id) if option_id is not None else None,
        prerequisites=prerequisites,
        blockers=constraints,
        evidence_ids=list(decision_record.evidence_ids),
        verification_required=action in {"MIGRATE", "REMEDIATE"},
        rationale=decision_record.rationale,
        provenance=dict(decision_record.provenance),
    )


def build_intelligence_snapshot(
    artifact: Any,
    business_context: Any = None,
    migration_options: Optional[Iterable[Any]] = None,
    dependency_ids: Optional[Iterable[str]] = None,
    policy: DecisionPolicy = DEFAULT_POLICY,
) -> IntelligenceSnapshot:
    """Build the Workbench-ready decision snapshot."""
    decision = build_decision_record(
        artifact=artifact,
        business_context=business_context,
        migration_options=migration_options,
        dependency_ids=dependency_ids,
        policy=policy,
    )
    action = build_action_vector(
        artifact=artifact,
        decision_record=decision,
        migration_options=migration_options,
    )
    return IntelligenceSnapshot(decision=decision, action=action)


def decision_to_dict(record: DecisionRecord) -> Dict[str, Any]:
    return asdict(record)


def action_to_dict(action: ActionVector) -> Dict[str, Any]:
    return asdict(action)


def snapshot_to_dict(snapshot: IntelligenceSnapshot) -> Dict[str, Any]:
    return asdict(snapshot)
