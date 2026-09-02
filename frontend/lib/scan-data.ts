import "server-only";

import { readFile } from "node:fs/promises";
import path from "node:path";

import type { CryptoArtifact, RiskLevel, ScanResult } from "./types";

interface BackendArtifact {
  algorithm: string;
  type: string;
  key_size: number | null;
  mode: string | null;
  curve: string | null;
  version: string | null;
  file: string;
  line: number | null;
  evidence: string;
  quantum_risk: RiskLevel;
  risk_reason: string;
  mosca_risk: RiskLevel | null;
  mosca_status: string | null;
  mosca_explanation: string | null;
  recommendation: string;
}

interface BackendScanResult {
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
    algorithm: artifact.algorithm,
    type: artifact.type,
    key_size: artifact.key_size,
    file: artifact.file.replaceAll("\\", "/"),
    line: artifact.line,
    evidence: artifact.evidence,
    quantum_risk: artifact.quantum_risk,
    risk_reason: artifact.risk_reason,
    mosca_risk: artifact.mosca_risk,
    recommendation: artifact.recommendation,
  };
}

export async function getScanResult(): Promise<ScanResult> {
  const filePath = path.resolve(
    process.cwd(),
    "../backend/output/scan_results.json",
  );

  const raw = await readFile(filePath, "utf-8");

  const data: BackendScanResult = JSON.parse(raw);

  return {
    repository: data.target,
    generated_at: data.generated_at,
    prototype_scope: data.prototype_scope,

    files_scanned: data.total_files_scanned,
    total_artifacts: data.total_artifacts,
    quantum_vulnerable_assets:
      data.quantum_vulnerable_assets,

    risk_summary: data.risk_summary,

    mosca_inputs: data.mosca_inputs,

    artifacts: data.artifacts.map(normalizeArtifact),
  };
}
