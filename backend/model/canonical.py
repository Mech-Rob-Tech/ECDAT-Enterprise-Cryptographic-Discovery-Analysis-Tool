from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from analysis.mosca import calculate_mosca_risk
from analysis.recommendations import get_recommendation
from analysis.quantum_risk import assess_quantum_risk

from model.identity import (
    build_artifact_id,
    build_evidence_id,
)
from model.relationships import (
    build_components,
    build_relationships,
    map_components_to_artifacts,
)
from model.schema import (
    Algorithm,
    Application,
    BusinessContext,
    CryptoArtifact,
    Detection,
    ECDATScan,
    Evidence,
    MigrationOption,
    MoscaAssessment,
    Purpose,
    Recommendation,
    Risk,
    RiskAssessment,
    ScanMetadata,
    ScanSummary,
    VerificationState,
)


def stable_id(prefix: str, *parts: Any) -> str:
    """
    Build a deterministic identifier from stable model attributes.
    """
    normalized = ":".join(
        str(part).strip()
        for part in parts
        if part is not None
    )

    return f"{prefix}:{normalized}"


def normalize_confidence(value: Any) -> str:
    """
    Normalize confidence values into the canonical string form.
    """
    if value is None:
        return "low"

    if isinstance(value, (int, float)):
        if value >= 0.9:
            return "high"

        if value >= 0.6:
            return "medium"

        return "low"

    value = str(value).strip().lower()

    if value in {"high", "medium", "low"}:
        return value

    return "low"


def normalize_business_criticality(value: Any) -> str:
    """
    Normalize business criticality values for the existing MOSCA engine.
    """
    if value is None:
        return "Medium"

    if isinstance(value, (int, float)):
        if value >= 4:
            return "High"

        if value >= 3:
            return "Medium"

        return "Low"

    normalized = str(value).strip().lower()

    mapping = {
        "1": "Low",
        "2": "Low",
        "3": "Medium",
        "4": "High",
        "5": "High",
        "low": "Low",
        "medium": "Medium",
        "high": "High",
        "critical": "High",
    }

    return mapping.get(normalized, "Medium")


def normalize_purpose(
    artifact: Dict[str, Any],
) -> Purpose:
    """
    Convert scanner purpose information into the canonical model.
    """
    value = artifact.get("purpose") or "unknown"

    confidence = normalize_confidence(
        artifact.get("purpose_confidence")
    )

    return Purpose(
        value=str(value),
        confidence=confidence,
    )


def normalize_detection(
    artifact: Dict[str, Any],
) -> Detection:
    """
    Convert scanner detection metadata into the canonical model.
    """
    return Detection(
        method=str(
            artifact.get(
                "detection_method",
                "pattern_match",
            )
        ),
        confidence=normalize_confidence(
            artifact.get("detection_confidence")
        ),
    )


def build_evidence(
    artifact: Dict[str, Any],
    artifact_id: str,
) -> Evidence:
    """
    Convert one scanner observation into canonical evidence.

    Evidence identity intentionally retains source location because
    evidence represents where and how the artifact was observed.
    """
    evidence_id = build_evidence_id(
        artifact_id=artifact_id,
        file=str(
            artifact.get(
                "file",
                "",
            )
        ),
        line=int(
            artifact.get(
                "line",
                0,
            )
        ),
        evidence=str(
            artifact.get(
                "evidence",
                "",
            )
        ),
    )

    context = artifact.get(
        "evidence_context"
    ) or []

    return Evidence(
        evidence_id=evidence_id,
        file=str(
            artifact.get(
                "file",
                "",
            )
        ),
        line=int(
            artifact.get(
                "line",
                0,
            )
        ),
        text=str(
            artifact.get(
                "evidence",
                "",
            )
        ),
        context=context,
    )


def build_algorithm(
    artifact: Dict[str, Any],
) -> Algorithm:
    """
    Convert scanner algorithm information into the canonical model.
    """
    name = str(
        artifact.get(
            "algorithm",
            "UNKNOWN",
        )
    )

    family = artifact.get(
        "algorithm_family"
    )

    return Algorithm(
        name=name,
        family=(
            str(family)
            if family is not None
            else None
        ),
    )


