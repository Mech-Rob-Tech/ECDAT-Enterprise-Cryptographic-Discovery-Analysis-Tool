from __future__ import annotations

from typing import Iterable

from knowledge.schema import (
    AlgorithmKnowledge,
    CompatibilityConstraint,
    KnowledgeRegistry,
    MigrationRelationship,
    StandardKnowledge,
    VALID_COMPATIBILITY_STATUS,
    VALID_CONFIDENCE,
    VALID_PRIMITIVES,
    VALID_QUANTUM_POSTURES,
    VALID_RELATIONSHIP_TYPES,
)
from knowledge.lifecycle import validate_status
from knowledge.provenance import validate_provenance


def _require(value, field: str, record_id: str):
    if value is None or value == "":
        raise ValueError(
            f"{record_id}: missing required field '{field}'"
        )


def validate_algorithm(
    algorithm: AlgorithmKnowledge,
) -> None:
    _require(algorithm.name, "name", algorithm.knowledge_id)

    if algorithm.primitive not in VALID_PRIMITIVES:
        raise ValueError(
            f"{algorithm.knowledge_id}: invalid primitive"
        )

    if algorithm.quantum_posture not in VALID_QUANTUM_POSTURES:
        raise ValueError(
            f"{algorithm.knowledge_id}: invalid quantum posture"
        )

    if algorithm.confidence not in VALID_CONFIDENCE:
        raise ValueError(
            f"{algorithm.knowledge_id}: invalid confidence"
        )

    validate_status(algorithm.lifecycle_status)

    if any(size <= 0 for size in algorithm.key_sizes):
        raise ValueError(
            f"{algorithm.knowledge_id}: invalid key size"
        )

    if not algorithm.source_ids:
        raise ValueError(
            f"{algorithm.knowledge_id}: no provenance"
        )


def validate_standard(
    standard: StandardKnowledge,
) -> None:
    _require(standard.identifier, "identifier", standard.standard_id)
    _require(standard.authority, "authority", standard.standard_id)

    if standard.confidence not in VALID_CONFIDENCE:
        raise ValueError(
            f"{standard.standard_id}: invalid confidence"
        )

    if not standard.source_ids:
        raise ValueError(
            f"{standard.standard_id}: no provenance"
        )


def validate_compatibility(
    compatibility: CompatibilityConstraint,
) -> None:
    if compatibility.status not in VALID_COMPATIBILITY_STATUS:
        raise ValueError(
            f"{compatibility.compatibility_id}: invalid status"
        )

    if compatibility.confidence not in VALID_CONFIDENCE:
        raise ValueError(
            f"{compatibility.compatibility_id}: invalid confidence"
        )

    if not compatibility.source_ids:
        raise ValueError(
            f"{compatibility.compatibility_id}: no provenance"
        )


def validate_migration(
    migration: MigrationRelationship,
) -> None:
    if migration.relationship_type not in VALID_RELATIONSHIP_TYPES:
        raise ValueError(
            f"{migration.relationship_id}: invalid relationship type"
        )

    if migration.source_algorithm.upper() == migration.target_algorithm.upper():
        raise ValueError(
            f"{migration.relationship_id}: self migration"
        )

    if migration.confidence not in VALID_CONFIDENCE:
        raise ValueError(
            f"{migration.relationship_id}: invalid confidence"
        )

    if not migration.source_ids:
        raise ValueError(
            f"{migration.relationship_id}: no provenance"
        )


def validate_registry(
    registry: KnowledgeRegistry,
) -> None:
    validate_provenance(registry.provenance)

    algorithm_ids = set()
    for item in registry.algorithms:
        validate_algorithm(item)

        if item.knowledge_id in algorithm_ids:
            raise ValueError(
                f"Duplicate algorithm knowledge ID: {item.knowledge_id}"
            )

        algorithm_ids.add(item.knowledge_id)

        for source_id in item.source_ids:
            if source_id not in {
                source.source_id
                for source in registry.provenance
            }:
                raise ValueError(
                    f"{item.knowledge_id}: unknown source {source_id}"
                )

    standard_ids = set()
    for item in registry.standards:
        validate_standard(item)

        if item.standard_id in standard_ids:
            raise ValueError(
                f"Duplicate standard ID: {item.standard_id}"
            )

        standard_ids.add(item.standard_id)

    for item in registry.compatibility:
        validate_compatibility(item)

    for item in registry.migrations:
        validate_migration(item)

    algorithm_names = {
        item.name.upper()
        for item in registry.algorithms
    }

    for migration in registry.migrations:
        if migration.source_algorithm.upper() not in algorithm_names:
            raise ValueError(
                f"{migration.relationship_id}: unknown source algorithm"
            )

        if migration.target_algorithm.upper() not in algorithm_names:
            raise ValueError(
                f"{migration.relationship_id}: unknown target algorithm"
            )

    expected_counts = {
        "algorithm_count": len(registry.algorithms),
        "standard_count": len(registry.standards),
        "compatibility_count": len(registry.compatibility),
        "migration_count": len(registry.migrations),
        "source_count": len(registry.provenance),
    }

    for field, expected in expected_counts.items():
        actual = getattr(registry.manifest, field)

        if actual != expected:
            raise ValueError(
                f"Manifest mismatch for {field}: "
                f"{actual} != {expected}"
            )
