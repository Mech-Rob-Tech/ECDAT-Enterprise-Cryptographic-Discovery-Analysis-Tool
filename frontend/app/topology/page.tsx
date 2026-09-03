"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import { CryptographicTopology } from "@/components/ecdat/cryptographic-topology";
import { getScanResult } from "@/lib/api";
import type { ScanResult } from "@/lib/types";

export default function TopologyPage() {
  const router = useRouter();

  const [scan, setScan] = useState<ScanResult | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let mounted = true;

    getScanResult()
      .then((result) => {
        if (!mounted) {
          return;
        }

        if (!result) {
          router.replace("/import");
          return;
        }

        setScan(result);
      })
      .catch(() => {
        if (mounted) {
          router.replace("/import");
        }
      })
      .finally(() => {
        if (mounted) {
          setLoading(false);
        }
      });

    return () => {
      mounted = false;
    };
  }, [router]);

  if (loading) {
    return (
      <main className="ecdat-page !w-full !max-w-none px-4 sm:px-6 lg:px-8">
        <section className="flex min-h-[calc(100dvh-7rem)] flex-col">
          <div className="mb-5">
            <Link
              href="/analysis"
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
                  text-[15px]
                  font-bold
                  leading-none
                  text-white/50
                  transition-transform
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

            <div className="mt-5 text-[11px] font-semibold uppercase tracking-[0.2em] text-[#f4c430]">
              ANALYZE
            </div>

            <h1 className="mt-2 text-2xl font-semibold tracking-tight text-white sm:text-3xl">
              Cryptographic Topology
            </h1>

            <p className="mt-2 max-w-3xl text-sm leading-6 text-white/40">
              Loading the canonical cryptographic graph…
            </p>
          </div>

          <div className="flex min-h-0 flex-1 items-center justify-center rounded-2xl border border-white/[0.08] bg-[#0d141f]">
            <div className="text-center">
              <div className="mx-auto h-8 w-8 animate-spin rounded-full border-2 border-white/10 border-t-[#f4c430]" />

              <p className="mt-4 text-sm text-white/45">
                Loading scan data
              </p>
            </div>
          </div>
        </section>
      </main>
    );
  }

  if (!scan) {
    return null;
  }

  return (
    <main className="ecdat-page !w-full !max-w-none px-4 sm:px-6 lg:px-8">
      <section className="flex min-h-[calc(100dvh-7rem)] flex-col">
        <header className="mb-4 shrink-0">
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

          <div className="mt-5 flex flex-col gap-2 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <div className="text-[11px] font-semibold uppercase tracking-[0.2em] text-[#f4c430]">
                ANALYZE
              </div>

              <h1 className="mt-1.5 text-2xl font-semibold tracking-tight text-white sm:text-3xl">
                Cryptographic Topology
              </h1>

              <p className="mt-2 max-w-4xl text-sm leading-5 text-white/45">
                Explore the relationships connecting applications,
                components, cryptographic artifacts, source evidence,
                risk assessments, migration options, and verification
                state.
              </p>
            </div>

            <div className="hidden shrink-0 text-right lg:block">
              <div className="text-[10px] font-semibold uppercase tracking-[0.18em] text-white/30">
                Evidence-linked analysis
              </div>

              <div className="mt-1 text-xs text-white/40">
                Discovery → Risk → MOSCA → Migration → Verification
              </div>
            </div>
          </div>
        </header>

        <div className="min-h-0 flex-1">
          <CryptographicTopology scan={scan} />
        </div>
      </section>
    </main>
  );
}
