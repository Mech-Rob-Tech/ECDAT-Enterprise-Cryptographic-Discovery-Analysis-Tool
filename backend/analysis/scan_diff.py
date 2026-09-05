from typing import Any, Dict, List, Tuple


RISK_ORDER = {
    "LOW": 0,
    "MEDIUM": 1,
    "HIGH": 2,
    "CRITICAL": 3,
}


def _risk_level(value: Any) -> str:
    if isinstance(value, dict):
        value = value.get("level")
    if value is None:
        return "UNKNOWN"
    return str(value).upper()


def _algorithm_value(artifact: Dict[str, Any]) -> str:
    value = artifact.get("algorithm")

    if isinstance(value, dict):
        return str(
            value.get("name")
            or value.get("algorithm")
            or ""
        ).upper()

    return str(value or "").upper()


def _artifact_type(artifact: Dict[str, Any]) -> str:
    return str(
        artifact.get("artifact_type")
        or artifact.get("type")
        or ""
    ).upper()


def _purpose_value(artifact: Dict[str, Any]) -> str:
    value = artifact.get("purpose")

    if isinstance(value, dict):
        value = value.get("name") or value.get("value")

    return str(value or "").lower()


def _detection_value(artifact: Dict[str, Any]) -> str:
    value = artifact.get("detection")

    if isinstance(value, dict):
        value = (
            value.get("method")
            or value.get("name")
            or value.get("value")
        )

    return str(
        value
        or artifact.get("detection_method")
        or ""
    ).lower()


def _application_id(artifact: Dict[str, Any]) -> str:
    return str(artifact.get("application_id") or "")


def _component_id(artifact: Dict[str, Any]) -> str:
    return str(artifact.get("component_id") or "")


def _algorithm_family(artifact: Dict[str, Any]) -> str:
    value = artifact.get("algorithm")

    if isinstance(value, dict):
        value = value.get("family")

    if value is None:
        value = artifact.get("algorithm_family")

    return str(value or "").upper()


def _details(artifact: Dict[str, Any]) -> Dict[str, Any]:
    value = artifact.get("details")
    return value if isinstance(value, dict) else {}


def _semantic_identity(artifact: Dict[str, Any]) -> Tuple[Any, ...]:
    """
    Stable identity for matching the same cryptographic artifact
    across historical scans.

    Source location is deliberately excluded.
    """
    return (
        _application_id(artifact),
        _component_id(artifact),
        _artifact_type(artifact),
        _algorithm_value(artifact),
        _algorithm_family(artifact),
        artifact.get("key_size"),
        artifact.get("mode"),
        artifact.get("curve"),
        artifact.get("version"),
        _purpose_value(artifact),
        _detection_value(artifact),
    )


