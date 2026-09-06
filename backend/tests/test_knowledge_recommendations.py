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


def test_recommendation_snapshot_is_current():
    from analysis.recommendations import (
        recommendation_freshness,
    )

    artifact = {
        "algorithm": "RSA",
        "purpose": "digital_signature",
        "risk": {
            "quantum": {
                "level": "HIGH"
            }
        },
    }

    recommendation = build_recommendation(
        artifact
    )

    state = recommendation_freshness(
        recommendation
    )

    assert state["state"] == "VALID"
    assert state["reanalysis_required"] is False


def test_old_recommendation_becomes_stale():
    from analysis.recommendations import (
        recommendation_freshness,
    )

    recommendation = {
        "knowledge_version": "0.4.0",
        "knowledge_hash": "0" * 64,
    }

    state = recommendation_freshness(
        recommendation
    )

    assert state["state"] == "STALE"
    assert state["reanalysis_required"] is True


def test_candidates_are_ranked_by_protocol_evidence():
    artifact = {
        "algorithm": "ECDH",
        "purpose": "key_establishment",
        "protocol": "TLS",
        "protocol_version": "1.3",
    }

    result = build_recommendation(artifact)

    assert result["candidate_count"] >= 2

    candidates = result["candidates"]

    assert all(
        "score" in candidate
        for candidate in candidates
    )

    assert all(
        "reasons" in candidate
        for candidate in candidates
    )

    assert all(
        "penalties" in candidate
        for candidate in candidates
    )

    scores = [
        candidate["score"]
        for candidate in candidates
    ]

    assert scores == sorted(
        scores,
        reverse=True,
    )


def test_protocol_recommendation_is_explainable():
    artifact = {
        "algorithm": "ECDH",
        "purpose": "key_establishment",
        "protocol": "TLS",
        "protocol_version": "1.3",
    }

    result = build_recommendation(artifact)

    primary = result["primary_candidate"]

    assert primary is not None
    assert primary["target_algorithm"]

    selection = result["explainability"]["selection"]

    assert (
        selection["target_algorithm"]
        == primary["target_algorithm"]
    )

    assert (
        selection["score"]
        == primary["score"]
    )

    assert (
        selection["decision"]
        == primary["decision"]
    )

    assert isinstance(
        selection["reasons"],
        list,
    )

    assert any(
        "recommended"
        in reason.lower()
        or "supported"
        in reason.lower()
        for reason in selection["reasons"]
    )


def test_ranking_is_deterministic():
    artifact = {
        "algorithm": "ECDH",
        "purpose": "key_establishment",
        "protocol": "TLS",
        "protocol_version": "1.3",
    }

    first = build_recommendation(artifact)
    second = build_recommendation(artifact)

    assert first["primary_candidate"] == second["primary_candidate"]
    assert first["candidates"] == second["candidates"]

# ---------------------------------------------------------------------------
# Production-grade v0.5 scoring audit
# ---------------------------------------------------------------------------

from types import SimpleNamespace

import pytest

from analysis.candidate_scoring import score_candidate, rank_candidates


def _scoring_artifact():
    return {
        "algorithm": "ECDH",
        "purpose": "key_establishment",
    }


def _scoring_candidate(**overrides):
    candidate = {
        "relationship_id": "test:relationship",
        "source_algorithm": "ECDH",
        "target_algorithm": "X25519MLKEM768",
        "relationship_type": "replaces",
        "hybrid": False,
        "confidence": "high",
        "applicable_purposes": ["key_establishment"],
        "prerequisites": [],
        "constraints": [],
    }
    candidate.update(overrides)
    return candidate


def _score(
    candidate,
    *,
    artifact=None,
    standards=(),
    protocols=(),
):
    return score_candidate(
        candidate,
        artifact=artifact or _scoring_artifact(),
        standards=standards,
        protocols=protocols,
    )


