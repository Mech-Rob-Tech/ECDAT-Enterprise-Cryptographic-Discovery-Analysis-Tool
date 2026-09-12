from typing import Any, Dict, List, Optional

from ai.schemas import AIContext
from model.scan_state_builder import build_scan_state


class AIContextError(ValueError):
    """
    Raised when deterministic ECDAT data cannot
    produce the requested AI context.
    """


def _list_of_dicts(
    report: Dict[str, Any],
    key: str,
) -> List[Dict[str, Any]]:
    value = report.get(key, []) or []

    return [
        dict(item)
        for item in value
        if isinstance(item, dict)
    ]


def _collect_ids(
    artifacts: List[Dict[str, Any]],
    field: str,
) -> set[str]:
    result: set[str] = set()

    for artifact in artifacts:
        values = artifact.get(field, []) or []

        if isinstance(values, (list, tuple, set)):
            for value in values:
                if value:
                    result.add(str(value))

    return result


def _filter_by_ids(
    items: List[Dict[str, Any]],
    field: str,
    allowed_ids: set[str],
) -> List[Dict[str, Any]]:
    if not allowed_ids:
        return []

    return [
        dict(item)
        for item in items
        if str(item.get(field, "")) in allowed_ids
    ]


def _prepare_evidence(
    item: Dict[str, Any],
    *,
    include_text: bool,
    max_text_chars: int,
) -> Dict[str, Any]:
    """
    Build cloud-safe evidence context.

    Raw source evidence is omitted by default.

    If explicitly enabled, evidence text is marked as
    untrusted data. It must never be interpreted as
    instructions to the AI model.
    """

    prepared: Dict[str, Any] = {
        "evidence_id": item.get("evidence_id"),
        "file": item.get("file"),
        "line": item.get("line"),
    }

    if include_text:
        text = str(item.get("text", ""))

        # Remove NUL characters and bound cloud payload size.
        text = text.replace("\x00", "")

        if max_text_chars >= 0:
            text = text[:max_text_chars]

        prepared["text"] = text
        prepared["trust"] = "untrusted_observation"
        prepared["instructions_allowed"] = False
    else:
        prepared["text_omitted"] = True

    return prepared


