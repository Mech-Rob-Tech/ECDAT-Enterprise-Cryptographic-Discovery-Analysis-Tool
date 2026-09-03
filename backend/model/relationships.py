from typing import Dict, List

from model.schema import (
    Application,
    Component,
    CryptoArtifact,
    Evidence,
    MigrationOption,
    MoscaAssessment,
    Recommendation,
    Relationship,
    RiskAssessment,
    VerificationState,
)


def relationship_id(
    source_id: str,
    relationship_type: str,
    target_id: str,
) -> str:
    """
    Generate a deterministic relationship identifier.

    The same source, relationship type, and target always produce
    the same relationship ID.
    """
    return f"{source_id}|{relationship_type}|{target_id}"


def build_relationship(
    source_id: str,
    target_id: str,
    relationship_type: str,
    confidence: str = "high",
    evidence_ids: List[str] | None = None,
) -> Relationship:
    """
    Construct a relationship with a deterministic ID.
    """
    return Relationship(
        relationship_id=relationship_id(
            source_id,
            relationship_type,
            target_id,
        ),
        source_id=source_id,
        target_id=target_id,
        relationship_type=relationship_type,
        confidence=confidence,
        evidence_ids=list(evidence_ids or []),
    )


def validate_relationship_endpoints(
    relationships: List[Relationship],
    valid_ids: set[str],
) -> List[str]:
    """
    Return validation errors for relationships whose endpoints
    do not exist in the canonical model.
    """
    errors: List[str] = []

    for relationship in relationships:
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


def build_components(
    application: Application,
    artifacts: List[CryptoArtifact],
    evidence_by_id: Dict[str, Evidence],
) -> List[Component]:
    """
    Build conservative source-file components.

    A component is created only for a source file that contains
    cryptographic evidence.
    """
    component_by_path: Dict[str, Component] = {}

    for artifact in artifacts:
        for evidence_id in artifact.evidence_ids:
            evidence = evidence_by_id.get(evidence_id)

            if evidence is None:
                continue

            path = evidence.file

            if path not in component_by_path:
                component_by_path[path] = Component(
                    component_id=(
                        f"{application.application_id}"
                        f":component:{path}"
                    ),
                    name=path,
                    component_type="source_file",
                    version=None,
                    path=path,
                )

    return list(component_by_path.values())


def map_components_to_artifacts(
    components: List[Component],
    artifacts: List[CryptoArtifact],
    evidence_by_id: Dict[str, Evidence],
) -> None:
    """
    Attach each artifact to the source-file component containing
    its evidence.
    """
    component_by_path = {
        component.path: component
        for component in components
        if component.path
    }

    for artifact in artifacts:
        component = None

        for evidence_id in artifact.evidence_ids:
            evidence = evidence_by_id.get(evidence_id)

            if evidence is None:
                continue

            component = component_by_path.get(evidence.file)

            if component is not None:
                break

        if component is not None:
            artifact.component_id = component.component_id


def build_structural_relationships(
    application: Application,
    components: List[Component],
    artifacts: List[CryptoArtifact],
    evidence_by_id: Dict[str, Evidence],
) -> List[Relationship]:
    """
    Build the structural relationships:

        Application contains Component
        Component uses CryptoArtifact
        CryptoArtifact evidenced_by Evidence
    """
    relationships: List[Relationship] = []

    for component in components:
        relationships.append(
            build_relationship(
                source_id=application.application_id,
                target_id=component.component_id,
                relationship_type="contains",
                confidence="high",
            )
        )

    component_by_id = {
        component.component_id: component
        for component in components
    }

    for artifact in artifacts:
        if artifact.component_id:
            if artifact.component_id in component_by_id:
                relationships.append(
                    build_relationship(
                        source_id=artifact.component_id,
                        target_id=artifact.artifact_id,
                        relationship_type="uses",
                        confidence="high",
                    )
                )

        for evidence_id in artifact.evidence_ids:
            evidence = evidence_by_id.get(evidence_id)

            if evidence is None:
                continue

            relationships.append(
                build_relationship(
                    source_id=artifact.artifact_id,
                    target_id=evidence.evidence_id,
                    relationship_type="evidenced_by",
                    confidence="high",
                    evidence_ids=[evidence.evidence_id],
                )
            )

    return relationships


