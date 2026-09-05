from __future__ import annotations

from datetime import date
from typing import Optional


def age_days(retrieved_at: Optional[str]) -> Optional[int]:
    if not retrieved_at:
        return None

    retrieved = date.fromisoformat(
        retrieved_at[:10]
    )

    return (date.today() - retrieved).days


def freshness_state(
    retrieved_at: Optional[str],
    max_age_days: int = 180,
) -> str:
    age = age_days(retrieved_at)

    if age is None:
        return "unknown"

    if age < 0:
        return "invalid"

    if age <= max_age_days:
        return "fresh"

    return "stale"
