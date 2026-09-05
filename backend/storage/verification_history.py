import json
from pathlib import Path
from typing import Any, Dict, List, Optional


BASE_DIR = Path(__file__).resolve().parents[1]
VERIFICATION_DIR = BASE_DIR / "output" / "verifications"


def _verification_filename(
    verification_id: str,
) -> str:
    """
    Convert a logical verification ID into a
    filesystem-safe filename.

    The logical verification ID itself remains
    unchanged inside the persisted record.
    """
    safe_id = (
        str(verification_id)
        .replace("/", "_")
        .replace("\\", "_")
        .replace(":", "_")
    )

    return f"{safe_id}.json"


def ensure_verification_directory() -> Path:
    VERIFICATION_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    return VERIFICATION_DIR


def save_verification(
    verification: Dict[str, Any],
) -> Path:
    """
    Persist one immutable verification result.
    """
    ensure_verification_directory()

    verification_id = str(
        verification.get(
            "verification_id",
            "",
        )
    ).strip()

    if not verification_id:
        raise ValueError(
            "verification.verification_id is required."
        )

    file_path = (
        VERIFICATION_DIR
        / _verification_filename(
            verification_id
        )
    )

    payload = json.dumps(
        verification,
        indent=2,
        ensure_ascii=False,
    )

    file_path.write_text(
        payload,
        encoding="utf-8",
    )

    return file_path


def load_verification(
    verification_id: str,
) -> Optional[Dict[str, Any]]:
    """
    Load one persisted verification result.
    """
    ensure_verification_directory()

    verification_id = str(
        verification_id
    ).strip()

    if not verification_id:
        return None

    file_path = (
        VERIFICATION_DIR
        / _verification_filename(
            verification_id
        )
    )

    if not file_path.exists():
        return None

    try:
        return json.loads(
            file_path.read_text(
                encoding="utf-8"
            )
        )
    except (
        OSError,
        json.JSONDecodeError,
    ):
        return None


def list_verifications() -> List[Dict[str, Any]]:
    """
    Return verification summaries ordered
    newest first.
    """
    ensure_verification_directory()

    records: List[Dict[str, Any]] = []

    for file_path in VERIFICATION_DIR.glob(
        "*.json"
    ):
        try:
            data = json.loads(
                file_path.read_text(
                    encoding="utf-8"
                )
            )

            records.append(
                {
                    "verification_id":
                        data.get(
                            "verification_id"
                        ),
                    "status":
                        data.get(
                            "status"
                        ),
                    "from_scan_id":
                        data.get(
                            "from_scan_id"
                        ),
                    "to_scan_id":
                        data.get(
                            "to_scan_id"
                        ),
                    "artifact_id":
                        data.get(
                            "artifact_id"
                        ),
                    "migration_option_id":
                        data.get(
                            "migration_option_id"
                        ),
                    "risk_before":
                        data.get(
                            "risk_before"
                        ),
                    "risk_after":
                        data.get(
                            "risk_after"
                        ),
                    "mosca_before":
                        data.get(
                            "mosca_before"
                        ),
                    "mosca_after":
                        data.get(
                            "mosca_after"
                        ),
                    "verified_at":
                        data.get(
                            "verified_at"
                        ),
                }
            )

        except (
            OSError,
            json.JSONDecodeError,
        ):
            # Ignore malformed records so one
            # corrupt verification does not break
            # the entire verification history.
            continue

    records.sort(
        key=lambda item:
            str(
                item.get(
                    "verified_at",
                    "",
                )
            ),
        reverse=True,
    )

    return records
