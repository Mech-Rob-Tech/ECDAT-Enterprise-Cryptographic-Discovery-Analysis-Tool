export type RiskLevel =
  | "CRITICAL"
  | "HIGH"
  | "MEDIUM"
  | "LOW";

export type ConfidenceLevel =
  | "high"
  | "medium"
  | "low";

export type DetectionMethod =
  | "api_invocation"
  | "protocol_configuration"
  | "configuration"
  | "algorithm_reference"
  | "pattern_match"
  | string;


/* =========================================================
   EXISTING / FLAT ARTIFACT CONTRACT
   ========================================================= */

export interface CryptoArtifact {
  artifact_id: string;

  algorithm: string;
  type: string;

  key_size: number | null;
  mode: string | null;
  curve: string | null;
  version: string | null;

  file: string;
  line: number;

  evidence: string;
  evidence_context: EvidenceContext[];

  detection_method: DetectionMethod;
  confidence: ConfidenceLevel;

  purpose: string;
  purpose_confidence: ConfidenceLevel;

  quantum_risk: RiskLevel;
  risk_reason: string;

  mosca_risk: RiskLevel | null;
  mosca_status: string | null;
  mosca_explanation: string | null;

  recommendation: string;
}

export type Artifact = CryptoArtifact;


/* =========================================================
   RISK
   ========================================================= */

export interface RiskSummary {
  critical: number;
  high: number;
  medium: number;
  low: number;
}

export interface MoscaInputs {
  data_lifetime: number;
  migration_time: number;
  quantum_horizon: number;
  business_criticality: string;
}


/* =========================================================
   CANONICAL MODEL
   ========================================================= */

export interface ScanMetadata {
  target: string;
  generated_at: string;
  prototype_scope: string;
}

export interface ScanSummary {
  total_files_scanned: number;
  total_artifacts: number;

  security_risk_summary: {
    CRITICAL: number;
    HIGH: number;
    MEDIUM: number;
    LOW: number;
  };

  quantum_relevant_assets: number;
}

export interface Application {
  application_id: string;
  name: string;
  path: string | null;
}

export interface Component {
  component_id: string;
  name: string;
  component_type: string;
  version: string | null;
  path?: string | null;
}

export interface Algorithm {
  name: string;
  family: string;
}

export interface Purpose {
  value: string;
  confidence: ConfidenceLevel;
}

export interface Detection {
  method: DetectionMethod;
  confidence: ConfidenceLevel;
}

export interface EvidenceContext {
  line: number;
  text: string;
}

export interface Evidence {
  evidence_id: string;
  file: string;
  line: number;
  text: string;
  context: EvidenceContext[];
}

export interface RiskAssessment {
  assessment_id: string;
  level: RiskLevel;
  reason: string;
}

export interface QuantumRisk {
  level: RiskLevel;
  reason: string;
}

export interface Risk {
  security: RiskAssessment;
  quantum: QuantumRisk;
}

export interface MoscaAssessment {
  assessment_id: string;
  risk: RiskLevel | null;
  status: string | null;
  explanation: string | null;
}

export interface Recommendation {
  recommendation_id: string;
  category:
    | "monitor"
    | "replace"
    | "migrate"
    | "inspect"
    | "manual_review"
    | string;
  priority: string;
  text: string;
  rationale: string;
}

export interface MigrationOption {
  option_id: string;
  name: string;
  rationale: string | null;
  compatibility: string | null;
  effort: string | null;
}

export interface VerificationState {
  verification_id?: string;
  status: string;
  verified_at: string | null;
  notes: string | null;
}

export interface Relationship {
  relationship_id: string;
  source_id: string;
  target_id: string;
  relationship_type: string;
  confidence?: ConfidenceLevel | string;
  evidence_ids?: string[];
}


/* =========================================================
   CANONICAL CRYPTOGRAPHIC ARTIFACT
   ========================================================= */

export interface CanonicalCryptoArtifact {
  artifact_id: string;

  algorithm:
    | Algorithm
    | string;

  artifact_type: string;

  purpose:
    | Purpose
    | string;

  detection: Detection;

  evidence: Evidence[];

  key_size: number | null;
  mode: string | null;
  curve: string | null;
  version: string | null;

  risk: Risk | null;

  mosca: MoscaAssessment | null;

  migration_options: MigrationOption[];

  recommendation_ids?: string[];

  verification: VerificationState | null;

  application_id: string | null;
  component_id: string | null;

  details?: Record<
    string,
    unknown
  >;
}


/* =========================================================
   SCAN RESULT
   ========================================================= */

export interface ScanResult {
  metadata: ScanMetadata;

  summary: ScanSummary;

  applications: Application[];

  components: Component[];

  canonical_artifacts: CanonicalCryptoArtifact[];

  evidence: Evidence[];

  relationships: Relationship[];

  risk_assessments: RiskAssessment[];

  mosca_assessments: MoscaAssessment[];

  recommendations?: Recommendation[];

  migration_options: MigrationOption[];

  verification:
    | VerificationState[]
    | VerificationState
    | null;

  target: string;

  generated_at: string;

  prototype_scope: string;

  total_files_scanned: number;

  total_artifacts: number;

  quantum_vulnerable_assets: number;

  risk_summary: RiskSummary;

  mosca_inputs: MoscaInputs;

  artifacts: CryptoArtifact[];

  repository?: string;
}
