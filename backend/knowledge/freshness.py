from __future__ import annotations

from datetime import date
from typing import Optional


DEFAULT_MAX_AGE_DAYS = 180


def _parse_date(value: Optional[str]) -> Optional[date]:
    if not value:
        return None

    return date.fromisoformat(
        value[:10]
    )


def age_days(
    retrieved_at: Optional[str],
    *,
    as_of: Optional[str] = None,
) -> Optional[int]:
    retrieved = _parse_date(retrieved_at)

    if retrieved is None:
        return None

    point = (
        _parse_date(as_of)
        if as_of
        else date.today()
    )

    if point is None:
        return None

    return (point - retrieved).days


def freshness_state(
    retrieved_at: Optional[str],
    *,
    max_age_days: int = DEFAULT_MAX_AGE_DAYS,
    as_of: Optional[str] = None,
) -> str:
    age = age_days(
        retrieved_at,
        as_of=as_of,
    )

    if age is None:
        return "unknown"

    if age < 0:
        return "invalid"

    if age <= max_age_days:
        return "fresh"

    return "stale"


def evaluate_source(
    retrieved_at: Optional[str],
    *,
    max_age_days: int = DEFAULT_MAX_AGE_DAYS,
    as_of: Optional[str] = None,
) -> dict:
    age = age_days(
        retrieved_at,
        as_of=as_of,
    )

    state = freshness_state(
        retrieved_at,
        max_age_days=max_age_days,
        as_of=as_of,
    )

    return {
        "state": state,
        "age_days": age,
        "max_age_days": max_age_days,
        "retrieved_at": retrieved_at,
    }


def registry_freshness(
    provenance,
    *,
    max_age_days: int = DEFAULT_MAX_AGE_DAYS,
    as_of: Optional[str] = None,
) -> dict:
    records = [
        evaluate_source(
            source.retrieved_at,
            max_age_days=max_age_days,
            as_of=as_of,
        )
        for source in provenance
    ]

    states = {
        item["state"]
        for item in records
    }

    if "invalid" in states:
        overall = "invalid"
    elif "stale" in states:
        overall = "stale"
    elif "unknown" in states:
        overall = "unknown"
    else:
        overall = "fresh"

    return {
        "state": overall,
        "sources": records,
        "source_count": len(records),
        "stale_count": sum(
            item["state"] == "stale"
            for item in records
        ),
        "unknown_count": sum(
            item["state"] == "unknown"
            for item in records
        ),
    }