def test_scoring_factor_relationship_quality_is_sensitive():
    strong = _score(
        _scoring_candidate(
            relationship_type="replaces",
        )
    )
    weak = _score(
        _scoring_candidate(
            relationship_type="related_to",
        )
    )

    assert strong["score"] > weak["score"]
    assert any(
        "relationship" in reason.lower()
        for reason in strong["reasons"]
    )


def test_scoring_factor_hybrid_is_sensitive():
    non_hybrid = _score(
        _scoring_candidate(
            hybrid=False,
        )
    )
    hybrid = _score(
        _scoring_candidate(
            hybrid=True,
        )
    )

    assert hybrid["score"] == non_hybrid["score"] + 8
    assert any(
        "hybrid" in reason.lower()
        for reason in hybrid["reasons"]
    )


@pytest.mark.parametrize(
    "confidence",
    [
        "high",
        "medium",
        "low",
        "unknown",
    ],
)
def test_scoring_factor_confidence_is_sensitive(confidence):
    result = _score(
        _scoring_candidate(
            confidence=confidence,
        )
    )

    expected_deltas = {
        "high": 8,
        "medium": 4,
        "low": -5,
        "unknown": -8,
    }

    baseline = 50 + 18 + 6 + 5

    assert result["score"] == (
        baseline + expected_deltas[confidence]
    )


def test_scoring_factor_purpose_alignment_is_sensitive():
    matching = _score(
        _scoring_candidate(
            applicable_purposes=["key_establishment"],
        )
    )

    mismatching = _score(
        _scoring_candidate(
            applicable_purposes=["digital_signature"],
        )
    )

    assert matching["score"] > mismatching["score"]
    assert matching["score"] - mismatching["score"] == 24

    assert any(
        "purpose" in reason.lower()
        for reason in matching["reasons"]
    )

    assert any(
        "purpose" in penalty.lower()
        for penalty in mismatching["penalties"]
    )


@pytest.mark.parametrize(
    "status,expected_delta",
    [
        ("approved", 8),
        ("active", 8),
        ("standardized", 8),
        ("final", 8),
        ("candidate", 2),
        ("draft", 2),
    ],
)
def test_scoring_factor_standard_status_is_sensitive(
    status,
    expected_delta,
):
    standard = SimpleNamespace(
        related_algorithms=("X25519MLKEM768",),
        status=status,
    )

    baseline = _score(
        _scoring_candidate(),
    )

    result = _score(
        _scoring_candidate(),
        standards=(standard,),
    )

    assert result["score"] == (
        baseline["score"] + expected_delta
    )


@pytest.mark.parametrize(
    "status,recommended,expected_delta",
    [
        ("supported", False, 5),
        ("supported", True, 12),
        ("conditional", False, -5),
        ("unsupported", False, -25),
    ],
)
def test_scoring_factor_protocol_applicability_is_sensitive(
    status,
    recommended,
    expected_delta,
):
    artifact = {
        **_scoring_artifact(),
        "protocol": "TLS",
        "protocol_version": "1.3",
    }

    baseline = _score(
        _scoring_candidate(),
        artifact=artifact,
    )

    protocol = SimpleNamespace(
        algorithm="X25519MLKEM768",
        protocol="TLS",
        protocol_version="1.3",
        status=status,
        recommended=recommended,
    )

    result = _score(
        _scoring_candidate(),
        artifact=artifact,
        protocols=(protocol,),
    )

    assert result["score"] == (
        baseline["score"] + expected_delta
    )


def test_scoring_factor_constraint_burden_is_sensitive():
    clear = _score(
        _scoring_candidate(
            prerequisites=[],
            constraints=[],
        )
    )

    small = _score(
        _scoring_candidate(
            prerequisites=["runtime"],
            constraints=[],
        )
    )

    large = _score(
        _scoring_candidate(
            prerequisites=["runtime", "provider"],
            constraints=["interop", "deployment"],
        )
    )

    assert clear["score"] > small["score"]
    assert small["score"] > large["score"]

    assert clear["score"] - small["score"] == 7


