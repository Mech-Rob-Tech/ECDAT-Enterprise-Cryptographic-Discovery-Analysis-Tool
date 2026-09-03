from typing import Dict, List, Set, Tuple

from model.schema import ECDATScan


def _duplicate_ids(ids: List[str]) -> List[str]:
    seen: Set[str] = set()
    duplicates: Set[str] = set()

    for item_id in ids:
        if item_id in seen:
            duplicates.add(item_id)
        else:
            seen.add(item_id)

    return sorted(duplicates)


def validate_unique_ids(scan: ECDATScan) -> List[str]:
    errors: List[str] = []

    collections = {
        "applications": [
            item.application_id
            for item in scan.applications
        ],
        "components": [
            item.component_id
            for item in scan.components
        ],
        "artifacts": [
            item.artifact_id
            for item in scan.artifacts
        ],
        "evidence": [
            item.evidence_id
            for item in scan.evidence
        ],
        "risk_assessments": [
            item.assessment_id
            for item in scan.risk_assessments
        ],
        "mosca_assessments": [
            item.assessment_id
            for item in scan.mosca_assessments
        ],
        "recommendations": [
            item.recommendation_id
            for item in scan.recommendations
        ],
        "migration_options": [
            item.option_id
            for item in scan.migration_options
        ],
        "verification": [
            item.verification_id
            for item in scan.verification
        ],
    }

    for collection_name, ids in collections.items():
        duplicates = _duplicate_ids(ids)

        for duplicate in duplicates:
            errors.append(
                f"Duplicate {collection_name} ID: {duplicate}"
            )

    relationship_ids = [
        relationship.relationship_id
        for relationship in scan.relationships
    ]

    for duplicate in _duplicate_ids(relationship_ids):
        errors.append(
            f"Duplicate relationship ID: {duplicate}"
        )

    return errors


def build_valid_entity_ids(scan: ECDATScan) -> Set[str]:
    valid_ids: Set[str] = set()

    valid_ids.update(
        item.application_id
        for item in scan.applications
    )

    valid_ids.update(
        item.component_id
        for item in scan.components
    )

    valid_ids.update(
        item.artifact_id
        for item in scan.artifacts
    )

    valid_ids.update(
        item.evidence_id
        for item in scan.evidence
    )

    valid_ids.update(
        item.assessment_id
        for item in scan.risk_assessments
    )

    valid_ids.update(
        item.assessment_id
        for item in scan.mosca_assessments
    )

    valid_ids.update(
        item.recommendation_id
        for item in scan.recommendations
    )

    valid_ids.update(
        item.option_id
        for item in scan.migration_options
    )

    valid_ids.update(
        item.verification_id
        for item in scan.verification
    )

    return valid_ids


def validate_relationship_endpoints(
    scan: ECDATScan,
) -> List[str]:
    errors: List[str] = []

    valid_ids = build_valid_entity_ids(scan)

    for relationship in scan.relationships:
        if relationship.source_id not in valid_ids:
            errors.append(
                f"Invalid relationship source: "
                f"{relationship.relationship_id} -> "
                f"{relationship.source_id}"
            )

        if relationship.target_id not in valid_ids:
            errors.append(
                f"Invalid relationship target: "
                f"{relationship.relationship_id} -> "
                f"{relationship.target_id}"
            )

    return errors


def build_entity_type_map(
    scan: ECDATScan,
) -> Dict[str, str]:
    """
    Build a map from canonical entity ID to entity type.

    This allows relationship validation to check semantic
    compatibility rather than only checking whether IDs exist.
    """
    entity_types: Dict[str, str] = {}

    for item in scan.applications:
        entity_types[item.application_id] = "Application"

    for item in scan.components:
        entity_types[item.component_id] = "Component"

    for item in scan.artifacts:
        entity_types[item.artifact_id] = "CryptoArtifact"

    for item in scan.evidence:
        entity_types[item.evidence_id] = "Evidence"

    for item in scan.risk_assessments:
        entity_types[item.assessment_id] = "RiskAssessment"

    for item in scan.mosca_assessments:
        entity_types[item.assessment_id] = "MoscaAssessment"

    for item in scan.recommendations:
        entity_types[item.recommendation_id] = "Recommendation"

    for item in scan.migration_options:
        entity_types[item.option_id] = "MigrationOption"

    for item in scan.verification:
        entity_types[item.verification_id] = "VerificationState"

    return entity_types