def build_ai_context(
    report: Dict[str, Any],
    *,
    artifact_id: Optional[str] = None,
    scan_id: Optional[str] = None,
    include_evidence_text: bool = False,
    max_artifacts: int = 50,
    max_evidence: int = 100,
    max_relationships: int = 100,
    max_business_contexts: int = 50,
    max_evidence_text_chars: int = 500,
) -> AIContext:
    """
    Convert an ECDAT canonical report into bounded,
    structured context for the AI intelligence layer.

    Security principles:

    - deterministic ECDAT results remain authoritative
    - raw source evidence is excluded by default
    - evidence text is treated as untrusted data
    - context size is bounded
    - related records are selected deterministically
    """

    if not isinstance(report, dict):
        raise AIContextError(
            "ECDAT report must be a dictionary."
        )

    if max_artifacts <= 0:
        raise AIContextError(
            "max_artifacts must be greater than zero."
        )

    artifacts = _list_of_dicts(
        report,
        "canonical_artifacts",
    )

    all_artifact_count = len(artifacts)

    selected_artifact: Dict[str, Any] = {}

    if artifact_id:
        for artifact in artifacts:
            if (
                str(artifact.get("artifact_id"))
                == str(artifact_id)
            ):
                selected_artifact = dict(artifact)
                break

        if not selected_artifact:
            raise AIContextError(
                "Requested artifact was not found in "
                f"ECDAT report: {artifact_id}"
            )

        selected_artifacts = [
            selected_artifact
        ]

    else:
        selected_artifacts = artifacts[
            :max_artifacts
        ]

    # Determine the authoritative scan identity using
    # ECDAT's existing deterministic scan-state builder.
    resolved_scan_id = scan_id

    if not resolved_scan_id:
        resolved_scan_id = build_scan_state(
            report
        ).scan_id

    evidence_ids = _collect_ids(
        selected_artifacts,
        "evidence_ids",
    )

    recommendation_ids = _collect_ids(
        selected_artifacts,
        "recommendation_ids",
    )

    migration_option_ids = _collect_ids(
        selected_artifacts,
        "migration_option_ids",
    )

    all_evidence = _list_of_dicts(
        report,
        "evidence",
    )

    evidence = [
        item
        for item in all_evidence
        if str(item.get("evidence_id"))
        in evidence_ids
    ][:max_evidence]

    prepared_evidence = [
        _prepare_evidence(
            item,
            include_text=include_evidence_text,
            max_text_chars=(
                max_evidence_text_chars
            ),
        )
        for item in evidence
    ]

    recommendations = _filter_by_ids(
        _list_of_dicts(
            report,
            "recommendations",
        ),
        "recommendation_id",
        recommendation_ids,
    )

    migration_options = _filter_by_ids(
        _list_of_dicts(
            report,
            "migration_options",
        ),
        "option_id",
        migration_option_ids,
    )

    relationships = _list_of_dicts(
        report,
        "relationships",
    )

    business_contexts = _list_of_dicts(
        report,
        "business_contexts",
    )

    if artifact_id:
        related_ids = {
            str(artifact_id),
        }

        application_id = selected_artifact.get(
            "application_id"
        )

        component_id = selected_artifact.get(
            "component_id"
        )

        if application_id:
            related_ids.add(
                str(application_id)
            )

        if component_id:
            related_ids.add(
                str(component_id)
            )

        relationships = [
            relationship
            for relationship in relationships
            if (
                str(
                    relationship.get(
                        "source_id",
                        "",
                    )
                )
                in related_ids
                or str(
                    relationship.get(
                        "target_id",
                        "",
                    )
                )
                in related_ids
            )
        ]

        if application_id:
            business_contexts = [
                context
                for context in business_contexts
                if str(
                    context.get(
                        "application_id",
                        "",
                    )
                )
                == str(application_id)
            ]
        else:
            business_contexts = []

    relationships = relationships[
        :max_relationships
    ]

    business_contexts = business_contexts[
        :max_business_contexts
    ]

    verification: Dict[str, Any] = {}

    if selected_artifact:
        verification_id = (
            selected_artifact.get(
                "verification_id"
            )
        )

        if verification_id:
            for state in _list_of_dicts(
                report,
                "verification",
            ):
                if (
                    str(
                        state.get(
                            "verification_id"
                        )
                    )
                    == str(verification_id)
                ):
                    verification = dict(state)
                    break

    metadata = dict(
        report.get("metadata", {}) or {}
    )

    metadata["knowledge_snapshot"] = dict(
        report.get(
            "knowledge_snapshot",
            {},
        )
        or {}
    )

    metadata["ai_context"] = {
        "raw_source_code_included": False,
        "evidence_text_included": (
            include_evidence_text
        ),
        "evidence_is_untrusted_data": True,
        "artifact_count_total": (
            all_artifact_count
        ),
        "artifact_count_in_context": (
            len(selected_artifacts)
        ),
        "artifact_context_truncated": (
            not artifact_id
            and all_artifact_count
            > len(selected_artifacts)
        ),
    }

    return AIContext(
        scan_id=str(resolved_scan_id),
        artifact_id=(
            str(artifact_id)
            if artifact_id
            else None
        ),
        scan_summary=dict(
            report.get(
                "summary",
                {},
            )
            or {}
        ),
        artifact=selected_artifact,
        artifacts=[
            dict(item)
            for item in selected_artifacts
        ],
        business_contexts=[
            dict(item)
            for item in business_contexts
        ],
        relationships=[
            dict(item)
            for item in relationships
        ],
        recommendations=recommendations,
        migration_options=migration_options,

        # Direct knowledge-record retrieval will be
        # connected through KnowledgeService later.
        knowledge=[],

        # v0.6 dependency intelligence remains a
        # separate deterministic integration point.
        dependencies=[],

        verification=verification,
        evidence=prepared_evidence,
        metadata=metadata,
    )