import "server-only";

import { readFile } from "node:fs/promises";
import path from "node:path";

import type {
  Application,
  CanonicalCryptoArtifact,
  Component,
  CryptoArtifact,
  Evidence,
  MigrationOption,
  MoscaAssessment,
  Recommendation,
  Relationship,
  RiskAssessment,
  ScanResult,
  VerificationState,
} from "./types";


interface BackendArtifact {
  artifact_id: string;
  algorithm: string;
  type: string;

  key_size: number | null;
  mode: string | null;
  curve: string | null;
  version: string | null;

  file: string;
  line: number | null;

  evidence: string;
  evidence_context?: {
    line: number;
    text: string;
  }[];

  detection_method?: string;
  confidence?: "high" | "medium" | "low";

  purpose?: string;
  purpose_confidence?: "high" | "medium" | "low";

  quantum_risk: "CRITICAL" | "HIGH" | "MEDIUM" | "LOW";
  risk_reason: string;

  mosca_risk:
    | "CRITICAL"
    | "HIGH"
    | "MEDIUM"
    | "LOW"
    | null;

  mosca_status: string | null;
  mosca_explanation: string | null;

  recommendation: string;
}


interface BackendCanonicalArtifact {
  artifact_id: string;

  algorithm: {
    name: string;
    family: string;
  };

  artifact_type: string;

  purpose: {
    value: string;
    confidence: "high" | "medium" | "low";
  };

  detection: {
    method: string;
    confidence: "high" | "medium" | "low";
  };

  evidence: {
    evidence_id: string;
    file: string;
    line: number;
    text: string;
    context: {
      line: number;
      text: string;
    }[];
  }[];

  key_size: number | null;
  mode: string | null;
  curve: string | null;
  version: string | null;

  risk: {
    security: {
      assessment_id: string;
      level:
        | "CRITICAL"
        | "HIGH"
        | "MEDIUM"
        | "LOW";
      reason: string;
    };

    quantum: {
      level:
        | "CRITICAL"
        | "HIGH"
        | "MEDIUM"
        | "LOW";
      reason: string;
    };
  } | null;

  mosca: {
    assessment_id: string;
    risk:
      | "CRITICAL"
      | "HIGH"
      | "MEDIUM"
      | "LOW"
      | null;
    status: string | null;
    explanation: string | null;
  } | null;

  recommendation_ids?: string[];

  migration_option_ids?: string[];

  verification_id?: string;

  migration_options?: MigrationOption[];

  verification?: VerificationState | null;

  application_id: string | null;
  component_id: string | null;

  details?: Record<string, unknown>;
}


interface BackendScanResult {
  metadata?: {
    target: string;
    generated_at: string;
    prototype_scope: string;
  };

  summary?: {
    total_files_scanned: number;
    total_artifacts: number;

    security_risk_summary: {
      CRITICAL: number;
      HIGH: number;
      MEDIUM: number;
      LOW: number;
    };

    quantum_relevant_assets: number;
  };

  applications?: Application[];

  components?: Component[];

  canonical_artifacts?: BackendCanonicalArtifact[];

  evidence?: Evidence[];

  relationships?: Relationship[];

  risk_assessments?: RiskAssessment[];

  mosca_assessments?: MoscaAssessment[];

  recommendations?: Recommendation[];

  migration_options?: MigrationOption[];

  verification?:
    | VerificationState[]
    | VerificationState
    | null;

  target: string;
  generated_at: string;
  prototype_scope: string;

  total_files_scanned: number;
  total_artifacts: number;
  quantum_vulnerable_assets: number;

  risk_summary: {
    critical: number;
    high: number;
    medium: number;
    low: number;
  };

  mosca_inputs: {
    data_lifetime: number;
    migration_time: number;
    quantum_horizon: number;
    business_criticality: string;
  };

  artifacts: BackendArtifact[];
}


function normalizeArtifact(
  artifact: BackendArtifact,
): CryptoArtifact {
  return {
    artifact_id: artifact.artifact_id,

    algorithm: artifact.algorithm,
    type: artifact.type,

    key_size: artifact.key_size,
    mode: artifact.mode,
    curve: artifact.curve,
    version: artifact.version,

    file: artifact.file.replaceAll("\\", "/"),
    line: artifact.line ?? 0,

    evidence: artifact.evidence,

    evidence_context:
      artifact.evidence_context ?? [],

    detection_method:
      artifact.detection_method ??
      "pattern_match",

    confidence:
      artifact.confidence ?? "low",

    purpose:
      artifact.purpose ?? "unknown",

    purpose_confidence:
      artifact.purpose_confidence ?? "low",

    quantum_risk:
      artifact.quantum_risk,

    risk_reason:
      artifact.risk_reason,

    mosca_risk:
      artifact.mosca_risk,

    mosca_status:
      artifact.mosca_status,

    mosca_explanation:
      artifact.mosca_explanation,

    recommendation:
      artifact.recommendation,
  };
}


