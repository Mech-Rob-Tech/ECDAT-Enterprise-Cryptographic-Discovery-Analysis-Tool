import pytest

from ai.grounding import (
    GroundingError,
    collect_allowed_reference_ids,
    enforce_grounding,
    validate_evidence_references,
)

from ai.schemas import (
    AIConfidence,
    AIContext,
    AIResponse,
    EvidenceReference,
)


def build_test_context() -> AIContext:
    return AIContext(
        scan_id="scan:test-001",
        artifact_id="artifact:rsa-001",

        artifact={
            "artifact_id": "artifact:rsa-001",
            "evidence_ids": [
                "evidence:rsa-001",
            ],
            "recommendation_ids": [
                "recommendation:rsa-001",
            ],
            "migration_option_ids": [
                "migration:ml-kem-001",
            ],
        },

        evidence=[
            {
                "evidence_id": "evidence:rsa-001",
                "file": "security/key_manager.py",
                "line": 42,
                "text": "RSA.generate(2048)",
            }
        ],

        recommendations=[
            {
                "recommendation_id":
                    "recommendation:rsa-001",

                "candidate_ids": [
                    "knowledge:ml-kem",
                ],
            }
        ],

        migration_options=[
            {
                "option_id":
                    "migration:ml-kem-001",

                "relationship_id":
                    "relationship:rsa-ml-kem",
            }
        ],

        knowledge=[
            {
                "knowledge_id":
                    "knowledge:ml-kem",

                "source_ids": [
                    "source:fips-203",
                ],
            }
        ],

        verification={
            "verification_id":
                "verification:test-001",

            "evidence_ids": [
                "evidence:rsa-001",
            ],
        },
    )


def test_collect_allowed_reference_ids():
    context = build_test_context()

    allowed = collect_allowed_reference_ids(
        context
    )

    assert "scan:test-001" in allowed
    assert "artifact:rsa-001" in allowed
    assert "evidence:rsa-001" in allowed

    assert (
        "recommendation:rsa-001"
        in allowed
    )

    assert (
        "migration:ml-kem-001"
        in allowed
    )

    assert "knowledge:ml-kem" in allowed

    assert (
        "relationship:rsa-ml-kem"
        in allowed
    )

    assert "source:fips-203" in allowed

    assert (
        "verification:test-001"
        in allowed
    )


def test_valid_ai_reference_is_accepted():
    context = build_test_context()

    response = AIResponse(
        answer=(
            "RSA usage was observed in the "
            "application."
        ),
        confidence=AIConfidence.HIGH,
        evidence_refs=[
            EvidenceReference(
                reference_id="artifact:rsa-001",
                reference_type="artifact",
            ),
            EvidenceReference(
                reference_id="evidence:rsa-001",
                reference_type="evidence",
            ),
        ],
    )

    result = validate_evidence_references(
        response=response,
        context=context,
    )

    assert result.is_valid is True
    assert result.invalid_reference_ids == []


def test_hallucinated_reference_is_rejected():
    context = build_test_context()

    response = AIResponse(
        answer="A fictional artifact exists.",
        confidence=AIConfidence.HIGH,
        evidence_refs=[
            EvidenceReference(
                reference_id=(
                    "artifact:"
                    "hallucinated-69420"
                ),
                reference_type="artifact",
            )
        ],
    )

    result = validate_evidence_references(
        response=response,
        context=context,
    )

    assert result.is_valid is False

    assert (
        "artifact:hallucinated-69420"
        in result.invalid_reference_ids
    )


def test_enforce_grounding_rejects_fake_reference():
    context = build_test_context()

    response = AIResponse(
        answer="Unsupported claim.",
        confidence=AIConfidence.HIGH,
        evidence_refs=[
            EvidenceReference(
                reference_id="standard:fake",
                reference_type="standard",
            )
        ],
    )

    with pytest.raises(GroundingError):
        enforce_grounding(
            response=response,
            context=context,
        )


def test_substantive_answer_requires_evidence():
    context = build_test_context()

    response = AIResponse(
        answer="RSA should be migrated.",
        confidence=AIConfidence.HIGH,
        evidence_refs=[],
    )

    with pytest.raises(GroundingError):
        enforce_grounding(
            response=response,
            context=context,
        )


def test_insufficient_answer_can_have_no_evidence():
    context = AIContext()

    response = AIResponse(
        answer=(
            "There is insufficient ECDAT evidence "
            "to answer this question."
        ),
        confidence=AIConfidence.INSUFFICIENT,
        evidence_refs=[],
        missing_context=[
            "cryptographic artifact evidence"
        ],
    )

    result = enforce_grounding(
        response=response,
        context=context,
    )

    assert (
        result.confidence
        == AIConfidence.INSUFFICIENT
    )