import Link from "next/link";
import { getScanResult } from "@/lib/scan-data";
import { RiskBadge } from "@/components/ecdat/risk-badge";

interface ArtifactPageProps {
  params: Promise<{
    id: string;
  }>;
}

export default async function ArtifactPage({
  params,
}: ArtifactPageProps) {
  const { id } = await params;
  const scan = await getScanResult();

  const index = Number(id);
  const artifact = scan.artifacts[index];

  if (!artifact) {
    return (
      <div className="mx-auto max-w-[1200px] px-6 py-10">
        <p className="font-mono text-xs text-muted-foreground">
          ARTIFACT NOT FOUND
        </p>

        <Link
          href="/overview"
          className="mt-4 inline-block font-mono text-xs text-primary"
        >
          ← BACK TO OVERVIEW
        </Link>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-[1200px] px-6 py-10">
      <Link
        href="/overview"
        className="font-mono text-[9px] uppercase tracking-[0.15em] text-muted-foreground transition-colors hover:text-primary"
      >
        ← Overview
      </Link>

      <div className="mt-8">
        <p className="font-mono text-[9px] uppercase tracking-[0.2em] text-primary">
          Cryptographic artifact
        </p>

        <div className="mt-3 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <h1 className="font-display text-3xl font-semibold tracking-[-0.04em]">
            {artifact.algorithm}
          </h1>

          <RiskBadge level={artifact.quantum_risk} />
        </div>
      </div>

      <div className="mt-10 grid gap-4 md:grid-cols-2">
        <section className="rounded-lg border border-white/[0.07] bg-card p-6">
          <p className="font-mono text-[9px] uppercase tracking-[0.18em] text-muted-foreground">
            Location
          </p>

          <p className="mt-3 font-mono text-sm text-foreground">
            {artifact.file}
          </p>

          {artifact.line !== null && (
            <p className="mt-2 font-mono text-xs text-muted-foreground">
              Line {artifact.line}
            </p>
          )}
        </section>

        <section className="rounded-lg border border-white/[0.07] bg-card p-6">
          <p className="font-mono text-[9px] uppercase tracking-[0.18em] text-muted-foreground">
            Classification
          </p>

          <dl className="mt-4 space-y-3 text-sm">
            <div className="flex justify-between gap-4">
              <dt className="text-muted-foreground">Type</dt>
              <dd>{artifact.type}</dd>
            </div>

            <div className="flex justify-between gap-4">
              <dt className="text-muted-foreground">Key size</dt>
              <dd className="font-mono">
                {artifact.key_size ?? "—"}
              </dd>
            </div>

            <div className="flex justify-between gap-4">
              <dt className="text-muted-foreground">MOSCA risk</dt>
              <dd>
                {artifact.mosca_risk ?? "—"}
              </dd>
            </div>
          </dl>
        </section>
      </div>

      <section className="mt-4 rounded-lg border border-white/[0.07] bg-card p-6">
        <p className="font-mono text-[9px] uppercase tracking-[0.18em] text-muted-foreground">
          Evidence
        </p>

        <pre className="mt-4 overflow-x-auto rounded-md border border-white/[0.06] bg-black/20 p-4 font-mono text-xs leading-6 text-foreground">
          {artifact.evidence}
        </pre>
      </section>

      <section className="mt-4 rounded-lg border border-white/[0.07] bg-card p-6">
        <p className="font-mono text-[9px] uppercase tracking-[0.18em] text-muted-foreground">
          Risk assessment
        </p>

        <p className="mt-4 max-w-3xl text-sm leading-7 text-muted-foreground">
          {artifact.risk_reason}
        </p>
      </section>

      <section className="mt-4 rounded-lg border border-primary/15 bg-primary/[0.025] p-6">
        <p className="font-mono text-[9px] uppercase tracking-[0.18em] text-primary">
          Recommended action
        </p>

        <p className="mt-4 max-w-3xl text-sm leading-7 text-foreground">
          {artifact.recommendation}
        </p>
      </section>
    </div>
  );
}
