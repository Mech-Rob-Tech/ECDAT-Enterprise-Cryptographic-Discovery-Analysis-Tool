from __future__ import annotations

from typing import Iterable, List, Optional

from knowledge.schema import (
    CompatibilityConstraint,
)


def _version_tuple(value: Optional[str]):
    if not value:
        return None

    parts = []
    for part in value.split("."):
        number = ""
        for char in part:
            if char.isdigit():
                number += char
            else:
                break

        parts.append(int(number or 0))

    return tuple(parts)


def version_matches(
    version: Optional[str],
    version_min: Optional[str],
    version_max: Optional[str],
) -> bool:
    if not version:
        return True

    current = _version_tuple(version)

    minimum = _version_tuple(version_min)
    maximum = _version_tuple(version_max)

    if minimum and current < minimum:
        return False

    if maximum and current > maximum:
        return False

    return True


def applicable_constraints(
    constraints: Iterable[CompatibilityConstraint],
    target_type: Optional[str] = None,
    target_name: Optional[str] = None,
    version: Optional[str] = None,
) -> List[CompatibilityConstraint]:
    result = []

    for constraint in constraints:
        if target_type and constraint.target_type != target_type:
            continue

        if target_name and constraint.target_name.lower() != target_name.lower():
            continue

        if not version_matches(
            version,
            constraint.version_min,
            constraint.version_max,
        ):
            continue

        result.append(constraint)

    return result


def compatibility_status(
    constraints: Iterable[CompatibilityConstraint],
) -> str:
    statuses = {item.status for item in constraints}

    if "unsupported" in statuses:
        return "unsupported"

    if "conditional" in statuses:
        return "conditional"

    if "supported" in statuses:
        return "supported"

    return "unknown"
