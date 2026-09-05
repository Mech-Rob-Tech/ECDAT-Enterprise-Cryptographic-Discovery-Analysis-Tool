"""
ECDAT Risk Matrix analytical projection.

The risk matrix is a decision-support projection of the
canonical cryptographic model.

It does NOT replace the underlying security-risk,
quantum-risk, MOSCA, evidence, business-context, or
migration assessments.

Matrix design:
    X axis = Cryptographic Exposure
    Y axis = Business Consequence

Both axes use an even-numbered 4-level scale:

    1 = LOW
    2 = MEDIUM
    3 = HIGH
    4 = CRITICAL

Business consequence is resolved from canonical BusinessContext
when available.

The matrix additionally derives a decision zone:

    REVIEW
    PRIORITIZE
    ACTION

Decision-zone logic is deliberately deterministic and
explainable. It is not presented as a universal risk
standard; organizations may later configure their
decision boundary according to risk appetite.
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

DECISION_ZONES = (
    DECISION_REVIEW,
    DECISION_PRIORITIZE,
    DECISION_ACTION,
)


@dataclass(frozen=True)
class RiskMatrixPoint:
    """
    One canonical artifact projected onto the risk matrix.
    """

    artifact_id: str
    algorithm: str

    exposure_level: str
    consequence_level: str

    exposure_score: int
    consequence_score: int

    security_risk: Optional[str]
    quantum_risk: Optional[str]
    mosca_risk: Optional[str]
    mosca_status: Optional[str]

    business_criticality: str
    business_context_id: Optional[str]
    business_context_source: Optional[str]
    business_context_confidence: Optional[str]

    decision: str
    zone: str

    migration_required: bool
    migration_option_count: int

    evidence_count: int

    explanation: str


@dataclass(frozen=True)
class DecisionBoundary:
    """
    Deterministic v1 decision-boundary definition.

    The boundary is represented numerically so the frontend
    can render it independently of the backend implementation.
    """

    minimum_exposure_score: int
    minimum_consequence_score: int
    action_rule: str
    priority_rule: str
    review_rule: str


def normalize_level(
    value: Any,
    default: str = "LOW",
) -> str:
    """
    Normalize an arbitrary risk/criticality value into
    the ECDAT four-level vocabulary.
    """

    if value is None:
        return default

    normalized = str(value).strip().upper()

    if normalized in RISK_SCORE:
        return normalized

    return default


def get_nested_level(
    value: Any,
) -> Optional[str]:
    """
    Read a risk level from either a canonical assessment
    dictionary/object or a direct string.
    """

    if value is None:
        return None

    if isinstance(value, str):
        return normalize_level(value)

    if isinstance(value, dict):
        return normalize_level(
            value.get("level"),
            default="LOW",
        )

    level = getattr(value, "level", None)

    if level is not None:
        return normalize_level(level)

    return None


def get_nested_value(
    value: Any,
    key: str,
    default: Any = None,
) -> Any:
    """
    Safely read a dictionary or object field.
    """

    if value is None:
        return default

    if isinstance(value, dict):
        return value.get(key, default)

    return getattr(value, key, default)


def get_algorithm_name(
    artifact: Any,
) -> str:
    """
    Extract the canonical algorithm name.
    """

    algorithm = get_nested_value(
        artifact,
        "algorithm",
    )

    if isinstance(algorithm, str):
        return algorithm

    name = get_nested_value(
        algorithm,
        "name",
    )

    if name is not None:
        return str(name)

    return "UNKNOWN"


def get_security_risk(
    artifact: Any,
) -> Optional[str]:
    """
    Extract canonical security risk.
    """

    risk = get_nested_value(
        artifact,
        "risk",
    )

    security = get_nested_value(
        risk,
        "security",
    )

    return get_nested_level(security)


def get_quantum_risk(
    artifact: Any,
) -> Optional[str]:
    """
    Extract canonical quantum risk.
    """

    risk = get_nested_value(
        artifact,
        "risk",
    )

    quantum = get_nested_value(
        risk,
        "quantum",
    )

    return get_nested_level(quantum)


def get_mosca_risk(
    artifact: Any,
) -> Optional[str]:
    """
    Extract canonical MOSCA risk.
    """

    mosca = get_nested_value(
        artifact,
        "mosca",
    )

    return get_nested_level(
        get_nested_value(
            mosca,
            "risk",
        )
    )


def get_mosca_status(
    artifact: Any,
) -> Optional[str]:
    """
    Extract canonical MOSCA status.
    """

    mosca = get_nested_value(
        artifact,
        "mosca",
    )

    status = get_nested_value(
        mosca,
        "status",
    )

    if status is None:
        return None

    return str(status).upper()


def get_artifact_application_id(
    artifact: Any,
) -> Optional[str]:
    """
    Resolve the application owning an artifact.
    """

    application_id = get_nested_value(
        artifact,
        "application_id",
    )

    if application_id is None:
        return None

    return str(application_id)


def build_business_context_lookup(
    business_contexts: Optional[Iterable[Any]],
) -> Dict[str, Any]:
    """
    Build an application_id -> BusinessContext lookup.

    BusinessContext is application-scoped in the canonical model.
    """

    lookup: Dict[str, Any] = {}

    if business_contexts is None:
        return lookup

    for context in business_contexts:
        application_id = get_nested_value(
            context,
            "application_id",
        )

        if application_id is None:
            continue

        lookup[str(application_id)] = context

    return lookup


def get_business_context(
    artifact: Any,
    business_context_lookup: Optional[Dict[str, Any]] = None,
) -> Optional[Any]:
    """
    Resolve the canonical BusinessContext for an artifact.
    """

    if not business_context_lookup:
        return None

    application_id = get_artifact_application_id(
        artifact
    )

    if application_id is None:
        return None

    return business_context_lookup.get(
        application_id
    )


def get_business_criticality(
    artifact: Any,
    business_context: Optional[Any] = None,
    default: str = "MEDIUM",
) -> str:
    """
    Resolve business consequence.

    Resolution precedence:

        1. Canonical BusinessContext
        2. Explicit artifact.business_criticality
        3. Explicit artifact.business_consequence
        4. Organizational/default fallback

    BusinessContext consequence is derived conservatively from
    the strongest declared business-impact dimension:

        operational criticality
        financial impact
        regulatory exposure
        customer impact

    This avoids pretending that one dimension is universally
    more important than another.

    The scanner itself must never invent business importance.
    """

    if business_context is not None:
        context_levels = [
            get_nested_value(
                business_context,
                "operational_criticality",
            ),
            get_nested_value(
                business_context,
                "financial_impact",
            ),
            get_nested_value(
                business_context,
                "regulatory_exposure",
            ),
            get_nested_value(
                business_context,
                "customer_impact",
            ),
        ]

        normalized_levels = [
            normalize_level(
                level,
                default="MEDIUM",
            )
            for level in context_levels
            if level is not None
        ]

        if normalized_levels:
            strongest = max(
                normalized_levels,
                key=lambda level: RISK_SCORE[level],
            )

            return strongest

    value = get_nested_value(
        artifact,
        "business_criticality",
    )

    if value is None:
        value = get_nested_value(
            artifact,
            "business_consequence",
        )

    return normalize_level(
        value,
        default=default,
    )


def get_business_context_id(
    business_context: Optional[Any],
) -> Optional[str]:
    if business_context is None:
        return None

    context_id = get_nested_value(
        business_context,
        "context_id",
    )

    return (
        str(context_id)
        if context_id is not None
        else None
    )


def get_business_context_source(
    business_context: Optional[Any],
) -> Optional[str]:
    if business_context is None:
        return None

    source = get_nested_value(
        business_context,
        "source",
    )

    return (
        str(source)
        if source is not None
        else None
    )


def get_business_context_confidence(
    business_context: Optional[Any],
) -> Optional[str]:
    if business_context is None:
        return None

    confidence = get_nested_value(
        business_context,
        "confidence",
    )

    return (
        str(confidence)
        if confidence is not None
        else None
    )


def get_business_context_dimensions(
    business_context: Optional[Any],
) -> Dict[str, Optional[str]]:
    """
    Return the business-impact dimensions used to derive
    business consequence.

    This is useful for frontend explanation and future
    weighted organizational models.
    """

    if business_context is None:
        return {
            "operational_criticality": None,
            "financial_impact": None,
            "regulatory_exposure": None,
            "customer_impact": None,
        }

    return {
        "operational_criticality": get_nested_value(
            business_context,
            "operational_criticality",
        ),
        "financial_impact": get_nested_value(
            business_context,
            "financial_impact",
        ),
        "regulatory_exposure": get_nested_value(
            business_context,
            "regulatory_exposure",
        ),
        "customer_impact": get_nested_value(
            business_context,
            "customer_impact",
        ),
    }


def get_migration_option_count(
    artifact: Any,
) -> int:
    """
    Count available canonical migration options.
    """

    options = get_nested_value(
        artifact,
        "migration_options",
        [],
    )

    if options is None:
        return 0

    try:
        return len(options)
    except TypeError:
        return 0


def get_evidence_count(
    artifact: Any,
) -> int:
    """
    Count source-evidence records attached to an artifact.
    """

    evidence = get_nested_value(
        artifact,
        "evidence",
        [],
    )

    if evidence is None:
        return 0

    try:
        return len(evidence)
    except TypeError:
        return 0


def calculate_exposure_level(
    security_risk: Optional[str],
    quantum_risk: Optional[str],
) -> str:
    """
    Derive cryptographic exposure from the strongest
    available security or quantum assessment.

    This preserves the distinction between:
        - security risk
        - quantum risk

    while providing one deterministic X-axis value.
    """

    candidates = [
        normalize_level(security_risk)
        if security_risk
        else None,
        normalize_level(quantum_risk)
        if quantum_risk
        else None,
    ]

    scores = [
        RISK_SCORE[level]
        for level in candidates
        if level is not None
    ]

    if not scores:
        return "LOW"

    strongest_score = max(scores)

    for level, score in RISK_SCORE.items():
        if score == strongest_score:
            return level

    return "LOW"


def calculate_decision(
    exposure_level: str,
    consequence_level: str,
    quantum_risk: Optional[str],
    mosca_risk: Optional[str],
    mosca_status: Optional[str],
) -> str:
    """
    Determine the v1 decision zone.

    ACTION:
        - both exposure and consequence are HIGH+
        - OR either dimension is CRITICAL
        - OR MOSCA indicates an AT_RISK critical/high condition

    PRIORITIZE:
        - one dimension is HIGH+
        - OR MOSCA is HIGH / AT_RISK

    REVIEW:
        - everything else

    This is deliberately conservative and explainable.
    It is not a universal risk appetite model.
    """

    exposure_score = RISK_SCORE[
        normalize_level(exposure_level)
    ]

    consequence_score = RISK_SCORE[
        normalize_level(consequence_level)
    ]

    quantum_score = (
        RISK_SCORE.get(
            normalize_level(quantum_risk),
            0,
        )
        if quantum_risk
        else 0
    )

    mosca_score = (
        RISK_SCORE.get(
            normalize_level(mosca_risk),
            0,
        )
        if mosca_risk
        else 0
    )

    mosca_at_risk = (
        str(mosca_status).upper() == "AT_RISK"
        if mosca_status
        else False
    )

    if (
        exposure_score >= 4
        or consequence_score >= 4
        or (
            exposure_score >= 3
            and consequence_score >= 3
        )
        or (
            mosca_at_risk
            and (
                mosca_score >= 3
                or quantum_score >= 3
            )
        )
    ):
        return DECISION_ACTION

    if (
        exposure_score >= 3
        or consequence_score >= 3
        or quantum_score >= 3
        or mosca_score >= 3
        or mosca_at_risk
    ):
        return DECISION_PRIORITIZE

    return DECISION_REVIEW


def build_explanation(
    exposure_level: str,
    consequence_level: str,
    security_risk: Optional[str],
    quantum_risk: Optional[str],
    mosca_risk: Optional[str],
    mosca_status: Optional[str],
    decision: str,
    business_context: Optional[Any] = None,
) -> str:
    """
    Produce a concise, deterministic explanation for
    the matrix placement.
    """

    factors: List[str] = []

    factors.append(
        f"exposure={exposure_level}"
    )

    factors.append(
        f"business_consequence={consequence_level}"
    )

    if security_risk:
        factors.append(
            f"security_risk={security_risk}"
        )

    if quantum_risk:
        factors.append(
            f"quantum_risk={quantum_risk}"
        )

    if mosca_risk:
        factors.append(
            f"mosca_risk={mosca_risk}"
        )

    if mosca_status:
        factors.append(
            f"mosca_status={mosca_status}"
        )

    if business_context is not None:
        source = get_business_context_source(
            business_context
        )
        confidence = get_business_context_confidence(
            business_context
        )

        if source:
            factors.append(
                f"business_context_source={source}"
            )

        if confidence:
            factors.append(
                f"business_context_confidence={confidence}"
            )
    else:
        factors.append(
            "business_context=unavailable"
        )

    return (
        f"Decision={decision}. "
        f"Matrix placement is based on "
        f"{', '.join(factors)}."
    )


def build_risk_matrix_point(
    artifact: Any,
    business_context: Optional[Any] = None,
    business_criticality: str = "MEDIUM",
) -> RiskMatrixPoint:
    """
    Project one canonical artifact into the matrix.
    """

    artifact_id = str(
        get_nested_value(
            artifact,
            "artifact_id",
            "unknown",
        )
    )

    algorithm = get_algorithm_name(
        artifact
    )

    security_risk = get_security_risk(
        artifact
    )

    quantum_risk = get_quantum_risk(
        artifact
    )

    mosca_risk = get_mosca_risk(
        artifact
    )

    mosca_status = get_mosca_status(
        artifact
    )

    exposure_level = calculate_exposure_level(
        security_risk,
        quantum_risk,
    )

    consequence_level = get_business_criticality(
        artifact=artifact,
        business_context=business_context,
        default=business_criticality,
    )

    decision = calculate_decision(
        exposure_level=exposure_level,
        consequence_level=consequence_level,
        quantum_risk=quantum_risk,
        mosca_risk=mosca_risk,
        mosca_status=mosca_status,
    )

    migration_option_count = (
        get_migration_option_count(
            artifact
        )
    )

    evidence_count = (
        get_evidence_count(
            artifact
        )
    )

    explanation = build_explanation(
        exposure_level=exposure_level,
        consequence_level=consequence_level,
        security_risk=security_risk,
        quantum_risk=quantum_risk,
        mosca_risk=mosca_risk,
        mosca_status=mosca_status,
        decision=decision,
        business_context=business_context,
    )

    return RiskMatrixPoint(
        artifact_id=artifact_id,
        algorithm=algorithm,
        exposure_level=exposure_level,
        consequence_level=consequence_level,
        exposure_score=RISK_SCORE[
            exposure_level
        ],
        consequence_score=RISK_SCORE[
            consequence_level
        ],
        security_risk=security_risk,
        quantum_risk=quantum_risk,
        mosca_risk=mosca_risk,
        mosca_status=mosca_status,
        business_criticality=consequence_level,
        business_context_id=(
            get_business_context_id(
                business_context
            )
        ),
        business_context_source=(
            get_business_context_source(
                business_context
            )
        ),
        business_context_confidence=(
            get_business_context_confidence(
                business_context
            )
        ),
        decision=decision,
        zone=decision,
        migration_required=(
            migration_option_count > 0
            and decision != DECISION_REVIEW
        ),
        migration_option_count=migration_option_count,
        evidence_count=evidence_count,
        explanation=explanation,
    )


def get_decision_boundary() -> DecisionBoundary:
    """
    Return the v1 decision-boundary definition.

    The boundary is intentionally expressed as rules rather
    than a visual coordinate. The frontend can use this
    contract to render the boundary consistently.
    """

    return DecisionBoundary(
        minimum_exposure_score=3,
        minimum_consequence_score=3,
        action_rule=(
            "ACTION when exposure or consequence is "
            "CRITICAL, or both are HIGH, or MOSCA "
            "indicates an AT_RISK high/critical condition."
        ),
        priority_rule=(
            "PRIORITIZE when either exposure or consequence "
            "is HIGH, or when quantum/MOSCA pressure is HIGH."
        ),
        review_rule=(
            "REVIEW when no higher-priority decision rule applies."
        ),
    )


def build_risk_matrix(
    artifacts: Iterable[Any],
    business_criticality: str = "MEDIUM",
    business_contexts: Optional[Iterable[Any]] = None,
) -> Dict[str, Any]:
    """
    Build the complete Risk Matrix analytical projection.

    Parameters
    ----------
    artifacts:
        Canonical CryptoArtifact objects.

    business_criticality:
        Backward-compatible fallback used only when no
        BusinessContext is available.

    business_contexts:
        Canonical BusinessContext objects.

    BusinessContext resolution is performed through the
    artifact's application_id.
    """

    business_context_lookup = (
        build_business_context_lookup(
            business_contexts
        )
    )

    points: List[RiskMatrixPoint] = []

    for artifact in artifacts:
        context = get_business_context(
            artifact,
            business_context_lookup,
        )

        points.append(
            build_risk_matrix_point(
                artifact,
                business_context=context,
                business_criticality=business_criticality,
            )
        )

    decision_boundary = get_decision_boundary()

    return {
        "version": "1.1",
        "matrix_type": "4x4",
        "x_axis": {
            "name": "cryptographic_exposure",
            "levels": list(RISK_LEVELS),
            "minimum": 1,
            "maximum": 4,
        },
        "y_axis": {
            "name": "business_consequence",
            "levels": list(RISK_LEVELS),
            "minimum": 1,
            "maximum": 4,
        },
        "decision_boundary": asdict(
            decision_boundary
        ),
        "points": [
            asdict(point)
            for point in points
        ],
        "summary": {
            "total": len(points),
            "review": sum(
                point.decision == DECISION_REVIEW
                for point in points
            ),
            "prioritize": sum(
                point.decision == DECISION_PRIORITIZE
                for point in points
            ),
            "action": sum(
                point.decision == DECISION_ACTION
                for point in points
            ),
            "business_context_resolved": sum(
                point.business_context_id is not None
                for point in points
            ),
            "business_context_unresolved": sum(
                point.business_context_id is None
                for point in points
            ),
        },
        "business_context_resolution": {
            "strategy": "application_id_exact_match",
            "resolved": sum(
                point.business_context_id is not None
                for point in points
            ),
            "unresolved": sum(
                point.business_context_id is None
                for point in points
            ),
        },
    }
