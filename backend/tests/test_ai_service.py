import pytest

from ai.grounding import GroundingError
from ai.schemas import (
    AIConfidence,
    AIContext,
    AIQuery,
)
from ai.service import (
    AIResponseValidationError,
    AIService,
    parse_ai_response,
)


class FakeProvider:
    def __init__(self, payload):
        self.payload = payload
        self.calls = []

    def generate_structured(
        self,
        **kwargs,
    ):
        self.calls.append(kwargs)
        return self.payload


def valid_payload():
    return {
        "answer": (
            "RSA requires migration review."
        ),
        "confidence": "high",
        "evidence_refs": [
            {
                "reference_id": "artifact:rsa",
                "reference_type": "artifact",
                "source": None,
                "description": None,
            }
        ],
        "assumptions": [],
        "missing_context": [],
        "advisory_only": True,
    }


def test_parse_valid_response():
    response = parse_ai_response(
        valid_payload()
    )

    assert (
        response.confidence
        == AIConfidence.HIGH
    )

    assert response.advisory_only is True

    assert (
        response.evidence_refs[0]
        .reference_id
        == "artifact:rsa"
    )


def test_service_accepts_grounded_response():
    provider = FakeProvider(
        valid_payload()
    )

    service = AIService(
        provider=provider
    )

    context = AIContext(
        artifact_id="artifact:rsa",
        artifact={
            "artifact_id": "artifact:rsa",
        },
    )

    response = service.execute(
        query=AIQuery(
            question=(
                "Explain the RSA risk."
            )
        ),
        context=context,
        operation="explain",
    )

    assert (
        response.answer
        == "RSA requires migration review."
    )

    assert len(provider.calls) == 1


def test_service_rejects_hallucinated_reference():
    payload = valid_payload()

    payload["evidence_refs"][0][
        "reference_id"
    ] = "artifact:invented"

    service = AIService(
        provider=FakeProvider(
            payload
        )
    )

    context = AIContext(
        artifact_id="artifact:rsa",
    )

    with pytest.raises(
        GroundingError
    ):
        service.execute(
            query=AIQuery(
                question="Explain."
            ),
            context=context,
        )


def test_insufficient_response_can_have_no_refs():
    payload = {
        "answer": (
            "There is insufficient evidence."
        ),
        "confidence": "insufficient",
        "evidence_refs": [],
        "assumptions": [],
        "missing_context": [
            "protocol version",
        ],
        "advisory_only": True,
    }

    service = AIService(
        provider=FakeProvider(
            payload
        )
    )

    response = service.execute(
        query=AIQuery(
            question="Is this vulnerable?"
        ),
        context=AIContext(),
    )

    assert (
        response.confidence
        == AIConfidence.INSUFFICIENT
    )


def test_invalid_confidence_is_rejected():
    payload = valid_payload()

    payload["confidence"] = "super-certain"

    with pytest.raises(
        AIResponseValidationError
    ):
        parse_ai_response(payload)


def test_non_advisory_response_is_rejected():
    payload = valid_payload()

    payload["advisory_only"] = False

    with pytest.raises(
        AIResponseValidationError
    ):
        parse_ai_response(payload)


def test_empty_answer_is_rejected():
    payload = valid_payload()

    payload["answer"] = "   "

    with pytest.raises(
        AIResponseValidationError
    ):
        parse_ai_response(payload)


def test_invalid_assumptions_are_rejected():
    payload = valid_payload()

    payload["assumptions"] = [
        "valid",
        123,
    ]

    with pytest.raises(
        AIResponseValidationError
    ):
        parse_ai_response(payload)