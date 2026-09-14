from analysis.decision_engine import (
    build_action_vector,
    build_decision_record,
    build_intelligence_snapshot,
)


def artifact(**overrides):
    value = {
        "artifact_id": "artifact:payment:rsa",
        "application_id": "app:payment",
        "algorithm": {"name": "RSA-2048"},
        "evidence_ids": ["evidence:1"],
        "recommendation_ids": ["recommendation:1"],
        "migration_option_ids": ["migration:1"],
        "risk": {
            "security": {"level": "HIGH"},
            "quantum": {"level": "CRITICAL"},
        },
        "mosca": {"risk": "HIGH", "status": "AT_RISK"},
    }
    value.update(overrides)
    return value


def context(**overrides):
    value = {
        "business_context_id": "business:payment",
        "application_id": "app:payment",
        "operational_criticality": "CRITICAL",
        "financial_impact": "HIGH",
        "regulatory_exposure": "HIGH",
        "customer_impact": "HIGH",
        "confidence": "high",
    }
    value.update(overrides)
    return value


def migration():
    return {
        "option_id": "migration:1",
        "name": "ML-KEM hybrid",
        "target_algorithm": "X25519MLKEM768",
        "confidence": "high",
        "prerequisites": ["provider"],
        "constraints": ["interop"],
    }


def test_action_is_deterministic_and_migration_driven():
    first = build_intelligence_snapshot(
        artifact(), context(), [migration()]
    )
    second = build_intelligence_snapshot(
        artifact(), context(), [migration()]
    )

    assert first == second
    assert first.decision.decision == "ACTION"
    assert first.decision.decision_id == "decision:0.8:artifact:payment:rsa"
    assert first.action.action == "MIGRATE"
    assert first.action.target == "X25519MLKEM768"
    assert first.action.migration_option_id == "migration:1"
    assert first.action.verification_required is True
    assert first.action.prerequisites == ["provider"]
    assert first.action.blockers == ["interop"]


def test_review_does_not_invent_migration():
    result = build_decision_record(
        artifact(
            risk={
                "security": {"level": "LOW"},
                "quantum": {"level": "LOW"},
            },
            mosca={"risk": "LOW", "status": "OK"},
            migration_option_ids=[],
            recommendation_ids=[],
            evidence_ids=[],
        ),
        business_context={
            "application_id": "app:payment",
            "operational_criticality": "LOW",
            "financial_impact": "LOW",
            "regulatory_exposure": "LOW",
            "customer_impact": "LOW",
        },
        migration_options=[],
    )

    assert result.decision == "REVIEW"
    assert result.migration_option_ids == []


def test_prioritize_when_business_is_high():
    result = build_decision_record(
        artifact(
            risk={
                "security": {"level": "MEDIUM"},
                "quantum": {"level": "LOW"},
            },
            mosca={"risk": "LOW", "status": "OK"},
            migration_option_ids=[],
        ),
        context(
            operational_criticality="HIGH",
            financial_impact="MEDIUM",
            regulatory_exposure="MEDIUM",
            customer_impact="MEDIUM",
        ),
    )

    assert result.decision == "PRIORITIZE"
