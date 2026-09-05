"""
ECDAT Risk Landscape analytical projection.

The Risk Landscape is a synthesis layer over the canonical ECDAT
model.

It does NOT create a second risk model and does NOT replace:
    - security-risk assessment
    - quantum-risk assessment
    - MOSCA analysis
    - migration recommendations
    - business-context modelling

Instead, it projects those existing canonical assessments into
decision-oriented views.

Projection levels:
    1. Artifact exposure
    2. Application exposure
    3. Portfolio exposure

The projection is deterministic and explainable.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, Iterable, List, Optional


RISK_LEVELS = (
    "LOW",
    "MEDIUM",
    "HIGH",
    "CRITICAL",
)

RISK_SCORE = {
    "LOW": 1,
    "MEDIUM": 2,
    "HIGH": 3,
    "CRITICAL": 4,
}

DECISION_REVIEW = "REVIEW"
DECISION_PRIORITIZE = "PRIORITIZE"
DECISION_ACTION = "ACTION"


@dataclass(frozen=True)
class RiskLandscapePoint:
    """
    One artifact projected into the Risk Landscape.
    """

    artifact_id: str
    application_id: Optional[str]
    algorithm: str

    security_risk: Optional[str]
    quantum_risk: Optional[str]
    mosca_risk: Optional[str]
    mosca_status: Optional[str]

    business_consequence: str
    business_context_id: Optional[str]
    business_context_source: Optional[str]
    business_context_confidence: Optional[str]

    evidence_count: int
    migration_option_count: int

    decision: str
    priority_score: int

    migration_required: bool

    explanation: str


@dataclass(frozen=True)
class ApplicationRiskLandscape:
    """
    Aggregated Risk Landscape view for one application.
    """

    application_id: str
    artifact_count: int

    highest_security_risk: str
    highest_quantum_risk: str
    highest_mosca_risk: str
    mosca_at_risk_count: int

    business_consequence: str
    business_context_id: Optional[str]
    business_context_source: Optional[str]
    business_context_confidence: Optional[str]

    evidence_count: int
    migration_required_count: int

    decision: str
    priority_score: int

    artifact_ids: List[str]


def _get(value: Any, key: str, default: Any = None) -> Any:
    """
    Safely read a dictionary or object field.
    """

    if value is None:
        return default

    if isinstance(value, dict):
        return value.get(key, default)

    return getattr(value, key, default)


def _normalize_level(
    value: Any,
    default: str = "LOW",
) -> str:
    """
    Normalize a risk/criticality value.
    """

    if value is None:
        return default

    normalized = str(value).strip().upper()

    if normalized in RISK_SCORE:
        return normalized

    return default


def _artifact_id(artifact: Any) -> str:
    return str(
        _get(
            artifact,
            "artifact_id",
            _get(artifact, "id", "unknown"),
        )
    )


def _application_id(artifact: Any) -> Optional[str]:
    value = _get(artifact, "application_id")

    if value is None:
        return None

    return str(value)


def _algorithm(artifact: Any) -> str:
    value = _get(artifact, "algorithm", "UNKNOWN")

    if isinstance(value, str):
        return value

    name = _get(value, "name")

    if name is not None:
        return str(name)

    return "UNKNOWN"


def _risk_level(
    artifact: Any,
    risk_name: str,
) -> Optional[str]:
    """
    Extract a nested risk level from the canonical artifact.
    """

    risk = _get(artifact, "risk")

    value = _get(risk, risk_name)

    if value is None:
        return None

    level = _get(value, "level")

    if level is None and isinstance(value, str):
        level = value

    if level is None:
        return None

    return _normalize_level(level)


def _mosca_values(
    artifact: Any,
) -> tuple[Optional[str], Optional[str]]:
    """
    Extract MOSCA risk and status.
    """

    mosca = _get(artifact, "mosca")

    if mosca is None:
        return None, None

    risk = _get(mosca, "risk")
    status = _get(mosca, "status")

    if not isinstance(risk, str):
        risk = _get(risk, "level")

    if risk is not None:
        risk = _normalize_level(risk)

    if status is not None:
        status = str(status).strip().upper()

    return risk, status


def _business_context_lookup(
    business_contexts: Iterable[Any],
) -> Dict[str, Any]:
    """
    Map application_id -> BusinessContext.

    Exact application matching is the authoritative lookup strategy.
    """

    lookup: Dict[str, Any] = {}

    for context in business_contexts:
        application_id = _get(context, "application_id")

        if application_id is None:
            continue

        lookup[str(application_id)] = context

    return lookup


def _business_consequence(
    context: Any,
    artifact: Any,
) -> str:
    """
    Determine business consequence.

    Precedence:
        1. BusinessContext dimensions
        2. artifact.business_criticality
        3. artifact.business_consequence
        4. MEDIUM
    """

    if context is not None:
        values = []

        for field_name in (
            "operational_criticality",
            "financial_impact",
            "regulatory_exposure",
            "customer_impact",
        ):
            value = _get(context, field_name)

            if value is not None:
                values.append(
                    _normalize_level(value)
                )

        if values:
            return max(
                values,
                key=lambda value: RISK_SCORE[value],
            )

    explicit = _get(
        artifact,
        "business_criticality",
    )

    if explicit is not None:
        return _normalize_level(
            explicit,
            default="MEDIUM",
        )

    explicit = _get(
        artifact,
        "business_consequence",
    )

    if explicit is not None:
        return _normalize_level(
            explicit,
            default="MEDIUM",
        )

    return "MEDIUM"


def _evidence_count(artifact: Any) -> int:
    evidence_ids = _get(
        artifact,
        "evidence_ids",
        [],
    )

    if evidence_ids is None:
        return 0

    if isinstance(evidence_ids, (list, tuple, set)):
        return len(evidence_ids)

    return 0


def _migration_option_count(
    artifact: Any,
) -> int:
    option_ids = _get(
        artifact,
        "migration_option_ids",
        [],
    )

    if option_ids is None:
        return 0

    if isinstance(option_ids, (list, tuple, set)):
        return len(option_ids)

    return 0


def _priority_score(
    security_risk: Optional[str],
    quantum_risk: Optional[str],
    mosca_risk: Optional[str],
    mosca_status: Optional[str],
    business_consequence: str,
    migration_option_count: int,
    evidence_count: int,
) -> int:
    """
    Produce a deterministic prioritization score.

    This is an internal ranking mechanism, not a universal
    enterprise risk standard.
    """

    security_score = RISK_SCORE.get(
        security_risk or "LOW",
        1,
    )

    quantum_score = RISK_SCORE.get(
        quantum_risk or "LOW",
        1,
    )

    mosca_score = RISK_SCORE.get(
        mosca_risk or "LOW",
        1,
    )

    business_score = RISK_SCORE.get(
        business_consequence,
        2,
    )

    migration_score = 2 if migration_option_count > 0 else 0
    evidence_score = 2 if evidence_count > 0 else 0

    score = (
        security_score
        + quantum_score
        + mosca_score
        + business_score
        + migration_score
        + evidence_score
    )

    if mosca_status == "AT_RISK":
        score += 2

    return score


def _decision_from_point(
    security_risk: Optional[str],
    quantum_risk: Optional[str],
    mosca_risk: Optional[str],
    mosca_status: Optional[str],
    business_consequence: str,
) -> str:
    """
    Derive a deterministic decision zone.
    """

    exposure_levels = [
        level
        for level in (
            security_risk,
            quantum_risk,
        )
        if level is not None
    ]

    if (
        "CRITICAL" in exposure_levels
        or business_consequence == "CRITICAL"
        or (
            "HIGH" in exposure_levels
            and business_consequence == "HIGH"
        )
        or (
            mosca_status == "AT_RISK"
            and mosca_risk in {
                "HIGH",
                "CRITICAL",
            }
        )
    ):
        return DECISION_ACTION

    if (
        "HIGH" in exposure_levels
        or business_consequence == "HIGH"
        or quantum_risk == "HIGH"
        or mosca_risk == "HIGH"
    ):
        return DECISION_PRIORITIZE

    return DECISION_REVIEW


def _explanation(
    decision: str,
    security_risk: Optional[str],
    quantum_risk: Optional[str],
    mosca_risk: Optional[str],
    mosca_status: Optional[str],
    business_consequence: str,
    evidence_count: int,
    migration_option_count: int,
) -> str:
    reasons: List[str] = []

    if security_risk in {
        "HIGH",
        "CRITICAL",
    }:
        reasons.append(
            f"security risk is {security_risk}"
        )

    if quantum_risk in {
        "HIGH",
        "CRITICAL",
    }:
        reasons.append(
            f"quantum risk is {quantum_risk}"
        )

    if (
        mosca_status == "AT_RISK"
        and mosca_risk is not None
    ):
        reasons.append(
            f"MOSCA is AT_RISK with {mosca_risk} risk"
        )

    if business_consequence in {
        "HIGH",
        "CRITICAL",
    }:
        reasons.append(
            f"business consequence is {business_consequence}"
        )

    if migration_option_count > 0:
        reasons.append(
            f"{migration_option_count} migration option(s) available"
        )

    if evidence_count == 0:
        reasons.append(
            "evidence coverage is currently unresolved"
        )

    if not reasons:
        reasons.append(
            "no higher-priority analytical condition is present"
        )

    return (
        f"{decision}: "
        + "; ".join(reasons)
        + "."
    )


def build_risk_landscape_point(
    artifact: Any,
    business_context: Any = None,
) -> RiskLandscapePoint:
    """
    Project one canonical artifact into the Risk Landscape.
    """

    artifact_id = _artifact_id(artifact)
    application_id = _application_id(artifact)
    algorithm = _algorithm(artifact)

    security_risk = _risk_level(
        artifact,
        "security",
    )

    quantum_risk = _risk_level(
        artifact,
        "quantum",
    )

    mosca_risk, mosca_status = _mosca_values(
        artifact
    )

    consequence = _business_consequence(
        business_context,
        artifact,
    )

    evidence_count = _evidence_count(
        artifact
    )

    migration_option_count = _migration_option_count(
        artifact
    )

    decision = _decision_from_point(
        security_risk=security_risk,
        quantum_risk=quantum_risk,
        mosca_risk=mosca_risk,
        mosca_status=mosca_status,
        business_consequence=consequence,
    )

    priority_score = _priority_score(
        security_risk=security_risk,
        quantum_risk=quantum_risk,
        mosca_risk=mosca_risk,
        mosca_status=mosca_status,
        business_consequence=consequence,
        migration_option_count=migration_option_count,
        evidence_count=evidence_count,
    )

    migration_required = (
        migration_option_count > 0
        and decision != DECISION_REVIEW
    )

    context_id = (
        _get(business_context, "context_id")
        if business_context is not None
        else None
    )

    context_source = (
        _get(business_context, "source")
        if business_context is not None
        else None
    )

    context_confidence = (
        _get(business_context, "confidence")
        if business_context is not None
        else None
    )

    return RiskLandscapePoint(
        artifact_id=artifact_id,
        application_id=application_id,
        algorithm=algorithm,
        security_risk=security_risk,
        quantum_risk=quantum_risk,
        mosca_risk=mosca_risk,
        mosca_status=mosca_status,
        business_consequence=consequence,
        business_context_id=(
            str(context_id)
            if context_id is not None
            else None
        ),
        business_context_source=(
            str(context_source)
            if context_source is not None
            else None
        ),
        business_context_confidence=(
            str(context_confidence)
            if context_confidence is not None
            else None
        ),
        evidence_count=evidence_count,
        migration_option_count=migration_option_count,
        decision=decision,
        priority_score=priority_score,
        migration_required=migration_required,
        explanation=_explanation(
            decision=decision,
            security_risk=security_risk,
            quantum_risk=quantum_risk,
            mosca_risk=mosca_risk,
            mosca_status=mosca_status,
            business_consequence=consequence,
            evidence_count=evidence_count,
            migration_option_count=migration_option_count,
        ),
    )


def _highest_risk(
    values: Iterable[Optional[str]],
) -> str:
    normalized = [
        _normalize_level(value)
        for value in values
        if value is not None
    ]

    if not normalized:
        return "LOW"

    return max(
        normalized,
        key=lambda value: RISK_SCORE[value],
    )


def _highest_decision(
    decisions: Iterable[str],
) -> str:
    ranking = {
        DECISION_REVIEW: 1,
        DECISION_PRIORITIZE: 2,
        DECISION_ACTION: 3,
    }

    decisions = list(decisions)

    if not decisions:
        return DECISION_REVIEW

    return max(
        decisions,
        key=lambda decision: ranking.get(
            decision,
            0,
        ),
    )


def build_application_risk_landscape(
    points: Iterable[RiskLandscapePoint],
) -> List[ApplicationRiskLandscape]:
    """
    Aggregate artifact-level Risk Landscape points by application.
    """

    grouped: Dict[str, List[RiskLandscapePoint]] = {}

    for point in points:
        if point.application_id is None:
            continue

        grouped.setdefault(
            point.application_id,
            [],
        ).append(point)

    applications: List[ApplicationRiskLandscape] = []

    for application_id, artifact_points in grouped.items():
        highest_business = _highest_risk(
            point.business_consequence
            for point in artifact_points
        )

        contexts = [
            point
            for point in artifact_points
            if point.business_context_id is not None
        ]

        context = (
            max(
                contexts,
                key=lambda point: (
                    RISK_SCORE.get(
                        point.business_consequence,
                        1,
                    ),
                    point.business_context_confidence == "high",
                ),
            )
            if contexts
            else None
        )

        priority_score = max(
            point.priority_score
            for point in artifact_points
        )

        applications.append(
            ApplicationRiskLandscape(
                application_id=application_id,
                artifact_count=len(artifact_points),
                highest_security_risk=_highest_risk(
                    point.security_risk
                    for point in artifact_points
                ),
                highest_quantum_risk=_highest_risk(
                    point.quantum_risk
                    for point in artifact_points
                ),
                highest_mosca_risk=_highest_risk(
                    point.mosca_risk
                    for point in artifact_points
                ),
                mosca_at_risk_count=sum(
                    point.mosca_status == "AT_RISK"
                    for point in artifact_points
                ),
                business_consequence=highest_business,
                business_context_id=(
                    context.business_context_id
                    if context
                    else None
                ),
                business_context_source=(
                    context.business_context_source
                    if context
                    else None
                ),
                business_context_confidence=(
                    context.business_context_confidence
                    if context
                    else None
                ),
                evidence_count=sum(
                    point.evidence_count
                    for point in artifact_points
                ),
                migration_required_count=sum(
                    point.migration_required
                    for point in artifact_points
                ),
                decision=_highest_decision(
                    point.decision
                    for point in artifact_points
                ),
                priority_score=priority_score,
                artifact_ids=[
                    point.artifact_id
                    for point in artifact_points
                ],
            )
        )

    applications.sort(
        key=lambda application: (
            -application.priority_score,
            -RISK_SCORE.get(
                application.business_consequence,
                1,
            ),
            application.application_id,
        )
    )

    return applications


def build_risk_landscape(
    artifacts: Iterable[Any],
    business_contexts: Optional[Iterable[Any]] = None,
) -> Dict[str, Any]:
    """
    Build the complete Risk Landscape projection.

    Projection levels:
        - artifact
        - application
        - portfolio
    """

    contexts = list(
        business_contexts or []
    )

    context_lookup = _business_context_lookup(
        contexts
    )

    points: List[RiskLandscapePoint] = []

    for artifact in artifacts:
        application_id = _application_id(
            artifact
        )

        context = (
            context_lookup.get(application_id)
            if application_id is not None
            else None
        )

        points.append(
            build_risk_landscape_point(
                artifact=artifact,
                business_context=context,
            )
        )

    points.sort(
        key=lambda point: (
            -point.priority_score,
            -RISK_SCORE.get(
                point.business_consequence,
                1,
            ),
            point.algorithm,
            point.artifact_id,
        )
    )

    applications = build_application_risk_landscape(
        points
    )

    total = len(points)

    decision_summary = {
        DECISION_REVIEW.lower(): sum(
            point.decision == DECISION_REVIEW
            for point in points
        ),
        DECISION_PRIORITIZE.lower(): sum(
            point.decision == DECISION_PRIORITIZE
            for point in points
        ),
        DECISION_ACTION.lower(): sum(
            point.decision == DECISION_ACTION
            for point in points
        ),
    }

    risk_summary = {
        level.lower(): sum(
            (
                point.security_risk == level
                or point.quantum_risk == level
                or point.business_consequence == level
            )
            for point in points
        )
        for level in RISK_LEVELS
    }

    mosca_at_risk = sum(
        point.mosca_status == "AT_RISK"
        for point in points
    )

    migration_required = sum(
        point.migration_required
        for point in points
    )

    resolved_contexts = sum(
        point.business_context_id is not None
        for point in points
    )

    unresolved_contexts = (
        total - resolved_contexts
    )

    high_confidence_contexts = sum(
        point.business_context_confidence == "high"
        for point in points
    )

    return {
        "version": "1.1",
        "projection": "risk_landscape",
        "points": [
            asdict(point)
            for point in points
        ],
        "applications": [
            asdict(application)
            for application in applications
        ],
        "summary": {
            "total_artifacts": total,
            "total_applications": len(
                applications
            ),
            "decision_distribution": decision_summary,
            "risk_summary": risk_summary,
            "mosca_at_risk": mosca_at_risk,
            "migration_required": migration_required,
            "business_context_resolved": resolved_contexts,
            "business_context_unresolved": unresolved_contexts,
            "business_context_high_confidence": (
                high_confidence_contexts
            ),
            "applications_requiring_action": sum(
                application.decision == DECISION_ACTION
                for application in applications
            ),
        },
        "methodology": {
            "decision_model": (
                "deterministic_evidence_linked_projection"
            ),
            "business_context_resolution": (
                "application_id_exact_match"
            ),
            "aggregation": (
                "artifact_to_application_max_risk"
            ),
            "priority_score": (
                "security + quantum + MOSCA + "
                "business consequence + migration "
                "availability + evidence coverage"
            ),
            "note": (
                "Priority scores are an internal analytical "
                "ranking mechanism, not a universal risk standard."
            ),
        },
    }

