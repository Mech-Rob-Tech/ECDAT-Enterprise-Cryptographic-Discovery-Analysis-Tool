"use client";

import { useEffect, useMemo, useState } from "react";
import { useSessionStorageValue } from "@/lib/session-storage";
import { useRouter } from "next/navigation";

type Artifact = {
  algorithm: string;
  type: string;
  key_size?: number | null;
  mode?: string | null;
  curve?: string | null;
  file: string;
  line: number;
  evidence: string;
  security_risk?: string | null;
  quantum_risk: string;
  risk_reason: string;
  recommendation: string;
  mosca_risk?: string | null;
  mosca_status?: string | null;
};

type ScanResult = {
  target: string;
  generated_at?: string;
  prototype_scope?: string;
  total_files_scanned: number;
  total_artifacts: number;
  quantum_vulnerable_assets: number;
  risk_summary: {
    critical: number;
    high: number;
    medium: number;
    low: number;
  };
  mosca_inputs?: {
    data_lifetime: number;
    migration_time: number;
    quantum_horizon: number;
    business_criticality: string;
  };
  artifacts: Artifact[];
};

function normalizeReportsScanResult(raw: unknown): ScanResult {
  if (!raw || typeof raw !== "object") {
    throw new Error("Invalid scan result");
  }

  const data = raw as Record<string, unknown>;
  const summary =
    data.summary && typeof data.summary === "object"
      ? (data.summary as Record<string, unknown>)
      : {};

  const risk =
    summary.security_risk_summary &&
    typeof summary.security_risk_summary === "object"
      ? (summary.security_risk_summary as Record<string, unknown>)
      : {};

  const legacyRisk =
    data.risk_summary &&
    typeof data.risk_summary === "object"
      ? (data.risk_summary as Record<string, unknown>)
      : {};

  const numberValue = (
    value: unknown,
    fallback = 0,
  ): number =>
    typeof value === "number" && Number.isFinite(value)
      ? value
      : fallback;

  const rawArtifacts =
    Array.isArray(data.artifacts)
      ? data.artifacts
      : [];

  const artifacts: Artifact[] = rawArtifacts
    .filter(
      (item): item is Record<string, unknown> =>
        Boolean(item) &&
        typeof item === "object",
    )
    .map((item) => {
      const risk =
        item.risk &&
        typeof item.risk === "object"
          ? (item.risk as Record<string, unknown>)
          : {};

      return {
        algorithm:
          typeof item.algorithm === "string"
            ? item.algorithm
            : "",
        type:
          typeof item.type === "string"
            ? item.type
            : "",
        key_size:
          typeof item.key_size === "number"
            ? item.key_size
            : null,
        mode:
          typeof item.mode === "string"
            ? item.mode
            : null,
        curve:
          typeof item.curve === "string"
            ? item.curve
            : null,
        file:
          typeof item.file === "string"
            ? item.file
            : "",
        line:
          typeof item.line === "number"
            ? item.line
            : 0,
        evidence:
          typeof item.evidence === "string"
            ? item.evidence
            : "",
        security_risk:
          typeof item.security_risk === "string"
            ? item.security_risk
            : typeof risk.security === "string"
              ? risk.security
              : null,
        quantum_risk:
          typeof item.quantum_risk === "string"
            ? item.quantum_risk
            : typeof risk.quantum === "string"
              ? risk.quantum
              : "LOW",
        risk_reason:
          typeof item.risk_reason === "string"
            ? item.risk_reason
            : "",
        recommendation:
          typeof item.recommendation === "string"
            ? item.recommendation
            : "",
        mosca_risk:
          typeof item.mosca_risk === "string"
            ? item.mosca_risk
            : null,
        mosca_status:
          typeof item.mosca_status === "string"
            ? item.mosca_status
            : null,
      };
    });

  return {
    target:
      typeof data.target === "string"
        ? data.target
        : "",

    generated_at:
      typeof data.generated_at === "string"
        ? data.generated_at
        : undefined,

    prototype_scope:
      typeof data.prototype_scope === "string"
        ? data.prototype_scope
        : undefined,

    total_files_scanned: numberValue(
      summary.total_files_scanned,
      numberValue(data.total_files_scanned),
    ),

    total_artifacts: numberValue(
      summary.total_artifacts,
      numberValue(data.total_artifacts),
    ),

    quantum_vulnerable_assets: numberValue(
      summary.quantum_relevant_assets,
      numberValue(data.quantum_vulnerable_assets),
    ),

    risk_summary: {
      critical: numberValue(
        risk.CRITICAL,
        numberValue(legacyRisk.critical),
      ),
      high: numberValue(
        risk.HIGH,
        numberValue(legacyRisk.high),
      ),
      medium: numberValue(
        risk.MEDIUM,
        numberValue(legacyRisk.medium),
      ),
      low: numberValue(
        risk.LOW,
        numberValue(legacyRisk.low),
      ),
    },

    mosca_inputs:
      data.mosca_inputs &&
      typeof data.mosca_inputs === "object"
        ? (data.mosca_inputs as ScanResult["mosca_inputs"])
        : undefined,

    artifacts,
  };
}
export default function ReportsPage() {
  const router = useRouter();
  const stored = useSessionStorageValue("ecdat_scan_result");

  const result = useMemo<ScanResult | null>(() => {
    if (!stored) {
      return null;
    }

    try {
      return normalizeReportsScanResult(JSON.parse(stored));
    } catch {
      return null;
    }
  }, [stored]);

  const [exporting, setExporting] =
    useState<"json" | "pdf" | null>(null);

  const [exportError, setExportError] =
    useState<string | null>(null);

  useEffect(() => {
    if (stored === null) {
      if (!sessionStorage.getItem("ecdat_scan_result")) {
        router.replace("/import");
      }
      return;
    }

    if (!result) {
      router.replace("/import");
    }
  }, [result, router, stored]);

  const stats = useMemo(() => {
    if (!result) {
      return {
        exposure: 0,
        criticalOrHigh: 0,
        lowRisk: 0,
        quantumPercent: 0,
        quantumRisk: {
          CRITICAL: 0,
          HIGH: 0,
          MEDIUM: 0,
          LOW: 0,
        },
      };
    }

    const criticalOrHigh =
      result.risk_summary.critical +
      result.risk_summary.high;

    const exposure =
      result.total_artifacts > 0
        ? Math.round(
            (criticalOrHigh /
              result.total_artifacts) *
              100
          )
        : 0;

    const quantumRisk = {
      CRITICAL: 0,
      HIGH: 0,
      MEDIUM: 0,
      LOW: 0,
    };

    for (const artifact of result.artifacts) {
      const risk = artifact.quantum_risk.toUpperCase();

      if (risk in quantumRisk) {
        quantumRisk[
          risk as keyof typeof quantumRisk
        ] += 1;
      }
    }

    const quantumExposed =
      quantumRisk.CRITICAL +
      quantumRisk.HIGH;

    const quantumPercent =
      result.total_artifacts > 0
        ? Math.round(
            (quantumExposed /
              result.total_artifacts) *
              100
          )
        : 0;

    return {
      exposure,
      criticalOrHigh,
      lowRisk:
        result.risk_summary.low,
      quantumPercent,
      quantumRisk,
    };
  }, [result]);

  async function exportReport(
    format: "json" | "pdf"
  ) {
    if (!result) return;

    setExporting(format);
    setExportError(null);

    try {
      const response = await fetch(
        `http://localhost:8000/export/${format}`,
        {
          method: "POST",
          headers: {
            "Content-Type":
              "application/json",
          },
          body: JSON.stringify(result),
        }
      );

      if (!response.ok) {
        const errorBody =
          await response.json().catch(
            () => null
          );

        throw new Error(
          errorBody?.detail ||
            errorBody?.error ||
            `Export failed: ${response.status}`
        );
      }

      const blob =
        await response.blob();

      const url =
        window.URL.createObjectURL(
          blob
        );

      const link =
        document.createElement("a");

      link.href = url;

      link.download =
        format === "pdf"
          ? "ecdat-assessment.pdf"
          : "ecdat-assessment.json";

      document.body.appendChild(link);

      link.click();

      link.remove();

      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error(
        "ECDAT export failed:",
        error
      );

      setExportError(
        error instanceof Error
          ? error.message
          : "Unable to export report."
      );
    } finally {
      setExporting(null);
    }
  }

  if (!result) {
    return (
      <main className="mx-auto max-w-[1220px] px-10 py-10">
        <p className="font-mono text-[10px] uppercase tracking-[0.22em] text-[var(--primary)]">
          Assess / Reports
        </p>

        <h1 className="mt-3 text-3xl font-semibold tracking-tight">
          Security assessment report
        </h1>

        <section className="mt-8 rounded-lg border border-[var(--border)] bg-[var(--card)] p-7">
          <p className="text-sm text-[var(--muted-foreground)]">
            No scan result is loaded.
            Run a repository scan from
            Import before generating the
            assessment report.
          </p>
        </section>
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-[1220px] px-10 py-10">
      <header className="mb-9">
        <div className="flex items-start justify-between gap-8">
          <div>
            <p className="font-mono text-[10px] uppercase tracking-[0.22em] text-[var(--primary)]">
              Assess / Reports
            </p>

            <h1 className="mt-3 text-3xl font-semibold tracking-tight">
              Security assessment report
            </h1>

            <p className="mt-3 max-w-3xl text-sm leading-6 text-[var(--muted-foreground)]">
              Executive view of the cryptographic
              exposure identified during the
              current source-code assessment.
            </p>
          </div>

          <div className="flex flex-col items-end gap-4">
            <div className="text-right">
              <p className="font-mono text-[11px] uppercase tracking-[0.18em] text-[var(--muted-foreground)]">
                Generated
              </p>

              <p className="mt-2 font-mono text-xs">
                {result.generated_at ||
                  "Current scan"}
              </p>
            </div>

            <div className="flex gap-2">
              <button
                type="button"
                onClick={() =>
                  exportReport("json")
                }
                disabled={
                  exporting !== null
                }
                className="rounded-md border border-[var(--border)] bg-[var(--card)] px-4 py-2 font-mono text-[9px] font-semibold uppercase tracking-[0.14em] text-[var(--foreground)] transition hover:border-[var(--primary)] disabled:cursor-not-allowed disabled:opacity-40"
              >
                {exporting === "json"
                  ? "Exporting..."
                  : "Export JSON"}
              </button>

              <button
                type="button"
                onClick={() =>
                  exportReport("pdf")
                }
                disabled={
                  exporting !== null
                }
                className="rounded-md bg-[var(--primary)] px-4 py-2 font-mono text-[9px] font-semibold uppercase tracking-[0.14em] text-[var(--primary-foreground)] transition hover:brightness-105 disabled:cursor-not-allowed disabled:opacity-40"
              >
                {exporting === "pdf"
                  ? "Generating..."
                  : "Export PDF"}
              </button>
            </div>
          </div>
        </div>

        {exportError && (
          <div className="mt-5 border border-[var(--danger)]/30 bg-[var(--danger)]/10 px-4 py-3">
            <p className="font-mono text-[9px] uppercase tracking-[0.14em] text-[var(--danger)]">
              Export error
            </p>

            <p className="mt-1 text-xs text-[var(--muted-foreground)]">
              {exportError}
            </p>
          </div>
        )}
      </header>

      <section className="rounded-lg border border-[var(--border)] bg-[var(--card)] p-7">
        <div className="grid gap-8 lg:grid-cols-[1fr_auto]">
          <div>
            <p className="font-mono text-[9px] uppercase tracking-[0.18em] text-[var(--primary)]">
              Executive snapshot
            </p>

            <h2 className="mt-3 max-w-3xl text-2xl font-medium leading-tight">
              The current scan identified{" "}
              <span className="text-[var(--primary)]">
                {result.total_artifacts}
              </span>{" "}
              cryptographic artifacts across{" "}
              <span className="text-[var(--primary)]">
                {result.total_files_scanned}
              </span>{" "}
              source files.
            </h2>

            <p className="mt-5 max-w-3xl text-sm leading-6 text-[var(--muted-foreground)]">
              {result.quantum_vulnerable_assets} discovered
              assets are currently identified as
              quantum-relevant by the analysis engine.
              Migration planning should prioritize
              vulnerable public-key mechanisms and
              findings with urgent migration timing.
            </p>
          </div>

          <div className="flex min-w-[180px] flex-col justify-center border-l border-[var(--border)] pl-7">
            <span className="font-mono text-[9px] uppercase tracking-[0.16em] text-[var(--muted-foreground)]">
              High / critical security exposure
            </span>

            <span className="mt-3 font-mono text-4xl">
              {stats.exposure}%
            </span>

            <span className="mt-2 text-xs text-[var(--muted-foreground)]">
              of discovered artifacts
            </span>
          </div>
        </div>
      </section>

      <section className="mt-5 grid gap-4 md:grid-cols-4">
        <ReportMetric
          label="Critical security"
          value={result.risk_summary.critical}
          detail="current exposure"
        />

        <ReportMetric
          label="High security"
          value={result.risk_summary.high}
          detail="current exposure"
        />

        <ReportMetric
          label="Quantum exposed"
          value={
            stats.quantumRisk.CRITICAL +
            stats.quantumRisk.HIGH
          }
          detail={`${stats.quantumPercent}% of findings`}
        />

        <ReportMetric
          label="Low security"
          value={stats.lowRisk}
          detail="monitor"
        />
      </section>

      <section className="mt-5 rounded-lg border border-[var(--border)] bg-[var(--card)]">
        <div className="border-b border-[var(--border)] px-6 py-5">
          <p className="font-mono text-[9px] uppercase tracking-[0.18em] text-[var(--primary)]">
            Security risk posture
          </p>

          <h2 className="mt-2 text-lg font-medium">
            Current security exposure by severity
          </h2>
        </div>

        <div className="p-6">
          <RiskBar
            label="Critical security"
            value={
              result.risk_summary.critical
            }
            total={
              result.total_artifacts
            }
            risk="CRITICAL"
          />

          <RiskBar
            label="High security"
            value={
              result.risk_summary.high
            }
            total={
              result.total_artifacts
            }
            risk="HIGH"
          />

          <RiskBar
            label="Medium security"
            value={
              result.risk_summary.medium
            }
            total={
              result.total_artifacts
            }
            risk="MEDIUM"
          />

          <RiskBar
            label="Low security"
            value={
              result.risk_summary.low
            }
            total={
              result.total_artifacts
            }
            risk="LOW"
          />
        </div>
      </section>

      <section className="mt-5 grid gap-5 lg:grid-cols-2">
        <PriorityPanel
          number="01"
          title="Immediate remediation"
          description="Address findings whose migration timing is critical under the Mosca assessment."
          items={result.artifacts
            .filter(
              (artifact) =>
                artifact.mosca_risk?.toUpperCase() ===
                "CRITICAL"
            )
            .map(
              (artifact) =>
                artifact.algorithm
            )}
        />

        <PriorityPanel
          number="02"
          title="Post-quantum migration"
          description="Plan replacement or hybrid migration for quantum-vulnerable public-key cryptography."
          items={result.artifacts
            .filter(
              (artifact) =>
                artifact.quantum_risk.toUpperCase() ===
                "HIGH"
            )
            .map(
              (artifact) =>
                artifact.algorithm
            )}
        />

        <PriorityPanel
          number="03"
          title="Protocol review"
          description="Review protocol-level dependencies where the final security posture depends on configuration."
          items={result.artifacts
            .filter(
              (artifact) =>
                artifact.type.toLowerCase() ===
                "protocol"
            )
            .map(
              (artifact) =>
                artifact.algorithm
            )}
        />

        <PriorityPanel
          number="04"
          title="Continued monitoring"
          description="Maintain appropriate security controls for algorithms with lower immediate quantum exposure."
          items={result.artifacts
            .filter(
              (artifact) =>
                artifact.quantum_risk.toUpperCase() ===
                "LOW"
            )
            .map(
              (artifact) =>
                artifact.algorithm
            )}
        />
      </section>

      {result.mosca_inputs && (
        <section className="mt-5 rounded-lg border border-[var(--border)] bg-[var(--card)]">
          <div className="border-b border-[var(--border)] px-6 py-5">
            <p className="font-mono text-[9px] uppercase tracking-[0.18em] text-[var(--primary)]">
              Mosca assessment
            </p>

            <h2 className="mt-2 text-lg font-medium">
              Migration urgency
            </h2>
          </div>

          <div className="grid gap-5 p-6 md:grid-cols-4">
            <MoscaMetric
              label="Data lifetime"
              value={`${result.mosca_inputs.data_lifetime} yrs`}
            />

            <MoscaMetric
              label="Migration time"
              value={`${result.mosca_inputs.migration_time} yrs`}
            />

            <MoscaMetric
              label="Threat horizon"
              value={`${result.mosca_inputs.quantum_horizon} yrs`}
            />

            <MoscaMetric
              label="Criticality"
              value={
                result.mosca_inputs.business_criticality
              }
            />
          </div>

          <div className="mx-6 mb-6 border-l-2 border-[var(--primary)] bg-[var(--accent)]/30 p-5">
            <p className="font-mono text-[9px] uppercase tracking-[0.16em] text-[var(--primary)]">
              Assessment
            </p>

            <p className="mt-3 text-sm leading-6">
              Data lifetime + migration time ={" "}
              <span className="font-mono">
                {result.mosca_inputs.data_lifetime +
                  result.mosca_inputs.migration_time}{" "}
                years
              </span>
              , compared with a{" "}
              <span className="font-mono">
                {result.mosca_inputs.quantum_horizon}-year
              </span>{" "}
              assumed quantum-threat horizon.
            </p>
          </div>
        </section>
      )}

      <section className="mt-5 rounded-lg border border-[var(--border)] bg-[var(--card)]">
        <div className="border-b border-[var(--border)] px-6 py-5">
          <p className="font-mono text-[9px] uppercase tracking-[0.18em] text-[var(--primary)]">
            Recommended actions
          </p>

          <h2 className="mt-2 text-lg font-medium">
            Next decisions
          </h2>
        </div>

        <div className="divide-y divide-[var(--border)]">
          <ActionRow
            number="01"
            title="Remove broken legacy algorithms"
            text="Replace security-sensitive MD5 or equivalent legacy mechanisms immediately."
          />

          <ActionRow
            number="02"
            title="Inventory public-key dependencies"
            text="Map RSA, ECDSA, and related mechanisms to their actual cryptographic purpose and protocol."
          />

          <ActionRow
            number="03"
            title="Define PQC migration candidates"
            text="Evaluate standards-approved post-quantum or hybrid mechanisms against application requirements."
          />

          <ActionRow
            number="04"
            title="Validate the migration path"
            text="Test interoperability, performance, operational impact, and deployment sequencing before production replacement."
          />
        </div>
      </section>

      <section className="mt-5 border border-[var(--border)] bg-[var(--accent)]/30 p-6">
        <div className="flex gap-4">
          <span className="mt-1 h-2 w-2 shrink-0 rounded-full bg-[var(--primary)]" />

          <div>
            <p className="font-mono text-[9px] uppercase tracking-[0.18em] text-[var(--primary)]">
              Assessment scope
            </p>

            <p className="mt-3 text-sm leading-6 text-[var(--muted-foreground)]">
              {result.prototype_scope ||
                "Source-code cryptographic discovery"}
              . This report reflects the findings returned by
              the current ECDAT analysis pipeline and should
              not be interpreted as a complete enterprise-wide
              cryptographic inventory.
            </p>
          </div>
        </div>
      </section>
    </main>
  );
}

function ReportMetric({
  label,
  value,
  detail,
}: {
  label: string;
  value: number;
  detail: string;
}) {
  return (
    <div className="rounded-lg border border-[var(--border)] bg-[var(--card)] p-5">
      <p className="font-mono text-[11px] uppercase tracking-[0.18em] text-[var(--muted-foreground)]">
        {label}
      </p>

      <div className="mt-4">
        <p className="font-mono text-3xl">
          {value}
        </p>

        <p className="mt-2 text-[10px] text-[var(--muted-foreground)]">
          {detail}
        </p>
      </div>
    </div>
  );
}

function RiskBar({
  label,
  value,
  total,
  risk,
}: {
  label: string;
  value: number;
  total: number;
  risk: string;
}) {
  const safeValue = Number(value);
  const safeTotal = Number(total);

  const percentage =
    Number.isFinite(safeValue) &&
    Number.isFinite(safeTotal) &&
    safeTotal > 0
      ? Math.min(100, Math.max(0, (safeValue / safeTotal) * 100))
      : 0;

  return (
    <div className="mb-6 last:mb-0">
      <div className="flex items-center justify-between">
        <span
          className={`font-mono text-[9px] uppercase tracking-[0.14em] ${riskText(
            risk
          )}`}
        >
          {label}
        </span>

        <span className="font-mono text-[10px]">
          {value}
        </span>
      </div>

      <div className="mt-3 h-1.5 overflow-hidden rounded-full bg-[var(--accent)]">
        <div
          className={`h-full ${riskBar(
            risk
          )}`}
          style={{
            width: `${percentage}%`,
          }}
        />
      </div>
    </div>
  );
}

function PriorityPanel({
  number,
  title,
  description,
  items,
}: {
  number: string;
  title: string;
  description: string;
  items: string[];
}) {
  const uniqueItems = [
    ...new Set(items),
  ];

  return (
    <div className="rounded-lg border border-[var(--border)] bg-[var(--card)] p-6">
      <div className="flex items-start gap-4">
        <span className="font-mono text-[10px] text-[var(--primary)]">
          {number}
        </span>

        <div className="flex-1">
          <h3 className="text-base font-medium">
            {title}
          </h3>

          <p className="mt-2 text-xs leading-5 text-[var(--muted-foreground)]">
            {description}
          </p>

          <div className="mt-5 flex flex-wrap gap-2">
            {uniqueItems.length > 0 ? (
              uniqueItems.map(
                (item) => (
                  <span
                    key={item}
                    className="border border-[var(--border)] px-2 py-1 font-mono text-[8px] uppercase tracking-[0.1em]"
                  >
                    {item}
                  </span>
                )
              )
            ) : (
              <span className="font-mono text-[9px] text-[var(--muted-foreground)]">
                NONE IDENTIFIED
              </span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function MoscaMetric({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <div className="border border-[var(--border)] p-5">
      <p className="font-mono text-[8px] uppercase tracking-[0.14em] text-[var(--muted-foreground)]">
        {label}
      </p>

      <p className="mt-3 font-mono text-xl">
        {value}
      </p>
    </div>
  );
}

function ActionRow({
  number,
  title,
  text,
}: {
  number: string;
  title: string;
  text: string;
}) {
  return (
    <div className="grid gap-4 px-6 py-5 md:grid-cols-[50px_260px_1fr]">
      <span className="font-mono text-[10px] text-[var(--primary)]">
        {number}
      </span>

      <p className="text-sm font-medium">
        {title}
      </p>

      <p className="text-xs leading-5 text-[var(--muted-foreground)]">
        {text}
      </p>
    </div>
  );
}

function riskText(risk: string) {
  switch (risk.toUpperCase()) {
    case "CRITICAL":
      return "text-red-400";

    case "HIGH":
      return "text-amber-400";

    case "MEDIUM":
      return "text-yellow-300";

    case "LOW":
      return "text-emerald-400";

    default:
      return "text-[var(--muted-foreground)]";
  }
}

function riskBar(risk: string) {
  switch (risk.toUpperCase()) {
    case "CRITICAL":
      return "bg-red-400";

    case "HIGH":
      return "bg-amber-400";

    case "MEDIUM":
      return "bg-yellow-300";

    case "LOW":
      return "bg-emerald-400";

    default:
      return "bg-[var(--muted-foreground)]";
  }
}
