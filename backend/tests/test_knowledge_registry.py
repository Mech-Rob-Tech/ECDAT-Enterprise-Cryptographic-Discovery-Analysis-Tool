import sys
from pathlib import Path

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1]),
)

from knowledge.registry import get_registry
from knowledge.validation import validate_registry


def test_registry_validates():
    registry = get_registry()
    validate_registry(registry)


def test_registry_counts_match_manifest():
    registry = get_registry()

    assert registry.manifest.algorithm_count == len(
        registry.algorithms
    )

    assert registry.manifest.standard_count == len(
        registry.standards
    )

    assert registry.manifest.compatibility_count == len(
        registry.compatibility
    )

    assert registry.manifest.migration_count == len(
        registry.migrations
    )