def build_risk_assessment(
    artifact: Dict[str, Any],
) -> RiskAssessment:
    """
    Build a stable security-risk assessment object.

    Security severity is distinct from quantum-migration relevance.
    """
    assessment_id = stable_id(
        "risk",
        artifact.get(
            "artifact_id"
        ),
    )

    return RiskAssessment(
        assessment_id=assessment_id,
        level=str(
            artifact.get(
                "security_risk",
                artifact.get(
                    "quantum_risk",
                    "MEDIUM",
                ),
            )
        ),
        reason=str(
            artifact.get(
                "security_reason",
                artifact.get(
                    "risk_reason",
                    "Further security assessment required.",
                ),
            )
        ),
    )


def build_quantum_risk(
    artifact: Dict[str, Any],
) -> Any:
    """
    Preserve the scanner's current quantum-risk assessment.
    """
    result = assess_quantum_risk(
        artifact
    )

    from model.schema import QuantumRisk

    return QuantumRisk(
        level=str(
            result.get(
                "quantum_risk",
                "MEDIUM",
            )
        ),
        reason=str(
            result.get(
                "risk_reason",
                "Further quantum-security assessment required.",
            )
        ),
    )


def build_mosca_assessment(
    artifact: Dict[str, Any],
    mosca_inputs: Optional[Dict[str, Any]],
) -> Optional[MoscaAssessment]:
    """
    Build a MOSCA assessment for asymmetric cryptographic artifacts.

    The existing MOSCA engine is intentionally reused rather than
    reimplemented here.
    """
    algorithm = str(
        artifact.get(
            "algorithm",
            "",
        )
    )

    asymmetric_algorithms = {
        "RSA",
        "ECDSA",
        "ECDH",
        "Diffie-Hellman",
    }

    if algorithm not in asymmetric_algorithms:
        return None

    inputs = mosca_inputs or {}

    data_lifetime = inputs.get(
        "data_lifetime",
        10,
    )

    migration_time = inputs.get(
        "migration_time",
        5,
    )

    quantum_horizon = inputs.get(
        "quantum_horizon",
        15,
    )

    business_criticality = (
        normalize_business_criticality(
            inputs.get(
                "business_criticality",
                "Medium",
            )
        )
    )

    result = calculate_mosca_risk(
        data_lifetime,
        migration_time,
        quantum_horizon,
        business_criticality,
    )

    return MoscaAssessment(
        assessment_id=stable_id(
            "mosca",
            artifact.get(
                "artifact_id"
            ),
        ),
        risk=str(
            result.get(
                "mosca_risk",
                "UNKNOWN",
            )
        ),
        status=str(
            result.get(
                "mosca_status",
                "UNKNOWN",
            )
        ),
        explanation=str(
            result.get(
                "mosca_explanation",
                "",
            )
        ),
    )


