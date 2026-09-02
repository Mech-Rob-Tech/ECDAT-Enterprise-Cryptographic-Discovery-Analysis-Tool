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
  total_files_scanned: number;
  total_artifacts: number;
  quantum_vulnerable_assets: number;
  artifacts: Artifact[];
};

type Priority = "Immediate" | "High" | "Planned" | "Monitor";

function getPriority(artifact: Artifact): Priority {
  const algorithm = artifact.algorithm.toUpperCase();
  const risk = artifact.quantum_risk.toUpperCase();

  if (algorithm === "MD5" || risk === "CRITICAL") {
    return "Immediate";
  }

  if (
    algorithm === "RSA" ||
    algorithm === "ECDSA" ||
    algorithm === "ECDH" ||
    algorithm === "DSA" ||
    risk === "HIGH"
  ) {
    return "High";
  }

  if (risk === "MEDIUM") {
    return "Planned";
  }

  return "Monitor";
}

function getMigrationArea(artifact: Artifact) {
  const algorithm = artifact.algorithm.toUpperCase();

  if (
    algorithm === "RSA" ||
    algorithm === "ECDH" ||
    algorithm === "DH"
  ) {
    return "Key establishment / encryption";
  }

  if (
    algorithm === "ECDSA" ||
    algorithm === "DSA" ||
    algorithm === "ED25519"
  ) {
    return "Digital signatures";
  }

  if (
    algorithm === "AES" ||
    algorithm === "CHACHA20"
  ) {
    return "Symmetric cryptography";
  }

  if (
    algorithm === "MD5" ||
    algorithm === "SHA-1"
  ) {
    return "Legacy hashing";
  }

  if (algorithm === "TLS") {
    return "Transport security";
  }

  return "Cryptographic implementation";
}

function priorityClasses(priority: Priority) {
  switch (priority) {
    case "Immediate":
      return "border-red-400/30 bg-red-400/[0.04] text-red-400";

    case "High":
      return "border-amber-400/30 bg-amber-400/[0.04] text-amber-400";

    case "Planned":
      return "border-yellow-400/30 bg-yellow-400/[0.04] text-yellow-300";

    default:
      return "border-emerald-400/30 bg-emerald-400/[0.04] text-emerald-400";
  }
}

