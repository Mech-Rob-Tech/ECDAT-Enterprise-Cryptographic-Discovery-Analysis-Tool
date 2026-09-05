from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from typing import Iterable, Optional

from knowledge.conflicts import (
    detect_algorithm_conflicts,
    resolve_conflicts,
)
from knowledge.schema import (
    AlgorithmKnowledge,
    CompatibilityConstraint,
    KnowledgeManifest,
    KnowledgeProvenance,
    KnowledgeRegistry,
    MigrationRelationship,
    SecurityStrength,
    StandardKnowledge,
    SCHEMA_VERSION,
)
from knowledge.validation import validate_registry


KNOWLEDGE_VERSION = "0.5.0"


def _provenance() -> tuple[KnowledgeProvenance, ...]:
    return (
        KnowledgeProvenance(
            source_id="nist:pqc",
            source_type="official_web",
            authority="NIST",
            title="Post-Quantum Cryptography",
            uri="https://www.nist.gov/pqc",
            retrieved_at="2026-09-05",
        ),
        KnowledgeProvenance(
            source_id="nist:fips-203",
            source_type="standard",
            authority="NIST",
            title="FIPS 203: Module-Lattice-Based Key-Encapsulation Mechanism Standard",
            uri="https://csrc.nist.gov/pubs/fips/203/final",
            published_at="2024-08-13",
            effective_from="2024-08-13",
            retrieved_at="2026-09-05",
        ),
        KnowledgeProvenance(
            source_id="nist:fips-204",
            source_type="standard",
            authority="NIST",
            title="FIPS 204: Module-Lattice-Based Digital Signature Standard",
            uri="https://csrc.nist.gov/pubs/fips/204/final",
            published_at="2024-08-13",
            effective_from="2024-08-13",
            retrieved_at="2026-09-05",
        ),
        KnowledgeProvenance(
            source_id="nist:fips-205",
            source_type="standard",
            authority="NIST",
            title="FIPS 205: Stateless Hash-Based Digital Signature Standard",
            uri="https://csrc.nist.gov/pubs/fips/205/final",
            published_at="2024-08-13",
            effective_from="2024-08-13",
            retrieved_at="2026-09-05",
        ),
        KnowledgeProvenance(
            source_id="ietf:rfc-10024",
            source_type="rfc",
            authority="IETF",
            title="Post-quantum Hybrid Key Exchange for TLS 1.3",
            uri="https://datatracker.ietf.org/doc/rfc10024/",
            published_at="2026-08-04",
            effective_from="2026-08-04",
            retrieved_at="2026-09-05",
        ),
        KnowledgeProvenance(
            source_id="nist:crypto-agility",
            source_type="official_web",
            authority="NIST",
            title="Crypto Agility",
            uri="https://csrc.nist.gov/projects/crypto-agility",
            retrieved_at="2026-09-05",
        ),
    )