def classify_recommendation(
    artifact: Dict[str, Any],
    recommendation_text: str,
) -> Dict[str, str]:
    """
    Classify the existing recommendation into a semantic category.

    This does not rewrite the recommendation text. It only determines
    how the recommendation should be represented in the canonical model.
    """
    algorithm = str(
        artifact.get(
            "algorithm",
            "",
        )
    )

    text = recommendation_text.lower()

    if algorithm in {
        "AES",
        "SHA-256",
        "SHA-384",
        "SHA-512",
    }:
        return {
            "category": "monitor",
            "priority": "low",
            "rationale": (
                "The current recommendation does not require "
                "an immediate cryptographic migration."
            ),
        }

    if algorithm in {
        "MD5",
        "SHA-1",
        "DES",
    }:
        return {
            "category": "replace",
            "priority": "critical",
            "rationale": (
                "The detected algorithm requires replacement "
                "because of inadequate cryptographic security."
            ),
        }

    if algorithm == "ECDSA":
        return {
            "category": "migrate",
            "priority": "high",
            "rationale": (
                "ECDSA uses public-key cryptography that is "
                "vulnerable to sufficiently capable quantum attacks."
            ),
        }

    if algorithm in {
        "ECDH",
        "Diffie-Hellman",
    }:
        return {
            "category": "migrate",
            "priority": "high",
            "rationale": (
                "The key-establishment mechanism is vulnerable "
                "to sufficiently capable quantum attacks."
            ),
        }

    if algorithm == "RSA":
        return {
            "category": "manual_review",
            "priority": "high",
            "rationale": (
                "RSA migration depends on the cryptographic purpose. "
                "The current finding does not establish whether RSA "
                "is being used for encryption, key establishment, "
                "or digital signatures."
            ),
        }

    if algorithm == "TLS":
        return {
            "category": "inspect",
            "priority": "medium",
            "rationale": (
                "TLS quantum exposure depends on the configured "
                "authentication and key-establishment algorithms."
            ),
        }

    if "replace" in text:
        return {
            "category": "replace",
            "priority": "high",
            "rationale": (
                "The recommendation explicitly calls for replacement."
            ),
        }

    if "migrat" in text:
        return {
            "category": "migrate",
            "priority": "medium",
            "rationale": (
                "The recommendation identifies a migration action."
            ),
        }

    return {
        "category": "manual_review",
        "priority": "medium",
        "rationale": (
            "The recommendation requires further cryptographic review."
        ),
    }


def build_recommendation(
    artifact: Dict[str, Any],
) -> Recommendation:
    """
    Build a deterministic first-class recommendation.
    """
    recommendation_text = str(
        artifact.get(
            "recommendation",
            "Perform manual cryptographic review.",
        )
    )

    classification = classify_recommendation(
        artifact,
        recommendation_text,
    )

    return Recommendation(
        recommendation_id=stable_id(
            "recommendation",
            artifact.get(
                "artifact_id"
            ),
            classification["category"],
        ),
        category=classification["category"],
        priority=classification["priority"],
        text=recommendation_text,
        rationale=classification["rationale"],
    )


def build_migration_options(
    artifact: Dict[str, Any],
    recommendation: Recommendation,
) -> List[MigrationOption]:
    """
    Build only genuine migration/replacement options.

    Advisory recommendations such as AES-256 monitoring do not
    produce migration options.
    """
    algorithm = str(
        artifact.get(
            "algorithm",
            "",
        )
    )

    purpose = str(
        artifact.get(
            "purpose",
            "unknown",
        )
    )

    options: List[MigrationOption] = []

    def add_option(
        name: str,
        rationale: str,
        compatibility: str,
        effort: str,
    ) -> None:
        options.append(
            MigrationOption(
                option_id=stable_id(
                    "migration",
                    artifact.get(
                        "artifact_id"
                    ),
                    name,
                ),
                name=name,
                rationale=rationale,
                compatibility=compatibility,
                effort=effort,
            )
        )

    if algorithm == "ECDSA":
        add_option(
            "ML-DSA",
            "Post-quantum digital-signature migration candidate.",
            "Requires application and protocol compatibility assessment.",
            "Medium",
        )

        add_option(
            "SLH-DSA",
            "Hash-based post-quantum digital-signature alternative.",
            "Requires application and protocol compatibility assessment.",
            "Medium",
        )

        add_option(
            "Hybrid digital signature",
            "Provides a transition path combining classical and post-quantum mechanisms.",
            "Depends on protocol and implementation support.",
            "High",
        )

    elif algorithm in {
        "ECDH",
        "Diffie-Hellman",
    }:
        add_option(
            "ML-KEM",
            "Post-quantum key-establishment migration candidate.",
            "Requires protocol and implementation compatibility assessment.",
            "Medium",
        )

        add_option(
            "Hybrid key establishment",
            "Combines classical and post-quantum key-establishment mechanisms during transition.",
            "Depends on protocol and implementation support.",
            "High",
        )

    elif algorithm == "RSA":
        if purpose in {
            "encryption",
            "key_establishment",
        }:
            add_option(
                "ML-KEM",
                "Post-quantum key-establishment or encryption migration candidate.",
                "Requires workflow and protocol compatibility assessment.",
                "Medium",
            )

            add_option(
                "Hybrid key establishment",
                "Transition path combining classical RSA-based protection with a post-quantum mechanism.",
                "Requires protocol and implementation support.",
                "High",
            )

        elif purpose == "digital_signature":
            add_option(
                "ML-DSA",
                "Post-quantum digital-signature migration candidate.",
                "Requires application and protocol compatibility assessment.",
                "Medium",
            )

            add_option(
                "SLH-DSA",
                "Hash-based post-quantum digital-signature alternative.",
                "Requires application and protocol compatibility assessment.",
                "Medium",
            )

            add_option(
                "Hybrid digital signature",
                "Transition path combining classical and post-quantum signatures.",
                "Depends on protocol and implementation support.",
                "High",
            )

    elif algorithm == "MD5":
        add_option(
            "Modern approved hash",
            "Replace MD5 with an approved modern hash construction appropriate to the use case.",
            "Usually high, subject to application-specific compatibility testing.",
            "Low",
        )

    elif algorithm == "SHA-1":
        add_option(
            "SHA-256",
            "Modern replacement for SHA-1 in security-sensitive applications.",
            "Generally high, subject to use-case validation.",
            "Low",
        )

        add_option(
            "SHA-384 / SHA-512",
            "Alternative approved modern hash constructions.",
            "Generally high, subject to use-case validation.",
            "Low",
        )

    elif algorithm == "DES":
        add_option(
            "AES",
            "Modern symmetric-cipher replacement for DES or legacy 3DES.",
            "Requires mode, key-size, and protocol compatibility testing.",
            "Medium",
        )

    elif algorithm == "TLS":
        add_option(
            "PQC / hybrid TLS",
            "Migration candidate when TLS uses quantum-vulnerable public-key authentication or key establishment.",
            "Depends on TLS implementation, protocol, certificate, and endpoint support.",
            "High",
        )

    return options


