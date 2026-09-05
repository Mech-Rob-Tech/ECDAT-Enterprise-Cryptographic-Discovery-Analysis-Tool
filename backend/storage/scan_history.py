import json
from pathlib import Path
from typing import Any, Dict, List, Optional


BASE_DIR = Path(__file__).resolve().parents[1]
HISTORY_DIR = BASE_DIR / "output" / "history"
def _history_filename(scan_id: str) -> str:
    """
    Convert a logical scan ID into a filesystem-safe filename.

    The logical scan ID remains unchanged in the stored JSON.
    """
    safe_id = (
        str(scan_id)
        .replace("/", "_")
        .replace("\\", "_")
        .replace(":", "_")
    )

    return f"{safe_id}.json"

def ensure_history_directory() -> Path:
    HISTORY_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    return HISTORY_DIR


def save_scan_state(
    scan_state: Dict[str, Any],
) -> Path:
    """
    Persist one immutable historical scan state.

    Each scan is stored as its own JSON document.
    """
    ensure_history_directory()

    scan_id = str(
        scan_state.get(
            "scan_id",
            "",
        )
    ).strip()

    if not scan_id:
        raise ValueError(
            "scan_state.scan_id is required."
        )

    file_path = (
        HISTORY_DIR /
        _history_filename(scan_id)
    )

    payload = json.dumps(
        scan_state,
        indent=2,
        ensure_ascii=False,
    )

    file_path.write_text(
        payload,
        encoding="utf-8",
    )

    return file_path


def load_scan_state(
    scan_id: str,
) -> Optional[Dict[str, Any]]:
    """
    Load one historical scan state.
    """
    ensure_history_directory()

    scan_id = str(
        scan_id
    ).strip()

    if not scan_id:
        return None

    file_path = (
        HISTORY_DIR /
        _history_filename(scan_id)
    )
    if not file_path.exists():
        return None

    return json.loads(
        file_path.read_text(
            encoding="utf-8"
        )
    )


def list_scan_states() -> List[Dict[str, Any]]:
    """
    Return historical scan summaries ordered
    newest first.
    """
    ensure_history_directory()

    states: List[Dict[str, Any]] = []

    for file_path in HISTORY_DIR.glob(
        "*.json"
    ):
        try:
            data = json.loads(
                file_path.read_text(
                    encoding="utf-8"
                )
            )

            states.append(
                {
                    "scan_id":
                        data.get(
                            "scan_id"
                        ),
                    "generated_at":
                        data.get(
                            "generated_at"
                        ),
                    "target":
                        data.get(
                            "target"
                        ),
                    "application_ids":
                        data.get(
                            "application_ids",
                            [],
                        ),
		    "artifact_count":
		        len(
                            data.get(
                               "artifact_ids",
                               [],
                            )
                        ),
                     "evidence_count":
                         len(
                             data.get(
                                "evidence",
                                 [],
                              )
                          ),
                      "relationship_count":
                          len(
                              data.get(
                                 "relationships",
                                 [],
                               )
                           ),
                       "business_context_count":
                           len(
                               data.get(
                                  "business_contexts",
                                  [],
                                )
                           ),
                        "summary":
                            data.get(
                                "summary",
                                {},
                            ),
                }
            )

        except (
            OSError,
            json.JSONDecodeError,
        ):
            # Ignore malformed historical
            # entries rather than breaking
            # the entire history view.
            continue

    states.sort(
        key=lambda item:
            str(
                item.get(
                    "generated_at",
                    "",
                )
            ),
        reverse=True,
    )

    return states
