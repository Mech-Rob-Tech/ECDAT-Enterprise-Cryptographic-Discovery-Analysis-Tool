import sys
from pathlib import Path

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1]),
)

from knowledge.service import KnowledgeService


def test_rsa_resolution():
    service = KnowledgeService()

    result = service.resolve(
        "rsa-2048",
        purpose="digital_signature",
    )

    assert result.algorithm is not None
    assert result.algorithm.name == "RSA"
    assert result.matched_by == "alias"
    assert result.algorithm.quantum_posture == "quantum_vulnerable"
    assert any(
        item.target_algorithm == "ML-DSA"
        for item in result.migrations
    )


def test_ml_dsa_resolution():
    service = KnowledgeService()

    result = service.resolve("MLDSA")

    assert result.algorithm is not None
    assert result.algorithm.name == "ML-DSA"
    assert result.algorithm.lifecycle_status == "standardized"
    assert result.current is True
    assert "FIPS 204" in result.algorithm.standards


def test_unknown_resolution():
    service = KnowledgeService()

    result = service.resolve(
        "NOT-A-REAL-ALGORITHM"
    )

    assert result.algorithm is None
    assert result.explainability["status"] == "unresolved"