def test_score_is_clamped_and_decision_is_classified():
    result = _score(
        _scoring_candidate(
            relationship_type="replaces",
            hybrid=True,
            confidence="high",
        )
    )

    assert 0 <= result["score"] <= 100

    assert result["decision"] in {
        "preferred",
        "alternative",
        "conditional",
        "weak",
    }


def test_ranking_order_is_exactly_score_descending():
    candidates = [
        _scoring_candidate(
            relationship_id="candidate-b",
            confidence="medium",
        ),
        _scoring_candidate(
            relationship_id="candidate-a",
            confidence="high",
        ),
        _scoring_candidate(
            relationship_id="candidate-c",
            confidence="low",
        ),
    ]

    ranked = rank_candidates(
        candidates,
        artifact=_scoring_artifact(),
    )

    scores = [
        candidate["score"]
        for candidate in ranked
    ]

    assert scores == sorted(
        scores,
        reverse=True,
    )

    assert ranked[0]["relationship_id"] == "candidate-a"
    assert ranked[-1]["relationship_id"] == "candidate-c"


def test_ranking_tie_break_is_deterministic():
    candidates = [
        _scoring_candidate(
            relationship_id="z",
            target_algorithm="Z-ALGORITHM",
        ),
        _scoring_candidate(
            relationship_id="a",
            target_algorithm="A-ALGORITHM",
        ),
    ]

    first = rank_candidates(
        candidates,
        artifact=_scoring_artifact(),
    )

    second = rank_candidates(
        list(reversed(candidates)),
        artifact=_scoring_artifact(),
    )

    assert first == second

    assert [
        item["target_algorithm"]
        for item in first
    ] == [
        "A-ALGORITHM",
        "Z-ALGORITHM",
    ]


def test_explanation_reconciles_with_selected_candidate():
    artifact = {
        "algorithm": "ECDH",
        "purpose": "key_establishment",
        "protocol": "TLS",
        "protocol_version": "1.3",
    }

    result = build_recommendation(artifact)

    primary = result["primary_candidate"]
    selection = result["explainability"]["selection"]
    selected = result["candidates"][0]

    assert primary == {
        "relationship_id": selected["relationship_id"],
        "target_algorithm": selected["target_algorithm"],
        "score": selected["score"],
        "decision": selected["decision"],
    }

    assert selection["target_algorithm"] == (
        selected["target_algorithm"]
    )

    assert selection["relationship_id"] == (
        selected["relationship_id"]
    )

    assert selection["score"] == selected["score"]
    assert selection["decision"] == selected["decision"]
    assert selection["reasons"] == selected["reasons"]
    assert selection["penalties"] == selected["penalties"]


def test_explanation_contains_protocol_driver_for_tls_recommendation():
    artifact = {
        "algorithm": "ECDH",
        "purpose": "key_establishment",
        "protocol": "TLS",
        "protocol_version": "1.3",
    }

    result = build_recommendation(artifact)

    primary = result["primary_candidate"]
    selected = result["candidates"][0]
    selection = result["explainability"]["selection"]

    assert primary["target_algorithm"] == (
        "X25519MLKEM768"
    )

    assert any(
        "recommended" in reason.lower()
        for reason in selected["reasons"]
    )

    assert selection["target_algorithm"] == (
        selected["target_algorithm"]
    )

    assert selection["reasons"] == selected["reasons"]


def test_score_and_explanation_are_stable_across_repeated_runs():
    artifact = {
        "algorithm": "ECDH",
        "purpose": "key_establishment",
        "protocol": "TLS",
        "protocol_version": "1.3",
    }

    results = [
        build_recommendation(artifact)
        for _ in range(5)
    ]

    assert all(
        result == results[0]
        for result in results[1:]
    )
