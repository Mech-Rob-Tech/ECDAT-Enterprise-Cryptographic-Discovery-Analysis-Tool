import sys
from pathlib import Path

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1]),
)

from knowledge.service import KnowledgeService


def test_purpose_aware_rsa_signature_candidates():
    service = KnowledgeService()

    result = service.resolve(
        "RSA",
        purpose="digital_signature",
    )

    targets = {
        item.target_algorithm
        for item in result.migrations
    }

    assert "ML-DSA" in targets
    assert "ML-KEM" not in targets


def test_purpose_aware_rsa_key_establishment_candidates():
    service = KnowledgeService()

    result = service.resolve(
        "RSA",
        purpose="key_establishment",
    )

    targets = {
        item.target_algorithm
        for item in result.migrations
    }

    assert "ML-KEM" in targets
    assert "ML-DSA" not in targets
