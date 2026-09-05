import sys
from pathlib import Path

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1]),
)

from knowledge.registry import get_registry
from knowledge.schema import SCHEMA_VERSION


def test_schema_and_registry():
    registry = get_registry()

    assert registry.manifest.schema_version == SCHEMA_VERSION
    assert registry.manifest.algorithm_count >= 10
    assert registry.manifest.standard_count >= 4
    assert registry.manifest.registry_hash


def test_required_pqc_algorithms():
    registry = get_registry()

    names = {
        item.name
        for item in registry.algorithms
    }

    assert "ML-KEM" in names
    assert "ML-DSA" in names
    assert "SLH-DSA" in names
