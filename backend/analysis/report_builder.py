from typing import Any, Dict, Optional

from model.canonical import build_canonical_scan
from analysis.risk_landscape import build_risk_landscape

from knowledge.service import KnowledgeService

def build_artifact_record(
    artifact: Dict[str, Any],
    mosca_inputs: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Preserve the existing flat artifact output contract.

    The canonical model is now the analytical source of truth, while
    this flattened representation keeps the existing API/frontend
    contract working during the migration.
    """
    record = dict(artifact)

    return record


def build_report(
    scan_results: Dict[str, Any],
    mosca_inputs: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Build the canonical ECDAT report while preserving legacy fields.
    """
    knowledge_service = KnowledgeService()

    canonical_scan = build_canonical_scan(
        scan_results,
        mosca_inputs=mosca_inputs,
    )

    knowledge_snapshot = knowledge_service.snapshot()
    risk_landscape = build_risk_landscape(
        artifacts=canonical_scan.artifacts,
        business_contexts=canonical_scan.business_contexts,
    )
    canonical_artifacts = []

    for artifact in canonical_scan.artifacts:
        canonical_artifacts.append(
            {
                "artifact_id": artifact.artifact_id,
                "algorithm": artifact.algorithm.name,
                "algorithm_family": artifact.algorithm.family,
                "type": artifact.artifact_type,
                "key_size": artifact.key_size,
                "mode": artifact.mode,
                "curve": artifact.curve,
                "version": artifact.version,
                "purpose": (
                    artifact.purpose.value
                    if artifact.purpose
                    else "unknown"
                ),
                "purpose_confidence": (
                    artifact.purpose.confidence
                    if artifact.purpose
                    else "low"
                ),
                "detection_method": (
                    artifact.detection.method
                    if artifact.detection
                    else None
                ),
                "detection_confidence": (
                    artifact.detection.confidence
                    if artifact.detection
                    else "low"
                ),
                "evidence_ids": list(
                    artifact.evidence_ids
                ),
                "risk": (
                    {
                        "security": (
                            {
                                "assessment_id": (
                                    artifact.risk.security.assessment_id
                                ),
                                "level": (
                                    artifact.risk.security.level
                                ),
                                "reason": (
                                    artifact.risk.security.reason
                                ),
                            }
                            if artifact.risk
                            and artifact.risk.security
                            else None
                        ),
                        "quantum": (
                            {
                                "level": (
                                    artifact.risk.quantum.level
                                ),
                                "reason": (
                                    artifact.risk.quantum.reason
                                ),
                            }
                            if artifact.risk
                            and artifact.risk.quantum
                            else None
                        ),
                    }
                    if artifact.risk
                    else None
                ),
                "mosca": (
                    {
                        "assessment_id": (
                            artifact.mosca.assessment_id
                        ),
                        "risk": artifact.mosca.risk,
                        "status": artifact.mosca.status,
                        "explanation": artifact.mosca.explanation,
                    }
                    if artifact.mosca
                    else None
                ),
                "recommendation_ids": list(
                    artifact.recommendation_ids
                ),
                "migration_option_ids": list(
                    artifact.migration_option_ids
                ),
                "verification_id": artifact.verification_id,
                "application_id": artifact.application_id,
                "component_id": artifact.component_id,
                "details": dict(artifact.details),
            }
        )

    recommendations = []

    for recommendation in canonical_scan.recommendations:
        recommendations.append(
            {
                "recommendation_id": (
                    recommendation.recommendation_id
                ),
                "category": recommendation.category,
                "priority": recommendation.priority,
                "text": recommendation.text,
                "rationale": recommendation.rationale,
                "knowledge_version": recommendation.knowledge_version,
                "knowledge_hash": recommendation.knowledge_hash,
                "status": recommendation.status,
                "matched_by": recommendation.matched_by,
                "lifecycle_status": recommendation.lifecycle_status,
                "quantum_posture": recommendation.quantum_posture,
                "primitive": recommendation.primitive,
                "standards": list(recommendation.standards),
                "candidate_ids": list(recommendation.candidate_ids),
                "candidates": list(recommendation.candidates),
                "compatibility": dict(recommendation.compatibility),
                "conflict_count": recommendation.conflict_count,
                "explainability": dict(recommendation.explainability),
            }
        )

    migration_options = []

    for option in canonical_scan.migration_options:
        migration_options.append(
            {
                "option_id": option.option_id,
                "name": option.name,
                "rationale": option.rationale,
                "compatibility": option.compatibility,
                "effort": option.effort,
                "relationship_id": option.relationship_id,
                "source_algorithm": option.source_algorithm,
                "target_algorithm": option.target_algorithm,
                "relationship_type": option.relationship_type,
                "hybrid": option.hybrid,
                "confidence": option.confidence,
                "prerequisites": list(option.prerequisites),
                "constraints": list(option.constraints),
                "knowledge_version": option.knowledge_version,
                "knowledge_hash": option.knowledge_hash,
            }
        )

    risk_assessments = []

    for assessment in canonical_scan.risk_assessments:
        risk_assessments.append(
            {
                "assessment_id": assessment.assessment_id,
                "level": assessment.level,
                "reason": assessment.reason,
            }
        )

    mosca_assessments = []

    for assessment in canonical_scan.mosca_assessments:
        mosca_assessments.append(
            {
                "assessment_id": assessment.assessment_id,
                "risk": assessment.risk,
                "status": assessment.status,
                "explanation": assessment.explanation,
            }
        )

    verification = []

    for state in canonical_scan.verification:
        verification.append(
            {
                "verification_id": state.verification_id,
                "status": state.status,
                "verified_at": state.verified_at,
                "notes": state.notes,
            }
        )

    relationships = []

    for relationship in canonical_scan.relationships:
        relationships.append(
            {
                "relationship_id": relationship.relationship_id,
                "source_id": relationship.source_id,
                "target_id": relationship.target_id,
                "relationship_type": relationship.relationship_type,
                "confidence": relationship.confidence,
                "evidence_ids": list(
                    relationship.evidence_ids
                ),
            }
        )

    applications = []

    for application in canonical_scan.applications:
        applications.append(
            {
                "application_id": application.application_id,
                "name": application.name,
                "path": application.path,
            }
        )

    components = []

    for component in canonical_scan.components:
        components.append(
            {
                "component_id": component.component_id,
                "name": component.name,
                "component_type": component.component_type,
                "version": component.version,
                "path": component.path,
            }
        )

    evidence = []

    for item in canonical_scan.evidence:
        evidence.append(
            {
                "evidence_id": item.evidence_id,
                "file": item.file,
                "line": item.line,
                "text": item.text,
                "context": list(item.context),
            }
        )

    return {
        # Knowledge context used for this analytical result.
        "knowledge_snapshot": knowledge_snapshot,

        # Canonical analytical model
        "metadata": {
            "target": canonical_scan.metadata.target,
            "generated_at": canonical_scan.metadata.generated_at,
            "prototype_scope": (
                canonical_scan.metadata.prototype_scope
            ),
        },
        "summary": {
            "total_files_scanned": (
                canonical_scan.summary.total_files_scanned
            ),
            "total_artifacts": (
                canonical_scan.summary.total_artifacts
            ),
            "security_risk_summary": dict(
                canonical_scan.summary.security_risk_summary
            ),
            "quantum_relevant_assets": (
                canonical_scan.summary.quantum_relevant_assets
            ),
        },
        "applications": applications,
        "components": components,
        "business_contexts": [
            {
                "context_id": context.context_id,
                "application_id": context.application_id,
                "business_unit": context.business_unit,
                "owner": context.owner,
                "service": context.service,
                "data_classification": context.data_classification,
                "data_lifetime_years": context.data_lifetime_years,
                "operational_criticality": context.operational_criticality,
                "financial_impact": context.financial_impact,
                "regulatory_exposure": context.regulatory_exposure,
                "customer_impact": context.customer_impact,
                "risk_appetite": context.risk_appetite,
                "source": context.source,
                "confidence": context.confidence,
                "evidence_ids": list(context.evidence_ids),
            }
            for context in canonical_scan.business_contexts
        ],
        "evidence": evidence,
        "relationships": relationships,
        "risk_assessments": risk_assessments,
        "mosca_assessments": mosca_assessments,
        "recommendations": recommendations,
        "migration_options": migration_options,
        "verification": verification,
        "canonical_artifacts": canonical_artifacts,
        "risk_landscape": risk_landscape,

        # Legacy compatibility
        "target": scan_results.get("target"),
        "generated_at": scan_results.get("generated_at"),
        "prototype_scope": scan_results.get(
            "prototype_scope"
        ),
        "total_files_scanned": scan_results.get(
            "total_files_scanned",
            0,
        ),
        "total_artifacts": scan_results.get(
            "total_artifacts",
            len(scan_results.get("artifacts", [])),
        ),
        "quantum_vulnerable_assets": scan_results.get(
            "quantum_vulnerable_assets",
            0,
        ),
        "risk_summary": dict(
            scan_results.get(
                "risk_summary",
                {},
            )
        ),
        "mosca_inputs": mosca_inputs or {},
        "artifacts": [
            build_artifact_record(
                artifact,
                mosca_inputs=mosca_inputs,
            )
            for artifact in scan_results.get(
                "artifacts",
                [],
            )
        ],
    }
