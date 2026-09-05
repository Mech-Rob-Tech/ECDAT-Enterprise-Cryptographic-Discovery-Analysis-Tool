from __future__ import annotations

from typing import Optional

from knowledge.compatibility import applicable_constraints
from knowledge.migration import candidate_migrations
from knowledge.schema import KnowledgeRegistry, KnowledgeResolution
from knowledge.temporal import is_effective


def _normalize(value: str) -> str:
    return (
        value
        .strip()
        .upper()
        .replace("_", "-")
        .replace(" ", "-")
    )


def resolve_algorithm(
    registry: KnowledgeRegistry,
    query: str,
    purpose: Optional[str] = None,
    as_of: Optional[str] = None,
    target_type: Optional[str] = None,
    target_name: Optional[str] = None,
    target_version: Optional[str] = None,
) -> KnowledgeResolution:
    normalized = _normalize(query)

    exact = None
    matched_by = None

    for algorithm in registry.algorithms:
        candidates = {
            _normalize(algorithm.name),
            *{
                _normalize(alias)
                for alias in algorithm.aliases
            },
        }

        if normalized in candidates:
            exact = algorithm
            matched_by = (
                "canonical_name"
                if normalized == _normalize(algorithm.name)
                else "alias"
            )
            break

    if exact is None:
        return KnowledgeResolution(
            query=query,
            normalized_query=normalized,
            algorithm=None,
            matched_by=None,
            standards=(),
            compatibility=(),
            migrations=(),
            conflicts=(),
            current=False,
            knowledge_version=registry.manifest.knowledge_version,
            explainability={
                "status": "unresolved",
                "reason": "No canonical name or alias matched.",
            },
        )

    current = is_effective(
        exact.effective_from,
        exact.effective_until,
        as_of,
    )

    standards = tuple(
        standard
        for standard in registry.standards
        if exact.name in standard.related_algorithms
        and is_effective(
            standard.effective_from,
            standard.effective_until,
            as_of,
        )
    )

    compatibility = tuple(
        item
        for item in applicable_constraints(
            registry.compatibility,
            target_type=target_type,
            target_name=target_name,
            version=target_version,
        )
        if _normalize(item.algorithm) == normalized
        and is_effective(
            item.effective_from,
            item.effective_until,
            as_of,
        )
    )

    migrations = tuple(
        item
        for item in candidate_migrations(
            registry.migrations,
            exact.name,
            purpose=purpose,
        )
        if is_effective(
            item.effective_from,
            item.effective_until,
            as_of,
        )
    )

    conflicts = tuple(
        conflict
        for conflict in registry.conflicts
        if conflict.subject_id.upper() == exact.name.upper()
    )

    return KnowledgeResolution(
        query=query,
        normalized_query=normalized,
        algorithm=exact,
        matched_by=matched_by,
        standards=standards,
        compatibility=compatibility,
        migrations=migrations,
        conflicts=conflicts,
        current=current,
        knowledge_version=registry.manifest.knowledge_version,
        explainability={
            "matched_by": matched_by,
            "algorithm": exact.name,
            "purpose_filter": purpose,
            "as_of": as_of,
            "standards_found": len(standards),
            "compatibility_records_found": len(compatibility),
            "migration_candidates_found": len(migrations),
            "conflicts_found": len(conflicts),
        },
    )
