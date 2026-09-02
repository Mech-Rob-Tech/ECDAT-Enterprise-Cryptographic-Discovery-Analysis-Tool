export type RiskLevel =
  | "CRITICAL"
  | "HIGH"
  | "MEDIUM"
  | "LOW";

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

export interface Artifact {
  algorithm: string;
  type: string;

  key_size: number | null;
  mode: string | null;
  curve: string | null;
  version: string | null;

  file: string;
  line: number;

  evidence: string;

  quantum_risk: RiskLevel;
  risk_reason: string;

  mosca_risk: RiskLevel | null;
  mosca_status: string | null;
  mosca_explanation: string | null;

  recommendation: string;
}

export interface ScanResult {
  target: string;
  generated_at: string;
  prototype_scope: string;

  total_files_scanned: number;
  total_artifacts: number;
  quantum_vulnerable_assets: number;

  risk_summary: RiskSummary;

  mosca_inputs: MoscaInputs;

  artifacts: Artifact[];
}
