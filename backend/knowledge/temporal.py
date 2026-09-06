from __future__ import annotations

from datetime import date
from typing import Optional


def parse_date(
    value: Optional[str],
) -> Optional[date]:
    if not value:
        return None

    return date.fromisoformat(
        value[:10]
    )


def is_effective(
    effective_from: Optional[str],
    effective_until: Optional[str],
    as_of: Optional[str] = None,
) -> bool:
    point = (
        parse_date(as_of)
        if as_of
        else date.today()
    )

    if point is None:
        return False

    start = parse_date(
        effective_from
    )

    end = parse_date(
        effective_until
    )

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


def snapshot_matches(
    snapshot_version: Optional[str],
    snapshot_hash: Optional[str],
    current_version: str,
    current_hash: str,
) -> bool:
    return (
        bool(snapshot_version)
        and bool(snapshot_hash)
        and snapshot_version == current_version
        and snapshot_hash == current_hash
    )


def snapshot_state(
    snapshot_version: Optional[str],
    snapshot_hash: Optional[str],
    current_version: str,
    current_hash: str,
) -> str:
    if not snapshot_version or not snapshot_hash:
        return "UNKNOWN"

    if snapshot_matches(
        snapshot_version,
        snapshot_hash,
        current_version,
        current_hash,
    ):
        return "VALID"

    return "STALE"
