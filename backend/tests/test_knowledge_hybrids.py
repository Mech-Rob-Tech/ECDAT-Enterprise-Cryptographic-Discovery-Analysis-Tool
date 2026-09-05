from dataclasses import replace

import pytest

from knowledge.registry import get_registry
from knowledge.validation import validate_registry


HYBRID_IDS = (
    "alg:x25519mlkem768",
    "alg:secp256r1mlkem768",
    "alg:secp384r1mlkem1024",
)


def _by_id():
    return {
        item.knowledge_id: item
        for item in get_registry().algorithms
    }


def _registry_with_algorithm(replacement):
    registry = get_registry()
    algorithms = tuple(
        replacement if item.knowledge_id == replacement.knowledge_id else item
        for item in registry.algorithms
    )
    return replace(registry, algorithms=algorithms)


def test_rfc_10024_hybrids_have_expected_components():
    algorithms = _by_id()

    assert algorithms["alg:x25519mlkem768"].components == (
        "alg:x25519",
        "alg:ml-kem",
    )
    assert algorithms["alg:x25519mlkem768"].parameters == ("ML-KEM-768",)

    assert algorithms["alg:secp256r1mlkem768"].components == (
        "alg:secp256r1",
        "alg:ml-kem",
    )
    assert algorithms["alg:secp256r1mlkem768"].parameters == ("ML-KEM-768",)

    assert algorithms["alg:secp384r1mlkem1024"].components == (
        "alg:secp384r1",
        "alg:ml-kem",
    )
    assert algorithms["alg:secp384r1mlkem1024"].parameters == (
        "ML-KEM-1024",
    )


def test_hybrid_components_resolve():
    algorithms = _by_id()

    for hybrid_id in HYBRID_IDS:
        hybrid = algorithms[hybrid_id]

        assert hybrid.primitive == "composite"
        assert hybrid.components

        for component_id in hybrid.components:
            assert component_id in algorithms


def test_hybrid_parameters_belong_to_declared_components():
    algorithms = _by_id()

    for hybrid_id in HYBRID_IDS:
        hybrid = algorithms[hybrid_id]
        components = [
            algorithms[component_id]
            for component_id in hybrid.components
        ]

        for parameter in hybrid.parameters:
            assert any(
                parameter in component.parameters
                for component in components
            )


def test_registry_rejects_unknown_hybrid_component():
    algorithms = _by_id()
    hybrid = algorithms["alg:x25519mlkem768"]

    broken_hybrid = replace(
        hybrid,
        components=(
            "alg:x25519",
            "alg:does-not-exist",
        ),
    )

    broken_registry = _registry_with_algorithm(broken_hybrid)

    with pytest.raises(ValueError, match="unknown component"):
        validate_registry(broken_registry)


def test_registry_rejects_unknown_hybrid_parameter():
    algorithms = _by_id()
    hybrid = algorithms["alg:x25519mlkem768"]

    broken_hybrid = replace(
        hybrid,
        parameters=("ML-KEM-999",),
    )

    broken_registry = _registry_with_algorithm(broken_hybrid)

    with pytest.raises(ValueError, match="unknown component parameter"):
        validate_registry(broken_registry)