def _algorithms() -> tuple[AlgorithmKnowledge, ...]:
    return (
        AlgorithmKnowledge(
            knowledge_id="alg:rsa",
            name="RSA",
            aliases=("RSA", "RSA-2048", "RSA-3072", "RSA-4096"),
            family="RSA",
            primitive="signature",
            purposes=("digital_signature", "key_establishment", "encryption"),
            lifecycle_status="active",
            quantum_posture="quantum_vulnerable",
            security_strength=SecurityStrength(
                classical_bits=112,
                quantum_bits=None,
                basis="Key-size dependent classical security estimate.",
            ),
            key_sizes=(2048, 3072, 4096),
            standards=("PKCS#1",),
            description="Integer-factorization public-key cryptography.",
            notes="Quantum-vulnerable public-key primitive; exact migration depends on purpose and protocol.",
            effective_from=None,
            effective_until=None,
            source_ids=("nist:pqc",),
            confidence="high",
        ),
        AlgorithmKnowledge(
            knowledge_id="alg:ecdsa",
            name="ECDSA",
            aliases=("ECDSA", "EC", "Elliptic Curve Digital Signature Algorithm"),
            family="ECC",
            primitive="signature",
            purposes=("digital_signature",),
            lifecycle_status="active",
            quantum_posture="quantum_vulnerable",
            security_strength=SecurityStrength(
                classical_bits=128,
                basis="Curve dependent classical security estimate.",
            ),
            key_sizes=(256, 384, 521),
            standards=("FIPS 186-5",),
            description="Elliptic-curve digital signature algorithm.",
            notes="Quantum-vulnerable public-key signature primitive.",
            effective_from=None,
            effective_until=None,
            source_ids=("nist:pqc",),
            confidence="high",
        ),
        AlgorithmKnowledge(
            knowledge_id="alg:ecdh",
            name="ECDH",
            aliases=("ECDH", "Elliptic Curve Diffie-Hellman"),
            family="ECC",
            primitive="key_exchange",
            purposes=("key_establishment",),
            lifecycle_status="active",
            quantum_posture="quantum_vulnerable",
            security_strength=SecurityStrength(
                classical_bits=128,
                basis="Curve dependent classical security estimate.",
            ),
            key_sizes=(256, 384, 521),
            standards=(),
            description="Elliptic-curve key agreement.",
            notes="Quantum-vulnerable public-key key-establishment primitive.",
            effective_from=None,
            effective_until=None,
            source_ids=("nist:pqc",),
            confidence="high",
        ),
        AlgorithmKnowledge(
            knowledge_id="alg:dh",
            name="Diffie-Hellman",
            aliases=("Diffie-Hellman", "DH", "DHE"),
            family="finite_field",
            primitive="key_exchange",
            purposes=("key_establishment",),
            lifecycle_status="active",
            quantum_posture="quantum_vulnerable",
            security_strength=SecurityStrength(
                classical_bits=112,
                basis="Parameter dependent classical security estimate.",
            ),
            key_sizes=(2048, 3072, 4096),
            standards=(),
            description="Finite-field Diffie-Hellman key agreement.",
            notes="Quantum-vulnerable public-key key-establishment primitive.",
            effective_from=None,
            effective_until=None,
            source_ids=("nist:pqc",),
            confidence="high",
        ),
        AlgorithmKnowledge(
            knowledge_id="alg:ml-kem",
            name="ML-KEM",
            aliases=(
                "ML-KEM",
                "MLKEM",
                "Module-Lattice-Based Key-Encapsulation Mechanism",
            ),
            family="module_lattice",
            primitive="kem",
            purposes=("key_establishment",),
            lifecycle_status="standardized",
            quantum_posture="quantum_resistant",
            security_strength=SecurityStrength(
                quantum_bits=None,
                basis="Security levels are parameter-set dependent; see FIPS 203.",
            ),
            key_sizes=(),
            standards=("FIPS 203",),
            description="NIST standardized module-lattice-based KEM.",
            notes="Use a specific parameter set and implementation profile when assessing compatibility.",
            effective_from="2024-08-13",
            effective_until=None,
            source_ids=("nist:fips-203",),
            confidence="high",
        ),
        AlgorithmKnowledge(
            knowledge_id="alg:ml-dsa",
            name="ML-DSA",
            aliases=(
                "ML-DSA",
                "MLDSA",
                "Module-Lattice-Based Digital Signature Algorithm",
            ),
            family="module_lattice",
            primitive="signature",
            purposes=("digital_signature",),
            lifecycle_status="standardized",
            quantum_posture="quantum_resistant",
            security_strength=SecurityStrength(
                quantum_bits=None,
                basis="Security levels are parameter-set dependent; see FIPS 204.",
            ),
            key_sizes=(),
            standards=("FIPS 204",),
            description="NIST standardized module-lattice-based digital signature algorithm.",
            notes="Use a specific parameter set and implementation profile when assessing compatibility.",
            effective_from="2024-08-13",
            effective_until=None,
            source_ids=("nist:fips-204",),
            confidence="high",
        ),
        AlgorithmKnowledge(
            knowledge_id="alg:slh-dsa",
            name="SLH-DSA",
            aliases=(
                "SLH-DSA",
                "SLHDSA",
                "Stateless Hash-Based Digital Signature Algorithm",
            ),
            family="hash_based",
            primitive="signature",
            purposes=("digital_signature",),
            lifecycle_status="standardized",
            quantum_posture="quantum_resistant",
            security_strength=SecurityStrength(
                quantum_bits=None,
                basis="Security levels are parameter-set dependent; see FIPS 205.",
            ),
            key_sizes=(),
            standards=("FIPS 205",),
            description="NIST standardized stateless hash-based digital signature algorithm.",
            notes="Parameter-set selection and implementation constraints must be evaluated.",
            effective_from="2024-08-13",
            effective_until=None,
            source_ids=("nist:fips-205",),
            confidence="high",
        ),
        AlgorithmKnowledge(
            knowledge_id="alg:x25519mlkem768",
            name="X25519MLKEM768",
            aliases=(
                "X25519MLKEM768",
                "X25519-MLKEM-768",
            ),
            family="hybrid",
            primitive="composite",
            purposes=("key_establishment",),
            lifecycle_status="standardized",
            quantum_posture="quantum_resistant",
            security_strength=SecurityStrength(
                basis="Hybrid TLS 1.3 mechanism combining X25519 with ML-KEM-768.",
            ),
            key_sizes=(),
            standards=("RFC 10024",),
            description="Hybrid TLS 1.3 key-establishment mechanism combining X25519 and ML-KEM-768.",
            notes="Compatibility is protocol and implementation dependent.",
            effective_from="2026-08-04",
            effective_until=None,
            source_ids=("ietf:rfc-10024",),
            confidence="high",
        ),
        AlgorithmKnowledge(
            knowledge_id="alg:secp256r1mlkem768",
            name="SecP256r1MLKEM768",
            aliases=(
                "SecP256r1MLKEM768",
                "P256MLKEM768",
            ),
            family="hybrid",
            primitive="composite",
            purposes=("key_establishment",),
            lifecycle_status="standardized",
            quantum_posture="quantum_resistant",
            security_strength=SecurityStrength(
                basis="Hybrid TLS 1.3 mechanism combining secP256r1 with ML-KEM-768.",
            ),
            key_sizes=(),
            standards=("RFC 10024",),
            description="Hybrid TLS 1.3 key-establishment mechanism combining secP256r1 and ML-KEM-768.",
            notes="Compatibility is protocol and implementation dependent.",
            effective_from="2026-08-04",
            effective_until=None,
            source_ids=("ietf:rfc-10024",),
            confidence="high",
        ),
        AlgorithmKnowledge(
            knowledge_id="alg:secp384r1mlkem1024",
            name="SecP384r1MLKEM1024",
            aliases=(
                "SecP384r1MLKEM1024",
                "P384MLKEM1024",
            ),
            family="hybrid",
            primitive="composite",
            purposes=("key_establishment",),
            lifecycle_status="standardized",
            quantum_posture="quantum_resistant",
            security_strength=SecurityStrength(
                basis="Hybrid TLS 1.3 mechanism combining secP384r1 with ML-KEM-1024.",
            ),
            key_sizes=(),
            standards=("RFC 10024",),
            description="Hybrid TLS 1.3 key-establishment mechanism combining secP384r1 and ML-KEM-1024.",
            notes="Compatibility is protocol and implementation dependent.",
            effective_from="2026-08-04",
            effective_until=None,
            source_ids=("ietf:rfc-10024",),
            confidence="high",
        ),
        AlgorithmKnowledge(
            knowledge_id="alg:aes",
            name="AES",
            aliases=("AES", "AES-128", "AES-192", "AES-256"),
            family="AES",
            primitive="encryption",
            purposes=("encryption",),
            lifecycle_status="active",
            quantum_posture="quantum_dependent",
            security_strength=SecurityStrength(
                classical_bits=128,
                basis="Key-size dependent; quantum security requires appropriate analysis.",
            ),
            key_sizes=(128, 192, 256),
            standards=("FIPS 197",),
            description="Advanced Encryption Standard.",
            notes="Symmetric cryptography is affected differently by quantum search than public-key cryptography.",
            effective_from=None,
            effective_until=None,
            source_ids=("nist:pqc",),
            confidence="high",
        ),
        AlgorithmKnowledge(
            knowledge_id="alg:sha-2",
            name="SHA-256",
            aliases=("SHA-256", "SHA256"),
            family="SHA-2",
            primitive="hash",
            purposes=("hash", "integrity"),
            lifecycle_status="active",
            quantum_posture="quantum_dependent",
            security_strength=SecurityStrength(
                classical_bits=128,
                basis="Digest-length dependent security assessment.",
            ),
            key_sizes=(),
            standards=("FIPS 180-4",),
            description="SHA-2 family hash function.",
            notes="Quantum impact differs between collision and preimage properties; do not treat as equivalent to public-key breakage.",
            effective_from=None,
            effective_until=None,
            source_ids=("nist:pqc",),
            confidence="high",
        ),
        AlgorithmKnowledge(
            knowledge_id="alg:sha-1",
            name="SHA-1",
            aliases=("SHA-1", "SHA1"),
            family="SHA",
            primitive="hash",
            purposes=("hash", "integrity"),
            lifecycle_status="deprecated",
            quantum_posture="quantum_vulnerable",
            security_strength=SecurityStrength(
                classical_bits=0,
                basis="Collision attacks are practical.",
            ),
            key_sizes=(),
            standards=(),
            description="Legacy cryptographic hash function.",
            notes="Deprecated and unsuitable for modern security-sensitive cryptographic uses.",
            effective_from=None,
            effective_until=None,
            source_ids=("nist:pqc",),
            confidence="high",
        ),
        AlgorithmKnowledge(
            knowledge_id="alg:md5",
            name="MD5",
            aliases=("MD5",),
            family="MD",
            primitive="hash",
            purposes=("hash", "integrity"),
            lifecycle_status="deprecated",
            quantum_posture="quantum_vulnerable",
            security_strength=SecurityStrength(
                classical_bits=0,
                basis="Collision attacks are practical.",
            ),
            key_sizes=(),
            standards=(),
            description="Legacy cryptographic hash function.",
            notes="Unsuitable for security-sensitive integrity or authentication applications.",
            effective_from=None,
            effective_until=None,
            source_ids=("nist:pqc",),
            confidence="high",
        ),
        AlgorithmKnowledge(
            knowledge_id="alg:des",
            name="DES",
            aliases=("DES",),
            family="DES",
            primitive="encryption",
            purposes=("encryption",),
            lifecycle_status="deprecated",
            quantum_posture="quantum_dependent",
            security_strength=SecurityStrength(
                classical_bits=56,
                basis="56-bit key.",
            ),
            key_sizes=(56,),
            standards=(),
            description="Legacy Data Encryption Standard.",
            notes="Legacy cipher with inadequate classical security.",
            effective_from=None,
            effective_until=None,
            source_ids=("nist:pqc",),
            confidence="high",
        ),
    )


