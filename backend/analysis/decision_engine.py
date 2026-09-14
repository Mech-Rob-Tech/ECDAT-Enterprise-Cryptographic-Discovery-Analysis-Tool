"""Deterministic decision engine for ECDAT v0.8."""

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
    calculate_decision,
    calculate_exposure_level,
    get_business_criticality,
    get_business_context_id,
    get_business_context_source,
    get_business_context_confidence,
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


def _best_migration(artifact: Any, migration_options: Optional[Iterable[Any]]) -> Optional[Any]:
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
    consequence = get_business_criticality(artifact, business_context=business_context)
    exposure = calculate_exposure_level(security, quantum)
    decision = calculate_decision(exposure, consequence, quantum, mosca, mosca_status)

    evidence_ids = _ids(artifact, "evidence_ids")
    recommendation_ids = _ids(artifact, "recommendation_ids")
    migration_ids = _ids(artifact, "migration_option_ids")
    dependency_list = [str(item) for item in (dependency_ids or [])]

    context_id = get_business_context_id(business_context)
    context_ids = [context_id] if context_id else []

    reasons: List[str] = [f"exposure={exposure}", f"business_consequence={consequence}"]
    if security:
        reasons.append(f"security_risk={security}")
    if quantum:
        reasons.append(f"quantum_risk={quantum}")
    if mosca:
        reasons.append(f"mosca_risk={mosca}")
    if mosca_status:
        reasons.append(f"mosca_status={mosca_status}")
    rationale = f"{decision}: " + "; ".join(reasons) + "."

    confidence = "high" if evidence_ids else "medium"
    context_confidence = get_business_context_confidence(business_context)
    if context_confidence:
        confidence = str(context_confidence).lower()

    provenance: Dict[str, Any] = {
        "source": "canonical-risk-matrix-risk-landscape",
        "policy_id": policy.policy_id,
        "policy_version": policy.version,
    }
    context_source = get_business_context_source(business_context)
    if context_source:
        provenance["business_context_source"] = context_source

    return DecisionRecord(
        decision_id=stable_id("decision", policy.version, artifact_id),
        artifact_id=artifact_id,
        application_id=application_id,
        decision=decision,
        policy_id=policy.policy_id,
        policy_version=policy.version,
        exposure_level=exposure,
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
        priority={DECISION_ACTION: "HIGH", DECISION_PRIORITIZE: "MEDIUM", DECISION_REVIEW: "LOW"}[decision_record.decision],
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
    decision = build_decision_record(artifact, business_context, migration_options, dependency_ids, policy)
    action = build_action_vector(artifact, decision, migration_options)
    return IntelligenceSnapshot(decision=decision, action=action)


def decision_to_dict(record: DecisionRecord) -> Dict[str, Any]:
    return asdict(record)


def action_to_dict(action: ActionVector) -> Dict[str, Any]:
    return asdict(action)


def snapshot_to_dict(snapshot: IntelligenceSnapshot) -> Dict[str, Any]:
    return asdict(snapshot)
