from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from model.schema import VerificationState
from model.identity import build_verification_id


RISK_ORDER = {
    "LOW": 0,
    "MEDIUM": 1,
    "HIGH": 2,
    "CRITICAL": 3,
}


def _level(value: Any) -> str:
    if isinstance(value, dict):
        value = value.get("level")

    if value is None:
        return "UNKNOWN"

    return str(value).upper()


def _artifact_risk(artifact: Dict[str, Any]) -> str:
    risk = artifact.get("risk") or {}

    security = _level(risk.get("security"))
    quantum = _level(risk.get("quantum"))

    security_score = RISK_ORDER.get(security, -1)
    quantum_score = RISK_ORDER.get(quantum, -1)

    if security_score < 0 and quantum_score < 0:
        return "UNKNOWN"

    if security_score >= quantum_score:
        return security

    return quantum


def _mosca_status(artifact: Dict[str, Any]) -> str:
    mosca = artifact.get("mosca") or {}

    if not isinstance(mosca, dict):
        return "UNKNOWN"

    return str(
        mosca.get("status") or "UNKNOWN"
    ).upper()


def _index_artifacts(
    scan: Dict[str, Any],
) -> Dict[str, Dict[str, Any]]:
    return {
        str(artifact.get("artifact_id")): artifact
        for artifact in (
            scan.get("canonical_artifacts") or []
        )
        if artifact.get("artifact_id")
    }