def _standards() -> tuple[StandardKnowledge, ...]:
    return (
        StandardKnowledge(
            standard_id="standard:fips-203",
            authority="NIST",
            identifier="FIPS 203",
            title="Module-Lattice-Based Key-Encapsulation Mechanism Standard",
            status="final",
            published_at="2024-08-13",
            effective_from="2024-08-13",
            effective_until=None,
            related_algorithms=("ML-KEM",),
            supersedes=(),
            source_ids=("nist:fips-203",),
            confidence="high",
        ),
        StandardKnowledge(
            standard_id="standard:fips-204",
            authority="NIST",
            identifier="FIPS 204",
            title="Module-Lattice-Based Digital Signature Standard",
            status="final",
            published_at="2024-08-13",
            effective_from="2024-08-13",
            effective_until=None,
            related_algorithms=("ML-DSA",),
            supersedes=(),
            source_ids=("nist:fips-204",),
            confidence="high",
        ),
        StandardKnowledge(
            standard_id="standard:fips-205",
            authority="NIST",
            identifier="FIPS 205",
            title="Stateless Hash-Based Digital Signature Standard",
            status="final",
            published_at="2024-08-13",
            effective_from="2024-08-13",
            effective_until=None,
            related_algorithms=("SLH-DSA",),
            supersedes=(),
            source_ids=("nist:fips-205",),
            confidence="high",
        ),
        StandardKnowledge(
            standard_id="standard:rfc-10024",
            authority="IETF",
            identifier="RFC 10024",
            title="Post-quantum Hybrid Key Exchange for TLS 1.3",
            status="published",
            published_at="2026-08-04",
            effective_from="2026-08-04",
            effective_until=None,
            related_algorithms=(
                "ML-KEM",
                "X25519MLKEM768",
                "SecP256r1MLKEM768",
                "SecP384r1MLKEM1024",
            ),
            supersedes=(),
            source_ids=("ietf:rfc-10024",),
            confidence="high",
        ),
    )