def build_verification_state(
    artifact_id: str,
) -> VerificationState:
    """
    Create the initial verification state for an artifact.
    """
    return VerificationState(
        verification_id=stable_id(
            "verification",
            artifact_id,
        ),
        status="not_verified",
        artifact_id=artifact_id,
        verified_at=None,
        notes=(
            "Verification requires a subsequent scan after "
            "migration or remediation."
        ),
    )


def build_canonical_artifact_id(
    artifact: Dict[str, Any],
    application_id: str,
) -> str:
    """
    Build stable logical identity for a cryptographic artifact.

    Source file, line number, scan timestamp, and scanner
    discovery order are deliberately excluded.

    Multiple indistinguishable source observations represent
    one logical artifact and are modeled through evidence.
    """
    algorithm = str(
        artifact.get(
            "algorithm",
            "UNKNOWN",
        )
    )

    artifact_type = str(
        artifact.get(
            "type",
            "cryptographic_artifact",
        )
    )

    purpose = str(
        artifact.get(
            "purpose",
            "unknown",
        )
    )

    details = dict(
        artifact.get(
            "details",
            {},
        )
    )

    for key in (
        "key_size",
        "mode",
        "curve",
        "version",
        "algorithm_family",
    ):
        value = artifact.get(key)

        if value is not None:
            details[key] = value

    semantic_signature = artifact.get(
        "semantic_signature"
    )

    return build_artifact_id(
        application_id=application_id,
        algorithm=algorithm,
        artifact_type=artifact_type,
        purpose=purpose,
        details=details,
        semantic_signature=semantic_signature,
    )

