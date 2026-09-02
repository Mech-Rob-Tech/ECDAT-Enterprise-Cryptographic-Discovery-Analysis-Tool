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
  artifacts: Artifact[];
};

type Filter = "ALL" | "CRITICAL" | "HIGH" | "MEDIUM" | "LOW";

export default function ArtifactsPage() {
  const router = useRouter();
  const [result, setResult] = useState<ScanResult | null>(null);
  const [filter, setFilter] = useState<Filter>("ALL");
  const [search, setSearch] = useState("");

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

  const filteredArtifacts = useMemo(() => {
    const query = search.trim().toLowerCase();

    return artifacts.filter((artifact) => {
      const matchesRisk =
        filter === "ALL" ||
        artifact.quantum_risk.toUpperCase() === filter;

      const matchesSearch =
        !query ||
        artifact.algorithm.toLowerCase().includes(query) ||
        artifact.type.toLowerCase().includes(query) ||
        artifact.file.toLowerCase().includes(query) ||
        artifact.evidence.toLowerCase().includes(query);

      return matchesRisk && matchesSearch;
    });
  }, [artifacts, filter, search]);

  if (!result) {
    return (
      <main className="mx-auto max-w-[1220px] px-10 py-10">
        <p className="font-mono text-[10px] uppercase tracking-[0.22em] text-[var(--primary)]">
          Discover / Artifacts
        </p>

        <h1 className="mt-3 text-3xl font-semibold tracking-tight">
          Cryptographic inventory
        </h1>

        <section className="mt-8 rounded-lg border border-[var(--border)] bg-[var(--card)] p-7">
          <p className="text-sm text-[var(--muted-foreground)]">
            No scan result is loaded. Run a repository scan from Import
            before viewing discovered cryptographic artifacts.
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
              Discover / Artifacts
            </p>

            <h1 className="mt-3 text-3xl font-semibold tracking-tight">
              Cryptographic inventory
            </h1>

            <p className="mt-3 max-w-3xl text-sm leading-6 text-[var(--muted-foreground)]">
              Every cryptographic artifact discovered during the current
              repository scan, including its source location, implementation
              details, quantum risk, and recommended action.
            </p>
          </div>

          <div className="text-right">
            <p className="font-mono text-[9px] uppercase tracking-[0.18em] text-[var(--muted-foreground)]">
              Target
            </p>

            <p className="mt-2 max-w-[280px] break-all font-mono text-xs">
              {result.target}
            </p>
          </div>
        </div>
      </header>

      {/* METRICS */}

      <section className="grid gap-4 md:grid-cols-4">
        <Metric
          label="Total artifacts"
          value={result.total_artifacts}
        />

        <Metric
          label="Critical"
          value={countRisk(artifacts, "CRITICAL")}
        />

        <Metric
          label="High"
          value={countRisk(artifacts, "HIGH")}
        />

        <Metric
          label="Files scanned"
          value={result.total_files_scanned}
        />
      </section>

      {/* FILTER BAR */}

      <section className="mt-5 rounded-lg border border-[var(--border)] bg-[var(--card)] p-5">
        <div className="flex flex-col gap-5 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <p className="font-mono text-[9px] uppercase tracking-[0.18em] text-[var(--primary)]">
              Inventory controls
            </p>

            <p className="mt-2 text-xs text-[var(--muted-foreground)]">
              Filter the current scan without triggering another scan.
            </p>
          </div>

          <input
            type="search"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Search algorithm, file, evidence..."
            className="w-full rounded-md border border-[var(--input)] bg-[var(--background)] px-4 py-2.5 font-mono text-[10px] text-[var(--foreground)] outline-none placeholder:text-[var(--muted-foreground)] focus:border-[var(--primary)] lg:w-[330px]"
          />
        </div>

        <div className="mt-5 flex flex-wrap gap-2">
          {(["ALL", "CRITICAL", "HIGH", "MEDIUM", "LOW"] as Filter[]).map(
            (option) => {
              const selected = filter === option;

              return (
                <button
                  key={option}
                  type="button"
                  onClick={() => setFilter(option)}
                  className={`border px-3 py-2 font-mono text-[9px] uppercase tracking-[0.13em] transition ${
                    selected
                      ? "border-[var(--primary)] bg-[var(--primary)]/[0.08] text-[var(--primary)]"
                      : "border-[var(--border)] text-[var(--muted-foreground)] hover:border-[var(--primary)]/40 hover:text-[var(--foreground)]"
                  }`}
                >
                  {option}
                </button>
              );
            }
          )}
        </div>
      </section>

      {/* TABLE */}

      <section className="mt-5 overflow-hidden rounded-lg border border-[var(--border)] bg-[var(--card)]">
        <div className="flex items-center justify-between border-b border-[var(--border)] px-6 py-5">
          <div>
            <p className="font-mono text-[9px] uppercase tracking-[0.18em] text-[var(--primary)]">
              Discovered assets
            </p>

            <h2 className="mt-2 text-lg font-medium">
              Artifact registry
            </h2>
          </div>

          <span className="font-mono text-[9px] uppercase tracking-[0.14em] text-[var(--muted-foreground)]">
            {filteredArtifacts.length} / {artifacts.length}
          </span>
        </div>

        {filteredArtifacts.length === 0 ? (
          <div className="px-6 py-10 text-sm text-[var(--muted-foreground)]">
            No artifacts match the current filters.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[1050px] border-collapse">
              <thead>
                <tr className="border-b border-[var(--border)] text-left">
                  <th className="px-6 py-4 font-mono text-[9px] uppercase tracking-[0.14em] text-[var(--muted-foreground)]">
                    Algorithm
                  </th>

                  <th className="px-6 py-4 font-mono text-[9px] uppercase tracking-[0.14em] text-[var(--muted-foreground)]">
                    Type
                  </th>

                  <th className="px-6 py-4 font-mono text-[9px] uppercase tracking-[0.14em] text-[var(--muted-foreground)]">
                    Parameters
                  </th>

                  <th className="px-6 py-4 font-mono text-[9px] uppercase tracking-[0.14em] text-[var(--muted-foreground)]">
                    Location
                  </th>

                  <th className="px-6 py-4 font-mono text-[9px] uppercase tracking-[0.14em] text-[var(--muted-foreground)]">
                    Risk
                  </th>
                </tr>
              </thead>

              <tbody>
                {filteredArtifacts.map((artifact, index) => (
                  <ArtifactRow
                    key={`${artifact.file}-${artifact.line}-${index}`}
                    artifact={artifact}
                  />
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {/* DETAILS */}

      <section className="mt-5 rounded-lg border border-[var(--border)] bg-[var(--card)] p-6">
        <div className="grid gap-8 lg:grid-cols-3">
          <InfoBlock
            title="Discovery"
            text="Artifacts represent cryptographic technologies detected directly from the scanned source repository."
          />

          <InfoBlock
            title="Risk"
            text="Risk values are produced by the backend analysis layer and are not inferred by the frontend."
          />

          <InfoBlock
            title="Evidence"
            text="Each finding retains the source file, line number, and matching evidence used during discovery."
          />
        </div>
      </section>
    </main>
  );
}

function ArtifactRow({
  artifact,
}: {
  artifact: Artifact;
}) {
  return (
    <tr className="border-b border-[var(--border)] align-top last:border-b-0">
      <td className="px-6 py-5">
        <p className="font-mono text-sm text-[var(--foreground)]">
          {artifact.algorithm}
        </p>

        {artifact.curve && (
          <p className="mt-2 font-mono text-[9px] text-[var(--muted-foreground)]">
            {artifact.curve}
          </p>
        )}
      </td>

      <td className="px-6 py-5">
        <span className="rounded-full border border-[var(--border)] px-2 py-1 font-mono text-[8px] uppercase tracking-[0.12em] text-[var(--muted-foreground)]">
          {artifact.type}
        </span>
      </td>

      <td className="px-6 py-5">
        <div className="space-y-1 font-mono text-[9px] text-[var(--muted-foreground)]">
          {artifact.key_size && (
            <p>key: {artifact.key_size}</p>
          )}

          {artifact.mode && (
            <p>mode: {artifact.mode}</p>
          )}

          {artifact.version && (
            <p>version: {artifact.version}</p>
          )}

          {!artifact.key_size &&
            !artifact.mode &&
            !artifact.version && (
              <p>—</p>
            )}
        </div>
      </td>

      <td className="max-w-[340px] px-6 py-5">
        <p className="break-all font-mono text-[10px] leading-5">
          {artifact.file}
        </p>

        <p className="mt-2 font-mono text-[9px] uppercase tracking-[0.1em] text-[var(--muted-foreground)]">
          line {artifact.line}
        </p>

        <div className="mt-3 border-l border-[var(--primary)]/40 pl-3">
          <p className="font-mono text-[8px] uppercase tracking-[0.12em] text-[var(--muted-foreground)]">
            Evidence
          </p>

          <p className="mt-1 break-words font-mono text-[9px] leading-5 text-[var(--foreground)]">
            {artifact.evidence}
          </p>
        </div>
      </td>

      <td className="px-6 py-5">
        <RiskBadge risk={artifact.quantum_risk} />

        <p className="mt-3 max-w-[260px] text-[10px] leading-5 text-[var(--muted-foreground)]">
          {artifact.risk_reason}
        </p>

        <p className="mt-3 max-w-[260px] text-[10px] leading-5 text-[var(--foreground)]">
          {artifact.recommendation}
        </p>
      </td>
    </tr>
  );
}

function RiskBadge({
  risk,
}: {
  risk: string;
}) {
  const normalized = risk.toUpperCase();

  const classes =
    normalized === "CRITICAL"
      ? "border-red-400/30 text-red-400"
      : normalized === "HIGH"
        ? "border-amber-400/30 text-amber-400"
        : normalized === "MEDIUM"
          ? "border-yellow-400/30 text-yellow-300"
          : "border-emerald-400/30 text-emerald-400";

  return (
    <span
      className={`inline-flex rounded-full border px-2 py-1 font-mono text-[8px] uppercase tracking-[0.14em] ${classes}`}
    >
      {normalized}
    </span>
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
      <p className="font-mono text-[9px] uppercase tracking-[0.18em] text-[var(--muted-foreground)]">
        {label}
      </p>

      <p className="mt-4 text-3xl font-medium">
        {value}
      </p>
    </div>
  );
}

function InfoBlock({
  title,
  text,
}: {
  title: string;
  text: string;
}) {
  return (
    <div>
      <h3 className="font-mono text-[10px] uppercase tracking-[0.16em] text-[var(--primary)]">
        {title}
      </h3>

      <p className="mt-3 text-xs leading-5 text-[var(--muted-foreground)]">
        {text}
      </p>
    </div>
  );
}

function countRisk(
  artifacts: Artifact[],
  risk: string
) {
  return artifacts.filter(
    (artifact) =>
      artifact.quantum_risk.toUpperCase() === risk
  ).length;
}
