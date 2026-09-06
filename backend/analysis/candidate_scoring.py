"""
ECDAT candidate scoring engine.

This module ranks already-resolved knowledge candidates.

Important:
- It does not invent migration relationships.
- It does not contain algorithm-specific replacement tables.
- It only scores evidence already supplied by the knowledge layer.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, Optional


def _norm(value: Any) -> str:
    return str(value or "").strip().lower()


def _purpose_match(
    purpose: Optional[str],
    candidate: Dict[str, Any],
) -> bool:
    if not purpose:
        return True

    purposes = candidate.get("applicable_purposes") or []

    if isinstance(purposes, str):
        purposes = [purposes]

    return _norm(purpose) in {
        _norm(item)
        for item in purposes
    }


def _protocol_records(
    target_algorithm: str,
    protocols: Iterable[Any],
    artifact: Dict[str, Any],
) -> list[Any]:
    requested_protocol = _norm(
        artifact.get("protocol")
        or artifact.get("protocol_name")
    )

    requested_version = _norm(
        artifact.get("protocol_version")
    )

    matches = []

    for record in protocols:
        if _norm(record.algorithm) != _norm(target_algorithm):
            continue

        if requested_protocol:
            if _norm(record.protocol) != requested_protocol:
                continue

        if requested_version:
            if _norm(record.protocol_version) != requested_version:
                continue

        matches.append(record)

    return matches


def score_candidate(
    candidate: Dict[str, Any],
    *,
    artifact: Dict[str, Any],
    target_algorithm: Optional[Any] = None,
    standards: Iterable[Any] = (),
    protocols: Iterable[Any] = (),
) -> Dict[str, Any]:
    """
    Score one already-resolved migration candidate.

    Score range: 0..100.

    The score represents migration suitability, not cryptographic
    security strength by itself.
    """

    target = (
        target_algorithm
        or candidate.get("target_algorithm")
        or ""
    )

    score = 50
    reasons: list[str] = []
    penalties: list[str] = []

    relationship = _norm(
        candidate.get("relationship_type")
    )

    confidence = _norm(
        candidate.get("confidence")
    )

    purpose = artifact.get("purpose")

    # ------------------------------------------------------------
    # Relationship quality
    # ------------------------------------------------------------

    relationship_scores = {
        "replaces": 18,
        "supersedes": 16,
        "hybrid_with": 15,
        "alternative_to": 10,
        "compatible_with": 6,
        "related_to": 2,
    }

    relationship_bonus = relationship_scores.get(
        relationship,
        0,
    )

    score += relationship_bonus

    if relationship_bonus:
        reasons.append(
            f"knowledge relationship '{relationship}' "
            f"supports migration suitability"
        )
    else:
        penalties.append(
            "candidate has no strongly directional "
            "migration relationship"
        )

    # ------------------------------------------------------------
    # Hybrid transition value
    # ------------------------------------------------------------

    if candidate.get("hybrid"):
        score += 8
        reasons.append(
            "hybrid mechanism provides a transition-oriented path"
        )

    # ------------------------------------------------------------
    # Candidate confidence
    # ------------------------------------------------------------

    confidence_scores = {
        "high": 8,
        "medium": 4,
        "low": -5,
        "unknown": -8,
    }

    confidence_delta = confidence_scores.get(
        confidence,
        -8,
    )

    score += confidence_delta

    if confidence in {"high", "medium"}:
        reasons.append(
            f"knowledge confidence is {confidence}"
        )
    else:
        penalties.append(
            "knowledge confidence is insufficiently strong"
        )

    # ------------------------------------------------------------
    # Purpose alignment
    # ------------------------------------------------------------

    if _purpose_match(
        purpose,
        candidate,
    ):
        score += 6

        if purpose:
            reasons.append(
                f"candidate explicitly applies to purpose '{purpose}'"
            )
    else:
        score -= 18
        penalties.append(
            "candidate purpose does not match the observed use"
        )

    # ------------------------------------------------------------
    # Target knowledge
    # ------------------------------------------------------------

    target_record = None

    for item in standards:
        related = getattr(
            item,
            "related_algorithms",
            (),
        )

        if any(
            _norm(target) == _norm(value)
            for value in related
        ):
            target_record = item
            break

    if target_record is not None:
        status = _norm(
            getattr(
                target_record,
                "status",
                "",
            )
        )

        if status in {
            "approved",
            "active",
            "standardized",
            "final",
        }:
            score += 8
            reasons.append(
                "candidate is linked to an established standard"
            )
        elif status in {
            "candidate",
            "draft",
        }:
            score += 2
            penalties.append(
                "candidate standard status is not final"
            )

    # ------------------------------------------------------------
    # Protocol applicability
    # ------------------------------------------------------------

    applicable_protocols = _protocol_records(
        str(target),
        protocols,
        artifact,
    )

    if applicable_protocols:
        recommended = [
            item
            for item in applicable_protocols
            if getattr(item, "recommended", None) is True
        ]

        supported = [
            item
            for item in applicable_protocols
            if _norm(
                getattr(item, "status", "")
            ) == "supported"
        ]

        unsupported = [
            item
            for item in applicable_protocols
            if _norm(
                getattr(item, "status", "")
            ) == "unsupported"
        ]

        if recommended:
            score += 12
            reasons.append(
                "target is explicitly recommended for "
                "the observed protocol"
            )
        elif supported:
            score += 5
            reasons.append(
                "target is supported by the observed protocol"
            )

        if unsupported:
            score -= 25
            penalties.append(
                "target is unsupported by the observed protocol"
            )

        conditional = [
            item
            for item in applicable_protocols
            if _norm(
                getattr(item, "status", "")
            ) == "conditional"
        ]

        if conditional and not recommended:
            score -= 5
            penalties.append(
                "protocol applicability is conditional"
            )

    elif artifact.get("protocol"):
        penalties.append(
            "no protocol applicability record was found "
            "for the target"
        )

    # ------------------------------------------------------------
    # Constraint burden
    # ------------------------------------------------------------

    constraints = candidate.get(
        "constraints"
    ) or []

    prerequisites = candidate.get(
        "prerequisites"
    ) or []

    constraint_count = len(
        constraints
    )

    prerequisite_count = len(
        prerequisites
    )

    burden = (
        constraint_count
        + prerequisite_count
    )

    if burden == 0:
        score += 5
        reasons.append(
            "candidate has no recorded prerequisite or "
            "constraint burden"
        )
    elif burden <= 2:
        score -= 2
        penalties.append(
            "candidate has a small migration constraint burden"
        )
    else:
        score -= min(
            12,
            burden * 3,
        )
        penalties.append(
            f"candidate has {burden} recorded prerequisites/constraints"
        )

    # ------------------------------------------------------------
    # Clamp and classify
    # ------------------------------------------------------------

    score = max(
        0,
        min(
            100,
            score,
        ),
    )

    if score >= 85:
        decision = "preferred"
    elif score >= 70:
        decision = "alternative"
    elif score >= 50:
        decision = "conditional"
    else:
        decision = "weak"

    return {
        "score": score,
        "decision": decision,
        "reasons": reasons,
        "penalties": penalties,
        "scoring": {
            "relationship": relationship,
            "confidence": confidence,
            "purpose": purpose,
            "protocol_records": len(
                applicable_protocols
            ),
            "constraint_count": constraint_count,
            "prerequisite_count": prerequisite_count,
        },
    }


def rank_candidates(
    candidates: Iterable[Dict[str, Any]],
    *,
    artifact: Dict[str, Any],
    target_algorithms: Optional[Dict[str, Any]] = None,
    standards: Iterable[Any] = (),
    protocols: Iterable[Any] = (),
) -> list[Dict[str, Any]]:
    """
    Score and deterministically rank migration candidates.
    """

    target_algorithms = (
        target_algorithms or {}
    )

    ranked = []

    for candidate in candidates:
        result = dict(candidate)

        target = result.get(
            "target_algorithm",
            "",
        )

        score = score_candidate(
            result,
            artifact=artifact,
            target_algorithm=target,
            standards=standards,
            protocols=protocols,
        )

        result.update(score)

        ranked.append(result)

    ranked.sort(
        key=lambda item: (
            -int(item.get("score", 0)),
            str(
                item.get(
                    "target_algorithm",
                    "",
                )
            ),
            str(
                item.get(
                    "relationship_id",
                    "",
                )
            ),
        )
    )

    return ranked
