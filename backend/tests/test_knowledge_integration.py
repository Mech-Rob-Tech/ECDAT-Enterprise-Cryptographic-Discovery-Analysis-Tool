import sys
from pathlib import Path

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1]),
)

from knowledge.serialization import registry_to_json
from knowledge.service import KnowledgeService


def test_serialization_is_deterministic():
    service = KnowledgeService()

    first = registry_to_json(
        service.registry
    )

    second = registry_to_json(
        service.registry
    )

    assert first == second
    assert '"knowledge_version": "0.5.0"' in first


def test_service_exposes_integrity():
    service = KnowledgeService()

    assert service.version == "0.5.0"
    assert len(service.integrity_hash) == 64
