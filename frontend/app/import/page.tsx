"use client";

import { ChangeEvent, useState } from "react";
import { useRouter } from "next/navigation";

type ScanState = "idle" | "ready" | "scanning" | "success" | "error";

type ScanResult = {
  target: string;
  generated_at?: string;
  prototype_scope?: string;
  total_files_scanned: number;
  total_artifacts: number;
  quantum_vulnerable_assets: number;
  risk_summary?: {
    critical: number;
    high: number;
    medium: number;
    low: number;
  };
  artifacts?: unknown[];
};

export default function ImportPage() {
  const router = useRouter();

  const [state, setState] = useState<ScanState>("idle");
  const [repository, setRepository] = useState("");
  const [fileName, setFileName] = useState("");
  const [errorMessage, setErrorMessage] = useState("");
  const [scanResult, setScanResult] = useState<ScanResult | null>(null);

  const handleFile = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];

    if (!file) return;

    setFileName(file.name);
    setErrorMessage("");

    if (file.type === "application/json" || file.name.endsWith(".json")) {
      const reader = new FileReader();

      reader.onload = () => {
        try {
          const data = JSON.parse(String(reader.result));

          sessionStorage.setItem(
            "ecdat_scan_result",
            JSON.stringify(data)
          );

          if (data.target) {
            sessionStorage.setItem(
              "ecdat_scan_target",
              String(data.target)
            );
          }

          setScanResult(data);
          setState("success");
        } catch {
          setState("error");
          setErrorMessage(
            "The selected JSON file could not be parsed."
          );
        }
      };

      reader.readAsText(file);
    }
  };

  const handleScan = async () => {
    const target = repository.trim();

    if (!target) return;

    setState("scanning");
    setErrorMessage("");
    setScanResult(null);

    try {
      const response = await fetch(
        "http://localhost:8000/scan",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            repository: target,
          }),
        }
      );

      if (!response.ok) {
        let message = `Scan failed with status ${response.status}.`;

        try {
          const errorData = await response.json();

          if (errorData?.detail) {
            message = String(errorData.detail);
          }
        } catch {
          // Keep default error message.
        }

        throw new Error(message);
      }

      const data: ScanResult = await response.json();

      sessionStorage.setItem(
        "ecdat_scan_result",
        JSON.stringify(data)
      );

      sessionStorage.setItem(
        "ecdat_scan_target",
        target
      );

      setScanResult(data);
      setState("success");

      setTimeout(() => {
        router.push("/overview");
      }, 700);
    } catch (error) {
      console.error("ECDAT scan failed:", error);

      setState("error");

      setErrorMessage(
        error instanceof Error
          ? error.message
          : "Unable to connect to the ECDAT scan service."
      );
    }
  };

  const canScan =
    repository.trim().length > 0 &&
    state !== "scanning";

  return (
    <main className="mx-auto max-w-[1220px] px-10 py-10">
      {/* HEADER */}

      <header className="mb-9">
        <p className="font-mono text-[10px] uppercase tracking-[0.22em] text-[var(--primary)]">
          Discover / Import
        </p>

        <div className="mt-3 flex flex-col justify-between gap-5 lg:flex-row lg:items-end">
          <div>
            <h1 className="text-3xl font-semibold tracking-tight">
              Scan a repository
            </h1>

            <p className="mt-3 max-w-2xl text-sm leading-6 text-[var(--muted-foreground)]">
              Connect ECDAT to a source repository and run the
              cryptographic discovery pipeline against its actual
              source files.
            </p>
          </div>

          <div className="flex items-center gap-2 font-mono text-[9px] uppercase tracking-[0.14em] text-[var(--muted-foreground)]">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
            Scan engine available
          </div>
        </div>
      </header>

      {/* MAIN IMPORT PANEL */}

      <section className="overflow-hidden rounded-lg border border-[var(--border)] bg-[var(--card)]">
        <div className="grid lg:grid-cols-[1.1fr_0.9fr]">
          {/* SOURCE */}

          <div className="p-7 lg:p-8">
            <p className="font-mono text-[10px] uppercase tracking-[0.2em] text-[var(--primary)]">
              01 / Source
            </p>

            <h2 className="mt-3 text-xl font-medium">
              Repository source
            </h2>

            <p className="mt-2 max-w-xl text-sm leading-6 text-[var(--muted-foreground)]">
              Enter the local filesystem path that the ECDAT backend
              should analyze.
            </p>

            <label
              htmlFor="repository"
              className="mt-7 block font-mono text-[9px] uppercase tracking-[0.18em] text-[var(--muted-foreground)]"
            >
              Repository path
            </label>

            <div className="mt-2 flex items-center rounded-md border border-[var(--input)] bg-[var(--background)] transition focus-within:border-[var(--primary)]">
              <span className="pl-4 font-mono text-sm text-[var(--primary)]">
                $
              </span>

              <input
                id="repository"
                type="text"
                value={repository}
                onChange={(event) => {
                  setRepository(event.target.value);
                  setState("idle");
                  setErrorMessage("");
                }}
                onKeyDown={(event) => {
                  if (event.key === "Enter" && canScan) {
                    handleScan();
                  }
                }}
                placeholder="/path/to/repository"
                className="w-full bg-transparent px-3 py-3 font-mono text-sm text-[var(--foreground)] outline-none placeholder:text-[var(--muted-foreground)]"
              />
            </div>

            <div className="mt-3 flex items-start gap-2">
              <span className="mt-1 h-1.5 w-1.5 shrink-0 rounded-full bg-[var(--primary)]" />

              <p className="text-[10px] leading-5 text-[var(--muted-foreground)]">
                The path must be accessible to the machine running
                the ECDAT backend.
              </p>
            </div>

            {/* JSON IMPORT */}

            <div className="my-7 h-px bg-[var(--border)]" />

            <p className="font-mono text-[9px] uppercase tracking-[0.18em] text-[var(--muted-foreground)]">
              Existing result
            </p>

            <label
              htmlFor="file-upload"
              className="mt-3 flex cursor-pointer items-center justify-between gap-5 rounded-md border border-dashed border-[var(--input)] bg-[var(--background)] px-5 py-4 transition hover:border-[var(--primary)]"
            >
              <div className="min-w-0">
                <p className="text-sm font-medium">
                  Load JSON scan result
                </p>

                <p className="mt-1 text-xs text-[var(--muted-foreground)]">
                  Use a previously generated ECDAT result.
                </p>
              </div>

              <span className="shrink-0 font-mono text-[9px] uppercase tracking-[0.15em] text-[var(--primary)]">
                Choose file
              </span>

              <input
                id="file-upload"
                type="file"
                accept=".json,application/json"
                className="hidden"
                onChange={handleFile}
              />
            </label>

            {fileName && (
              <div className="mt-3 flex items-center gap-2">
                <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />

                <p className="font-mono text-[9px] text-[var(--muted-foreground)]">
                  Loaded: {fileName}
                </p>
              </div>
            )}
          </div>

          {/* PIPELINE */}

          <div className="border-t border-[var(--border)] bg-[var(--background)]/30 p-7 lg:border-l lg:border-t-0 lg:p-8">
            <p className="font-mono text-[10px] uppercase tracking-[0.2em] text-[var(--primary)]">
              02 / Pipeline
            </p>

            <h2 className="mt-3 text-xl font-medium">
              Cryptographic discovery
            </h2>

            <div className="mt-7">
              <PipelineStep
                number="01"
                title="Source discovery"
                text="Traverse supported source files."
                active={state === "scanning"}
              />

              <PipelineStep
                number="02"
                title="Cryptographic detection"
                text="Identify algorithms and implementations."
                active={state === "scanning"}
              />

              <PipelineStep
                number="03"
                title="Risk analysis"
                text="Assess quantum and cryptographic exposure."
                active={state === "scanning"}
              />

              <PipelineStep
                number="04"
                title="Migration intelligence"
                text="Generate recommendations from findings."
                active={state === "scanning"}
                last
              />
            </div>

            <button
              type="button"
              onClick={handleScan}
              disabled={!canScan}
              className="mt-8 w-full rounded-md bg-[var(--primary)] px-5 py-3.5 font-mono text-[10px] font-semibold uppercase tracking-[0.18em] text-[var(--primary-foreground)] transition hover:brightness-105 disabled:cursor-not-allowed disabled:opacity-40"
            >
              {state === "scanning"
                ? "Running discovery..."
                : "Start cryptographic scan →"}
            </button>

            <p className="mt-3 text-center font-mono text-[8px] uppercase tracking-[0.12em] text-[var(--muted-foreground)]">
              Enter path + press Enter also works
            </p>
          </div>
        </div>
      </section>

      {/* SCAN ERROR */}

      {state === "error" && (
        <section className="mt-5 rounded-lg border border-red-400/25 bg-red-400/[0.03] px-6 py-5">
          <div className="flex gap-3">
            <span className="mt-1 h-2 w-2 shrink-0 rounded-full bg-red-400" />

            <div>
              <p className="font-mono text-[9px] uppercase tracking-[0.16em] text-red-400">
                Scan error
              </p>

              <p className="mt-2 text-sm leading-6 text-[var(--muted-foreground)]">
                {errorMessage}
              </p>
            </div>
          </div>
        </section>
      )}

      {/* SUCCESS */}

      {state === "success" && scanResult && (
        <section className="mt-5 rounded-lg border border-emerald-400/25 bg-emerald-400/[0.025]">
          <div className="border-b border-[var(--border)] px-6 py-5">
            <div className="flex items-center gap-3">
              <span className="h-2 w-2 rounded-full bg-emerald-400" />

              <p className="font-mono text-[9px] uppercase tracking-[0.18em] text-emerald-400">
                Scan complete
              </p>
            </div>

            <p className="mt-3 text-sm text-[var(--muted-foreground)]">
              Analysis completed successfully. Opening the overview.
            </p>
          </div>

          <div className="grid gap-px bg-[var(--border)] sm:grid-cols-3">
            <ResultMetric
              label="Files scanned"
              value={scanResult.total_files_scanned}
            />

            <ResultMetric
              label="Artifacts"
              value={scanResult.total_artifacts}
            />

            <ResultMetric
              label="Quantum exposed"
              value={scanResult.quantum_vulnerable_assets}
            />
          </div>
        </section>
      )}

      {/* STATE */}

      {state !== "success" && (
        <section className="mt-5 rounded-lg border border-[var(--border)] bg-[var(--card)] px-6 py-5">
          <div className="flex items-center justify-between gap-5">
            <div>
              <p className="font-mono text-[9px] uppercase tracking-[0.16em] text-[var(--primary)]">
                Current state
              </p>

              <p className="mt-2 text-sm text-[var(--muted-foreground)]">
                {state === "idle" &&
                  "Awaiting a repository path."}

                {state === "ready" &&
                  "Repository source is ready for analysis."}

                {state === "scanning" &&
                  "ECDAT is analyzing the repository."}

                {state === "error" &&
                  "The scan did not complete."}
              </p>
            </div>

            <span
              className={`font-mono text-[9px] uppercase tracking-[0.15em] ${
                state === "error"
                  ? "text-red-400"
                  : state === "scanning"
                    ? "text-[var(--primary)]"
                    : "text-[var(--muted-foreground)]"
              }`}
            >
              {state}
            </span>
          </div>
        </section>
      )}

      {/* SCOPE */}

      <section className="mt-5 border border-[var(--border)] bg-[var(--accent)]/25 p-6">
        <div className="flex gap-4">
          <span className="mt-1 h-2 w-2 shrink-0 rounded-full bg-[var(--primary)]" />

          <div>
            <p className="font-mono text-[9px] uppercase tracking-[0.18em] text-[var(--primary)]">
              Prototype scope
            </p>

            <p className="mt-3 max-w-4xl text-xs leading-5 text-[var(--muted-foreground)]">
              ECDAT currently performs source-code cryptographic
              discovery. The scan result is generated by the backend
              analysis engine and passed directly into the dashboard
              for subsequent assessment views.
            </p>
          </div>
        </div>
      </section>
    </main>
  );
}

