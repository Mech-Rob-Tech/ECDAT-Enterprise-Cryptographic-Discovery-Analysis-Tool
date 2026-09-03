"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

type BusinessCriticality = "Low" | "Medium" | "High" | "Critical";

type ScanResult = {
  target?: string;
  mosca_inputs?: {
    data_lifetime?: number;
    migration_time?: number;
    quantum_horizon?: number;
    business_criticality?: BusinessCriticality;
  };
};

function getUrgency(
  total: number,
  horizon: number,
  criticality: BusinessCriticality
) {
  const atRisk = total > horizon;

  if (!atRisk) {
    return {
      status: "WITHIN HORIZON",
      level: "LOW",
      description:
        "The combined confidentiality lifetime and migration time remain within the assumed quantum-threat horizon.",
    };
  }

  if (criticality === "Critical") {
    return {
      status: "AT RISK",
      level: "CRITICAL",
      description:
        "The protected information may still require confidentiality after the assumed quantum horizon. Migration planning should begin now.",
    };
  }

  if (criticality === "High") {
    return {
      status: "AT RISK",
      level: "HIGH",
      description:
        "The combined protection lifetime and migration time exceed the assumed quantum horizon. Migration planning should be prioritized.",
    };
  }

  if (criticality === "Medium") {
    return {
      status: "AT RISK",
      level: "MEDIUM",
      description:
        "The combined protection lifetime and migration time exceed the assumed quantum horizon. Migration planning should be scheduled.",
    };
  }

  return {
    status: "AT RISK",
    level: "MEDIUM",
    description:
      "The combined protection lifetime and migration time exceed the assumed quantum horizon. Migration planning should be considered.",
  };
}

function riskClasses(level: string) {
  switch (level) {
    case "CRITICAL":
      return "border-red-400/30 bg-red-400/[0.04] text-red-400";

    case "HIGH":
      return "border-amber-400/30 bg-amber-400/[0.04] text-amber-400";

    case "MEDIUM":
      return "border-yellow-400/30 bg-yellow-400/[0.04] text-yellow-300";

    default:
      return "border-emerald-400/30 bg-emerald-400/[0.04] text-emerald-400";
  }
}

