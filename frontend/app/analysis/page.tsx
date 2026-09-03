"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { getScanResult } from "@/lib/api";
import type { ScanResult } from "@/lib/types";

export default function AnalysisPage() {
  const [result, setResult] =
    useState<ScanResult | null>(null);

  useEffect(() => {
    getScanResult()
      .then(setResult)
      .catch(() => {
        setResult(null);
      });
  }, []);

  const artifactCount =
    result?.canonical_artifacts?.length ??
    result?.artifacts?.length ??
    0;

  const relationshipCount =
    result?.relationships?.length ?? 0;

  const moscaCount =
    result?.mosca_assessments?.length ?? 0;

  const moscaAtRisk =
    result?.mosca_assessments?.filter(
      (assessment) =>
        assessment.risk?.toUpperCase() === "CRITICAL" ||
        assessment.risk?.toUpperCase() === "HIGH"
    ).length ?? 0;

  const hasScan = Boolean(result);

  return (
    <main className="mx-auto max-w-[1220px] px-10 py-10">
      {/* Header */}
      <header className="mb-10">
        <div className="flex items-start justify-between gap-8">
          <div>
            <p className="font-mono text-[10px] uppercase tracking-[0.22em] text-[var(--primary)]">
              Analysis / Tools
            </p>

            <h1 className="mt-3 text-3xl font-semibold tracking-tight">
              Analytical Workbench
            </h1>

            <p className="mt-3 max-w-3xl text-sm leading-6 text-[var(--muted-foreground)]">
              Explore ECDAT through connected analytical
              instruments. Each tool operates on the
              current cryptographic assessment and exposes
              a different decision-making lens.
            </p>
          </div>

          <div className="hidden text-right md:block">
            <p className="font-mono text-[9px] uppercase tracking-[0.18em] text-[var(--muted-foreground)]">
              Workspace
            </p>

            <p className="mt-2 font-mono text-xs text-foreground">
              {hasScan
                ? "LIVE SCAN"
                : "AWAITING SCAN"}
            </p>
          </div>
        </div>
      </header>

      {/* Tool cards */}
      <section
        aria-label="Analysis tools"
        className="grid gap-5 lg:grid-cols-2"
      >
        {/* Cryptographic Topology */}
        <Link
          href="/topology"
          className="group block"
        >
          <article className="relative h-full overflow-hidden rounded-2xl border border-white/[0.08] bg-[#111925] p-7 shadow-[0_18px_60px_rgba(0,0,0,0.24)] transition-all duration-200 hover:-translate-y-0.5 hover:border-primary/35 hover:shadow-[0_24px_70px_rgba(0,0,0,0.32)]">
            <div
              className="pointer-events-none absolute right-0 top-0 h-40 w-40 rounded-full bg-primary/[0.045] blur-3xl"
              aria-hidden="true"
            />

            <div className="relative">
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  <span className="flex h-10 w-10 items-center justify-center rounded-xl border border-primary/25 bg-primary/[0.06] font-mono text-sm text-primary">
                    ◈
                  </span>

                  <div>
                    <p className="font-mono text-[9px] uppercase tracking-[0.18em] text-primary">
                      Analytical Tool 01
                    </p>

                    <h2 className="mt-1 text-xl font-semibold tracking-tight text-foreground">
                      Cryptographic Topology
                    </h2>
                  </div>
                </div>

                <span className="rounded-full border border-emerald-400/20 bg-emerald-400/[0.04] px-2.5 py-1 font-mono text-[8px] uppercase tracking-[0.14em] text-emerald-300">
                  Live
                </span>
              </div>

              <div className="mt-7">
                <p className="font-mono text-[9px] uppercase tracking-[0.18em] text-[#d8a900]">
                  Evidence-linked analytical graph
                </p>

                <p className="mt-3 max-w-xl text-sm leading-6 text-white/55">
                  Trace cryptographic artifacts from
                  source evidence through risk, MOSCA,
                  recommendations, migration candidates
                  and verification.
                </p>
              </div>

              <div className="mt-7 grid grid-cols-2 border-y border-white/[0.06]">
                <div className="border-r border-white/[0.06] py-4 pr-5">
                  <p className="font-mono text-[8px] uppercase tracking-[0.16em] text-white/30">
                    Artifacts
                  </p>

                  <p className="mt-2 font-mono text-lg text-white">
                    {artifactCount}
                  </p>
                </div>

                <div className="py-4 pl-5">
                  <p className="font-mono text-[8px] uppercase tracking-[0.16em] text-white/30">
                    Relationships
                  </p>

                  <p className="mt-2 font-mono text-lg text-white">
                    {relationshipCount}
                  </p>
                </div>
              </div>

              <div className="mt-6 flex items-center justify-between">
                <span className="font-mono text-[9px] uppercase tracking-[0.16em] text-white/35">
                  Select an artifact to investigate
                </span>

                <span className="font-mono text-[10px] font-semibold uppercase tracking-[0.14em] text-primary transition-transform duration-200 group-hover:translate-x-1">
                  Open Tool →
                </span>
              </div>
            </div>
          </article>
        </Link>

        {/* MOSCA Analysis */}
        <Link
          href="/mosca"
          className="group block"
        >
          <article className="relative h-full overflow-hidden rounded-2xl border border-white/[0.08] bg-[#111925] p-7 shadow-[0_18px_60px_rgba(0,0,0,0.24)] transition-all duration-200 hover:-translate-y-0.5 hover:border-violet-400/30 hover:shadow-[0_24px_70px_rgba(0,0,0,0.32)]">
            <div
              className="pointer-events-none absolute right-0 top-0 h-40 w-40 rounded-full bg-violet-400/[0.045] blur-3xl"
              aria-hidden="true"
            />

            <div className="relative">
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  <span className="flex h-10 w-10 items-center justify-center rounded-xl border border-violet-400/20 bg-violet-400/[0.05] font-mono text-sm text-violet-300">
                    ◇
                  </span>

                  <div>
                    <p className="font-mono text-[9px] uppercase tracking-[0.18em] text-violet-300/80">
                      Analytical Tool 02
                    </p>

                    <h2 className="mt-1 text-xl font-semibold tracking-tight text-foreground">
                      MOSCA Analysis
                    </h2>
                  </div>
                </div>

                <span className="rounded-full border border-violet-400/20 bg-violet-400/[0.04] px-2.5 py-1 font-mono text-[8px] uppercase tracking-[0.14em] text-violet-300">
                  Active
                </span>
              </div>

              <div className="mt-7">
                <p className="font-mono text-[9px] uppercase tracking-[0.18em] text-violet-300/80">
                  Migration timing analysis
                </p>

                <p className="mt-3 max-w-xl text-sm leading-6 text-white/55">
                  Evaluate whether data lifetime and
                  migration time fit within the assumed
                  quantum planning horizon, with the
                  assessment linked back to discovered
                  assets.
                </p>
              </div>

              <div className="mt-7 grid grid-cols-2 border-y border-white/[0.06]">
                <div className="border-r border-white/[0.06] py-4 pr-5">
                  <p className="font-mono text-[8px] uppercase tracking-[0.16em] text-white/30">
                    Assessments
                  </p>

                  <p className="mt-2 font-mono text-lg text-white">
                    {moscaCount}
                  </p>
                </div>

                <div className="py-4 pl-5">
                  <p className="font-mono text-[8px] uppercase tracking-[0.16em] text-white/30">
                    At risk
                  </p>

                  <p className="mt-2 font-mono text-lg text-white">
                    {moscaAtRisk}
                  </p>
                </div>
              </div>

              <div className="mt-6 flex items-center justify-between">
                <span className="font-mono text-[9px] uppercase tracking-[0.16em] text-white/35">
                  Analyze migration timing
                </span>

                <span className="font-mono text-[10px] font-semibold uppercase tracking-[0.14em] text-violet-300 transition-transform duration-200 group-hover:translate-x-1">
                  Open Tool →
                </span>
              </div>
            </div>
          </article>
        </Link>
      </section>

      {/* Analytical model note */}
      <section className="mt-6 rounded-xl border border-white/[0.07] bg-white/[0.015] px-6 py-5">
        <div className="flex gap-4">
          <span
            className="mt-1 h-1.5 w-1.5 shrink-0 rounded-full bg-primary"
            aria-hidden="true"
          />

          <div>
            <p className="font-mono text-[9px] uppercase tracking-[0.18em] text-primary">
              Analytical model
            </p>

            <p className="mt-2 max-w-4xl text-xs leading-5 text-white/45">
              These tools operate on the same ECDAT
              assessment model rather than maintaining
              separate findings. The topology exposes
              relationships visually, while MOSCA provides
              migration-timing analysis over the same
              discovered cryptographic assets.
            </p>
          </div>
        </div>
      </section>
    </main>
  );
}
