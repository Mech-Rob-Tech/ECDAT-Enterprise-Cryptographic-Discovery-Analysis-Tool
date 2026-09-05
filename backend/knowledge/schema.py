"""
ECDAT v0.5 Cryptographic Knowledge Domain.

The knowledge layer is intentionally data-driven:
cryptographic facts live in versioned records, while the engines
interpret those records deterministically.

No recommendation logic belongs in this module.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Tuple


SCHEMA_VERSION = "1.0.0"

VALID_PRIMITIVES = {
    "signature",
    "kem",
    "key_exchange",
    "encryption",
    "hash",
    "mac",
    "protocol",
    "key_derivation",
    "composite",
    "unknown",
}

VALID_LIFECYCLE_STATUSES = {
    "standardized",
    "approved",
    "active",
    "deprecated",
    "legacy",
    "withdrawn",
    "candidate",
    "draft",
    "unknown",
}

VALID_QUANTUM_POSTURES = {
    "quantum_resistant",
    "quantum_vulnerable",
    "quantum_dependent",
    "not_applicable",
    "unknown",
}

VALID_CONFIDENCE = {
    "high",
    "medium",
    "low",
    "unknown",
}

VALID_RELATIONSHIP_TYPES = {
    "replaces",
    "alternative_to",
    "hybrid_with",
    "compatible_with",
    "requires",
    "supersedes",
    "related_to",
}

VALID_COMPATIBILITY_STATUS = {
    "supported",
    "conditional",
    "unsupported",
    "unknown",
}


@dataclass(frozen=True)
class KnowledgeProvenance:
    source_id: str
    source_type: str
    authority: str
    title: str
    uri: str
    published_at: Optional[str] = None
    retrieved_at: Optional[str] = None
    effective_from: Optional[str] = None
    effective_until: Optional[str] = None
    evidence_hash: Optional[str] = None


@dataclass(frozen=True)
class SecurityStrength:
    classical_bits: Optional[int] = None
    quantum_bits: Optional[int] = None
    basis: Optional[str] = None


@dataclass(frozen=True)
class AlgorithmKnowledge:
    knowledge_id: str
    name: str
    aliases: Tuple[str, ...]
    family: str
    primitive: str
    purposes: Tuple[str, ...]
    lifecycle_status: str
    quantum_posture: str
    security_strength: SecurityStrength
    key_sizes: Tuple[int, ...]
    parameters: Tuple[str, ...]
    components: Tuple[str, ...]
    standards: Tuple[str, ...]
    description: str
    notes: str
    effective_from: Optional[str]
    effective_until: Optional[str]
    source_ids: Tuple[str, ...]
    confidence: str
    record_version: int = 1


@dataclass(frozen=True)
class StandardKnowledge:
    standard_id: str
    authority: str
    identifier: str
    title: str
    status: str
    published_at: Optional[str]
    effective_from: Optional[str]
    effective_until: Optional[str]
    related_algorithms: Tuple[str, ...]
    supersedes: Tuple[str, ...]
    source_ids: Tuple[str, ...]
    confidence: str
    record_version: int = 1


@dataclass(frozen=True)
class CompatibilityConstraint:
    compatibility_id: str
    algorithm: str
    target_type: str
    target_name: str
    version_min: Optional[str]
    version_max: Optional[str]
    status: str
    constraints: Tuple[str, ...]
    source_ids: Tuple[str, ...]
    effective_from: Optional[str]
    effective_until: Optional[str]
    confidence: str
    record_version: int = 1


@dataclass(frozen=True)
class MigrationRelationship:
    relationship_id: str
    source_algorithm: str
    target_algorithm: str
    relationship_type: str
    applicable_purposes: Tuple[str, ...]
    hybrid: bool
    prerequisites: Tuple[str, ...]
    constraints: Tuple[str, ...]
    source_ids: Tuple[str, ...]
    effective_from: Optional[str]
    effective_until: Optional[str]
    confidence: str
    record_version: int = 1


@dataclass(frozen=True)
class KnowledgeConflict:
    conflict_id: str
    subject_type: str
    subject_id: str
    field: str
    values: Tuple[str, ...]
    source_ids: Tuple[str, ...]
    resolution: str
    severity: str


@dataclass(frozen=True)
class KnowledgeManifest:
    schema_version: str
    knowledge_version: str
    generated_at: str
    registry_hash: str
    source_count: int
    algorithm_count: int
    standard_count: int
    compatibility_count: int
    migration_count: int


@dataclass(frozen=True)
class KnowledgeRegistry:
    manifest: KnowledgeManifest
    algorithms: Tuple[AlgorithmKnowledge, ...] = field(default_factory=tuple)
    standards: Tuple[StandardKnowledge, ...] = field(default_factory=tuple)
    compatibility: Tuple[CompatibilityConstraint, ...] = field(default_factory=tuple)
    migrations: Tuple[MigrationRelationship, ...] = field(default_factory=tuple)
    provenance: Tuple[KnowledgeProvenance, ...] = field(default_factory=tuple)
    conflicts: Tuple[KnowledgeConflict, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class KnowledgeResolution:
    query: str
    normalized_query: str
    algorithm: Optional[AlgorithmKnowledge]
    matched_by: Optional[str]
    standards: Tuple[StandardKnowledge, ...]
    compatibility: Tuple[CompatibilityConstraint, ...]
    migrations: Tuple[MigrationRelationship, ...]
    conflicts: Tuple[KnowledgeConflict, ...]
    current: bool
    knowledge_version: str
    explainability: Dict[str, Any]


def dataclass_to_dict(value: Any) -> Any:
    if hasattr(value, "__dataclass_fields__"):
        return {
            key: dataclass_to_dict(item)
            for key, item in asdict(value).items()
        }
    if isinstance(value, tuple):
        return [dataclass_to_dict(item) for item in value]
    if isinstance(value, list):
        return [dataclass_to_dict(item) for item in value]
    if isinstance(value, dict):
        return {
            key: dataclass_to_dict(item)
            for key, item in value.items()
        }
    return value