def build_canonical_artifact(
    artifact: Dict[str, Any],
    evidence: Evidence,
    artifact_id: str,
    risk_assessment: RiskAssessment,
    quantum_risk: Any,
    mosca_assessment: Optional[MoscaAssessment],
    recommendation: Recommendation,
    migration_options: List[MigrationOption],
    verification: VerificationState,
    application_id: Optional[str] = None,
) -> CryptoArtifact:
    """
    Convert a scanner artifact into the canonical representation.
    """
    return CryptoArtifact(
        artifact_id=artifact_id,
        algorithm=build_algorithm(
            artifact
        ),
        artifact_type=str(
            artifact.get(
                "type",
                "cryptographic_artifact",
            )
        ),
        key_size=artifact.get(
            "key_size"
        ),
        mode=artifact.get(
            "mode"
        ),
        curve=artifact.get(
            "curve"
        ),
        version=artifact.get(
            "version"
        ),
        purpose=normalize_purpose(
            artifact
        ),
        detection=normalize_detection(
            artifact
        ),
        evidence_ids=[
            evidence.evidence_id
        ],
        risk=Risk(
            security=risk_assessment,
            quantum=quantum_risk,
        ),
        mosca=mosca_assessment,
        recommendation_ids=[
            recommendation.recommendation_id
        ],
        migration_option_ids=[
            option.option_id
            for option in migration_options
        ],
        verification_id=(
            verification.verification_id
        ),
        application_id=application_id,
        component_id=None,
        details=dict(
            artifact.get(
                "details",
                {},
            )
        ),
    )


