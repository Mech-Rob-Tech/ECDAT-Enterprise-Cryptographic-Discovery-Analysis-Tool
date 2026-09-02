"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { getScanResult } from "@/lib/api";
import type { ScanResult } from "@/lib/types";
import {
  getMoscaTotal,
  isMoscaAtRisk,
} from "@/lib/normalize";

export default function OverviewPage() {
  const router = useRouter();

  const [result, setResult] = useState<ScanResult | null>(null);
  const [error, setError] = useState<string | null>(null);

useEffect(() => {
  getScanResult()
    .then(setResult)
    .catch((err) => {
      const message =
        err instanceof Error
          ? err.message
          : "Unable to load scan results.";

      if (message.includes("No scan result")) {
        router.replace("/import");
        return;
      }

      setError(message);
    });
}, [router]);

  if (error) {
    return (
      <main className="mx-auto max-w-[1220px] px-10 py-10">
        <div className="rounded-lg border border-[var(--border)] bg-[var(--card)] p-6">
          <p className="font-mono text-[10px] uppercase tracking-[0.18em] text-[var(--danger)]">
            Data error
          </p>

          <h1 className="mt-3 text-xl font-medium">
            Unable to load assessment
          </h1>

          <p className="mt-2 text-sm text-[var(--muted-foreground)]">
            {error}
          </p>
        </div>
      </main>
    );
  }

  if (!result) {
    return (
      <main className="mx-auto max-w-[1220px] px-10 py-10">
        <p className="font-mono text-xs text-[var(--muted-foreground)]">
          LOADING ASSESSMENT...
        </p>
      </main>
    );
  }

  const moscaTotal = getMoscaTotal(result);
  const moscaRisk = isMoscaAtRisk(result);

  return (
    <main className="mx-auto max-w-[1220px] px-10 py-10">
      {/* HEADER */}

      <header className="mb-9 flex items-start justify-between">
        <div>
          <p className="font-mono text-[10px] uppercase tracking-[0.22em] text-[var(--primary)]">
            Assess / Overview
          </p>

          <h1 className="mt-3 text-3xl font-semibold tracking-tight">
            Cryptographic posture
          </h1>

          <p className="mt-3 max-w-3xl text-sm leading-6 text-[var(--muted-foreground)]">
            Current cryptographic discovery and post-quantum
            migration assessment for the scanned target.
          </p>
        </div>

        <div className="text-right">
          <p className="font-mono text-[9px] uppercase tracking-[0.18em] text-[var(--muted-foreground)]">
            Target
          </p>

          <p className="mt-2 font-mono text-sm">
            {result.target}
          </p>
        </div>
      </header>

      {/* METRICS */}

      <section className="grid grid-cols-4 gap-4">
        <Metric
          label="Files scanned"
          value={result.total_files_scanned}
        />

        <Metric
          label="Crypto artifacts"
          value={result.total_artifacts}
        />

        <Metric
          label="Quantum vulnerable"
          value={result.quantum_vulnerable_assets}
        />

        <Metric
          label="Critical findings"
          value={result.risk_summary.critical}
        />
      </section>

      {/* RISK */}

      <section className="mt-5 rounded-lg border border-[var(--border)] bg-[var(--card)]">
        <div className="border-b border-[var(--border)] px-6 py-5">
          <p className="font-mono text-[10px] uppercase tracking-[0.18em] text-[var(--primary)]">
            Risk distribution
          </p>

          <h2 className="mt-2 text-lg font-medium">
            Cryptographic exposure
          </h2>
        </div>

        <div className="grid grid-cols-4 gap-px bg-[var(--border)]">
          <RiskMetric
            label="CRITICAL"
            value={result.risk_summary.critical}
          />

          <RiskMetric
            label="HIGH"
            value={result.risk_summary.high}
          />

          <RiskMetric
            label="MEDIUM"
            value={result.risk_summary.medium}
          />

          <RiskMetric
            label="LOW"
            value={result.risk_summary.low}
          />
        </div>
      </section>

      {/* MOSCA */}

      <section className="mt-5 rounded-lg border border-[var(--border)] bg-[var(--card)]">
        <div className="flex items-center justify-between border-b border-[var(--border)] px-6 py-5">
          <div>
            <p className="font-mono text-[10px] uppercase tracking-[0.18em] text-[var(--primary)]">
              Mosca assessment
            </p>

            <h2 className="mt-2 text-lg font-medium">
              Migration timing
            </h2>
          </div>

          <span
            className={`risk-badge ${
              moscaRisk
                ? "risk-critical"
                : "risk-low"
            }`}
          >
            {moscaRisk
              ? "AT_RISK"
              : "WITHIN_HORIZON"}
          </span>
        </div>

        <div className="grid grid-cols-4 gap-px bg-[var(--border)]">
          <MoscaMetric
            label="Data lifetime"
            value={`${result.mosca_inputs.data_lifetime} yrs`}
          />

          <MoscaMetric
            label="Migration time"
            value={`${result.mosca_inputs.migration_time} yrs`}
          />

          <MoscaMetric
            label="X + Y"
            value={`${moscaTotal} yrs`}
          />

          <MoscaMetric
            label="Quantum horizon"
            value={`${result.mosca_inputs.quantum_horizon} yrs`}
          />
        </div>
      </section>

      {/* RECENT FINDINGS */}

      <section className="mt-5 rounded-lg border border-[var(--border)] bg-[var(--card)]">
        <div className="border-b border-[var(--border)] px-6 py-5">
          <p className="font-mono text-[10px] uppercase tracking-[0.18em] text-[var(--primary)]">
            Findings
          </p>

          <h2 className="mt-2 text-lg font-medium">
            Highest-priority artifacts
          </h2>
        </div>

        <div>
          {result.artifacts
            .filter(
              (artifact) =>
                artifact.quantum_risk === "CRITICAL" ||
                artifact.quantum_risk === "HIGH"
            )
            .map((artifact) => (
              <div
		key={`${artifact.algorithm}-${artifact.file}-${artifact.line}-${artifact.evidence}`}
                className="grid grid-cols-[140px_1fr_120px] gap-5 border-b border-[var(--border)] px-6 py-5 last:border-0"
              >
                <div>
                  <p className="font-mono text-sm">
                    {artifact.algorithm}
                  </p>

                  <p className="mt-1 text-[10px] text-[var(--muted-foreground)]">
                    {artifact.type}
                  </p>
                </div>

                <div>
                  <p className="font-mono text-xs">
                    {artifact.file.replaceAll("\\", "/")}
                  </p>

                  <p className="mt-2 text-xs text-[var(--muted-foreground)]">
                    Line {artifact.line} · {artifact.evidence}
                  </p>
                </div>

                <div className="flex justify-end">
                  <span
                    className={`risk-badge risk-${artifact.quantum_risk.toLowerCase()}`}
                  >
                    {artifact.quantum_risk}
                  </span>
                </div>
              </div>
            ))}
        </div>
      </section>

      {/* FOOTER */}

      <div className="mt-5 flex justify-between font-mono text-[9px] uppercase tracking-[0.14em] text-[var(--muted-foreground)]">
        <span>
          Scope · {result.prototype_scope}
        </span>

        <span>
          Generated · {result.generated_at}
        </span>
      </div>
    </main>
  );
}