def _semantic_projection(
    artifact: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Meaningful cryptographic state.

    Location and generated IDs are excluded.
    """
    return {
        "algorithm": _algorithm_value(artifact),
        "algorithm_family": _algorithm_family(artifact),
        "artifact_type": _artifact_type(artifact),
        "key_size": artifact.get("key_size"),
        "mode": artifact.get("mode"),
        "curve": artifact.get("curve"),
        "version": artifact.get("version"),
        "purpose": _purpose_value(artifact),
        "detection": _detection_value(artifact),
        "application_id": _application_id(artifact),
        "component_id": _component_id(artifact),
        "details": _details(artifact),
    }


def _changed_fields(
    before: Dict[str, Any],
    after: Dict[str, Any],
) -> List[str]:
    before_projection = _semantic_projection(before)
    after_projection = _semantic_projection(after)

    return sorted(
        field
        for field in before_projection
        if before_projection[field] != after_projection[field]
    )


def _risk_changes(
    before: Dict[str, Any],
    after: Dict[str, Any],
) -> Tuple[bool, bool]:
    before_risk = before.get("risk") or {}
    after_risk = after.get("risk") or {}

    before_security = _risk_level(
        before_risk.get("security")
    )
    after_security = _risk_level(
        after_risk.get("security")
    )

    before_quantum = _risk_level(
        before_risk.get("quantum")
    )
    after_quantum = _risk_level(
        after_risk.get("quantum")
    )

    before_score = max(
        RISK_ORDER.get(before_security, -1),
        RISK_ORDER.get(before_quantum, -1),
    )

    after_score = max(
        RISK_ORDER.get(after_security, -1),
        RISK_ORDER.get(after_quantum, -1),
    )

    return (
        after_score > before_score,
        after_score < before_score,
    )


def _mosca_projection(
    artifact: Dict[str, Any],
) -> Dict[str, Any]:
    mosca = artifact.get("mosca") or {}

    if not isinstance(mosca, dict):
        return {}

    return {
        "status": mosca.get("status"),
        "risk": mosca.get("risk"),
        "data_lifetime": mosca.get("data_lifetime"),
        "migration_time": mosca.get("migration_time"),
        "quantum_horizon": mosca.get("quantum_horizon"),
        "margin": mosca.get("margin"),
    }


def _semantic_related_id(
    related_id: Any,
    artifact: Dict[str, Any],
    related_type: str,
) -> str:
    """
    Normalize analytical IDs that are currently derived from
    location-sensitive artifact IDs.

    This prevents source-line movement from becoming a false
    recommendation or migration change.
    """
    raw = str(related_id or "")

    if not raw:
        return ""

    algorithm = _algorithm_value(artifact)
    action = raw.rsplit(":", 1)[-1]

    return (
        f"{related_type}:"
        f"{_application_id(artifact)}:"
        f"{_artifact_type(artifact)}:"
        f"{algorithm}:"
        f"{action}"
    )


def _artifact_context(
    artifact: Dict[str, Any],
) -> Dict[str, Any]:
    return {
        "recommendations": sorted(
            _semantic_related_id(
                value,
                artifact,
                "recommendation",
            )
            for value in (
                artifact.get("recommendation_ids") or []
            )
        ),
        "migrations": sorted(
            _semantic_related_id(
                value,
                artifact,
                "migration",
            )
            for value in (
                artifact.get("migration_option_ids") or []
            )
        ),
    }


def _evidence_projection(
    artifact: Dict[str, Any],
    evidence_by_id: Dict[str, Dict[str, Any]] | None = None,
) -> List[Dict[str, Any]]:
    """
    Build semantic evidence observations for temporal comparison.

    Evidence IDs are observation-specific and may change when source
    locations move. Therefore they are not sufficient to determine
    whether evidence itself changed.
    """
    evidence_by_id = evidence_by_id or {}

    projections = []

    for evidence_id in (
        artifact.get("evidence_ids") or []
    ):
        evidence = evidence_by_id.get(
            str(evidence_id)
        )

        if not evidence:
            projections.append(
                {
                    "evidence_id": str(evidence_id),
                }
            )
            continue

        projections.append(
            {
                "text": str(
                    evidence.get("text") or ""
                ),
                "context": evidence.get(
                    "context"
                ) or [],
                "file": str(
                    evidence.get("file") or ""
                ),
                "line": int(
                    evidence.get("line") or 0
                ),
            }
        )

    return sorted(
        projections,
        key=lambda value: (
            value.get("text", ""),
            str(value.get("context", "")),
            value.get("file", ""),
            value.get("line", 0),
        ),
    )

def _match_artifacts(
    before_artifacts: List[Dict[str, Any]],
    after_artifacts: List[Dict[str, Any]],
):
    before_by_id = {
        str(artifact.get("artifact_id")): artifact
        for artifact in before_artifacts
        if artifact.get("artifact_id")
    }

    after_by_id = {
        str(artifact.get("artifact_id")): artifact
        for artifact in after_artifacts
        if artifact.get("artifact_id")
    }

    matched = []

    unmatched_before = dict(before_by_id)
    unmatched_after = dict(after_by_id)

    # Exact artifact identity.
    for artifact_id in sorted(
        set(unmatched_before) & set(unmatched_after)
    ):
        before = unmatched_before.pop(artifact_id)
        after = unmatched_after.pop(artifact_id)

        matched.append(
            (
                before,
                after,
                "artifact_id",
            )
        )

    # Semantic identity fallback.
    before_semantic: Dict[Tuple[Any, ...], List[str]] = {}
    after_semantic: Dict[Tuple[Any, ...], List[str]] = {}

    for artifact_id, artifact in unmatched_before.items():
        before_semantic.setdefault(
            _semantic_identity(artifact),
            [],
        ).append(artifact_id)

    for artifact_id, artifact in unmatched_after.items():
        after_semantic.setdefault(
            _semantic_identity(artifact),
            [],
        ).append(artifact_id)

    for identity in sorted(
        set(before_semantic) & set(after_semantic),
        key=str,
    ):
        before_ids = before_semantic[identity]
        after_ids = after_semantic[identity]

        # Never guess if identity is ambiguous.
        if len(before_ids) != 1 or len(after_ids) != 1:
            continue

        before_id = before_ids[0]
        after_id = after_ids[0]

        before = unmatched_before.pop(before_id)
        after = unmatched_after.pop(after_id)

        matched.append(
            (
                before,
                after,
                "semantic_identity",
            )
        )

    return (
        matched,
        list(unmatched_before.values()),
        list(unmatched_after.values()),
    )


def build_scan_diff(
    from_scan: Dict[str, Any],
    to_scan: Dict[str, Any],
) -> Dict[str, Any]:
    from_scan_id = str(
        from_scan.get("scan_id") or ""
    )

    to_scan_id = str(
        to_scan.get("scan_id") or ""
    )

    before_artifacts = (
        from_scan.get("canonical_artifacts") or []
    )

    after_artifacts = (
        to_scan.get("canonical_artifacts") or []
    )

    before_evidence_by_id = {
        str(evidence.get("evidence_id")): evidence
        for evidence in (
            from_scan.get("evidence") or []
        )
        if evidence.get("evidence_id")
    }

    after_evidence_by_id = {
        str(evidence.get("evidence_id")): evidence
        for evidence in (
            to_scan.get("evidence") or []
        )
        if evidence.get("evidence_id")
    }

    (
        matched,
        removed_artifacts,
        added_artifacts,
    ) = _match_artifacts(
        before_artifacts,
        after_artifacts,
    )

    added_ids = sorted(
        str(artifact.get("artifact_id"))
        for artifact in added_artifacts
        if artifact.get("artifact_id")
    )

    removed_ids = sorted(
        str(artifact.get("artifact_id"))
        for artifact in removed_artifacts
        if artifact.get("artifact_id")
    )

    changed_ids: List[str] = []

    risk_increased = []
    risk_decreased = []
    mosca_changed = []

    recommendation_changed = []
    migration_changed = []
    relationship_changed = []

    business_context_changed = []

    evidence_relocated = []
    evidence_changed = []

    for before, after, match_method in matched:
        before_id = str(
            before.get("artifact_id")
        )

        after_id = str(
            after.get("artifact_id")
        )

        changed_fields = _changed_fields(
            before,
            after,
        )

        if changed_fields:
            changed_ids.append(after_id)

        risk_up, risk_down = _risk_changes(
            before,
            after,
        )

        if risk_up:
            risk_increased.append(
                {
                    "from_artifact_id": before_id,
                    "to_artifact_id": after_id,
                    "match_method": match_method,
                    "before": before.get("risk"),
                    "after": after.get("risk"),
                }
            )

        if risk_down:
            risk_decreased.append(
                {
                    "from_artifact_id": before_id,
                    "to_artifact_id": after_id,
                    "match_method": match_method,
                    "before": before.get("risk"),
                    "after": after.get("risk"),
                }
            )

        before_mosca = _mosca_projection(before)
        after_mosca = _mosca_projection(after)

        if before_mosca != after_mosca:
            mosca_changed.append(
                {
                    "from_artifact_id": before_id,
                    "to_artifact_id": after_id,
                    "match_method": match_method,
                    "before": before_mosca,
                    "after": after_mosca,
                }
            )

        before_context = _artifact_context(before)
        after_context = _artifact_context(after)

        if (
            before_context["recommendations"]
            != after_context["recommendations"]
        ):
            recommendation_changed.append(
                {
                    "from_artifact_id": before_id,
                    "to_artifact_id": after_id,
                    "match_method": match_method,
                    "before": before_context["recommendations"],
                    "after": after_context["recommendations"],
                }
            )

        if (
            before_context["migrations"]
            != after_context["migrations"]
        ):
            migration_changed.append(
                {
                    "from_artifact_id": before_id,
                    "to_artifact_id": after_id,
                    "match_method": match_method,
                    "before": before_context["migrations"],
                    "after": after_context["migrations"],
                }
            )

        # Evidence IDs currently contain source location.
        # If the artifact itself is semantically the same and only
        # the evidence reference changes, classify it as relocation.
        before_evidence = _evidence_projection(
            before,
            before_evidence_by_id,
        )

        after_evidence = _evidence_projection(
            after,
            after_evidence_by_id,
        )

        if before_evidence != after_evidence:
            before_semantic = sorted(
                {
                    item.get("text", "")
                    for item in before_evidence
                }
            )

            after_semantic = sorted(
                {
                    item.get("text", "")
                    for item in after_evidence
                }
            )

            if before_semantic == after_semantic:
                evidence_relocated.append(
                    {
                        "from_artifact_id": before_id,
                        "to_artifact_id": after_id,
                        "match_method": match_method,
                        "before": before_evidence,
                        "after": after_evidence,
                        "semantic_change": "evidence_relocated",
                    }
                )
            else:
                evidence_changed.append(
                    {
                        "from_artifact_id": before_id,
                        "to_artifact_id": after_id,
                        "match_method": match_method,
                        "before": before_evidence,
                        "after": after_evidence,
                        "semantic_change": "evidence_changed",
                    }
                )

        if before_context != after_context:
            relationship_changed.append(
                {
                    "from_artifact_id": before_id,
                    "to_artifact_id": after_id,
                    "match_method": match_method,
                    "before": before_context,
                    "after": after_context,
                }
            )

    changed_ids = sorted(set(changed_ids))

    summary = {
        "artifacts_added": len(added_ids),
        "artifacts_removed": len(removed_ids),
        "artifacts_changed": len(changed_ids),
        "risk_increased": len(risk_increased),
        "risk_decreased": len(risk_decreased),
        "mosca_changed": len(mosca_changed),
        "relationship_changed": len(relationship_changed),
        "recommendation_changed": len(
            recommendation_changed
        ),
        "migration_changed": len(
            migration_changed
        ),
        "evidence_relocated": len(
            evidence_relocated
        ),
        "evidence_changed": len(
            evidence_changed
        ),
        "business_context_changed": len(
            business_context_changed
        ),
        "net_artifact_change": (
            len(added_ids) - len(removed_ids)
        ),
    }

    return {
        "version": "1.4",
        "projection": "scan_diff",
        "from_scan_id": from_scan_id,
        "to_scan_id": to_scan_id,

        "added_artifact_ids": added_ids,
        "removed_artifact_ids": removed_ids,

        "changed_artifacts": changed_ids,
        "changed_artifact_ids": changed_ids,

        "risk_increased": risk_increased,
        "risk_decreased": risk_decreased,

        "mosca_changed": mosca_changed,

        "relationship_changed": relationship_changed,
        "recommendation_changed": recommendation_changed,
        "migration_changed": migration_changed,

        "business_context_changed": business_context_changed,

        "evidence_relocated": evidence_relocated,
        "evidence_changed": evidence_changed,

        "summary": summary,

        "methodology": {
            "comparison": "canonical_semantic_diff",
            "artifact_identity": (
                "exact_artifact_id_then_unique_semantic_identity"
            ),
            "relationship_identity": (
                "semantic_normalization_of_location_derived_ids"
            ),
            "location_semantics": (
                "source locations are evidence, not artifact identity"
            ),
            "evidence_semantics": (
                "location movement is relocation; "
                "non-relocation reference changes are evidence changes"
            ),
            "risk_order": (
                "LOW < MEDIUM < HIGH < CRITICAL"
            ),
            "ambiguity_policy": (
                "non-unique semantic matches remain unmatched"
            ),
            "note": (
                "Line movement must not be interpreted as "
                "cryptographic or analytical state change."
            ),
        },
    }
