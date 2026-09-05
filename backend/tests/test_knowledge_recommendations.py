import sys
from pathlib import Path

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1]),
)

from analysis.recommendations import (
    build_recommendation,
    get_migration_candidates,
    get_recommendation,
)


def test_rsa_signature_is_knowledge_driven():
    artifact = {
        "algorithm": "RSA",
        "purpose": "digital_signature",
        "risk": {
            "quantum": {
                "level": "HIGH"
            }
        },
    }

    result = build_recommendation(artifact)

    assert result["status"] == "RESOLVED"
    assert result["algorithm"] == "RSA"
    assert "ML-DSA" in {
        item["target_algorithm"]
        for item in result["candidates"]
    }

    assert result["knowledge_version"] == "0.5.0"
    assert result["knowledge_hash"]


def test_rsa_key_establishment_is_different():
    artifact = {
        "algorithm": "RSA",
        "purpose": "key_establishment",
        "risk": {
            "quantum": {
                "level": "HIGH"
            }
        },
    }

    result = build_recommendation(artifact)

    targets = {
        item["target_algorithm"]
        for item in result["candidates"]
    }

    assert "ML-KEM" in targets
    assert "ML-DSA" not in targets


def test_unknown_algorithm_does_not_invent_recommendation():
    artifact = {
        "algorithm": "FUTURE-CRYPTO-999",
        "purpose": "digital_signature",
    }

    result = build_recommendation(artifact)

    assert result["status"] == "UNRESOLVED"
    assert result["candidate_count"] == 0
    assert "manual review" in result["text"].lower()


def test_candidates_are_knowledge_records():
    artifact = {
        "algorithm": "ECDH",
        "purpose": "key_establishment",
    }

    candidates = get_migration_candidates(
        artifact
    )

    assert candidates

    for candidate in candidates:
        assert candidate["relationship_id"]
        assert candidate["target_algorithm"]
        assert candidate["confidence"]


def test_public_function_has_no_algorithm_specific_lookup_table():
    import inspect
    from analysis import recommendations

    source = inspect.getsource(
        recommendations.get_recommendation
    )

    forbidden = [
        'algorithm == "RSA"',
        'algorithm == "ECDSA"',
        'algorithm == "AES"',
        'algorithm == "SHA-1"',
        'algorithm == "MD5"',
        'algorithm == "DES"',
    ]

    for pattern in forbidden:
        assert pattern not in source
