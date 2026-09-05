from __future__ import annotations

from datetime import date
from typing import Optional


def parse_date(value: Optional[str]) -> Optional[date]:
    if not value:
        return None
    return date.fromisoformat(value)


def is_effective(
    effective_from: Optional[str],
    effective_until: Optional[str],
    as_of: Optional[str] = None,
) -> bool:
    point = (
        date.fromisoformat(as_of)
        if as_of
        else date.today()
    )

    start = parse_date(effective_from)
    end = parse_date(effective_until)

    if start and point < start:
        return False

    if end and point >= end:
        return False

    return True


def validity_label(
    effective_from: Optional[str],
    effective_until: Optional[str],
    as_of: Optional[str] = None,
) -> str:
    return (
        "current"
        if is_effective(
            effective_from,
            effective_until,
            as_of,
        )
        else "historical_or_future"
    )
