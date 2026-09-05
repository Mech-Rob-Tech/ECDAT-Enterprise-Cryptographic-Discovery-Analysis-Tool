"""
ECDAT Business Context Resolution

Resolves imported business-context records against the applications
known to the canonical ECDAT scan.

Resolution is deliberately explicit:

    exact       -> application_id directly matches
    inferred    -> application matched using a supplied identifier
    unresolved  -> no reliable application match

The resolver does not invent business criticality.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class ContextResolution:
    """
    Result of resolving one business-context record.
    """

    application_id: Optional[str]
    source: str
    confidence: str
    context: Dict[str, Any]
    reason: str


def _application_lookup(
    applications: List[Any],
) -> Dict[str, Any]:
    lookup: Dict[str, Any] = {}

    for application in applications:
        application_id = getattr(
            application,
            "application_id",
            None,
        )

        if application_id:
            lookup[str(application_id)] = application

    return lookup


def resolve_business_context(
    context: Dict[str, Any],
    applications: List[Any],
) -> ContextResolution:
    """
    Resolve a normalized business-context record.

    Current authoritative resolution strategy:
        application_id exact match.

    We intentionally do NOT perform fuzzy matching yet. A false
    business-to-application mapping is worse than an unresolved
    context because it can distort risk prioritization.
    """
    lookup = _application_lookup(applications)

    requested_application_id = context.get(
        "application_id"
    )

    if requested_application_id:
        requested_application_id = str(
            requested_application_id
        ).strip()

    if (
        requested_application_id
        and requested_application_id in lookup
    ):
        resolved = dict(context)

        resolved["application_id"] = (
            requested_application_id
        )

        resolved["source"] = "declared"
        resolved["confidence"] = "high"

        return ContextResolution(
            application_id=requested_application_id,
            source="declared",
            confidence="high",
            context=resolved,
            reason="Exact application_id match.",
        )

    unresolved = dict(context)

    unresolved["source"] = "unresolved"
    unresolved["confidence"] = "low"

    return ContextResolution(
        application_id=None,
        source="unresolved",
        confidence="low",
        context=unresolved,
        reason=(
            "No reliable application match was found."
        ),
    )


def resolve_business_contexts(
    contexts: List[Dict[str, Any]],
    applications: List[Any],
) -> List[ContextResolution]:
    """
    Resolve a collection of imported business-context records.
    """
    return [
        resolve_business_context(
            context,
            applications,
        )
        for context in contexts
    ]
