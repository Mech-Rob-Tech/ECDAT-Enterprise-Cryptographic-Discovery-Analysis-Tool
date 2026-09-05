"""
ECDAT recommendation engine.

Decision logic is knowledge-driven.

The engine does NOT contain algorithm-specific migration rules.
Cryptographic relationships, lifecycle state, applicability and
compatibility come from backend/knowledge.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from knowledge.service import KnowledgeService


SERVICE = KnowledgeService()


def _artifact_algorithm(artifact: Dict[str, Any]) -> str:
    return str(
        artifact.get("algorithm")
        or artifact.get("algorithm_name")
        or "UNKNOWN"
    ).strip()


def _artifact_purpose(
    artifact: Dict[str, Any],
) -> Optional[str]:
    purpose = artifact.get("purpose")

    if isinstance(purpose, dict):
        purpose = purpose.get("value")

    if purpose:
        return str(purpose).strip().lower()

    return None


def _risk_level(
    artifact: Dict[str, Any],
) -> str:
    risk = artifact.get("risk") or {}

    if isinstance(risk, dict):
        quantum = risk.get("quantum") or {}

        if isinstance(quantum, dict):
            level = quantum.get("level")
            if level:
                return str(level).upper()

    return "UNKNOWN"


def _priority(
    artifact: Dict[str, Any],
    lifecycle_status: str,
) -> str:
    risk = _risk_level(artifact)

    if lifecycle_status in {
        "withdrawn",
        "deprecated",
        "legacy",
    }:
        return "CRITICAL"

    if risk == "CRITICAL":
        return "CRITICAL"

    if risk == "HIGH":
        return "HIGH"

    if risk == "MEDIUM":
        return "MEDIUM"

    if risk == "LOW":
        return "LOW"

    return "REVIEW"


def _candidate_text(
    candidate,
    compatibility_status: Optional[str] = None,
) -> str:
    suffix = ""

    if compatibility_status == "unsupported":
        suffix = " Current target compatibility is unsupported."

    elif compatibility_status == "conditional":
        suffix = " Current target compatibility is conditional."

    elif compatibility_status == "unknown":
        suffix = " Target compatibility is not established."

    if candidate.hybrid:
        return (
            f"Evaluate the hybrid migration relationship "
            f"{candidate.source_algorithm} → {candidate.target_algorithm}."
            f"{suffix}"
        )

    return (
        f"Evaluate migration from "
        f"{candidate.source_algorithm} to "
        f"{candidate.target_algorithm}."
        f"{suffix}"
    )


def get_recommendation(
    artifact: Dict[str, Any],
    *,
    knowledge_service: Optional[KnowledgeService] = None,
    as_of: Optional[str] = None,
) -> str:
    """
    Return the primary explainable recommendation.

    This function intentionally contains no algorithm-specific branches.
    """

    service = knowledge_service or SERVICE

    algorithm = _artifact_algorithm(artifact)
    purpose = _artifact_purpose(artifact)

    result = service.resolve(
        algorithm,
        purpose=purpose,
        as_of=as_of,
    )

    if result.algorithm is None:
        return (
            "Cryptographic knowledge resolution is unresolved for "
            f"'{algorithm}'. Perform manual review before selecting "
            "a migration candidate."
        )

    knowledge = result.algorithm

    if knowledge.lifecycle_status in {
        "withdrawn",
        "deprecated",
        "legacy",
    }:
        candidates = result.migrations

        if candidates:
            target_names = ", ".join(
                sorted(
                    {
                        candidate.target_algorithm
                        for candidate in candidates
                    }
                )
            )

            return (
                f"{knowledge.name} has lifecycle status "
                f"{knowledge.lifecycle_status}. "
                f"Evaluate the knowledge-linked migration candidates: "
                f"{target_names}."
            )

        return (
            f"{knowledge.name} has lifecycle status "
            f"{knowledge.lifecycle_status}. "
            "No validated migration candidate was resolved; "
            "perform manual review."
        )

    if knowledge.quantum_posture == "quantum_vulnerable":
        if result.migrations:
            candidate = result.migrations[0]

            return _candidate_text(
                candidate
            )

        return (
            f"{knowledge.name} is classified as "
            "quantum-vulnerable, but no applicable migration "
            "relationship was resolved for the observed purpose."
        )

    if knowledge.quantum_posture == "quantum_dependent":
        return (
            f"{knowledge.name} requires parameter- and purpose-aware "
            "quantum security assessment rather than automatic "
            "replacement."
        )

    if knowledge.quantum_posture == "quantum_resistant":
        return (
            f"{knowledge.name} is currently classified as "
            "quantum-resistant according to the active knowledge "
            "snapshot. Continue validating implementation and "
            "protocol compatibility."
        )

    return (
        f"Knowledge resolution for {knowledge.name} does not establish "
        "a deterministic migration action. Perform contextual review."
    )


def build_recommendation(
    artifact: Dict[str, Any],
    *,
    knowledge_service: Optional[KnowledgeService] = None,
    as_of: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Produce a structured recommendation suitable for the canonical model,
    APIs and future UI.

    The result includes the knowledge snapshot so recommendations can
    later be reproduced and invalidated when knowledge changes.
    """

    service = knowledge_service or SERVICE

    algorithm = _artifact_algorithm(artifact)
    purpose = _artifact_purpose(artifact)

    resolution = service.resolve(
        algorithm,
        purpose=purpose,
        as_of=as_of,
    )

    if resolution.algorithm is None:
        return {
            "status": "UNRESOLVED",
            "algorithm": algorithm,
            "purpose": purpose,
            "priority": "REVIEW",
            "text": get_recommendation(
                artifact,
                knowledge_service=service,
                as_of=as_of,
            ),
            "rationale": (
                "No canonical knowledge record matched the observed "
                "cryptographic artifact."
            ),
            "knowledge_version": service.version,
            "knowledge_hash": service.integrity_hash,
            "matched_by": None,
            "candidate_count": 0,
            "candidate_ids": [],
            "conflict_count": 0,
        }

    knowledge = resolution.algorithm

    priority = _priority(
        artifact,
        knowledge.lifecycle_status,
    )

    candidates = list(
        resolution.migrations
    )

    compatibility_states = [
        item.status
        for item in resolution.compatibility
    ]

    if "unsupported" in compatibility_states:
        compatibility_state = "unsupported"
    elif "conditional" in compatibility_states:
        compatibility_state = "conditional"
    elif "supported" in compatibility_states:
        compatibility_state = "supported"
    else:
        compatibility_state = "unknown"

    status = (
        "CONFLICT"
        if resolution.conflicts
        else "RESOLVED"
    )

    return {
        "status": status,
        "algorithm": knowledge.name,
        "purpose": purpose,
        "priority": priority,
        "text": get_recommendation(
            artifact,
            knowledge_service=service,
            as_of=as_of,
        ),
        "rationale": knowledge.notes,
        "knowledge_version": service.version,
        "knowledge_hash": service.integrity_hash,
        "matched_by": resolution.matched_by,
        "lifecycle_status": knowledge.lifecycle_status,
        "quantum_posture": knowledge.quantum_posture,
        "primitive": knowledge.primitive,
        "standards": list(
            knowledge.standards
        ),
        "candidate_count": len(candidates),
        "candidate_ids": [
            candidate.relationship_id
            for candidate in candidates
        ],
        "candidates": [
            {
                "relationship_id": candidate.relationship_id,
                "target_algorithm": candidate.target_algorithm,
                "relationship_type": candidate.relationship_type,
                "hybrid": candidate.hybrid,
                "confidence": candidate.confidence,
                "prerequisites": list(
                    candidate.prerequisites
                ),
                "constraints": list(
                    candidate.constraints
                ),
            }
            for candidate in candidates
        ],
        "compatibility": {
            "status": compatibility_state,
            "records": len(
                resolution.compatibility
            ),
        },
        "conflict_count": len(
            resolution.conflicts
        ),
        "explainability": resolution.explainability,
    }


def get_migration_candidates(
    artifact: Dict[str, Any],
    *,
    knowledge_service: Optional[KnowledgeService] = None,
    as_of: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Expose knowledge-derived migration candidates without embedding
    cryptographic algorithm rules in the analysis layer.
    """

    service = knowledge_service or SERVICE

    result = service.resolve(
        _artifact_algorithm(artifact),
        purpose=_artifact_purpose(artifact),
        as_of=as_of,
    )

    return [
        {
            "relationship_id": candidate.relationship_id,
            "source_algorithm": candidate.source_algorithm,
            "target_algorithm": candidate.target_algorithm,
            "relationship_type": candidate.relationship_type,
            "hybrid": candidate.hybrid,
            "confidence": candidate.confidence,
            "prerequisites": list(
                candidate.prerequisites
            ),
            "constraints": list(
                candidate.constraints
            ),
        }
        for candidate in result.migrations
    ]
