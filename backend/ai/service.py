from typing import Any, Dict, List

from ai.grounding import enforce_grounding
from ai.prompts import (
    AI_RESPONSE_JSON_SCHEMA,
    build_system_prompt,
    build_user_prompt,
)
from ai.providers.base import AIProvider
from ai.schemas import (
    AIConfidence,
    AIContext,
    AIQuery,
    AIResponse,
    EvidenceReference,
)


class AIResponseValidationError(ValueError):
    """
    Raised when provider output cannot be converted
    into a valid ECDAT AIResponse.
    """


def _parse_string_list(
    value: Any,
    *,
    field_name: str,
) -> List[str]:
    if not isinstance(value, list):
        raise AIResponseValidationError(
            f"{field_name} must be a list."
        )

    if not all(
        isinstance(item, str)
        for item in value
    ):
        raise AIResponseValidationError(
            f"{field_name} must contain only strings."
        )

    return list(value)


def _parse_evidence_refs(
    value: Any,
) -> List[EvidenceReference]:
    if not isinstance(value, list):
        raise AIResponseValidationError(
            "evidence_refs must be a list."
        )

    references: List[EvidenceReference] = []

    for item in value:
        if not isinstance(item, dict):
            raise AIResponseValidationError(
                "Each evidence reference must "
                "be an object."
            )

        reference_id = str(
            item.get(
                "reference_id",
                "",
            )
        ).strip()

        reference_type = str(
            item.get(
                "reference_type",
                "",
            )
        ).strip()

        if not reference_id:
            raise AIResponseValidationError(
                "Evidence reference is missing "
                "reference_id."
            )

        if not reference_type:
            raise AIResponseValidationError(
                "Evidence reference is missing "
                "reference_type."
            )

        references.append(
            EvidenceReference(
                reference_id=reference_id,
                reference_type=reference_type,
                source=item.get("source"),
                description=item.get(
                    "description"
                ),
            )
        )

    return references


def parse_ai_response(
    payload: Dict[str, Any],
) -> AIResponse:
    """
    Convert untrusted provider JSON into ECDAT's
    strongly defined AIResponse contract.
    """

    if not isinstance(payload, dict):
        raise AIResponseValidationError(
            "AI provider response must be an object."
        )

    answer = payload.get("answer")

    if (
        not isinstance(answer, str)
        or not answer.strip()
    ):
        raise AIResponseValidationError(
            "AI response answer must be "
            "a non-empty string."
        )

    try:
        confidence = AIConfidence(
            str(
                payload.get(
                    "confidence",
                    "",
                )
            )
            .strip()
            .lower()
        )

    except ValueError as exc:
        raise AIResponseValidationError(
            "AI response contains an invalid "
            "confidence value."
        ) from exc

    if payload.get("advisory_only") is not True:
        raise AIResponseValidationError(
            "AI response must remain advisory_only."
        )

    evidence_refs = _parse_evidence_refs(
        payload.get(
            "evidence_refs",
            [],
        )
    )

    assumptions = _parse_string_list(
        payload.get(
            "assumptions",
            [],
        ),
        field_name="assumptions",
    )

    missing_context = _parse_string_list(
        payload.get(
            "missing_context",
            [],
        ),
        field_name="missing_context",
    )

    return AIResponse(
        answer=answer.strip(),
        confidence=confidence,
        evidence_refs=evidence_refs,
        assumptions=assumptions,
        missing_context=missing_context,
        advisory_only=True,
    )


class AIService:
    """
    Provider-independent orchestration layer for
    ECDAT AI Intelligence.

    Flow:

    ECDAT context
        -> prompt contract
        -> AI provider
        -> response validation
        -> evidence grounding
        -> accepted AIResponse
    """

    def __init__(
        self,
        *,
        provider: AIProvider,
    ) -> None:
        self.provider = provider

    def execute(
        self,
        *,
        query: AIQuery,
        context: AIContext,
        operation: str = "query",
    ) -> AIResponse:
        system_prompt = build_system_prompt()

        user_prompt = build_user_prompt(
            query=query,
            context=context,
            operation=operation,
        )

        payload = (
            self.provider.generate_structured(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                response_schema=(
                    AI_RESPONSE_JSON_SCHEMA
                ),
            )
        )

        response = parse_ai_response(
            payload
        )

        return enforce_grounding(
            response=response,
            context=context,
        )