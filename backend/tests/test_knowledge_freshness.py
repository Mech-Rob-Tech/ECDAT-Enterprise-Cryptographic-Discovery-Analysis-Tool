import sys
from pathlib import Path

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1]),
)

from knowledge.freshness import (
    age_days,
    freshness_state,
    registry_freshness,
)
from knowledge.service import KnowledgeService


def test_fresh_source():
    assert (
        freshness_state(
            "2026-09-01",
            as_of="2026-09-05",
            max_age_days=180,
        )
        == "fresh"
    )


def test_stale_source():
    assert (
        freshness_state(
            "2025-01-01",
            as_of="2026-09-05",
            max_age_days=180,
        )
        == "stale"
    )


def test_future_source_is_invalid():
    assert (
        freshness_state(
            "2026-10-01",
            as_of="2026-09-05",
        )
        == "invalid"
    )


def test_registry_is_fresh():
    service = KnowledgeService()

    result = service.freshness(
        as_of="2026-09-05"
    )

    assert result["state"] == "fresh"
    assert result["stale_count"] == 0


def test_snapshot_current():
    service = KnowledgeService()

    snapshot = service.snapshot()

    assert (
        service.snapshot_state(
            snapshot["knowledge_version"],
            snapshot["knowledge_hash"],
        )
        == "VALID"
    )


def test_snapshot_stale_version():
    service = KnowledgeService()

    assert (
        service.snapshot_state(
            "0.4.0",
            service.integrity_hash,
        )
        == "STALE"
    )


def test_snapshot_stale_hash():
    service = KnowledgeService()

    assert (
        service.snapshot_state(
            service.version,
            "0" * 64,
        )
        == "STALE"
    )
