"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";

type Artifact = {
  algorithm: string;
  type: string;
  key_size?: number | null;
  mode?: string | null;
  curve?: string | null;
  version?: string | null;
  file: string;
  line: number;
  evidence: string;
  quantum_risk: string;
  risk_reason: string;
  recommendation: string;
};

type ScanResult = {
  target: string;
  total_files_scanned: number;
  total_artifacts: number;
  quantum_vulnerable_assets: number;
  risk_summary: {
    critical: number;
    high: number;
    medium: number;
    low: number;
  };
  artifacts: Artifact[];
};

export default function InventoryPage() {
  const router = useRouter();
  const [result, setResult] = useState<ScanResult | null>(null);
  
useEffect(() => {
  const stored = sessionStorage.getItem("ecdat_scan_result");

  if (!stored) {
    router.replace("/import");
    return;
  }

  try {
    setResult(JSON.parse(stored));
  } catch {
    router.replace("/import");
  }
}, [router]);

  const artifacts = result?.artifacts ?? [];

  const algorithms = useMemo(() => {
    const map = new Map<
      string,
      {
        count: number;
        type: string;
        risks: Record<string, number>;
      }
    >();

    for (const artifact of artifacts) {
      const existing = map.get(artifact.algorithm);

      if (existing) {
        existing.count += 1;
        existing.risks[artifact.quantum_risk] =
          (existing.risks[artifact.quantum_risk] || 0) + 1;
      } else {
        map.set(artifact.algorithm, {
          count: 1,
          type: artifact.type,
          risks: {
            [artifact.quantum_risk]: 1,
          },
        });
      }
    }

    return Array.from(map.entries()).sort(
      (a, b) => b[1].count - a[1].count
    );
  }, [artifacts]);

  const files = useMemo(() => {
    const map = new Map<
      string,
      {
        count: number;
        risks: string[];
        algorithms: string[];
      }
    >();

    for (const artifact of artifacts) {
      const existing = map.get(artifact.file);

      if (existing) {
        existing.count += 1;

        if (!existing.risks.includes(artifact.quantum_risk)) {
          existing.risks.push(artifact.quantum_risk);
        }

        if (!existing.algorithms.includes(artifact.algorithm)) {
          existing.algorithms.push(artifact.algorithm);
        }
      } else {
        map.set(artifact.file, {
          count: 1,
          risks: [artifact.quantum_risk],
          algorithms: [artifact.algorithm],
        });
      }
    }

    return Array.from(map.entries()).sort(
      (a, b) => b[1].count - a[1].count
    );
  }, [artifacts]);

  const cryptoTypes = useMemo(() => {
    const counts: Record<string, number> = {};

    for (const artifact of artifacts) {
      counts[artifact.type] =
        (counts[artifact.type] || 0) + 1;
    }

    return Object.entries(counts).sort(
      (a, b) => b[1] - a[1]
    );
  }, [artifacts]);

  const uniqueAlgorithms = algorithms.length;
  const uniqueFiles = files.length;

  if (!result) {
    return (
      <main className="mx-auto max-w-[1220px] px-10 py-10">
        <p className="font-mono text-[10px] uppercase tracking-[0.22em] text-[var(--primary)]">
          Discover / Inventory
        </p>

        <h1 className="mt-3 text-3xl font-semibold tracking-tight">
          Cryptographic inventory
        </h1>

        <section className="mt-8 rounded-lg border border-[var(--border)] bg-[var(--card)] p-7">
          <p className="text-sm text-[var(--muted-foreground)]">
            No scan result is loaded. Run a repository scan from Import
            before viewing the cryptographic inventory.
          </p>
        </section>
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-[1220px] px-10 py-10">
      {/* HEADER */}

      <header className="mb-9">
        <div className="flex items-start justify-between gap-8">
          <div>
            <p className="font-mono text-[10px] uppercase tracking-[0.22em] text-[var(--primary)]">
              Discover / Inventory
            </p>

            <h1 className="mt-3 text-3xl font-semibold tracking-tight">
              Cryptographic inventory
            </h1>

            <p className="mt-3 max-w-3xl text-sm leading-6 text-[var(--muted-foreground)]">
              Portfolio-level visibility into the cryptographic technologies,
              source files, and risk categories discovered during the current
              repository scan.
            </p>
          </div>

          <div className="text-right">
            <p className="font-mono text-[9px] uppercase tracking-[0.18em] text-[var(--muted-foreground)]">
              Scan target
            </p>

            <p className="mt-2 max-w-[280px] break-all font-mono text-xs">
              {result.target}
            </p>
          </div>
        </div>
      </header>

      {/* SUMMARY */}

      <section className="grid gap-4 md:grid-cols-4">
        <Metric
          label="Algorithms"
          value={uniqueAlgorithms}
          detail="unique"
        />

        <Metric
          label="Artifacts"
          value={result.total_artifacts}
          detail="detected"
        />

        <Metric
          label="Source files"
          value={uniqueFiles}
          detail="with findings"
        />

        <Metric
          label="Quantum exposed"
          value={result.quantum_vulnerable_assets}
          detail="critical + high"
        />
      </section>

      {/* RISK DISTRIBUTION */}

      <section className="mt-5 rounded-lg border border-[var(--border)] bg-[var(--card)] p-6">
        <div className="flex items-end justify-between gap-6">
          <div>
            <p className="font-mono text-[9px] uppercase tracking-[0.18em] text-[var(--primary)]">
              Risk distribution
            </p>

            <h2 className="mt-2 text-lg font-medium">
              Current cryptographic exposure
            </h2>
          </div>

          <span className="font-mono text-[9px] uppercase tracking-[0.14em] text-[var(--muted-foreground)]">
            {result.total_artifacts} total
          </span>
        </div>

        <div className="mt-7 grid gap-4 md:grid-cols-4">
          <RiskCard
            label="Critical"
            value={result.risk_summary.critical}
            description="Immediate attention"
            risk="CRITICAL"
          />

          <RiskCard
            label="High"
            value={result.risk_summary.high}
            description="Migration priority"
            risk="HIGH"
          />

          <RiskCard
            label="Medium"
            value={result.risk_summary.medium}
            description="Planned review"
            risk="MEDIUM"
          />

          <RiskCard
            label="Low"
            value={result.risk_summary.low}
            description="Continue monitoring"
            risk="LOW"
          />
        </div>
      </section>

      {/* ALGORITHMS */}

      <section className="mt-5 grid gap-5 lg:grid-cols-[1.25fr_0.75fr]">
        <div className="rounded-lg border border-[var(--border)] bg-[var(--card)]">
          <div className="border-b border-[var(--border)] px-6 py-5">
            <p className="font-mono text-[9px] uppercase tracking-[0.18em] text-[var(--primary)]">
              Technology profile
            </p>

            <h2 className="mt-2 text-lg font-medium">
              Detected algorithms
            </h2>
          </div>

          <div className="divide-y divide-[var(--border)]">
            {algorithms.map(([algorithm, data]) => (
              <div
                key={algorithm}
                className="grid grid-cols-[1fr_auto] gap-6 px-6 py-5"
              >
                <div>
                  <div className="flex items-center gap-3">
                    <span className="font-mono text-sm">
                      {algorithm}
                    </span>

                    <span className="rounded-full border border-[var(--border)] px-2 py-1 font-mono text-[8px] uppercase tracking-[0.12em] text-[var(--muted-foreground)]">
                      {data.type}
                    </span>
                  </div>

                  <div className="mt-3 flex flex-wrap gap-2">
                    {Object.entries(data.risks).map(
                      ([risk, count]) => (
                        <span
                          key={risk}
                          className={`font-mono text-[8px] uppercase tracking-[0.1em] ${riskText(
                            risk
                          )}`}
                        >
                          {risk}: {count}
                        </span>
                      )
                    )}
                  </div>
                </div>

                <div className="text-right">
                  <p className="font-mono text-2xl">
                    {data.count}
                  </p>

                  <p className="mt-1 font-mono text-[8px] uppercase tracking-[0.12em] text-[var(--muted-foreground)]">
                    findings
                  </p>
                </div>
              </div>
            ))}

            {algorithms.length === 0 && (
              <div className="px-6 py-8 text-sm text-[var(--muted-foreground)]">
                No cryptographic algorithms were detected.
              </div>
            )}
          </div>
        </div>

        {/* TYPES */}

        <div className="rounded-lg border border-[var(--border)] bg-[var(--card)]">
          <div className="border-b border-[var(--border)] px-6 py-5">
            <p className="font-mono text-[9px] uppercase tracking-[0.18em] text-[var(--primary)]">
              Classification
            </p>

            <h2 className="mt-2 text-lg font-medium">
              Cryptographic types
            </h2>
          </div>

          <div className="p-6">
            <div className="space-y-5">
              {cryptoTypes.map(([type, count]) => {
                const percentage =
                  result.total_artifacts > 0
                    ? (count / result.total_artifacts) * 100
                    : 0;

                return (
                  <div key={type}>
                    <div className="flex items-center justify-between">
                      <span className="text-sm">
                        {type}
                      </span>

                      <span className="font-mono text-[10px] text-[var(--muted-foreground)]">
                        {count}
                      </span>
                    </div>

                    <div className="mt-2 h-1 rounded-full bg-[var(--accent)]">
                      <div
                        className="h-1 rounded-full bg-[var(--primary)]"
                        style={{
                          width: `${percentage}%`,
                        }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </section>

      {/* SOURCE FILES */}

      <section className="mt-5 rounded-lg border border-[var(--border)] bg-[var(--card)]">
        <div className="border-b border-[var(--border)] px-6 py-5">
          <p className="font-mono text-[9px] uppercase tracking-[0.18em] text-[var(--primary)]">
            Source distribution
          </p>

          <h2 className="mt-2 text-lg font-medium">
            Files containing cryptographic usage
          </h2>
        </div>

        {files.length === 0 ? (
          <div className="px-6 py-8 text-sm text-[var(--muted-foreground)]">
            No source files contain detected cryptographic artifacts.
          </div>
        ) : (
          <div className="divide-y divide-[var(--border)]">
            {files.map(([file, data]) => (
              <div
                key={file}
                className="grid gap-5 px-6 py-5 lg:grid-cols-[1fr_120px_260px]"
              >
                <div>
                  <p className="break-all font-mono text-xs">
                    {file}
                  </p>

                  <div className="mt-3 flex flex-wrap gap-2">
                    {data.algorithms.map((algorithm) => (
                      <span
                        key={algorithm}
                        className="border border-[var(--border)] px-2 py-1 font-mono text-[8px] uppercase tracking-[0.1em] text-[var(--muted-foreground)]"
                      >
                        {algorithm}
                      </span>
                    ))}
                  </div>
                </div>

                <div className="lg:text-right">
                  <p className="font-mono text-xl">
                    {data.count}
                  </p>

                  <p className="mt-1 font-mono text-[8px] uppercase tracking-[0.12em] text-[var(--muted-foreground)]">
                    artifacts
                  </p>
                </div>

                <div className="flex flex-wrap content-start gap-2 lg:justify-end">
                  {data.risks.map((risk) => (
                    <span
                      key={risk}
                      className={`font-mono text-[8px] uppercase tracking-[0.1em] ${riskText(
                        risk
                      )}`}
                    >
                      {risk}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* INVENTORY NOTE */}

      <section className="mt-5 border border-[var(--border)] bg-[var(--accent)]/30 p-6">
        <div className="flex gap-4">
          <span className="mt-1 h-2 w-2 shrink-0 rounded-full bg-[var(--primary)]" />

          <div>
            <p className="font-mono text-[9px] uppercase tracking-[0.18em] text-[var(--primary)]">
              Inventory boundary
            </p>

            <p className="mt-3 max-w-4xl text-sm leading-6 text-[var(--muted-foreground)]">
              This inventory represents cryptographic usage discovered
              by the current source-code scan. It is not a claim that
              every cryptographic dependency in the wider enterprise
              has been discovered.
            </p>
          </div>
        </div>
      </section>
    </main>
  );
}

function Metric({
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
      <p className="font-mono text-[9px] uppercase tracking-[0.18em] text-[var(--muted-foreground)]">
        {label}
      </p>

      <div className="mt-4 flex items-end justify-between">
        <span className="text-3xl font-medium">
          {value}
        </span>

        <span className="font-mono text-[9px] uppercase tracking-[0.12em] text-[var(--muted-foreground)]">
          {detail}
        </span>
      </div>
    </div>
  );
}

function RiskCard({
  label,
  value,
  description,
  risk,
}: {
  label: string;
  value: number;
  description: string;
  risk: string;
}) {
  return (
    <div className="border border-[var(--border)] p-5">
      <div className="flex items-center justify-between">
        <span
          className={`font-mono text-[9px] uppercase tracking-[0.14em] ${riskText(
            risk
          )}`}
        >
          {label}
        </span>

        <span className="font-mono text-xl">
          {value}
        </span>
      </div>

      <p className="mt-4 text-xs text-[var(--muted-foreground)]">
        {description}
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
