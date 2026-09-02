"use client";

import { useEffect, useMemo, useState } from "react";
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
  quantum_risk: string;
  risk_reason: string;
  recommendation: string;
};

type ScanResult = {
  target: string;
  generated_at?: string;
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

export default function QuantumPage() {
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

  const quantumExposure = useMemo(() => {
    return artifacts.filter((artifact) => {
      const risk = artifact.quantum_risk.toUpperCase();

      return (
        risk === "CRITICAL" ||
        risk === "HIGH"
      );
    });
  }, [artifacts]);

  const publicKeyFindings = useMemo(() => {
    return artifacts.filter((artifact) => {
      const type = artifact.type.toLowerCase();

      return (
        type === "asymmetric" ||
        ["rsa", "ecdsa", "ecdh", "dh", "dsa"].includes(
          artifact.algorithm.toLowerCase()
        )
      );
    });
  }, [artifacts]);

  const symmetricFindings = useMemo(() => {
    return artifacts.filter((artifact) => {
      const algorithm =
        artifact.algorithm.toUpperCase();

      return (
        algorithm === "AES" ||
        algorithm === "CHACHA20"
      );
    });
  }, [artifacts]);

  const exposurePercent =
    result && result.total_artifacts > 0
      ? Math.round(
          (result.quantum_vulnerable_assets /
            result.total_artifacts) *
            100
        )
      : 0;

  if (!result) {
    return (
      <main className="mx-auto max-w-[1220px] px-10 py-10">
        <p className="font-mono text-[10px] uppercase tracking-[0.22em] text-[var(--primary)]">
          Assess / Quantum
        </p>

        <h1 className="mt-3 text-3xl font-semibold tracking-tight">
          Quantum readiness
        </h1>

        <section className="mt-8 rounded-lg border border-[var(--border)] bg-[var(--card)] p-7">
          <p className="text-sm text-[var(--muted-foreground)]">
            No scan result is loaded. Run a repository scan from Import
            before assessing quantum exposure.
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
              Assess / Quantum
            </p>

            <h1 className="mt-3 text-3xl font-semibold tracking-tight">
              Quantum readiness
            </h1>

            <p className="mt-3 max-w-3xl text-sm leading-6 text-[var(--muted-foreground)]">
              Identify cryptographic mechanisms exposed to known
              quantum attack models and establish the priority for
              post-quantum migration.
            </p>
          </div>

          <div className="text-right">
            <p className="font-mono text-[9px] uppercase tracking-[0.18em] text-[var(--muted-foreground)]">
              Assessment
            </p>

            <p className="mt-2 font-mono text-xs">
              {result.quantum_vulnerable_assets} exposed assets
            </p>
          </div>
        </div>
      </header>

      {/* TOP METRICS */}

      <section className="grid gap-4 md:grid-cols-4">
        <Metric
          label="Quantum exposed"
          value={result.quantum_vulnerable_assets}
          detail={`${exposurePercent}% of findings`}
        />

        <Metric
          label="Critical"
          value={result.risk_summary.critical}
          detail="highest urgency"
        />

        <Metric
          label="High"
          value={result.risk_summary.high}
          detail="migration priority"
        />

        <Metric
          label="Public-key"
          value={publicKeyFindings.length}
          detail="quantum sensitive"
        />
      </section>

      {/* EXPOSURE POSITION */}

      <section className="mt-5 rounded-lg border border-[var(--border)] bg-[var(--card)] p-7">
        <div className="grid gap-10 lg:grid-cols-[1fr_280px]">
          <div>
            <p className="font-mono text-[9px] uppercase tracking-[0.18em] text-[var(--primary)]">
              Exposure assessment
            </p>

            <h2 className="mt-3 text-2xl font-medium">
              {result.quantum_vulnerable_assets > 0
                ? "Quantum-vulnerable cryptography is present."
                : "No high-priority quantum exposure detected."}
            </h2>

            <p className="mt-4 max-w-3xl text-sm leading-6 text-[var(--muted-foreground)]">
              The current analysis identifies public-key mechanisms
              whose underlying mathematical assumptions are vulnerable
              to sufficiently capable quantum computers. These findings
              should enter the migration roadmap according to their
              business purpose and deployment dependencies.
            </p>
          </div>

          <div className="border-l border-[var(--border)] pl-7">
            <p className="font-mono text-[9px] uppercase tracking-[0.16em] text-[var(--muted-foreground)]">
              Exposure ratio
            </p>

            <p className="mt-3 font-mono text-5xl">
              {exposurePercent}%
            </p>

            <div className="mt-4 h-1.5 rounded-full bg-[var(--accent)]">
              <div
                className="h-full rounded-full bg-[var(--primary)]"
                style={{
                  width: `${exposurePercent}%`,
                }}
              />
            </div>

            <p className="mt-3 text-[10px] text-[var(--muted-foreground)]">
              high + critical findings / total findings
            </p>
          </div>
        </div>
      </section>

      {/* THREAT MODEL */}

      <section className="mt-5 rounded-lg border border-[var(--border)] bg-[var(--card)]">
        <div className="border-b border-[var(--border)] px-6 py-5">
          <p className="font-mono text-[9px] uppercase tracking-[0.18em] text-[var(--primary)]">
            Threat model
          </p>

          <h2 className="mt-2 text-lg font-medium">
            Why these algorithms matter
          </h2>
        </div>

        <div className="grid gap-px bg-[var(--border)] md:grid-cols-3">
          <ThreatCard
            title="Public-key cryptography"
            description="RSA and elliptic-curve mechanisms depend on mathematical problems targeted by Shor's algorithm."
            count={publicKeyFindings.length}
          />

          <ThreatCard
            title="Symmetric cryptography"
            description="Strong symmetric constructions such as AES-256 are affected differently and generally retain substantial security against known quantum search advantages."
            count={symmetricFindings.length}
          />

          <ThreatCard
            title="Migration dependency"
            description="Actual migration priority depends on cryptographic purpose, protocol, data lifetime, and implementation constraints."
            count={quantumExposure.length}
          />
        </div>
      </section>

      {/* VULNERABLE ASSETS */}

      <section className="mt-5 rounded-lg border border-[var(--border)] bg-[var(--card)]">
        <div className="flex items-end justify-between gap-6 border-b border-[var(--border)] px-6 py-5">
          <div>
            <p className="font-mono text-[9px] uppercase tracking-[0.18em] text-[var(--primary)]">
              Quantum exposure
            </p>

            <h2 className="mt-2 text-lg font-medium">
              Vulnerable cryptographic assets
            </h2>
          </div>

          <span className="font-mono text-[9px] uppercase tracking-[0.14em] text-[var(--muted-foreground)]">
            {quantumExposure.length} findings
          </span>
        </div>

        {quantumExposure.length === 0 ? (
          <div className="px-6 py-9 text-sm text-[var(--muted-foreground)]">
            No critical or high quantum-vulnerability findings were
            returned by the current scan.
          </div>
        ) : (
          <div className="divide-y divide-[var(--border)]">
            {quantumExposure.map((artifact, index) => (
              <div
                key={`${artifact.file}-${artifact.line}-${index}`}
                className="grid gap-6 px-6 py-6 lg:grid-cols-[180px_1fr_1fr]"
              >
                <div>
                  <div className="flex items-center gap-3">
                    <span
                      className={`font-mono text-[9px] uppercase tracking-[0.14em] ${riskText(
                        artifact.quantum_risk
                      )}`}
                    >
                      {artifact.quantum_risk}
                    </span>
                  </div>

                  <p className="mt-3 font-mono text-sm">
                    {artifact.algorithm}
                  </p>

                  <p className="mt-2 text-[10px] text-[var(--muted-foreground)]">
                    {artifact.type}
                  </p>
                </div>

                <div>
                  <p className="break-all font-mono text-xs">
                    {artifact.file}
                  </p>

                  <p className="mt-2 font-mono text-[9px] uppercase tracking-[0.1em] text-[var(--muted-foreground)]">
                    line {artifact.line}
                  </p>

                  {artifact.key_size && (
                    <p className="mt-3 font-mono text-[9px] text-[var(--muted-foreground)]">
                      key size: {artifact.key_size}
                    </p>
                  )}

                  {artifact.curve && (
                    <p className="mt-1 font-mono text-[9px] text-[var(--muted-foreground)]">
                      curve: {artifact.curve}
                    </p>
                  )}
                </div>

                <div>
                  <p className="text-xs leading-5 text-[var(--muted-foreground)]">
                    {artifact.risk_reason}
                  </p>

                  <div className="mt-4 border-l border-[var(--primary)]/40 pl-4">
                    <p className="font-mono text-[9px] uppercase tracking-[0.12em] text-[var(--primary)]">
                      Recommended direction
                    </p>

                    <p className="mt-2 text-xs leading-5">
                      {artifact.recommendation}
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* MIGRATION TARGETS */}

      <section className="mt-5 rounded-lg border border-[var(--border)] bg-[var(--card)] p-6">
        <p className="font-mono text-[9px] uppercase tracking-[0.18em] text-[var(--primary)]">
          Migration targets
        </p>

        <h2 className="mt-2 text-lg font-medium">
          Post-quantum transition map
        </h2>

        <div className="mt-6 space-y-3">
          <Transition
            source="RSA"
            target="ML-KEM / appropriate hybrid mechanism"
            purpose="Key establishment or encryption"
          />

          <Transition
            source="ECDSA"
            target="ML-DSA / SLH-DSA / appropriate hybrid"
            purpose="Digital signatures"
          />

          <Transition
            source="Other quantum-vulnerable public-key crypto"
            target="Standards-approved PQC or hybrid mechanism"
            purpose="Application-dependent"
          />

          <Transition
            source="AES-256 / strong symmetric crypto"
            target="Continue with appropriate key sizes"
            purpose="Symmetric protection"
          />
        </div>
      </section>

      {/* NOTE */}

      <section className="mt-5 border border-[var(--border)] bg-[var(--accent)]/30 p-6">
        <div className="flex gap-4">
          <span className="mt-1 h-2 w-2 shrink-0 rounded-full bg-[var(--primary)]" />

          <div>
            <p className="font-mono text-[9px] uppercase tracking-[0.18em] text-[var(--primary)]">
              Assessment boundary
            </p>

            <p className="mt-3 max-w-4xl text-sm leading-6 text-[var(--muted-foreground)]">
              Quantum risk shown here is the classification returned
              by the ECDAT backend analysis engine. It is not a prediction
              of when a cryptographically relevant quantum computer will
              exist. Migration decisions should incorporate system
              lifetime, data sensitivity, implementation dependencies,
              interoperability, and applicable standards.
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

      <div className="mt-4 flex items-end justify-between gap-4">
        <span className="font-mono text-3xl">
          {value}
        </span>

        <span className="text-right font-mono text-[9px] uppercase tracking-[0.1em] text-[var(--muted-foreground)]">
          {detail}
        </span>
      </div>
    </div>
  );
}

function ThreatCard({
  title,
  description,
  count,
}: {
  title: string;
  description: string;
  count: number;
}) {
  return (
    <div className="bg-[var(--card)] p-6">
      <div className="flex items-start justify-between gap-4">
        <h3 className="text-sm font-medium">
          {title}
        </h3>

        <span className="font-mono text-xl text-[var(--primary)]">
          {count}
        </span>
      </div>

      <p className="mt-4 text-xs leading-5 text-[var(--muted-foreground)]">
        {description}
      </p>
    </div>
  );
}

function Transition({
  source,
  target,
  purpose,
}: {
  source: string;
  target: string;
  purpose: string;
}) {
  return (
    <div className="grid gap-4 border border-[var(--border)] p-4 md:grid-cols-[190px_30px_1fr_220px] md:items-center">
      <span className="font-mono text-xs">
        {source}
      </span>

      <span className="hidden font-mono text-[var(--primary)] md:block">
        →
      </span>

      <span className="text-xs">
        {target}
      </span>

      <span className="font-mono text-[8px] uppercase tracking-[0.1em] text-[var(--muted-foreground)]">
        {purpose}
      </span>
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