def _compatibility() -> tuple[CompatibilityConstraint, ...]:
    return (
        CompatibilityConstraint(
            compatibility_id="compat:tls:x25519mlkem768",
            algorithm="X25519MLKEM768",
            target_type="protocol",
            target_name="TLS 1.3",
            version_min=None,
            version_max=None,
            status="supported",
            constraints=(
                "Requires an implementation supporting the specified TLS hybrid group.",
                "Interoperability must be tested against the selected peer implementation.",
            ),
            source_ids=("ietf:rfc-10024",),
            effective_from="2026-08-04",
            effective_until=None,
            confidence="high",
        ),
        CompatibilityConstraint(
            compatibility_id="compat:tls:secp256r1mlkem768",
            algorithm="SecP256r1MLKEM768",
            target_type="protocol",
            target_name="TLS 1.3",
            version_min=None,
            version_max=None,
            status="supported",
            constraints=(
                "Requires an implementation supporting the specified TLS hybrid group.",
                "Interoperability must be tested against the selected peer implementation.",
            ),
            source_ids=("ietf:rfc-10024",),
            effective_from="2026-08-04",
            effective_until=None,
            confidence="high",
        ),
        CompatibilityConstraint(
            compatibility_id="compat:tls:secp384r1mlkem1024",
            algorithm="SecP384r1MLKEM1024",
            target_type="protocol",
            target_name="TLS 1.3",
            version_min=None,
            version_max=None,
            status="supported",
            constraints=(
                "Requires an implementation supporting the specified TLS hybrid group.",
                "Interoperability must be tested against the selected peer implementation.",
            ),
            source_ids=("ietf:rfc-10024",),
            effective_from="2026-08-04",
            effective_until=None,
            confidence="high",
        ),
    )