function PipelineStep({
  number,
  title,
  text,
  active,
  last = false,
}: {
  number: string;
  title: string;
  text: string;
  active: boolean;
  last?: boolean;
}) {
  return (
    <div className="flex gap-4">
      <div className="flex flex-col items-center">
        <span
          className={`flex h-7 w-7 items-center justify-center rounded-full border font-mono text-[9px] ${
            active
              ? "border-[var(--primary)] bg-[var(--primary)] text-[var(--primary-foreground)]"
              : "border-[var(--border)] text-[var(--primary)]"
          }`}
        >
          {number}
        </span>

        {!last && (
          <span className="mt-2 h-8 w-px bg-[var(--border)]" />
        )}
      </div>

      <div className="pb-6">
        <p className="text-sm font-medium">
          {title}
        </p>

        <p className="mt-1 text-xs leading-5 text-[var(--muted-foreground)]">
          {text}
        </p>
      </div>
    </div>
  );
}

function ResultMetric({
  label,
  value,
}: {
  label: string;
  value: number;
}) {
  return (
    <div className="bg-[var(--card)] px-6 py-5">
      <p className="font-mono text-[8px] uppercase tracking-[0.14em] text-[var(--muted-foreground)]">
        {label}
      </p>

      <p className="mt-3 font-mono text-2xl">
        {value}
      </p>
    </div>
  );
}
