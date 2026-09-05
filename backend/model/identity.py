"""
ECDAT canonical identity functions.

Identity rules:

- Logical entity identity must not depend on source line numbers.
- Logical entity identity must not depend on scan timestamps.
- Logical artifact identity must not depend on scanner discovery order.
- Evidence identity may include observation-specific information.
- Scan identity identifies a scan instance.
- Verification identity identifies a verification comparison.
"""

import hashlib
import json
from typing import Any, Dict


def _normalize(value: Any) -> str:
    """
    Normalize a value into a deterministic representation.
    """
    if value is None:
        return ""

    if isinstance(value, dict):
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
        )

    if isinstance(value, (list, tuple)):
        return json.dumps(
            list(value),
            sort_keys=True,
            separators=(",", ":"),
        )

    return str(value).strip()


def _digest(
    prefix: str,
    payload: Dict[str, Any],
) -> str:
    """
    Produce a compact deterministic identifier from
    canonical identity attributes.
    """
    canonical = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )

    digest = hashlib.sha256(
        canonical.encode("utf-8")
    ).hexdigest()[:20]

    return f"{prefix}:{digest}"


def build_application_id(
    application_name: str,
) -> str:
    """
    Build stable logical application identity.
    """
    return _digest(
        "application",
        {
            "name": _normalize(
                application_name
            ).lower(),
        },
    )


def build_artifact_id(
    application_id: str,
    algorithm: str,
    artifact_type: str,
    purpose: str,
    details: Dict[str, Any] | None = None,
    semantic_signature: str | None = None,
) -> str:
    """
    Build stable logical cryptographic artifact identity.

    Source file, line number, scan timestamp, and scanner
    discovery order are intentionally excluded.

    If the scanner can establish a stable semantic source
    signature, it may be included. Otherwise the artifact
    represents the semantic cryptographic construct itself
    and multiple observations attach as evidence.
    """
    semantic_details = details or {}

    payload = {
        "application_id": _normalize(
            application_id
        ),
        "algorithm": _normalize(
            algorithm
        ).upper(),
        "artifact_type": _normalize(
            artifact_type
        ).upper(),
        "purpose": _normalize(
            purpose
        ).lower(),
        "details": semantic_details,
    }

    if semantic_signature:
        payload["semantic_signature"] = _normalize(
            semantic_signature
        )

    return _digest(
        "artifact",
        payload,
    )


def build_evidence_id(
    artifact_id: str,
    file: str,
    line: int,
    evidence: str,
) -> str:
    """
    Build observation-specific evidence identity.

    Evidence intentionally retains source location because
    evidence represents where and how the artifact was observed.
    """
    payload = {
        "artifact_id": _normalize(
            artifact_id
        ),
        "file": _normalize(file),
        "line": int(line or 0),
        "evidence": _normalize(evidence),
    }

    return _digest(
        "evidence",
        payload,
    )


def build_scan_id(
    application_id: str,
    generated_at: str,
) -> str:
    """
    Build scan-instance identity.

    A scan is intentionally unique per observation timestamp.
    """
    return _digest(
        "scan",
        {
            "application_id": _normalize(
                application_id
            ),
            "generated_at": _normalize(
                generated_at
            ),
        },
    )


def build_verification_id(
    from_scan_id: str,
    to_scan_id: str,
    artifact_id: str,
    migration_option_id: str | None = None,
    replacement_artifact_id: str | None = None,
) -> str:
    """
    Build deterministic verification identity from
    the complete comparison context.
    """
    return _digest(
        "verification",
        {
            "from_scan_id": _normalize(
                from_scan_id
            ),
            "to_scan_id": _normalize(
                to_scan_id
            ),
            "artifact_id": _normalize(
                artifact_id
            ),
            "migration_option_id": _normalize(
                migration_option_id
            ),
            "replacement_artifact_id": _normalize(
                replacement_artifact_id
            ),
        },
    )