def _migrations() -> tuple[MigrationRelationship, ...]:
    return (
        MigrationRelationship(
            relationship_id="migration:rsa:ml-dsa",
            source_algorithm="RSA",
            target_algorithm="ML-DSA",
            relationship_type="replaces",
            applicable_purposes=("digital_signature",),
            hybrid=False,
            prerequisites=(
                "Confirm signature semantics and library support.",
                "Validate key/certificate/protocol dependencies.",
            ),
            constraints=(
                "Not a drop-in replacement for RSA encryption or key establishment.",
            ),
            source_ids=("nist:fips-204",),
            effective_from="2024-08-13",
            effective_until=None,
            confidence="high",
        ),
        MigrationRelationship(
            relationship_id="migration:ecdsa:ml-dsa",
            source_algorithm="ECDSA",
            target_algorithm="ML-DSA",
            relationship_type="replaces",
            applicable_purposes=("digital_signature",),
            hybrid=False,
            prerequisites=(
                "Confirm signature format and verifier compatibility.",
            ),
            constraints=(
                "Certificate and protocol support must be evaluated separately.",
            ),
            source_ids=("nist:fips-204",),
            effective_from="2024-08-13",
            effective_until=None,
            confidence="high",
        ),
        MigrationRelationship(
            relationship_id="migration:ecdh:ml-kem",
            source_algorithm="ECDH",
            target_algorithm="ML-KEM",
            relationship_type="replaces",
            applicable_purposes=("key_establishment",),
            hybrid=False,
            prerequisites=(
                "Validate protocol and peer interoperability.",
            ),
            constraints=(
                "Requires a KEM-capable protocol and implementation.",
            ),
            source_ids=("nist:fips-203",),
            effective_from="2024-08-13",
            effective_until=None,
            confidence="high",
        ),
        MigrationRelationship(
            relationship_id="migration:dh:ml-kem",
            source_algorithm="Diffie-Hellman",
            target_algorithm="ML-KEM",
            relationship_type="replaces",
            applicable_purposes=("key_establishment",),
            hybrid=False,
            prerequisites=(
                "Validate protocol and peer interoperability.",
            ),
            constraints=(
                "Requires a KEM-capable protocol and implementation.",
            ),
            source_ids=("nist:fips-203",),
            effective_from="2024-08-13",
            effective_until=None,
            confidence="high",
        ),
        MigrationRelationship(
            relationship_id="migration:rsa:ml-kem",
            source_algorithm="RSA",
            target_algorithm="ML-KEM",
            relationship_type="replaces",
            applicable_purposes=("key_establishment",),
            hybrid=False,
            prerequisites=(
                "Determine the actual RSA purpose before applying this candidate.",
            ),
            constraints=(
                "ML-KEM is a KEM and is not a replacement for RSA signatures.",
            ),
            source_ids=("nist:fips-203",),
            effective_from="2024-08-13",
            effective_until=None,
            confidence="high",
        ),
        MigrationRelationship(
            relationship_id="migration:rsa:ml-dsa-hybrid",
            source_algorithm="RSA",
            target_algorithm="ML-DSA",
            relationship_type="hybrid_with",
            applicable_purposes=("digital_signature",),
            hybrid=True,
            prerequisites=(
                "Protocol must support a defined hybrid/composite construction.",
                "Both classical and PQ verification paths must be validated.",
            ),
            constraints=(
                "Generic concatenation is not automatically a standardized hybrid signature.",
            ),
            source_ids=("nist:fips-204",),
            effective_from="2024-08-13",
            effective_until=None,
            confidence="medium",
        ),
        MigrationRelationship(
            relationship_id="migration:ecdsa:ml-dsa-hybrid",
            source_algorithm="ECDSA",
            target_algorithm="ML-DSA",
            relationship_type="hybrid_with",
            applicable_purposes=("digital_signature",),
            hybrid=True,
            prerequisites=(
                "Protocol must define the hybrid construction.",
                "Both classical and PQ verification paths must be validated.",
            ),
            constraints=(
                "Do not assume universal hybrid certificate or protocol support.",
            ),
            source_ids=("nist:fips-204",),
            effective_from="2024-08-13",
            effective_until=None,
            confidence="medium",
        ),
    )