export default function MoscaPage() {
  const router = useRouter();
  const [scanResult, setScanResult] = useState<ScanResult | null>(null);

  const [dataLifetime, setDataLifetime] = useState(12);
  const [migrationTime, setMigrationTime] = useState(4);
  const [quantumHorizon, setQuantumHorizon] = useState(10);
  const [businessCriticality, setBusinessCriticality] =
    useState<BusinessCriticality>("Critical");

  useEffect(() => {
    const stored = sessionStorage.getItem("ecdat_scan_result");

    if (!stored) {
      router.replace("/import");
      return;
    }

    try {
      const data: ScanResult = JSON.parse(stored);

      setScanResult(data);

      const inputs = data.mosca_inputs;

      if (!inputs) {
        return;
      }

      if (typeof inputs.data_lifetime === "number") {
        setDataLifetime(inputs.data_lifetime);
      }

      if (typeof inputs.migration_time === "number") {
        setMigrationTime(inputs.migration_time);
      }

      if (typeof inputs.quantum_horizon === "number") {
        setQuantumHorizon(inputs.quantum_horizon);
      }

      if (
        inputs.business_criticality === "Low" ||
        inputs.business_criticality === "Medium" ||
        inputs.business_criticality === "High" ||
        inputs.business_criticality === "Critical"
      ) {
        setBusinessCriticality(inputs.business_criticality);
      }
    } catch {
      router.replace("/import");
    }
  }, [router]);

  const total = dataLifetime + migrationTime;

  const urgency = getUrgency(
    total,
    quantumHorizon,
    businessCriticality
  );

  return (
    <main className="mx-auto max-w-[1220px] px-10 py-10">
      {/* HEADER */}

      <header className="mb-9">
        {/* Back to Analysis */}
        <Link
          href="/analysis"
          aria-label="Back to Analysis"
          className="
            group
            inline-flex
            h-9
            items-center
            gap-2
            rounded-lg
            px-2.5
            font-mono
            text-[10px]
            font-bold
            uppercase
            tracking-[0.12em]
            text-white/65
            transition-all
            duration-150
            ease-out
            hover:bg-white/[0.08]
            hover:text-white
            active:scale-[0.97]
            active:duration-100
            focus-visible:outline-none
            focus-visible:ring-2
            focus-visible:ring-[#f4c430]/60
            focus-visible:ring-offset-2
            focus-visible:ring-offset-[#0d141f]
          "
        >
          <span
            aria-hidden="true"
            className="
              flex
              h-5
              w-5
              items-center
              justify-center
              text-[15px]
              font-bold
              leading-none
              text-white/50
              transition-all
              duration-150
              ease-out
              group-hover:-translate-x-0.5
              group-hover:text-[#f4c430]
            "
          >
            ←
          </span>

          <span>Back to Analysis</span>
        </Link>

        <div className="mt-5 flex items-start justify-between gap-8">
          <div>
            <p className="font-mono text-[10px] uppercase tracking-[0.22em] text-[var(--primary)]">
              Assess / MOSCA Analysis
            </p>

            <h1 className="mt-3 text-3xl font-semibold tracking-tight">
              Migration risk assessment
            </h1>

            <p className="mt-3 max-w-3xl text-sm leading-6 text-[var(--muted-foreground)]">
              Evaluate whether the confidentiality lifetime of protected
              information and the estimated migration effort extend beyond
              the assumed quantum-threat horizon.
            </p>
          </div>

          <div className="text-right">
            <p className="font-mono text-[9px] uppercase tracking-[0.18em] text-[var(--muted-foreground)]">
              Target
            </p>

            <p className="mt-2 font-mono text-xs text-[var(--foreground)]">
              {scanResult?.target
                ? scanResult.target.split("/").pop()
                : "No scan loaded"}
            </p>
          </div>
        </div>
      </header>

      {/* CALCULATOR */}

      <section className="grid gap-5 lg:grid-cols-[1fr_0.9fr]">
        <div className="rounded-lg border border-[var(--border)] bg-[var(--card)]">
          <div className="border-b border-[var(--border)] px-6 py-5">
            <p className="font-mono text-[9px] uppercase tracking-[0.18em] text-[var(--primary)]">
              MOSCA model
            </p>

            <h2 className="mt-2 text-lg font-medium">
              Planning inputs
            </h2>
          </div>

          <div className="space-y-6 p-6">
            {/* X */}

            <div>
              <div className="flex items-center justify-between">
                <label className="font-mono text-xs uppercase tracking-[0.08em]">
                  Data confidentiality lifetime
                </label>

                <span className="font-mono text-sm text-[var(--primary)]">
                  X = {dataLifetime} years
                </span>
              </div>

              <input
                type="range"
                min="0"
                max="50"
                value={dataLifetime}
                onChange={(event) =>
                  setDataLifetime(Number(event.target.value))
                }
                className="mt-4 w-full accent-[var(--primary)]"
              />

              <p className="mt-2 text-xs text-[var(--muted-foreground)]">
                Required confidentiality lifetime of the protected data.
              </p>
            </div>

            {/* Y */}

            <div>
              <div className="flex items-center justify-between">
                <label className="font-mono text-xs uppercase tracking-[0.08em]">
                  Estimated migration time
                </label>

                <span className="font-mono text-sm text-[var(--primary)]">
                  Y = {migrationTime} years
                </span>
              </div>

              <input
                type="range"
                min="0"
                max="30"
                value={migrationTime}
                onChange={(event) =>
                  setMigrationTime(Number(event.target.value))
                }
                className="mt-4 w-full accent-[var(--primary)]"
              />

              <p className="mt-2 text-xs text-[var(--muted-foreground)]">
                Estimated time required to migrate the system.
              </p>
            </div>

            {/* Z */}

            <div>
              <div className="flex items-center justify-between">
                <label className="font-mono text-xs uppercase tracking-[0.08em]">
                  Assumed quantum horizon
                </label>

                <span className="font-mono text-sm text-[var(--primary)]">
                  Z = {quantumHorizon} years
                </span>
              </div>

              <input
                type="range"
                min="1"
                max="50"
                value={quantumHorizon}
                onChange={(event) =>
                  setQuantumHorizon(Number(event.target.value))
                }
                className="mt-4 w-full accent-[var(--primary)]"
              />

              <p className="mt-2 text-xs text-[var(--muted-foreground)]">
                Planning assumption for the arrival of a
                cryptographically relevant quantum threat.
              </p>
            </div>

            {/* CRITICALITY */}

            <div>
              <label className="font-mono text-xs uppercase tracking-[0.08em]">
                Business criticality
              </label>

              <div className="mt-3 grid grid-cols-4 gap-2">
                {(
                  [
                    "Low",
                    "Medium",
                    "High",
                    "Critical",
                  ] as BusinessCriticality[]
                ).map((level) => {
                  const selected =
                    businessCriticality === level;

                  return (
                    <button
                      key={level}
                      type="button"
                      onClick={() =>
                        setBusinessCriticality(level)
                      }
                      className={`border px-3 py-2 font-mono text-[9px] uppercase tracking-[0.12em] transition ${
                        selected
                          ? "border-[var(--primary)] bg-[var(--primary)]/[0.08] text-[var(--primary)]"
                          : "border-[var(--border)] text-[var(--muted-foreground)] hover:border-[var(--primary)]/40 hover:text-[var(--foreground)]"
                      }`}
                    >
                      {level}
                    </button>
                  );
                })}
              </div>
            </div>
          </div>
        </div>

        {/* RESULT */}

        <div
          className={`rounded-lg border p-6 ${riskClasses(
            urgency.level
          )}`}
        >
          <p className="font-mono text-[9px] uppercase tracking-[0.18em]">
            Assessment result
          </p>

          <div className="mt-7">
            <p className="font-mono text-[10px] uppercase tracking-[0.16em] opacity-70">
              Migration status
            </p>

            <h2 className="mt-3 text-3xl font-semibold">
              {urgency.status}
            </h2>

            <div className="mt-5 inline-flex rounded-full border px-3 py-1 font-mono text-[9px] uppercase tracking-[0.14em]">
              {urgency.level}
            </div>
          </div>

          {/* EQUATION */}

          <div className="mt-10 border-y border-current/10 py-7">
            <p className="font-mono text-[9px] uppercase tracking-[0.18em] opacity-60">
              MOSCA calculation
            </p>

            <div className="mt-5 flex items-center gap-3 font-mono text-lg">
              <span>{dataLifetime}</span>
              <span className="opacity-50">+</span>
              <span>{migrationTime}</span>
              <span className="opacity-50">=</span>
              <span className="text-xl font-semibold">
                {total}
              </span>
            </div>

            <div className="mt-4 font-mono text-sm">
              <span>{total}</span>

              <span className="mx-2 opacity-50">
                {total > quantumHorizon ? ">" : "≤"}
              </span>

              <span>{quantumHorizon}</span>
            </div>
          </div>

          <p className="mt-6 text-sm leading-6 opacity-80">
            {urgency.description}
          </p>
        </div>
      </section>

      {/* EXPLANATION */}

      <section className="mt-5 rounded-lg border border-[var(--border)] bg-[var(--card)] p-6">
        <div className="grid gap-8 lg:grid-cols-3">
          <Definition
            symbol="X"
            title="Confidentiality lifetime"
            description="How long the protected information is expected to require confidentiality."
          />

          <Definition
            symbol="Y"
            title="Migration time"
            description="How long the organization estimates it will take to migrate the system."
          />

          <Definition
            symbol="Z"
            title="Quantum horizon"
            description="A planning assumption for when a cryptographically relevant quantum threat may become available."
          />
        </div>
      </section>

      {/* IMPORTANT NOTE */}

      <section className="mt-5 border border-[var(--border)] bg-[var(--accent)]/30 p-6">
        <div className="flex gap-4">
          <span className="mt-1 h-2 w-2 shrink-0 rounded-full bg-[var(--primary)]" />

          <div>
            <p className="font-mono text-[9px] uppercase tracking-[0.18em] text-[var(--primary)]">
              Planning assumption
            </p>

            <p className="mt-3 max-w-4xl text-sm leading-6 text-[var(--muted-foreground)]">
              The quantum horizon used by this calculator is a planning
              assumption, not a prediction of the exact arrival date of a
              cryptographically relevant quantum computer. The calculation
              is intended to support migration prioritization.
            </p>
          </div>
        </div>
      </section>
    </main>
  );
}

function Definition({
  symbol,
  title,
  description,
}: {
  symbol: string;
  title: string;
  description: string;
}) {
  return (
    <div>
      <div className="flex items-center gap-3">
        <span className="font-mono text-lg text-[var(--primary)]">
          {symbol}
        </span>

        <h3 className="text-sm font-medium">
          {title}
        </h3>
      </div>

      <p className="mt-3 text-xs leading-5 text-[var(--muted-foreground)]">
        {description}
      </p>
    </div>
  );
}