def build_canonical_scan(
    scan_results: Dict[str, Any],
    mosca_inputs: Optional[Dict[str, Any]] = None,
    business_context: Optional[Dict[str, Any]] = None,
) -> ECDATScan:
    """
    Convert the existing scanner output into the canonical ECDAT model.
    """
    generated_at = datetime.now(
        timezone.utc
    ).isoformat()

    target = str(
        scan_results.get(
            "target",
            "",
        )
    )

    application = Application(
        application_id=stable_id(
            "application",
            target.rstrip("/").split("/")[-1]
            or "repository",
        ),
        name=(
            target.split("/")[-1]
            or target
        ),
        path=target,
    )

    evidence_objects: List[Evidence] = []
    evidence_by_id: Dict[str, Evidence] = {}

    artifacts: List[CryptoArtifact] = []

    risk_assessments: List[RiskAssessment] = []
    mosca_assessments: List[MoscaAssessment] = []
    recommendations: List[Recommendation] = []
    migration_options: List[MigrationOption] = []
    verification_states: List[VerificationState] = []

    business_contexts: List[BusinessContext] = []

    raw_business_context = (
        business_context
        or scan_results.get(
            "business_context"
        )
    )

    if raw_business_context:
        context_id = stable_id(
            "business_context",
            application.application_id,
        )

        business_contexts.append(
            BusinessContext(
                context_id=context_id,
                application_id=(
                    application.application_id
                ),
                business_unit=(
                    raw_business_context.get(
                        "business_unit"
                    )
                ),
                owner=(
                    raw_business_context.get(
                        "owner"
                    )
                ),
                service=(
                    raw_business_context.get(
                        "service"
                    )
                ),
                data_classification=(
                    raw_business_context.get(
                        "data_classification"
                    )
                ),
                data_lifetime_years=(
                    raw_business_context.get(
                        "data_lifetime_years"
                    )
                ),
                operational_criticality=str(
                    raw_business_context.get(
                        "operational_criticality",
                        "MEDIUM",
                    )
                ).upper(),
                financial_impact=str(
                    raw_business_context.get(
                        "financial_impact",
                        "MEDIUM",
                    )
                ).upper(),
                regulatory_exposure=str(
                    raw_business_context.get(
                        "regulatory_exposure",
                        "MEDIUM",
                    )
                ).upper(),
                customer_impact=str(
                    raw_business_context.get(
                        "customer_impact",
                        "MEDIUM",
                    )
                ).upper(),
                risk_appetite=(
                    raw_business_context.get(
                        "risk_appetite"
                    )
                ),
                source=str(
                    raw_business_context.get(
                        "source",
                        "declared",
                    )
                ),
                confidence=str(
                    raw_business_context.get(
                        "confidence",
                        "high",
                    )
                ).lower(),
                evidence_ids=list(
                    raw_business_context.get(
                        "evidence_ids",
                        [],
                    )
                ),
            )
        )

    raw_artifacts = scan_results.get(
        "artifacts",
        [],
    )

    artifact_by_id: Dict[str, CryptoArtifact] = {}

    for raw_artifact in raw_artifacts:
        canonical_artifact_id = (
            build_canonical_artifact_id(
                raw_artifact,
                application.application_id,
            )
        )

        existing_artifact = artifact_by_id.get(
            canonical_artifact_id
        )

        if existing_artifact is not None:
            evidence = build_evidence(
                raw_artifact,
                canonical_artifact_id,
            )

            evidence_objects.append(
                evidence
            )

            evidence_by_id[
                evidence.evidence_id
            ] = evidence

            existing_artifact.evidence_ids.append(
                evidence.evidence_id
            )

            continue

        evidence = build_evidence(
            raw_artifact,
            canonical_artifact_id,
        )

        evidence_objects.append(
            evidence
        )

        evidence_by_id[
            evidence.evidence_id
        ] = evidence

        artifact_for_analysis = dict(
            raw_artifact
        )

        artifact_for_analysis[
            "artifact_id"
        ] = canonical_artifact_id

        risk_assessment = (
            build_risk_assessment(
                artifact_for_analysis
            )
        )

        quantum_risk = build_quantum_risk(
            artifact_for_analysis
        )

        mosca_assessment = (
            build_mosca_assessment(
                artifact_for_analysis,
                mosca_inputs,
            )
        )

        recommendation = (
            build_recommendation(
                artifact_for_analysis
            )
        )

        options = build_migration_options(
            artifact_for_analysis,
            recommendation,
        )

        verification = (
            build_verification_state(
                canonical_artifact_id
            )
        )

        canonical_artifact = (
            build_canonical_artifact(
                artifact=artifact_for_analysis,
                evidence=evidence,
                artifact_id=canonical_artifact_id,
                risk_assessment=risk_assessment,
                quantum_risk=quantum_risk,
                mosca_assessment=mosca_assessment,
                recommendation=recommendation,
                migration_options=options,
                verification=verification,
                application_id=(
                    application.application_id
                ),
            )
        )

        artifact_by_id[
            canonical_artifact_id
        ] = canonical_artifact

        artifacts.append(
            canonical_artifact
        )

        risk_assessments.append(
            risk_assessment
        )

        if mosca_assessment is not None:
            mosca_assessments.append(
                mosca_assessment
            )

        recommendations.append(
            recommendation
        )

        migration_options.extend(
            options
        )

        verification_states.append(
            verification
        )

    components = build_components(
        application=application,
        artifacts=artifacts,
        evidence_by_id=evidence_by_id,
    )

    map_components_to_artifacts(
        components=components,
        artifacts=artifacts,
        evidence_by_id=evidence_by_id,
    )

    relationships = build_relationships(
        application=application,
        components=components,
        artifacts=artifacts,
        evidence_by_id=evidence_by_id,
        risk_assessments=risk_assessments,
        mosca_assessments=mosca_assessments,
        recommendations=recommendations,
        migration_options=migration_options,
        verification_states=verification_states,
        business_contexts=business_contexts,
    )

    risk_summary = dict(
        scan_results.get(
            "risk_summary",
            {},
        )
    )

    quantum_relevant_assets = int(
        scan_results.get(
            "quantum_vulnerable_assets",
            0,
        )
    )

    summary = ScanSummary(
        total_files_scanned=int(
            scan_results.get(
                "total_files_scanned",
                0,
            )
        ),
        total_artifacts=len(
            artifacts
        ),
        security_risk_summary=risk_summary,
        quantum_relevant_assets=(
            quantum_relevant_assets
        ),
    )

    metadata = ScanMetadata(
        target=target,
        generated_at=generated_at,
        prototype_scope=(
            "Source-code cryptographic discovery with "
            "canonical analytical modeling."
        ),
    )

    return ECDATScan(
        metadata=metadata,
        summary=summary,
        applications=[
            application
        ],
        business_contexts=(
            business_contexts
        ),
        components=components,
        artifacts=artifacts,
        evidence=evidence_objects,
        relationships=relationships,
        risk_assessments=(
            risk_assessments
        ),
        mosca_assessments=(
            mosca_assessments
        ),
        recommendations=(
            recommendations
        ),
        migration_options=(
            migration_options
        ),
        verification=(
            verification_states
        ),
    )
