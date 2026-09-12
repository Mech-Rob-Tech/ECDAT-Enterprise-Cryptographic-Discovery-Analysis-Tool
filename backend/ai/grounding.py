from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Set

from ai.schemas import (
    AIConfidence,
    AIContext,
    AIResponse,
)


class GroundingError(ValueError):
    """
    Raised when an AI response violates ECDAT's
    evidence-grounding contract.
    """


@dataclass(frozen=True)
class GroundingResult:
    """
    Result of validating AI evidence references.
    """

    allowed_reference_ids: Set[str]
    valid_reference_ids: List[str]
    invalid_reference_ids: List[str]

    @property
    def is_valid(self) -> bool:
        return not self.invalid_reference_ids


# Explicitly supported structural identity fields.
#
# We intentionally do not treat every string containing
# "id" as evidence. Only canonical ECDAT identity fields
# are trusted.
REFERENCE_ID_FIELDS = {
    "scan_id",
    "application_id",
    "component_id",
    "artifact_id",
    "evidence_id",
    "assessment_id",
    "recommendation_id",
    "option_id",
    "migration_option_id",
    "verification_id",
    "relationship_id",
    "knowledge_id",
    "standard_id",
    "compatibility_id",
    "applicability_id",
    "conflict_id",
    "source_id",
    "candidate_id",
    "subject_id",
    "replacement_artifact_id",
    "from_scan_id",
    "to_scan_id",
}


REFERENCE_ID_LIST_FIELDS = {
    "application_ids",
    "component_ids",
    "artifact_ids",
    "evidence_ids",
    "recommendation_ids",
    "migration_option_ids",
    "candidate_ids",
    "source_ids",
}


def _add_reference(
    references: Set[str],
    value: Any,
) -> None:
    """
    Add one valid string identity value.
    """

    if not isinstance(value, str):
        return

    normalized = value.strip()

    if normalized:
        references.add(normalized)


def _collect_from_mapping(
    value: Dict[str, Any],
    references: Set[str],
) -> None:
    """
    Recursively collect only explicitly recognized
    ECDAT identity fields.

    Free-form evidence text is never interpreted as
    an identity reference.
    """

    for key, item in value.items():
        if key in REFERENCE_ID_FIELDS:
            _add_reference(
                references,
                item,
            )

        elif key in REFERENCE_ID_LIST_FIELDS:
            if isinstance(item, (list, tuple, set)):
                for reference_id in item:
                    _add_reference(
                        references,
                        reference_id,
                    )

        if isinstance(item, dict):
            _collect_from_mapping(
                item,
                references,
            )

        elif isinstance(item, list):
            for child in item:
                if isinstance(child, dict):
                    _collect_from_mapping(
                        child,
                        references,
                    )


def _collect_from_items(
    items: Iterable[Dict[str, Any]],
    references: Set[str],
) -> None:
    for item in items:
        if isinstance(item, dict):
            _collect_from_mapping(
                item,
                references,
            )


def collect_allowed_reference_ids(
    context: AIContext,
) -> Set[str]:
    """
    Build the complete set of evidence identifiers that
    the AI is allowed to cite for one request.

    The returned identifiers originate from deterministic
    ECDAT context, not from model output.
    """

    references: Set[str] = set()

    _add_reference(
        references,
        context.scan_id,
    )

    _add_reference(
        references,
        context.artifact_id,
    )

    _collect_from_mapping(
        context.scan_summary,
        references,
    )

    _collect_from_mapping(
        context.artifact,
        references,
    )

    _collect_from_items(
        context.recommendations,
        references,
    )

    _collect_from_items(
        context.migration_options,
        references,
    )

    _collect_from_items(
        context.knowledge,
        references,
    )

    _collect_from_items(
        context.dependencies,
        references,
    )

    _collect_from_mapping(
        context.verification,
        references,
    )

    _collect_from_items(
        context.evidence,
        references,
    )

    _collect_from_mapping(
        context.metadata,
        references,
    )

    return references


def validate_evidence_references(
    response: AIResponse,
    context: AIContext,
) -> GroundingResult:
    """
    Validate every AI-provided evidence reference against
    the deterministic context supplied to the model.
    """

    allowed = collect_allowed_reference_ids(
        context
    )

    valid: List[str] = []
    invalid: List[str] = []

    for reference in response.evidence_refs:
        reference_id = reference.reference_id.strip()

        if reference_id in allowed:
            valid.append(reference_id)
        else:
            invalid.append(reference_id)

    return GroundingResult(
        allowed_reference_ids=allowed,
        valid_reference_ids=valid,
        invalid_reference_ids=invalid,
    )


def enforce_grounding(
    response: AIResponse,
    context: AIContext,
) -> AIResponse:
    """
    Enforce ECDAT's grounding contract.

    Rules:

    1. The AI may cite only references present in the
       deterministic context.

    2. A substantive answer must contain at least one
       valid evidence reference.

    3. An INSUFFICIENT response may contain no references,
       because the purpose of that response may be to
       explicitly report missing evidence.
    """

    result = validate_evidence_references(
        response=response,
        context=context,
    )

    if result.invalid_reference_ids:
        invalid = ", ".join(
            result.invalid_reference_ids
        )

        raise GroundingError(
            "AI response contains ungrounded "
            f"evidence references: {invalid}"
        )

    if (
        response.confidence
        != AIConfidence.INSUFFICIENT
        and not result.valid_reference_ids
    ):
        raise GroundingError(
            "AI response makes a substantive claim "
            "without citing deterministic ECDAT evidence."
        )

    return response