def _registry_payload(
    algorithms,
    standards,
    compatibility,
    migrations,
    provenance,
):
    payload = {
        "algorithms": [
            {
                "knowledge_id": item.knowledge_id,
                "name": item.name,
                "version": item.record_version,
                "status": item.lifecycle_status,
                "quantum": item.quantum_posture,
                "sources": item.source_ids,
            }
            for item in algorithms
        ],
        "standards": [
            {
                "standard_id": item.standard_id,
                "identifier": item.identifier,
                "status": item.status,
            }
            for item in standards
        ],
        "compatibility": [
            {
                "compatibility_id": item.compatibility_id,
                "algorithm": item.algorithm,
                "target": item.target_name,
                "status": item.status,
            }
            for item in compatibility
        ],
        "migrations": [
            {
                "relationship_id": item.relationship_id,
                "source": item.source_algorithm,
                "target": item.target_algorithm,
                "type": item.relationship_type,
            }
            for item in migrations
        ],
        "sources": [
            {
                "source_id": item.source_id,
                "authority": item.authority,
                "uri": item.uri,
            }
            for item in provenance
        ],
    }

    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
    )


def build_registry() -> KnowledgeRegistry:
    provenance = _provenance()
    algorithms = _algorithms()
    standards = _standards()
    compatibility = _compatibility()
    migrations = _migrations()

    conflicts = tuple(
        resolve_conflicts(
            detect_algorithm_conflicts(algorithms)
        )
    )

    payload = _registry_payload(
        algorithms,
        standards,
        compatibility,
        migrations,
        provenance,
    )

    registry_hash = hashlib.sha256(
        payload.encode("utf-8")
    ).hexdigest()

    manifest = KnowledgeManifest(
        schema_version=SCHEMA_VERSION,
        knowledge_version=KNOWLEDGE_VERSION,
        generated_at="2026-09-05",
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
        conflicts=conflicts,
    )

    validate_registry(registry)

    return registry


_DEFAULT_REGISTRY = build_registry()


def get_registry() -> KnowledgeRegistry:
    return _DEFAULT_REGISTRY


def reload_registry() -> KnowledgeRegistry:
    global _DEFAULT_REGISTRY
    _DEFAULT_REGISTRY = build_registry()
    return _DEFAULT_REGISTRY