def _find_semantic_artifact(
    artifacts: List[Dict[str, Any]],
    target: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    """
    Find a unique semantic match when artifact IDs changed
    between scans.

    This intentionally mirrors the conservative identity concept
    used by the temporal diff engine.
    """
    target_algorithm = str(
        target.get("algorithm") or ""
    ).upper()

    if isinstance(target.get("algorithm"), dict):
        target_algorithm = str(
            target["algorithm"].get("name") or ""
        ).upper()

    target_application = str(
        target.get("application_id") or ""
    )

    target_type = str(
        target.get("artifact_type")
        or target.get("type")
        or ""
    ).upper()

    matches = []

    for artifact in artifacts:
        algorithm = artifact.get("algorithm")

        if isinstance(algorithm, dict):
            algorithm = algorithm.get("name")

        algorithm = str(
            algorithm or ""
        ).upper()

        artifact_application = str(
            artifact.get("application_id") or ""
        )

        artifact_type = str(
            artifact.get("artifact_type")
            or artifact.get("type")
            or ""
        ).upper()

        if (
            algorithm == target_algorithm
            and artifact_application == target_application
            and artifact_type == target_type
        ):
            matches.append(artifact)

    if len(matches) == 1:
        return matches[0]

    return None


def _find_target_artifact(
    scan: Dict[str, Any],
    artifact_id: str,
) -> Optional[Dict[str, Any]]:
    artifacts = scan.get("canonical_artifacts") or []

    by_id = _index_artifacts(scan)

    if artifact_id in by_id:
        return by_id[artifact_id]

    # The requested artifact may have a location-sensitive ID.
    # Search the source scan using the artifact ID first.
    for artifact in artifacts:
        if str(artifact.get("artifact_id")) == artifact_id:
            return artifact

    return None


def _risk_improved(
    before: str,
    after: str,
) -> bool:
    before_score = RISK_ORDER.get(before, -1)
    after_score = RISK_ORDER.get(after, -1)

    return (
        before_score >= 0
        and after_score >= 0
        and after_score < before_score
    )


def _mosca_improved(
    before: str,
    after: str,
) -> bool:
    at_risk = {
        "AT_RISK",
        "CRITICAL",
        "HIGH",
    }

    safe = {
        "NOT_AT_RISK",
        "LOW",
        "MEDIUM",
    }

    return before in at_risk and after in safe


def _verification_status(
    artifact_before: Optional[Dict[str, Any]],
    artifact_after: Optional[Dict[str, Any]],
    diff: Dict[str, Any],
) -> str:
    """
    Determine verification status using explicit observable evidence.

    VERIFIED:
        Targeted exposure disappeared or materially improved.

    FAILED:
        The vulnerable artifact remains without sufficient improvement.

    INCONCLUSIVE:
        There is insufficient evidence to make a reliable determination.
    """
    if artifact_before is None:
        return "INCONCLUSIVE"

    before_risk = _artifact_risk(artifact_before)

    if artifact_after is None:
        # The targeted artifact disappeared from the subsequent scan.
        return "VERIFIED"

    after_risk = _artifact_risk(artifact_after)

    before_mosca = _mosca_status(artifact_before)
    after_mosca = _mosca_status(artifact_after)

    risk_improved = _risk_improved(
        before_risk,
        after_risk,
    )

    mosca_improved = _mosca_improved(
        before_mosca,
        after_mosca,
    )

    if risk_improved or mosca_improved:
        return "VERIFIED"

    return "FAILED"


def build_verification(
    from_scan: Dict[str, Any],
    to_scan: Dict[str, Any],
    diff: Dict[str, Any],
    artifact_id: str,
    migration_option_id: Optional[str] = None,
    replacement_artifact_id: Optional[str] = None,
) -> VerificationState:
    """
    Verify the outcome of a migration/remediation by comparing
    two persisted ECDAT scan states.

    This function is deterministic and does not perform scanning.
    """
    before_artifacts = (
        from_scan.get("canonical_artifacts") or []
    )

    after_artifacts = (
        to_scan.get("canonical_artifacts") or []
    )

    artifact_before = _find_target_artifact(
        from_scan,
        artifact_id,
    )

    if artifact_before is None:
        verification_id = build_verification_id(
            from_scan_id=from_scan.get("scan_id", "unknown"),
            to_scan_id=to_scan.get("scan_id", "unknown"),
            artifact_id=artifact_id,
            migration_option_id=migration_option_id,
            replacement_artifact_id=replacement_artifact_id,
        )

        return VerificationState(
            verification_id=verification_id,
            status="INCONCLUSIVE",
            from_scan_id=from_scan.get("scan_id"),
            to_scan_id=to_scan.get("scan_id"),
            artifact_id=artifact_id,
            migration_option_id=migration_option_id,
            verified_at=None,
            notes=(
                "Target artifact was not present in the source "
                "scan state."
            ),
        )

    artifact_after = _find_target_artifact(
        to_scan,
        artifact_id,
    )

    if artifact_after is None:
        artifact_after = _find_semantic_artifact(
            after_artifacts,
            artifact_before,
        )

    # A migration may intentionally replace the original algorithm
    # with a different cryptographic artifact. In that case the
    # caller must explicitly identify the replacement rather than
    # relying on heuristic matching.
    if (
        artifact_after is None
        and replacement_artifact_id
    ):
        artifact_after = _find_target_artifact(
            to_scan,
            replacement_artifact_id,
        )

    status = _verification_status(
        artifact_before,
        artifact_after,
        diff,
    )

    before_risk = _artifact_risk(
        artifact_before
    )

    after_risk = (
        _artifact_risk(artifact_after)
        if artifact_after is not None
        else "ABSENT"
    )

    before_mosca = _mosca_status(
        artifact_before
    )

    after_mosca = (
        _mosca_status(artifact_after)
        if artifact_after is not None
        else "ABSENT"
    )

    remaining_exposure: List[str] = []

    if artifact_after is not None:
        if after_risk in {
            "HIGH",
            "CRITICAL",
        }:
            remaining_exposure.append(
                f"risk remains {after_risk}"
            )

        if after_mosca in {
            "AT_RISK",
            "HIGH",
            "CRITICAL",
        }:
            remaining_exposure.append(
                f"MOSCA remains {after_mosca}"
            )

    evidence_ids = list(
        artifact_after.get("evidence_ids", [])
        if artifact_after is not None
        else artifact_before.get("evidence_ids", [])
    )

    if status == "VERIFIED":
        notes = (
            "Post-migration scan provides sufficient evidence "
            "that the targeted cryptographic exposure was "
            "removed or materially improved."
        )
        verified_at = datetime.now(
            timezone.utc
        ).isoformat()
    elif status == "FAILED":
        notes = (
            "Post-migration scan confirms that the targeted "
            "cryptographic exposure remains without sufficient "
            "analytical improvement."
        )
        verified_at = None
    else:
        notes = (
            "The available scan states do not provide enough "
            "evidence for a reliable verification decision."
        )
        verified_at = None

    verification_id = build_verification_id(
        from_scan_id=from_scan.get("scan_id", "unknown"),
        to_scan_id=to_scan.get("scan_id", "unknown"),
        artifact_id=artifact_id,
        migration_option_id=migration_option_id,
        replacement_artifact_id=replacement_artifact_id,
    )

    return VerificationState(
        verification_id=verification_id,
        status=status,
        from_scan_id=from_scan.get("scan_id"),
        to_scan_id=to_scan.get("scan_id"),
        artifact_id=artifact_id,
        migration_option_id=migration_option_id,
        risk_before=before_risk,
        risk_after=after_risk,
        mosca_before=before_mosca,
        mosca_after=after_mosca,
        remaining_exposure=remaining_exposure,
        evidence_ids=evidence_ids,
        verified_at=verified_at,
        notes=notes,
    )


def verification_to_dict(
    verification: VerificationState,
) -> Dict[str, Any]:
    """
    Serialize VerificationState without introducing another
    verification representation.
    """
    return {
        "verification_id": verification.verification_id,
        "status": verification.status,
        "from_scan_id": verification.from_scan_id,
        "to_scan_id": verification.to_scan_id,
        "artifact_id": verification.artifact_id,
        "migration_option_id": verification.migration_option_id,
        "risk_before": verification.risk_before,
        "risk_after": verification.risk_after,
        "mosca_before": verification.mosca_before,
        "mosca_after": verification.mosca_after,
        "remaining_exposure": list(
            verification.remaining_exposure
        ),
        "evidence_ids": list(
            verification.evidence_ids
        ),
        "verified_at": verification.verified_at,
        "notes": verification.notes,
    }