# Relationship semantic contract:
#
# source type       relationship       target type
#
# Application       contains            Component
# Component         uses                CryptoArtifact
# CryptoArtifact    evidenced_by       Evidence
# CryptoArtifact    has_risk            RiskAssessment
# CryptoArtifact    evaluated_by        MoscaAssessment
# CryptoArtifact    has_recommendation Recommendation
# CryptoArtifact    candidate_for       MigrationOption
# CryptoArtifact    verified_by         VerificationState
#
RELATIONSHIP_CONTRACT: Dict[
    str,
    Tuple[str, str],
] = {
    "contains": (
        "Application",
        "Component",
    ),
    "uses": (
        "Component",
        "CryptoArtifact",
    ),
    "evidenced_by": (
        "CryptoArtifact",
        "Evidence",
    ),
    "has_risk": (
        "CryptoArtifact",
        "RiskAssessment",
    ),
    "evaluated_by": (
        "CryptoArtifact",
        "MoscaAssessment",
    ),
    "has_recommendation": (
        "CryptoArtifact",
        "Recommendation",
    ),
    "candidate_for": (
        "CryptoArtifact",
        "MigrationOption",
    ),
    "verified_by": (
        "CryptoArtifact",
        "VerificationState",
    ),
}


def validate_relationship_semantics(
    scan: ECDATScan,
) -> List[str]:
    """
    Validate that every relationship connects the correct
    canonical entity types.
    """
    errors: List[str] = []

    entity_types = build_entity_type_map(scan)

    for relationship in scan.relationships:
        source_type = entity_types.get(
            relationship.source_id
        )

        target_type = entity_types.get(
            relationship.target_id
        )

        expected = RELATIONSHIP_CONTRACT.get(
            relationship.relationship_type
        )

        if expected is None:
            errors.append(
                f"Unknown relationship type: "
                f"{relationship.relationship_id} -> "
                f"{relationship.relationship_type}"
            )
            continue

        expected_source, expected_target = expected

        if source_type != expected_source:
            errors.append(
                f"Invalid relationship source type: "
                f"{relationship.relationship_id} "
                f"expected {expected_source}, "
                f"got {source_type}"
            )

        if target_type != expected_target:
            errors.append(
                f"Invalid relationship target type: "
                f"{relationship.relationship_id} "
                f"expected {expected_target}, "
                f"got {target_type}"
            )

    return errors


def validate_artifact_completeness(
    scan: ECDATScan,
) -> List[str]:
    errors: List[str] = []

    evidence_ids = {
        evidence.evidence_id
        for evidence in scan.evidence
    }

    component_ids = {
        component.component_id
        for component in scan.components
    }

    risk_ids = {
        assessment.assessment_id
        for assessment in scan.risk_assessments
    }

    recommendation_ids = {
        recommendation.recommendation_id
        for recommendation in scan.recommendations
    }

    verification_ids = {
        verification.verification_id
        for verification in scan.verification
    }

    mosca_ids = {
        assessment.assessment_id
        for assessment in scan.mosca_assessments
    }

    migration_ids = {
        option.option_id
        for option in scan.migration_options
    }

    for artifact in scan.artifacts:
        if not artifact.evidence_ids:
            errors.append(
                f"Artifact has no evidence: "
                f"{artifact.artifact_id}"
            )

        for evidence_id in artifact.evidence_ids:
            if evidence_id not in evidence_ids:
                errors.append(
                    f"Artifact references missing evidence: "
                    f"{artifact.artifact_id} -> {evidence_id}"
                )

        if not artifact.component_id:
            errors.append(
                f"Artifact has no component: "
                f"{artifact.artifact_id}"
            )
        elif artifact.component_id not in component_ids:
            errors.append(
                f"Artifact references missing component: "
                f"{artifact.artifact_id} -> "
                f"{artifact.component_id}"
            )

        if artifact.risk is None:
            errors.append(
                f"Artifact has no risk assessment: "
                f"{artifact.artifact_id}"
            )
        elif artifact.risk.security is not None:
            if (
                artifact.risk.security.assessment_id
                not in risk_ids
            ):
                errors.append(
                    f"Artifact references missing risk assessment: "
                    f"{artifact.artifact_id} -> "
                    f"{artifact.risk.security.assessment_id}"
                )

        if not artifact.recommendation_ids:
            errors.append(
                f"Artifact has no recommendation: "
                f"{artifact.artifact_id}"
            )

        for recommendation_id in artifact.recommendation_ids:
            if recommendation_id not in recommendation_ids:
                errors.append(
                    f"Artifact references missing recommendation: "
                    f"{artifact.artifact_id} -> "
                    f"{recommendation_id}"
                )

        for migration_id in artifact.migration_option_ids:
            if migration_id not in migration_ids:
                errors.append(
                    f"Artifact references missing migration option: "
                    f"{artifact.artifact_id} -> "
                    f"{migration_id}"
                )

        if not artifact.verification_id:
            errors.append(
                f"Artifact has no verification state: "
                f"{artifact.artifact_id}"
            )
        elif artifact.verification_id not in verification_ids:
            errors.append(
                f"Artifact references missing verification state: "
                f"{artifact.artifact_id} -> "
                f"{artifact.verification_id}"
            )

        if artifact.mosca is not None:
            if artifact.mosca.assessment_id not in mosca_ids:
                errors.append(
                    f"Artifact references missing MOSCA assessment: "
                    f"{artifact.artifact_id} -> "
                    f"{artifact.mosca.assessment_id}"
                )

    return errors


