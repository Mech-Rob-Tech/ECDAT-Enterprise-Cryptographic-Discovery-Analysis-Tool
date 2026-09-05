from typing import Any, Dict

from model.identity import build_scan_id
from model.scan_state import ScanState


def build_scan_state(report: Dict[str, Any]) -> ScanState:
    """
    Build a historical ECDAT scan snapshot from the canonical report.

    The snapshot intentionally preserves the analytical source data
    required for future diffing without rescanning the repository.

    Scan identity is derived from the logical application identity
    and scan generation timestamp. Source paths are not embedded in
    the public scan identifier.
    """

    metadata = report.get("metadata", {}) or {}
    knowledge_snapshot = (
        report.get("knowledge_snapshot", {}) or {}
    )

    applications = report.get("applications", []) or []
    canonical_artifacts = (
        report.get("canonical_artifacts", []) or []
    )
    evidence = report.get("evidence", []) or []
    business_contexts = (
        report.get("business_contexts", []) or []
    )
    relationships = (
        report.get("relationships", []) or []
    )

    application_ids = [
        str(application.get("application_id"))
        for application in applications
        if application.get("application_id")
    ]

    artifact_ids = [
        str(artifact.get("artifact_id"))
        for artifact in canonical_artifacts
        if artifact.get("artifact_id")
    ]

    generated_at = metadata.get("generated_at")
    target = metadata.get("target")

    if not generated_at:
        generated_at = "unknown"

    if application_ids:
        scan_application_id = application_ids[0]
    else:
        scan_application_id = "application:unknown"

    scan_id = build_scan_id(
        application_id=scan_application_id,
        generated_at=str(generated_at),
    )

    return ScanState(
        scan_id=scan_id,
        application_ids=application_ids,
        generated_at=generated_at,
        target=target,
        artifact_ids=artifact_ids,
        canonical_artifacts=canonical_artifacts,
        evidence=evidence,
        business_contexts=business_contexts,
        relationships=relationships,
        risk_landscape=(
            report.get("risk_landscape", {}) or {}
        ),
        summary=(
            report.get("summary", {}) or {}
        ),
        metadata=metadata,
        knowledge_snapshot=knowledge_snapshot,
    )
