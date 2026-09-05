from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from model.business_context import BusinessContext
from model.scan_state import ScanState

@dataclass
class ScanMetadata:
    target: str
    generated_at: str
    prototype_scope: str


@dataclass
class ScanSummary:
    total_files_scanned: int
    total_artifacts: int
    security_risk_summary: Dict[str, int]
    quantum_relevant_assets: int


@dataclass
class Application:
    application_id: str
    name: str
    path: str


@dataclass
class Component:
    component_id: str
    name: str
    component_type: str
    version: Optional[str] = None
    path: Optional[str] = None


@dataclass
class Algorithm:
    name: str
    family: Optional[str] = None


@dataclass
class Purpose:
    value: str
    confidence: str


@dataclass
class Detection:
    method: str
    confidence: str


@dataclass
class Evidence:
    evidence_id: str
    file: str
    line: int
    text: str
    context: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class RiskAssessment:
    assessment_id: str
    level: str
    reason: str


@dataclass
class QuantumRisk:
    level: str
    reason: str


@dataclass
class Risk:
    security: Optional[RiskAssessment] = None
    quantum: Optional[QuantumRisk] = None


@dataclass
class MoscaAssessment:
    assessment_id: str
    risk: str
    status: str
    explanation: str


@dataclass
class Recommendation:
    recommendation_id: str
    category: str
    priority: str
    text: str
    rationale: str
    knowledge_version: Optional[str] = None
    knowledge_hash: Optional[str] = None
    status: Optional[str] = None
    matched_by: Optional[str] = None
    lifecycle_status: Optional[str] = None
    quantum_posture: Optional[str] = None
    primitive: Optional[str] = None
    standards: List[str] = field(default_factory=list)
    candidate_ids: List[str] = field(default_factory=list)
    candidates: List[Dict[str, Any]] = field(default_factory=list)
    compatibility: Dict[str, Any] = field(default_factory=dict)
    conflict_count: int = 0
    explainability: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MigrationOption:
    option_id: str
    name: str
    rationale: str
    compatibility: str
    effort: str
    relationship_id: Optional[str] = None
    source_algorithm: Optional[str] = None
    target_algorithm: Optional[str] = None
    relationship_type: Optional[str] = None
    hybrid: bool = False
    confidence: Optional[str] = None
    prerequisites: List[str] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)
    knowledge_version: Optional[str] = None
    knowledge_hash: Optional[str] = None


@dataclass
class VerificationState:
    """
    Verification result for an artifact migration/remediation.

    Verification is an analytical state derived from comparing
    persisted scan states. It does not itself perform scanning.
    """

    verification_id: str
    status: str

    from_scan_id: Optional[str] = None
    to_scan_id: Optional[str] = None

    artifact_id: Optional[str] = None
    migration_option_id: Optional[str] = None

    risk_before: Optional[str] = None
    risk_after: Optional[str] = None

    mosca_before: Optional[str] = None
    mosca_after: Optional[str] = None

    remaining_exposure: List[str] = field(default_factory=list)
    evidence_ids: List[str] = field(default_factory=list)

    verified_at: Optional[str] = None
    notes: Optional[str] = None


@dataclass
class Relationship:
    relationship_id: str
    source_id: str
    target_id: str
    relationship_type: str
    confidence: str = "high"
    evidence_ids: List[str] = field(default_factory=list)


@dataclass
class CryptoArtifact:
    artifact_id: str
    algorithm: Algorithm
    artifact_type: str

    key_size: Optional[int] = None
    mode: Optional[str] = None
    curve: Optional[str] = None
    version: Optional[str] = None

    purpose: Optional[Purpose] = None
    detection: Optional[Detection] = None

    evidence_ids: List[str] = field(default_factory=list)

    risk: Optional[Risk] = None
    mosca: Optional[MoscaAssessment] = None

    recommendation_ids: List[str] = field(default_factory=list)
    migration_option_ids: List[str] = field(default_factory=list)

    verification_id: Optional[str] = None

    application_id: Optional[str] = None
    component_id: Optional[str] = None

    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class KnowledgeSnapshot:
    """
    Immutable knowledge context used to produce an ECDAT analysis.

    The version and integrity hash identify the exact knowledge
    registry state used by the analysis.
    """

    knowledge_version: str
    knowledge_hash: str
    generated_at: Optional[str] = None


@dataclass
class ECDATScan:
    metadata: ScanMetadata
    summary: ScanSummary

    knowledge_snapshot: Optional[KnowledgeSnapshot] = None

    applications: List[Application] = field(default_factory=list)
    components: List[Component] = field(default_factory=list)

    business_contexts: List[BusinessContext] = field(
        default_factory=list
    )

    scan_state: Optional[ScanState] = None
    artifacts: List[CryptoArtifact] = field(default_factory=list)
    evidence: List[Evidence] = field(default_factory=list)

    relationships: List[Relationship] = field(default_factory=list)

    risk_assessments: List[RiskAssessment] = field(default_factory=list)
    mosca_assessments: List[MoscaAssessment] = field(default_factory=list)

    recommendations: List[Recommendation] = field(default_factory=list)
    migration_options: List[MigrationOption] = field(default_factory=list)

    verification: List[VerificationState] = field(default_factory=list)
