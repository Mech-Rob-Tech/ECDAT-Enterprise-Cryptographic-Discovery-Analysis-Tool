"""
ECDAT Business Context Import

Normalizes externally supplied business-context records into a
stable intermediate representation.

This module deliberately does NOT construct canonical BusinessContext
objects. Canonical construction remains the responsibility of the
model layer.

Supported input:
    - dict
    - list[dict]

The importer is intentionally format-agnostic so that future sources
such as CSV, CMDB exports, APIs, spreadsheets, or JSON can feed the
same normalization boundary.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, List


BUSINESS_CONTEXT_FIELDS = (
    "application_id",
    "business_unit",
    "owner",
    "service",
    "data_classification",
    "data_lifetime_years",
    "operational_criticality",
    "financial_impact",
    "regulatory_exposure",
    "customer_impact",
    "risk_appetite",
    "source",
    "confidence",
    "evidence_ids",
)


def _clean_string(value: Any) -> str | None:
    if value is None:
        return None

    value = str(value).strip()

    return value if value else None


def _normalize_level(
    value: Any,
    default: str = "MEDIUM",
) -> str:
    if value is None:
        return default

    normalized = str(value).strip().upper()

    if normalized in {
        "LOW",
        "MEDIUM",
        "HIGH",
        "CRITICAL",
    }:
        return normalized

    return default


def _normalize_confidence(
    value: Any,
    default: str = "low",
) -> str:
    if value is None:
        return default

    normalized = str(value).strip().lower()

    if normalized in {
        "high",
        "medium",
        "low",
    }:
        return normalized

    return default


def _normalize_source(
    value: Any,
    default: str = "imported",
) -> str:
    if value is None:
        return default

    normalized = str(value).strip().lower()

    if normalized in {
        "declared",
        "imported",
        "inferred",
        "unresolved",
    }:
        return normalized

    return default


def _normalize_lifetime(value: Any) -> int | None:
    if value is None or value == "":
        return None

    try:
        lifetime = int(value)
    except (TypeError, ValueError):
        return None

    return lifetime if lifetime >= 0 else None


def _normalize_evidence_ids(value: Any) -> List[str]:
    if value is None:
        return []

    if isinstance(value, str):
        values: Iterable[Any] = value.split(",")
    elif isinstance(value, (list, tuple, set)):
        values = value
    else:
        return []

    result: List[str] = []

    for item in values:
        cleaned = _clean_string(item)

        if cleaned and cleaned not in result:
            result.append(cleaned)

    return result


def normalize_business_context(
    raw: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Normalize one raw business-context record.

    Unknown fields are ignored.

    Missing business consequence dimensions receive MEDIUM
    defaults because the canonical model currently requires
    concrete levels. Missing provenance defaults to imported/low
    rather than pretending the value was declared.
    """
    return {
        "application_id": _clean_string(
            raw.get("application_id")
        ),
        "business_unit": _clean_string(
            raw.get("business_unit")
        ),
        "owner": _clean_string(
            raw.get("owner")
        ),
        "service": _clean_string(
            raw.get("service")
        ),
        "data_classification": _clean_string(
            raw.get("data_classification")
        ),
        "data_lifetime_years": _normalize_lifetime(
            raw.get("data_lifetime_years")
        ),
        "operational_criticality": _normalize_level(
            raw.get("operational_criticality")
        ),
        "financial_impact": _normalize_level(
            raw.get("financial_impact")
        ),
        "regulatory_exposure": _normalize_level(
            raw.get("regulatory_exposure")
        ),
        "customer_impact": _normalize_level(
            raw.get("customer_impact")
        ),
        "risk_appetite": _clean_string(
            raw.get("risk_appetite")
        ),
        "source": _normalize_source(
            raw.get("source")
        ),
        "confidence": _normalize_confidence(
            raw.get("confidence")
        ),
        "evidence_ids": _normalize_evidence_ids(
            raw.get("evidence_ids")
        ),
    }


def import_business_contexts(
    raw_contexts: Any,
) -> List[Dict[str, Any]]:
    """
    Normalize one or more business-context records.

    Accepted forms:

        {
            "application_id": "app-001",
            ...
        }

    or:

        [
            {
                "application_id": "app-001",
                ...
            },
            ...
        ]

    Invalid records are skipped rather than converted into fake
    business context.
    """
    if raw_contexts is None:
        return []

    if isinstance(raw_contexts, dict):
        records = [raw_contexts]
    elif isinstance(raw_contexts, list):
        records = raw_contexts
    else:
        return []

    normalized: List[Dict[str, Any]] = []

    for record in records:
        if not isinstance(record, dict):
            continue

        context = normalize_business_context(record)

        if not context["application_id"]:
            continue

        normalized.append(context)

    return normalized
