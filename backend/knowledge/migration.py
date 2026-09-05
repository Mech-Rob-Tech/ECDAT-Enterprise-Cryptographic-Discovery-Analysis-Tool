from __future__ import annotations

from typing import Iterable, List, Optional

from knowledge.schema import MigrationRelationship


def candidate_migrations(
    relationships: Iterable[MigrationRelationship],
    source_algorithm: str,
    purpose: Optional[str] = None,
    include_hybrid: bool = True,
) -> List[MigrationRelationship]:
    result = []

    for relationship in relationships:
        if relationship.source_algorithm.upper() != source_algorithm.upper():
            continue

        if not include_hybrid and relationship.hybrid:
            continue

        if (
            purpose
            and relationship.applicable_purposes
            and purpose.lower()
            not in {
                value.lower()
                for value in relationship.applicable_purposes
            }
        ):
            continue

        result.append(relationship)

    return sorted(
        result,
        key=lambda item: (
            item.hybrid,
            item.target_algorithm,
        ),
    )
