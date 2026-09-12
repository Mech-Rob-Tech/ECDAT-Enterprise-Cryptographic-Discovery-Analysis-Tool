from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class AIConfidence(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INSUFFICIENT = "insufficient"


class AIAudience(str, Enum):
    SECURITY_ENGINEER = "security_engineer"
    DEVELOPER = "developer"
    CISO = "ciso"
    AUDITOR = "auditor"
    GENERAL = "general"


@dataclass
class EvidenceReference:
    """
    Reference to deterministic ECDAT evidence or knowledge
    used to support an AI statement.

    The AI must not invent these references.
    """

    reference_id: str
    reference_type: str
    source: Optional[str] = None
    description: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "reference_id": self.reference_id,
            "reference_type": self.reference_type,
            "source": self.source,
            "description": self.description,
        }


@dataclass
class AIContext:
    """
    Structured context supplied to the AI layer.

    This contains results already produced by deterministic
    ECDAT components. The AI interprets this information;
    it does not replace the underlying analysis.
    """

    scan_id: Optional[str] = None
    artifact_id: Optional[str] = None

    scan_summary: Dict[str, Any] = field(default_factory=dict)
    artifact: Dict[str, Any] = field(default_factory=dict)

    recommendations: List[Dict[str, Any]] = field(
        default_factory=list
    )

    migration_options: List[Dict[str, Any]] = field(
        default_factory=list
    )

    knowledge: List[Dict[str, Any]] = field(
        default_factory=list
    )

    dependencies: List[Dict[str, Any]] = field(
        default_factory=list
    )

    verification: Dict[str, Any] = field(
        default_factory=dict
    )

    evidence: List[Dict[str, Any]] = field(
        default_factory=list
    )

    metadata: Dict[str, Any] = field(
        default_factory=dict
    )


@dataclass
class AIQuery:
    """
    User request sent to the AI intelligence layer.
    """

    question: str

    scan_id: Optional[str] = None
    artifact_id: Optional[str] = None

    audience: AIAudience = AIAudience.GENERAL


@dataclass
class AIResponse:
    """
    Grounded AI response.

    Important:
    - answer is AI-generated interpretation
    - evidence_refs must refer to real ECDAT data
    - assumptions must be explicit
    - missing_context must be explicit
    - advisory_only must remain True
    """

    answer: str

    confidence: AIConfidence = AIConfidence.INSUFFICIENT

    evidence_refs: List[EvidenceReference] = field(
        default_factory=list
    )

    assumptions: List[str] = field(
        default_factory=list
    )

    missing_context: List[str] = field(
        default_factory=list
    )

    advisory_only: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "answer": self.answer,
            "confidence": self.confidence.value,
            "evidence_refs": [
                reference.to_dict()
                for reference in self.evidence_refs
            ],
            "assumptions": list(self.assumptions),
            "missing_context": list(
                self.missing_context
            ),
            "advisory_only": True,
        }