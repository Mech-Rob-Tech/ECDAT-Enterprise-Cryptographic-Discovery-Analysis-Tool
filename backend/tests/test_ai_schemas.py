from ai.schemas import (
    AIAudience,
    AIConfidence,
    AIContext,
    AIQuery,
    AIResponse,
    EvidenceReference,
)


def test_ai_query_defaults():
    query = AIQuery(
        question="Why is this artifact high risk?"
    )

    assert query.question == (
        "Why is this artifact high risk?"
    )

    assert query.audience == AIAudience.GENERAL
    assert query.scan_id is None
    assert query.artifact_id is None


def test_ai_context_defaults_are_empty():
    context = AIContext()

    assert context.scan_summary == {}
    assert context.artifact == {}
    assert context.recommendations == []
    assert context.knowledge == []
    assert context.evidence == []


def test_ai_response_serialization():
    reference = EvidenceReference(
        reference_id="artifact:rsa-001",
        reference_type="artifact",
        source="security/key_manager.py",
        description="RSA usage detected",
    )

    response = AIResponse(
        answer="RSA was detected in the application.",
        confidence=AIConfidence.HIGH,
        evidence_refs=[reference],
        assumptions=[],
        missing_context=[],
    )

    payload = response.to_dict()

    assert payload["answer"] == (
        "RSA was detected in the application."
    )

    assert payload["confidence"] == "high"

    assert payload["evidence_refs"][0][
        "reference_id"
    ] == "artifact:rsa-001"

    assert payload["advisory_only"] is True


def test_ai_response_is_always_advisory():
    response = AIResponse(
        answer="Test response",
        advisory_only=False,
    )

    payload = response.to_dict()

    assert payload["advisory_only"] is True