def validate_recommendation_reachability(
    scan: ECDATScan,
) -> List[str]:
    errors: List[str] = []

    referenced_ids = {
        recommendation_id
        for artifact in scan.artifacts
        for recommendation_id in artifact.recommendation_ids
    }

    for recommendation in scan.recommendations:
        if recommendation.recommendation_id not in referenced_ids:
            errors.append(
                f"Orphan recommendation: "
                f"{recommendation.recommendation_id}"
            )

    return errors


def validate_migration_reachability(
    scan: ECDATScan,
) -> List[str]:
    errors: List[str] = []

    referenced_ids = {
        migration_id
        for artifact in scan.artifacts
        for migration_id in artifact.migration_option_ids
    }

    for option in scan.migration_options:
        if option.option_id not in referenced_ids:
            errors.append(
                f"Orphan migration option: "
                f"{option.option_id}"
            )

    return errors


def validate_analytical_reachability(
    scan: ECDATScan,
) -> List[str]:
    errors: List[str] = []

    referenced_risk_ids = {
        artifact.risk.security.assessment_id
        for artifact in scan.artifacts
        if artifact.risk is not None
        and artifact.risk.security is not None
    }

    for assessment in scan.risk_assessments:
        if assessment.assessment_id not in referenced_risk_ids:
            errors.append(
                f"Orphan risk assessment: "
                f"{assessment.assessment_id}"
            )

    referenced_mosca_ids = {
        artifact.mosca.assessment_id
        for artifact in scan.artifacts
        if artifact.mosca is not None
    }

    for assessment in scan.mosca_assessments:
        if assessment.assessment_id not in referenced_mosca_ids:
            errors.append(
                f"Orphan MOSCA assessment: "
                f"{assessment.assessment_id}"
            )

    referenced_verification_ids = {
        artifact.verification_id
        for artifact in scan.artifacts
        if artifact.verification_id
    }

    for verification in scan.verification:
        if verification.verification_id not in referenced_verification_ids:
            errors.append(
                f"Orphan verification state: "
                f"{verification.verification_id}"
            )

    return errors


def validate_canonical_scan(
    scan: ECDATScan,
) -> List[str]:
    """
    Run all canonical graph validation checks.

    An empty list means the canonical graph passed validation.
    """
    errors: List[str] = []

    errors.extend(
        validate_unique_ids(scan)
    )

    errors.extend(
        validate_relationship_endpoints(scan)
    )

    errors.extend(
        validate_relationship_semantics(scan)
    )

    errors.extend(
        validate_artifact_completeness(scan)
    )

    errors.extend(
        validate_recommendation_reachability(scan)
    )

    errors.extend(
        validate_migration_reachability(scan)
    )

    errors.extend(
        validate_analytical_reachability(scan)
    )

    return errors
