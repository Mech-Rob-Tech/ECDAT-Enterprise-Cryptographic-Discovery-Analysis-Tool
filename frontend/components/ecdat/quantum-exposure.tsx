import type { CryptoArtifact } from "@/lib/types";
import { RiskBadge } from "./risk-badge";

interface QuantumExposureProps {
  artifacts: CryptoArtifact[];
  totalArtifacts: number;
}

export function QuantumExposure({
  artifacts,
  totalArtifacts,
}: QuantumExposureProps) {
  const exposed = artifacts.filter(
    (artifact) =>
      artifact.quantum_risk === "HIGH" ||
      artifact.quantum_risk === "CRITICAL",
  );

  const percentage =
    totalArtifacts === 0
      ? 0
      : Math.round((exposed.length / totalArtifacts) * 100);

  return (
    <section className="rounded-lg border border-white/[0.07] bg-card p-6">
      <div className="flex flex-col justify-between gap-5 md:flex-row md:items-start">
        <div>
          <p className="font-mono text-[9px] uppercase tracking-[0.18em] text-muted-foreground">
            Post-quantum exposure
          </p>

          <h2 className="mt-2 font-display text-lg font-medium tracking-[-0.02em]">
            Assets requiring migration planning
          </h2>

          <p className="mt-2 max-w-xl text-sm leading-6 text-muted-foreground">
            Public-key cryptography currently exposed to quantum-relevant
            attack models.
          </p>
        </div>

        <div className="flex items-baseline gap-2 md:text-right">
          <span className="font-mono text-3xl tracking-[-0.04em] text-foreground">
            {exposed.length}
          </span>

          <span className="font-mono text-xs text-muted-foreground">
            / {totalArtifacts}
          </span>

          <span className="ml-2 font-mono text-[9px] uppercase tracking-[0.12em] text-primary">
            {percentage}%
          </span>
        </div>
      </div>

      <div className="mt-7 divide-y divide-white/[0.06]">
        {exposed.map((artifact) => (
          <div
            key={`${artifact.algorithm}-${artifact.file}-${artifact.line}`}
            className="flex flex-col gap-3 py-4 first:pt-0 last:pb-0 sm:flex-row sm:items-center sm:justify-between"
          >
            <div className="flex items-center gap-4">
              <span className="font-mono text-sm text-foreground">
                {artifact.algorithm}
              </span>

              <RiskBadge level={artifact.quantum_risk} />
            </div>

            <p className="max-w-xl text-xs text-muted-foreground">
              {artifact.risk_reason}
            </p>
          </div>
        ))}

        {exposed.length === 0 && (
          <p className="py-4 text-sm text-muted-foreground">
            No high or critical quantum-relevant assets detected.
          </p>
        )}
      </div>
    </section>
  );
}
