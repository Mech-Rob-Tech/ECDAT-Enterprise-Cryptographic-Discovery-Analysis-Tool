from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict

from knowledge.schema import (
    AlgorithmKnowledge,
    CompatibilityConstraint,
    KnowledgeManifest,
    KnowledgeProvenance,
    KnowledgeRegistry,
    MigrationRelationship,
    SecurityStrength,
    StandardKnowledge,
)
from knowledge.validation import validate_registry


DATA_PATH = (
    Path(__file__).resolve().parent
    / "data"
    / "registry.json"
)


def _load_raw() -> Dict[str, Any]:
    with DATA_PATH.open(
        "r",
        encoding="utf-8",
    ) as handle:
        return json.load(handle)


def _tuple(value):
    return tuple(value or [])


def _provenance(data):
    return tuple(
        KnowledgeProvenance(
            source_id=item["source_id"],
            source_type=item["source_type"],
            authority=item["authority"],
            title=item["title"],
            uri=item["uri"],
            published_at=item.get("published_at"),
            retrieved_at=item.get("retrieved_at"),
            effective_from=item.get("effective_from"),
            effective_until=item.get("effective_until"),
        )
        for item in data
    )


def _algorithm(item):
    strength = item.get(
        "security_strength",
        {},
    )

    return AlgorithmKnowledge(
        knowledge_id=item["knowledge_id"],
        name=item["name"],
        aliases=_tuple(item.get("aliases")),
        family=item["family"],
        primitive=item["primitive"],
        purposes=_tuple(item.get("purposes")),
        lifecycle_status=item["lifecycle_status"],
        quantum_posture=item["quantum_posture"],
        security_strength=SecurityStrength(
            classical_bits=strength.get("classical_bits"),
            quantum_bits=strength.get("quantum_bits"),
            basis=strength.get("basis"),
        ),
        key_sizes=_tuple(item.get("key_sizes")),
        standards=_tuple(item.get("standards")),
        description=item["description"],
        notes=item["notes"],
        effective_from=item.get("effective_from"),
        effective_until=item.get("effective_until"),
        source_ids=_tuple(item.get("source_ids")),
        confidence=item["confidence"],
        record_version=item.get("record_version", 1),
    )


def _standard(item):
    return StandardKnowledge(
        standard_id=item["standard_id"],
        authority=item["authority"],
        identifier=item["identifier"],
        title=item["title"],
        status=item["status"],
        published_at=item.get("published_at"),
        effective_from=item.get("effective_from"),
        effective_until=item.get("effective_until"),
        related_algorithms=_tuple(
            item.get("related_algorithms")
        ),
        supersedes=_tuple(
            item.get("supersedes")
        ),
        source_ids=_tuple(
            item.get("source_ids")
        ),
        confidence=item["confidence"],
        record_version=item.get("record_version", 1),
    )


def _compatibility(item):
    return CompatibilityConstraint(
        compatibility_id=item["compatibility_id"],
        algorithm=item["algorithm"],
        target_type=item["target_type"],
        target_name=item["target_name"],
        version_min=item.get("version_min"),
        version_max=item.get("version_max"),
        status=item["status"],
        constraints=_tuple(
            item.get("constraints")
        ),
        source_ids=_tuple(
            item.get("source_ids")
        ),
        effective_from=item.get("effective_from"),
        effective_until=item.get("effective_until"),
        confidence=item["confidence"],
        record_version=item.get("record_version", 1),
    )


def _migration(item):
    return MigrationRelationship(
        relationship_id=item["relationship_id"],
        source_algorithm=item["source_algorithm"],
        target_algorithm=item["target_algorithm"],
        relationship_type=item["relationship_type"],
        applicable_purposes=_tuple(
            item.get("applicable_purposes")
        ),
        hybrid=bool(item.get("hybrid", False)),
        prerequisites=_tuple(
            item.get("prerequisites")
        ),
        constraints=_tuple(
            item.get("constraints")
        ),
        source_ids=_tuple(
            item.get("source_ids")
        ),
        effective_from=item.get("effective_from"),
        effective_until=item.get("effective_until"),
        confidence=item["confidence"],
        record_version=item.get("record_version", 1),
    )


def _canonical_hash(data: Dict[str, Any]) -> str:
    canonical = json.dumps(
        data,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )

    return hashlib.sha256(
        canonical.encode("utf-8")
    ).hexdigest()


def load_registry() -> KnowledgeRegistry:
    raw = _load_raw()

    provenance = _provenance(
        raw.get("sources", [])
    )

    algorithms = tuple(
        _algorithm(item)
        for item in raw.get("algorithms", [])
    )

    standards = tuple(
        _standard(item)
        for item in raw.get("standards", [])
    )

    compatibility = tuple(
        _compatibility(item)
        for item in raw.get("compatibility", [])
    )

    migrations = tuple(
        _migration(item)
        for item in raw.get("migrations", [])
    )

    registry_hash = _canonical_hash(raw)

    manifest = KnowledgeManifest(
        schema_version=raw["schema_version"],
        knowledge_version=raw["knowledge_version"],
        generated_at=raw["generated_at"],
        registry_hash=registry_hash,
        source_count=len(provenance),
        algorithm_count=len(algorithms),
        standard_count=len(standards),
        compatibility_count=len(compatibility),
        migration_count=len(migrations),
    )

    registry = KnowledgeRegistry(
        manifest=manifest,
        algorithms=algorithms,
        standards=standards,
        compatibility=compatibility,
        migrations=migrations,
        provenance=provenance,
        conflicts=(),
    )

    validate_registry(registry)

    return registry


_DEFAULT_REGISTRY = load_registry()


def get_registry() -> KnowledgeRegistry:
    return _DEFAULT_REGISTRY


def reload_registry() -> KnowledgeRegistry:
    global _DEFAULT_REGISTRY

    _DEFAULT_REGISTRY = load_registry()

    return _DEFAULT_REGISTRY
