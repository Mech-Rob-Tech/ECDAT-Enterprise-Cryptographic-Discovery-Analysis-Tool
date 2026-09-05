from __future__ import annotations

from collections import defaultdict
from typing import Iterable, List

from knowledge.schema import (
    AlgorithmKnowledge,
    KnowledgeConflict,
)


def detect_algorithm_conflicts(
    algorithms: Iterable[AlgorithmKnowledge],
) -> List[KnowledgeConflict]:
    grouped = defaultdict(list)

    for algorithm in algorithms:
        grouped[algorithm.name.upper()].append(algorithm)

    conflicts = []

    for name, records in grouped.items():
        for field in (
            "lifecycle_status",
            "quantum_posture",
            "family",
            "primitive",
        ):
            values = {
                str(getattr(record, field))
                for record in records
            }

            if len(values) > 1:
                source_ids = sorted(
                    {
                        source_id
                        for record in records
                        for source_id in record.source_ids
                    }
                )

                conflicts.append(
                    KnowledgeConflict(
                        conflict_id=(
                            f"conflict:algorithm:{name.lower()}:{field}"
                        ),
                        subject_type="algorithm",
                        subject_id=name,
                        field=field,
                        values=tuple(sorted(values)),
                        source_ids=tuple(source_ids),
                        resolution=(
                            "manual_review_required"
                        ),
                        severity="HIGH",
                    )
                )

    return conflicts


def resolve_conflicts(
    conflicts: Iterable[KnowledgeConflict],
) -> List[KnowledgeConflict]:
    """
    Conservative policy:

    Never silently choose a cryptographic fact when authoritative
    sources disagree. Preserve the conflict and require review.
    """
    return list(conflicts)