def build_analytical_relationships(
    artifacts: List[CryptoArtifact],
    risk_assessments: List[RiskAssessment],
    mosca_assessments: List[MoscaAssessment],
    recommendations: List[Recommendation],
    migration_options: List[MigrationOption],
    verification_states: List[VerificationState],
) -> List[Relationship]:
    """
    Build analytical relationships:

        Artifact has_risk RiskAssessment
        Artifact evaluated_by MoscaAssessment
        Artifact has_recommendation Recommendation
        Artifact candidate_for MigrationOption
        Artifact verified_by VerificationState
    """
    relationships: List[Relationship] = []

    risk_by_id = {
        assessment.assessment_id: assessment
        for assessment in risk_assessments
    }

    mosca_by_id = {
        assessment.assessment_id: assessment
        for assessment in mosca_assessments
    }

    recommendation_by_id = {
        recommendation.recommendation_id: recommendation
        for recommendation in recommendations
    }

    migration_by_id = {
        option.option_id: option
        for option in migration_options
    }

    verification_by_id = {
        verification.verification_id: verification
        for verification in verification_states
    }

    for artifact in artifacts:
        if artifact.risk is not None:
            security = artifact.risk.security

            if security is not None:
                if security.assessment_id in risk_by_id:
                    relationships.append(
                        build_relationship(
                            source_id=artifact.artifact_id,
                            target_id=security.assessment_id,
                            relationship_type="has_risk",
                            confidence="high",
                        )
                    )

        if artifact.mosca is not None:
            if artifact.mosca.assessment_id in mosca_by_id:
                relationships.append(
                    build_relationship(
                        source_id=artifact.artifact_id,
                        target_id=artifact.mosca.assessment_id,
                        relationship_type="evaluated_by",
                        confidence="high",
                    )
                )

        for recommendation_id in artifact.recommendation_ids:
            if recommendation_id in recommendation_by_id:
                relationships.append(
                    build_relationship(
                        source_id=artifact.artifact_id,
                        target_id=recommendation_id,
                        relationship_type="has_recommendation",
                        confidence="high",
                    )
                )

        for migration_option_id in artifact.migration_option_ids:
            if migration_option_id in migration_by_id:
                relationships.append(
                    build_relationship(
                        source_id=artifact.artifact_id,
                        target_id=migration_option_id,
                        relationship_type="candidate_for",
                        confidence="high",
                    )
                )

        if artifact.verification_id:
            if artifact.verification_id in verification_by_id:
                relationships.append(
                    build_relationship(
                        source_id=artifact.artifact_id,
                        target_id=artifact.verification_id,
                        relationship_type="verified_by",
                        confidence="high",
                    )
                )

    return relationships


def build_relationships(
    application: Application,
    components: List[Component],
    artifacts: List[CryptoArtifact],
    evidence_by_id: Dict[str, Evidence],
    risk_assessments: List[RiskAssessment],
    mosca_assessments: List[MoscaAssessment],
    recommendations: List[Recommendation],
    migration_options: List[MigrationOption],
    verification_states: List[VerificationState],
) -> List[Relationship]:
    """
    Build the complete canonical relationship set.
    """
    structural = build_structural_relationships(
        application=application,
        components=components,
        artifacts=artifacts,
        evidence_by_id=evidence_by_id,
    )

    analytical = build_analytical_relationships(
        artifacts=artifacts,
        risk_assessments=risk_assessments,
        mosca_assessments=mosca_assessments,
        recommendations=recommendations,
        migration_options=migration_options,
        verification_states=verification_states,
    )

    return structural + analytical