function normalizeCanonicalArtifact(
  artifact: BackendCanonicalArtifact,
): CanonicalCryptoArtifact {
  return {
    artifact_id:
      artifact.artifact_id,

    algorithm: {
      name: artifact.algorithm.name,
      family: artifact.algorithm.family,
    },

    artifact_type:
      artifact.artifact_type,

    purpose: {
      value: artifact.purpose.value,
      confidence:
        artifact.purpose.confidence,
    },

    detection: {
      method:
        artifact.detection.method,
      confidence:
        artifact.detection.confidence,
    },

    evidence:
      (artifact.evidence ?? []).map(
        (item) => ({
          evidence_id:
            item.evidence_id,

          file:
            item.file.replaceAll(
              "\\",
              "/",
            ),

          line:
            item.line,

          text:
            item.text,

          context:
            item.context ?? [],
        }),
      ),

    key_size:
      artifact.key_size,

    mode:
      artifact.mode,

    curve:
      artifact.curve,

    version:
      artifact.version,

    risk: artifact.risk
      ? {
          security: {
            assessment_id:
              artifact.risk.security
                .assessment_id,

            level:
              artifact.risk.security
                .level,

            reason:
              artifact.risk.security
                .reason,
          },

          quantum: {
            level:
              artifact.risk.quantum
                .level,

            reason:
              artifact.risk.quantum
                .reason,
          },
        }
      : null,

    mosca: artifact.mosca
      ? {
          assessment_id:
            artifact.mosca
              .assessment_id,

          risk:
            artifact.mosca.risk,

          status:
            artifact.mosca.status,

          explanation:
            artifact.mosca.explanation,
        }
      : null,

    migration_options:
      artifact.migration_options ??
      [],

    recommendation_ids:
      artifact.recommendation_ids ??
      [],

    verification:
      artifact.verification
        ? {
            ...artifact.verification,
            verification_id:
              artifact.verification
                .verification_id ??
              artifact.verification_id,
          }
        : null,

    application_id:
      artifact.application_id,

    component_id:
      artifact.component_id,

    details:
      artifact.details ?? {},
  };
}


export async function getScanResult(): Promise<ScanResult> {
  const filePath = path.resolve(
    process.cwd(),
    "../backend/output/scan_results.json",
  );

  const raw = await readFile(
    filePath,
    "utf-8",
  );

  const data: BackendScanResult =
    JSON.parse(raw);


  const metadata =
    data.metadata ?? {
      target: data.target,
      generated_at:
        data.generated_at,
      prototype_scope:
        data.prototype_scope,
    };


  const summary =
    data.summary ?? {
      total_files_scanned:
        data.total_files_scanned,

      total_artifacts:
        data.total_artifacts,

      security_risk_summary: {
        CRITICAL:
          data.risk_summary.critical,

        HIGH:
          data.risk_summary.high,

        MEDIUM:
          data.risk_summary.medium,

        LOW:
          data.risk_summary.low,
      },

      quantum_relevant_assets:
        data.quantum_vulnerable_assets,
    };


  const canonicalArtifacts =
    (
      data.canonical_artifacts ??
      []
    ).map(
      normalizeCanonicalArtifact,
    );


  const artifacts =
    (data.artifacts ?? []).map(
      normalizeArtifact,
    );


  const applications =
    data.applications ?? [];


  const components =
    data.components ?? [];


  const evidence =
    data.evidence ?? [];


  const relationships =
    data.relationships ?? [];


  const riskAssessments =
    data.risk_assessments ?? [];


  const moscaAssessments =
    data.mosca_assessments ?? [];


  const recommendations =
    data.recommendations ?? [];


  const migrationOptions =
    data.migration_options ?? [];


  const verification = Array.isArray(
    data.verification,
  )
    ? data.verification
    : data.verification
      ? [data.verification]
      : [];


  return {
    metadata,
    summary,

    applications,
    components,

    canonical_artifacts:
      canonicalArtifacts,

    evidence,

    relationships,

    risk_assessments:
      riskAssessments,

    mosca_assessments:
      moscaAssessments,

    recommendations,

    migration_options:
      migrationOptions,

    verification,

    target:
      data.target,

    generated_at:
      data.generated_at,

    prototype_scope:
      data.prototype_scope,

    total_files_scanned:
      data.total_files_scanned,

    total_artifacts:
      data.total_artifacts,

    quantum_vulnerable_assets:
      data.quantum_vulnerable_assets,

    risk_summary: {
      critical:
        data.risk_summary.critical,

      high:
        data.risk_summary.high,

      medium:
        data.risk_summary.medium,

      low:
        data.risk_summary.low,
    },

    mosca_inputs:
      data.mosca_inputs,

    artifacts,

    repository:
      data.target,
  };
}
