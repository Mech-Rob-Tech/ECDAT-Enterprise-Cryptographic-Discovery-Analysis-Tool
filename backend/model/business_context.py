from dataclasses import dataclass, field
from typing import List, Optional


BUSINESS_LEVELS = (
    "LOW",
    "MEDIUM",
    "HIGH",
    "CRITICAL",
)

CONTEXT_SOURCES = (
    "declared",
    "imported",
    "inferred",
    "unresolved",
)


@dataclass
class BusinessContext:
    """
    Canonical business context attached to an application.

    Business context describes why cryptographic exposure
    matters to the organization. It is deliberately kept
    separate from cryptographic risk assessments.
    """

    context_id: str
    application_id: str

    business_unit: Optional[str] = None
    owner: Optional[str] = None
    service: Optional[str] = None

    data_classification: Optional[str] = None
    data_lifetime_years: Optional[int] = None

    operational_criticality: str = "MEDIUM"
    financial_impact: str = "MEDIUM"
    regulatory_exposure: str = "MEDIUM"
    customer_impact: str = "MEDIUM"

    risk_appetite: Optional[str] = None

    source: str = "unresolved"
    confidence: str = "low"

    evidence_ids: List[str] = field(
        default_factory=list
    )