function Metric({
  label,
  value,
}: {
  label: string;
  value: number;
}) {
  return (
    <div className="rounded-lg border border-[var(--border)] bg-[var(--card)] p-5">
      <p className="font-mono text-[9px] uppercase tracking-[0.16em] text-[var(--muted-foreground)]">
        {label}
      </p>

      <p className="mt-3 font-mono text-2xl">
        {value}
      </p>
    </div>
  );
}

function RiskMetric({
  label,
  value,
}: {
  label: string;
  value: number;
}) {
  const className =
    label === "CRITICAL"
      ? "text-[var(--danger)]"
      : label === "HIGH"
        ? "text-[var(--warning)]"
        : label === "LOW"
          ? "text-[var(--success)]"
          : "text-[var(--foreground)]";

  return (
    <div className="bg-[var(--card)] p-5">
      <p className="font-mono text-[9px] tracking-[0.16em] text-[var(--muted-foreground)]">
        {label}
      </p>

      <p className={`mt-3 font-mono text-2xl ${className}`}>
        {value}
      </p>
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
    <div className="bg-[var(--card)] p-5">
      <p className="font-mono text-[9px] tracking-[0.16em] text-[var(--muted-foreground)]">
        {label}
      </p>

      <p className="mt-3 font-mono text-lg">
        {value}
      </p>
    </div>
  );
}
