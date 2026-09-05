import sys
from pathlib import Path

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1]),
)

from knowledge.service import KnowledgeService
from knowledge.temporal import is_effective


def test_temporal_validity():
    assert is_effective(
        "2024-01-01",
        None,
        "2026-01-01",
    )

    assert not is_effective(
        "2027-01-01",
        None,
        "2026-01-01",
    )

    assert not is_effective(
        "2020-01-01",
        "2025-01-01",
        "2026-01-01",
    )


def test_historical_resolution():
    service = KnowledgeService()

    result = service.resolve(
        "ML-KEM",
        as_of="2023-01-01",
    )

    assert result.algorithm is not None
    assert result.current is False
    assert result.standards == ()
