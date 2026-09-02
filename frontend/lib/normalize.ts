import type {
  Artifact,
  RiskLevel,
  ScanResult,
} from "./types";

export function normalizePath(path: string): string {
  return path.replaceAll("\\", "/");
}

export function getRiskClass(risk: RiskLevel): string {
  switch (risk) {
    case "CRITICAL":
      return "risk-critical";

    case "HIGH":
      return "risk-high";

    case "MEDIUM":
      return "risk-medium";

    case "LOW":
      return "risk-low";

    default:
      return "";
  }
}

export function getArtifactLocation(
  artifact: Artifact
): string {
  return `${normalizePath(artifact.file)}:${artifact.line}`;
}

export function getMoscaTotal(
  result: ScanResult
): number {
  return (
    result.mosca_inputs.data_lifetime +
    result.mosca_inputs.migration_time
  );
}

export function isMoscaAtRisk(
  result: ScanResult
): boolean {
  return (
    getMoscaTotal(result) >
    result.mosca_inputs.quantum_horizon
  );
}

export function getRiskCount(
  result: ScanResult,
  risk: RiskLevel
): number {
  return result.risk_summary[risk.toLowerCase() as keyof typeof result.risk_summary];
}