export default function MigrationPage() {
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

  const prioritized = useMemo(() => {
    return artifacts
      .map((artifact) => ({
        ...artifact,
        priority: getPriority(artifact),
        area: getMigrationArea(artifact),
      }))
      .sort((a, b) => {
        const order: Record<Priority, number> = {
          Immediate: 0,
          High: 1,
          Planned: 2,
          Monitor: 3,
        };

        return order[a.priority] - order[b.priority];
      });
  }, [artifacts]);

  const immediate = prioritized.filter(
    (item) => item.priority === "Immediate"
  );

  const high = prioritized.filter(
    (item) => item.priority === "High"
  );

  const planned = prioritized.filter(
    (item) => item.priority === "Planned"
  );

  const monitor = prioritized.filter(
    (item) => item.priority === "Monitor"
  );

  if (!result) {
    return (
      <main className="mx-auto max-w-[1220px] px-10 py-10">
        <p className="font-mono text-[10px] uppercase tracking-[0.22em] text-[var(--primary)]">
          Plan / Migration
        </p>

        <h1 className="mt-3 text-3xl font-semibold tracking-tight">
          Migration planning
        </h1>

        <section className="mt-8 rounded-lg border border-[var(--border)] bg-[var(--card)] p-7">
          <p className="text-sm text-[var(--muted-foreground)]">
            No scan result is loaded. Run a repository scan from Import
            before generating migration priorities.
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
              Plan / Migration
            </p>

            <h1 className="mt-3 text-3xl font-semibold tracking-tight">
              Cryptographic migration plan
            </h1>

            <p className="mt-3 max-w-3xl text-sm leading-6 text-[var(--muted-foreground)]">
              Prioritize discovered cryptographic technologies according
              to quantum exposure, legacy status, and migration urgency.
            </p>
          </div>

          <div className="text-right">
            <p className="font-mono text-[9px] uppercase tracking-[0.18em] text-[var(--muted-foreground)]">
              Target
            </p>

            <p className="mt-2 font-mono text-xs text-[var(--foreground)]">
              {result.target.split("/").pop() || result.target}
            </p>
          </div>
        </div>
      </header>

      {/* SUMMARY */}

      <section className="grid gap-4 md:grid-cols-4">
        <Metric
          label="Immediate"
          value={immediate.length}
          detail="act now"
        />

        <Metric
          label="High"
          value={high.length}
          detail="prioritize"
        />

        <Metric
          label="Planned"
          value={planned.length}
          detail="schedule"
        />

        <Metric
          label="Monitor"
          value={monitor.length}
          detail="continue review"
        />
      </section>

      {/* STRATEGY */}

      <section className="mt-5 rounded-lg border border-[var(--border)] bg-[var(--card)] p-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="font-mono text-[9px] uppercase tracking-[0.18em] text-[var(--primary)]">
              Strategy
            </p>

            <h2 className="mt-2 text-lg font-medium">
              Recommended migration sequence
            </h2>
          </div>

          <span className="font-mono text-[9px] uppercase tracking-[0.16em] text-[var(--muted-foreground)]">
            {prioritized.length} assets
          </span>
        </div>

        <div className="mt-7 grid gap-4 lg:grid-cols-4">
          <Strategy
            number="01"
            title="Remove legacy crypto"
            description="Address broken or unsuitable legacy algorithms first."
          />

          <Strategy
            number="02"
            title="Map public-key usage"
            description="Identify RSA and elliptic-curve dependencies requiring PQC planning."
          />

          <Strategy
            number="03"
            title="Design replacements"
            description="Evaluate appropriate post-quantum or hybrid mechanisms for each use case."
          />

          <Strategy
            number="04"
            title="Validate migration"
            description="Test compatibility, security, performance, and operational impact."
          />
        </div>
      </section>

      {/* IMMEDIATE */}

      <MigrationSection
        title="Immediate action"
        eyebrow="Priority 01"
        description="Legacy or critically exposed findings requiring immediate attention."
        items={immediate}
      />

      {/* HIGH */}

      <MigrationSection
        title="High-priority migration"
        eyebrow="Priority 02"
        description="Public-key and other quantum-vulnerable technologies requiring migration planning."
        items={high}
      />

      {/* PLANNED */}

      <MigrationSection
        title="Planned migration"
        eyebrow="Priority 03"
        description="Findings that should enter the migration roadmap but do not require immediate replacement."
        items={planned}
      />

      {/* MONITOR */}

      <MigrationSection
        title="Monitor"
        eyebrow="Priority 04"
        description="Technologies with lower immediate quantum migration priority."
        items={monitor}
      />

      {/* FOOTER NOTE */}

      <section className="mt-5 border border-[var(--border)] bg-[var(--accent)]/30 p-6">
        <div className="flex gap-4">
          <span className="mt-1 h-2 w-2 shrink-0 rounded-full bg-[var(--primary)]" />

          <div>
            <p className="font-mono text-[9px] uppercase tracking-[0.18em] text-[var(--primary)]">
              Migration guidance
            </p>

            <p className="mt-3 max-w-4xl text-sm leading-6 text-[var(--muted-foreground)]">
              Migration priority is derived from the cryptographic
              artifacts discovered by the current scan. Replacement
              mechanisms should be selected according to the actual
              cryptographic purpose, protocol, interoperability
              requirements, and applicable security standards.
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

function Strategy({
  number,
  title,
  description,
}: {
  number: string;
  title: string;
  description: string;
}) {
  return (
    <div className="border border-[var(--border)] p-5">
      <span className="font-mono text-[10px] text-[var(--primary)]">
        {number}
      </span>

      <h3 className="mt-4 text-sm font-medium">
        {title}
      </h3>

      <p className="mt-2 text-xs leading-5 text-[var(--muted-foreground)]">
        {description}
      </p>
    </div>
  );
}

function MigrationSection({
  title,
  eyebrow,
  description,
  items,
}: {
  title: string;
  eyebrow: string;
  description: string;
  items: Array<
    Artifact & {
      priority: Priority;
      area: string;
    }
  >;
}) {
  return (
    <section className="mt-5 rounded-lg border border-[var(--border)] bg-[var(--card)]">
      <div className="border-b border-[var(--border)] px-6 py-5">
        <p className="font-mono text-[9px] uppercase tracking-[0.18em] text-[var(--primary)]">
          {eyebrow}
        </p>

        <div className="mt-2 flex items-end justify-between gap-6">
          <div>
            <h2 className="text-lg font-medium">
              {title}
            </h2>

            <p className="mt-2 text-xs leading-5 text-[var(--muted-foreground)]">
              {description}
            </p>
          </div>

          <span className="shrink-0 font-mono text-[9px] uppercase tracking-[0.14em] text-[var(--muted-foreground)]">
            {items.length} findings
          </span>
        </div>
      </div>

      {items.length === 0 ? (
        <div className="px-6 py-7 text-sm text-[var(--muted-foreground)]">
          No findings currently fall into this migration category.
        </div>
      ) : (
        <div className="divide-y divide-[var(--border)]">
          {items.map((artifact, index) => (
            <div
              key={`${artifact.file}-${artifact.line}-${index}`}
              className="grid gap-5 px-6 py-5 lg:grid-cols-[180px_1fr_1fr]"
            >
              <div>
                <div className="flex items-center gap-3">
                  <span
                    className={`rounded-full border px-2 py-1 font-mono text-[8px] uppercase tracking-[0.14em] ${priorityClasses(
                      artifact.priority
                    )}`}
                  >
                    {artifact.priority}
                  </span>

                  <span className="font-mono text-sm">
                    {artifact.algorithm}
                  </span>
                </div>

                <p className="mt-3 text-[10px] text-[var(--muted-foreground)]">
                  {artifact.area}
                </p>
              </div>

              <div>
                <p className="font-mono text-xs break-all">
                  {artifact.file}
                </p>

                <p className="mt-2 font-mono text-[9px] uppercase tracking-[0.12em] text-[var(--muted-foreground)]">
                  line {artifact.line}
                </p>

                {artifact.key_size && (
                  <p className="mt-2 font-mono text-[9px] text-[var(--muted-foreground)]">
                    key size: {artifact.key_size}
                  </p>
                )}
              </div>

              <div>
                <p className="text-xs leading-5 text-[var(--muted-foreground)]">
                  {artifact.recommendation}
                </p>

                <div className="mt-4 border-l border-[var(--primary)]/40 pl-3">
                  <p className="font-mono text-[9px] uppercase tracking-[0.12em] text-[var(--muted-foreground)]">
                    Evidence
                  </p>

                  <p className="mt-1 font-mono text-[10px] leading-5 text-[var(--foreground)]">
                    {artifact.evidence}
                  </p>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}
