from __future__ import annotations

from typing import Optional, Tuple

from knowledge.compatibility import applicable_constraints
from knowledge.migration import candidate_migrations
from knowledge.schema import (
    AlgorithmKnowledge,
    KnowledgeRegistry,
    KnowledgeResolution,
    ProtocolApplicability,
    ResolvedCandidate,
)
from knowledge.temporal import is_effective


def _normalize(value: str) -> str:
    return (
        value
        .strip()
        .upper()
        .replace("_", "-")
        .replace(" ", "-")
    )


def _protocol_matches(
    record: ProtocolApplicability,
    *,
    protocol: Optional[str],
    protocol_version: Optional[str],
    purpose: Optional[str],
) -> bool:
    if protocol and _normalize(record.protocol) != _normalize(protocol):
        return False

    if (
        protocol_version
        and _normalize(record.protocol_version or "")
        != _normalize(protocol_version)
    ):
        return False

    if purpose:
        usage = _normalize(record.usage)
        requested = _normalize(purpose)

        equivalent_usages = {
            "KEY-ESTABLISHMENT": {
                "KEY-ESTABLISHMENT",
                "KEY-AGREEMENT",
            },
            "KEY-AGREEMENT": {
                "KEY-ESTABLISHMENT",
                "KEY-AGREEMENT",
            },
        }

        accepted_usages = equivalent_usages.get(
            requested,
            {requested},
        )

        if usage not in {"", "UNKNOWN", *accepted_usages}:
            return False

    return True


def _contextual_candidates(
    registry: KnowledgeRegistry,
    migrations,
    *,
    purpose: Optional[str],
    protocol: Optional[str],
    protocol_version: Optional[str],
    as_of: Optional[str],
) -> Tuple[ResolvedCandidate, ...]:
    """
    Expand generic migration targets into concrete protocol mechanisms.

    Example:

        ECDH -> ML-KEM

    under TLS 1.3 becomes:

        X25519MLKEM768
        SecP256r1MLKEM768
        SecP384r1MLKEM1024

    when those concrete algorithms contain the generic migration target
    as a component and have matching protocol applicability evidence.
    """

    if not protocol:
        return ()


    resolved = []

    for relationship in migrations:
        target = next(
            (
                algorithm
                for algorithm in registry.algorithms
                if _normalize(algorithm.name)
                == _normalize(relationship.target_algorithm)
            ),
            None,
        )

        if target is None:
            continue

        target_id = _normalize(target.knowledge_id)

        for candidate in registry.algorithms:
            if candidate.primitive != "composite":
                continue

            if purpose and _normalize(purpose) not in {
                _normalize(item) for item in candidate.purposes
            }:
                continue

            if not is_effective(
                candidate.effective_from,
                candidate.effective_until,
                as_of,
            ):
                continue

            component_ids = {
                _normalize(component)
                for component in candidate.components
            }

            if target_id not in component_ids:
                continue

            applicability = tuple(
                record
                for record in registry.protocols
                if _normalize(record.algorithm)
                == _normalize(candidate.name)
                and _protocol_matches(
                    record,
                    protocol=protocol,
                    protocol_version=protocol_version,
                    purpose=purpose,
                )
                and is_effective(
                    record.effective_from,
                    record.effective_until,
                    as_of,
                )
            )

            if not applicability:
                continue

            resolved.append(
                ResolvedCandidate(
                    relationship=relationship,
                    target_algorithm=candidate,
                    protocol_applicability=applicability,
                )
            )

    return tuple(
        sorted(
            resolved,
            key=lambda item: (
                _normalize(item.target_algorithm.name),
                item.relationship.relationship_id,
            ),
        )
    )


def resolve_algorithm(
    registry: KnowledgeRegistry,
    query: str,
    purpose: Optional[str] = None,
    as_of: Optional[str] = None,
    target_type: Optional[str] = None,
    target_name: Optional[str] = None,
    target_version: Optional[str] = None,
    protocol: Optional[str] = None,
    protocol_version: Optional[str] = None,
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
            contextual_candidates=(),
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

    contextual_candidates = _contextual_candidates(
        registry,
        migrations,
        purpose=purpose,
        protocol=protocol,
        protocol_version=protocol_version,
        as_of=as_of,
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
        contextual_candidates=contextual_candidates,
        conflicts=conflicts,
        current=current,
        knowledge_version=registry.manifest.knowledge_version,
        explainability={
            "matched_by": matched_by,
            "algorithm": exact.name,
            "purpose_filter": purpose,
            "protocol_filter": protocol,
            "protocol_version_filter": protocol_version,
            "as_of": as_of,
            "standards_found": len(standards),
            "compatibility_records_found": len(compatibility),
            "migration_candidates_found": len(migrations),
            "contextual_candidates_found": len(
                contextual_candidates
            ),
            "conflicts_found": len(conflicts),
        },
    )
