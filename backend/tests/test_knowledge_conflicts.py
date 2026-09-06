import sys
from pathlib import Path

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1]),
)

from knowledge.conflicts import detect_algorithm_conflicts
from knowledge.schema import AlgorithmKnowledge, SecurityStrength


def test_conflicting_records_are_detected():
    records = (
        AlgorithmKnowledge(
            knowledge_id="a",
            name="TEST",
            aliases=("TEST",),
            family="x",
            primitive="signature",
            purposes=("digital_signature",),
            lifecycle_status="active",
            quantum_posture="quantum_vulnerable",
            security_strength=SecurityStrength(),
            key_sizes=(),
            parameters=(),
            components=(),
            standards=(),
            description="x",
            notes="x",
            effective_from=None,
            effective_until=None,
            source_ids=("source:a",),
            confidence="high",
        ),
        AlgorithmKnowledge(
            knowledge_id="b",
            name="TEST",
            aliases=("TEST",),
            family="x",
            primitive="signature",
            purposes=("digital_signature",),
            lifecycle_status="deprecated",
            quantum_posture="quantum_vulnerable",
            security_strength=SecurityStrength(),
            key_sizes=(),
            parameters=(),
            components=(),
            standards=(),
            description="x",
            notes="x",
            effective_from=None,
            effective_until=None,
            source_ids=("source:b",),
            confidence="high",
        ),
    )

    conflicts = detect_algorithm_conflicts(records)

    assert conflicts
    assert any(
        conflict.field == "lifecycle_status"
        for conflict in conflicts
    )
