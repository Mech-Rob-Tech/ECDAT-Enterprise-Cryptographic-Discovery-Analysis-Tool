from __future__ import annotations

from knowledge.schema import VALID_LIFECYCLE_STATUSES


STATUS_PRIORITY = {
    "withdrawn": 100,
    "deprecated": 90,
    "legacy": 80,
    "candidate": 60,
    "draft": 50,
    "standardized": 40,
    "approved": 30,
    "active": 20,
    "unknown": 0,
}


def validate_status(status: str) -> None:
    if status not in VALID_LIFECYCLE_STATUSES:
        raise ValueError(
            f"Unsupported lifecycle status: {status}"
        )


def status_priority(status: str) -> int:
    validate_status(status)
    return STATUS_PRIORITY[status]


def is_migration_relevant(status: str) -> bool:
    return status in {
        "withdrawn",
        "deprecated",
        "legacy",
    }


def is_usable(status: str) -> bool:
    return status in {
        "standardized",
        "approved",
        "active",
    }
