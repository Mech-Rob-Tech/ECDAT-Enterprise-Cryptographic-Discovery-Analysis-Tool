"use client";

import type { RefObject } from "react";
import {
  ChangeEvent,
  useMemo,
  useRef,
  useState,
  useEffect,
} from "react";
import { useRouter } from "next/navigation";

type SourceType = "folder" | "zip" | "github";
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

const MAX_UPLOAD_BYTES = 4_000_000;

const sourceOptions: Array<{
  value: SourceType;
  label: string;
  description: string;
}> = [
  {
    value: "folder",
    label: "Local repository",
    description: "Select a repository folder from this device.",
  },
  {
    value: "zip",
    label: "Repository ZIP",
    description: "Upload a repository archive.",
  },
  {
    value: "github",
    label: "GitHub repository",
    description: "Scan a public GitHub repository by URL.",
  },
];

const sourceIcon: Record<SourceType, string> = {
  folder: "01",
  zip: "02",
  github: "03",
};

export default function ImportPage() {
  const router = useRouter();

  const [sourceType, setSourceType] = useState<SourceType>("folder");
  const [state, setState] = useState<ScanState>("idle");
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [zipFile, setZipFile] = useState<File | null>(null);
  const [githubUrl, setGithubUrl] = useState("");
  const [githubRef, setGithubRef] = useState("main");
  const [fileName, setFileName] = useState("");
  const [errorMessage, setErrorMessage] = useState("");
  const [scanResult, setScanResult] = useState<ScanResult | null>(null);

  const folderInputRef = useRef<HTMLInputElement>(null);
  const zipInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const input = folderInputRef.current;
    if (!input) return;
    input.setAttribute("webkitdirectory", "");
    input.setAttribute("directory", "");
  }, []);

  const selectedBytes = useMemo(() => {
    if (sourceType === "zip") {
      return zipFile?.size ?? 0;
    }

    return selectedFiles.reduce((total, file) => total + file.size, 0);
  }, [selectedFiles, sourceType, zipFile]);

  const selectedSize = formatBytes(selectedBytes);
  const uploadTooLarge =
    sourceType !== "github" && selectedBytes > MAX_UPLOAD_BYTES;

  const resetState = () => {
    setState("idle");
    setErrorMessage("");
    setScanResult(null);
  };

  const handleSourceChange = (next: SourceType) => {
    if (next === sourceType) return;

    setSourceType(next);
    setSelectedFiles([]);
    setZipFile(null);
    setFileName("");
    setGithubUrl("");
    setGithubRef("main");
    resetState();
  };

  const handleFolder = (event: ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(event.target.files ?? []);

    if (!files.length) return;

    setSelectedFiles(files);
    setZipFile(null);
    setFileName(
      files.length === 1
        ? files[0].name
        : `${files.length.toLocaleString()} files selected`
    );
    setErrorMessage("");
    setState("ready");
  };

  const handleZipFile = (file: File) => {
    if (!file.name.toLowerCase().endsWith(".zip")) {
      setErrorMessage("Choose a ZIP repository archive.");
      setState("error");
      return;
    }

    setZipFile(file);
    setSelectedFiles([]);
    setSelectedFiles([]);
    setFileName(file.name);
    setErrorMessage("");
    setState("ready");
  };

  const handleZip = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) handleZipFile(file);
  };

  const handleJsonResult = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];

    if (!file) return;

    const reader = new FileReader();

    reader.onload = () => {
      try {
        const data = JSON.parse(String(reader.result)) as ScanResult;

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
        setErrorMessage("");
      } catch {
        setState("error");
        setErrorMessage(
          "The selected JSON file could not be parsed."
        );
      }
    };

    reader.readAsText(file);
  };

  const handleScan = async () => {
    if (sourceType === "github") {
      if (!githubUrl.trim()) {
        setErrorMessage("Enter a GitHub repository URL.");
        setState("error");
        return;
      }
    } else if (!selectedFiles.length && !zipFile) {
      setErrorMessage("Select a repository before starting the scan.");
      setState("error");
      return;
    }

    if (uploadTooLarge) {
      setErrorMessage(
        "This source is larger than the current 4 MB serverless upload limit. Use a smaller ZIP or scan the repository from a local ECDAT deployment."
      );
      setState("error");
      return;
    }

    setState("scanning");
    setErrorMessage("");
    setScanResult(null);

    try {
      const apiBase =
        process.env.NODE_ENV === "development"
          ? "http://localhost:8000/api"
          : "/api";

      let response: Response;

      if (sourceType === "github") {
        response = await fetch(`${apiBase}/scan`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            source_type: "github",
            repository_url: githubUrl.trim(),
            ref: githubRef.trim() || null,
          }),
        });
      } else {
        const formData = new FormData();

        formData.append("source_type", sourceType);

        if (sourceType === "zip" && zipFile) {
          formData.append("file", zipFile);
        }

        if (sourceType === "folder") {
          const paths = selectedFiles.map(
            (file) => file.webkitRelativePath || file.name
          );

          selectedFiles.forEach((file) => {
            formData.append("files", file, file.name);
          });

          formData.append("paths", JSON.stringify(paths));
        }

        response = await fetch(`${apiBase}/scan`, {
          method: "POST",
          body: formData,
        });
      }

      if (!response.ok) {
        let message = `Scan failed with status ${response.status}.`;

        try {
          const errorData = await response.json();

          if (errorData?.detail) {
            message = String(errorData.detail);
          } else if (errorData?.error) {
            message = String(errorData.error);
          }
        } catch {
          // Keep the HTTP status message.
        }

        throw new Error(message);
      }

      const data = (await response.json()) as ScanResult;

      sessionStorage.setItem(
        "ecdat_scan_result",
        JSON.stringify(data)
      );

      sessionStorage.setItem(
        "ecdat_scan_target",
        String(data.target ?? "")
      );

      setScanResult(data);
      setState("success");

      window.setTimeout(() => {
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
    state !== "scanning" &&
    (sourceType === "github"
      ? githubUrl.trim().length > 0
      : Boolean(selectedFiles.length || zipFile));

  return (
    <main className="mx-auto max-w-[1220px] px-10 py-10">
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
              Provide source code to ECDAT and run the cryptographic
              discovery pipeline against the repository you explicitly select.
            </p>
          </div>

          <div className="flex items-center gap-2 font-mono text-[9px] uppercase tracking-[0.14em] text-[var(--muted-foreground)]">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
            Scan engine available
          </div>
        </div>
      </header>

      <section className="overflow-hidden rounded-lg border border-[var(--border)] bg-[var(--card)]">
        <div className="grid lg:grid-cols-[1.1fr_0.9fr]">
          <div className="p-7 lg:p-8">
            <p className="font-mono text-[10px] uppercase tracking-[0.2em] text-[var(--primary)]">
              01 / Source
            </p>

            <h2 className="mt-3 text-xl font-medium">
              Repository source
            </h2>

            <p className="mt-2 max-w-xl text-sm leading-6 text-[var(--muted-foreground)]">
              Choose how you want to provide the repository. ECDAT only
              receives the source you explicitly select.
            </p>

            <div className="mt-7">
              <label
                htmlFor="source-type"
                className="block font-mono text-[11px] uppercase tracking-[0.18em] text-[var(--muted-foreground)]"
              >
                Source type
              </label>

              <div className="relative mt-2">
                <select
                  id="source-type"
                  value={sourceType}
                  onChange={(event) =>
                    handleSourceChange(
                      event.target.value as SourceType
                    )
                  }
                  className="w-full appearance-none rounded-md border border-[var(--input)] bg-[var(--background)] px-4 py-3 pr-10 text-sm text-[var(--foreground)] outline-none transition focus:border-[var(--primary)]"
                >
                  {sourceOptions.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>

                <span className="pointer-events-none absolute right-4 top-1/2 -translate-y-1/2 text-[var(--muted-foreground)]">
                  ▾
                </span>
              </div>
            </div>

            <div className="mt-5">
              {sourceType === "folder" && (
                <FolderSource
                  inputRef={folderInputRef}
                  onChange={handleFolder}
                  fileName={fileName}
                  fileCount={selectedFiles.length}
                  size={selectedSize}
                  onChoose={() => folderInputRef.current?.click()}
                />
              )}

              {sourceType === "zip" && (
                <ZipSource
                  inputRef={zipInputRef}
                  onChange={handleZip}
                  fileName={fileName}
                  size={selectedSize}
                  onChoose={() => zipInputRef.current?.click()}
                  onDrop={handleZipFile}
                />
              )}

              {sourceType === "github" && (
                <GithubSource
                  url={githubUrl}
                  refValue={githubRef}
                  onUrlChange={(value) => {
                    setGithubUrl(value);
                    setState(value.trim() ? "ready" : "idle");
                    setErrorMessage("");
                  }}
                  onRefChange={setGithubRef}
                />
              )}
            </div>

            {sourceType !== "github" && (
              <div className="mt-4 flex items-start gap-2">
                <span className="mt-1 h-1.5 w-1.5 shrink-0 rounded-full bg-[var(--primary)]" />

                <p className="text-[10px] leading-5 text-[var(--muted-foreground)]">
                  {uploadTooLarge
                    ? "This source exceeds the current public serverless upload limit."
                    : "Read-only analysis. Unsupported files are ignored by the ECDAT scanner."}
                </p>
              </div>
            )}

            <div className="my-7 h-px bg-[var(--border)]" />

            <p className="font-mono text-[11px] uppercase tracking-[0.18em] text-[var(--muted-foreground)]">
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
                  Open a previously generated ECDAT result without scanning again.
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
                onChange={handleJsonResult}
              />
            </label>
          </div>

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
                state={state}
              />

              <PipelineStep
                number="02"
                title="Cryptographic detection"
                text="Identify algorithms and implementations."
                state={state}
              />

              <PipelineStep
                number="03"
                title="Risk analysis"
                text="Assess quantum and cryptographic exposure."
                state={state}
              />

              <PipelineStep
                number="04"
                title="Migration intelligence"
                text="Generate recommendations from findings."
                state={state}
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
              The scan may take time on larger repositories
            </p>
          </div>
        </div>
      </section>

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

      {state !== "success" && (
        <section className="mt-5 rounded-lg border border-[var(--border)] bg-[var(--card)] px-6 py-5">
          <div className="flex items-center justify-between gap-5">
            <div>
              <p className="font-mono text-[9px] uppercase tracking-[0.16em] text-[var(--primary)]">
                Current state
              </p>

              <p className="mt-2 text-sm text-[var(--muted-foreground)]">
                {state === "idle" && "Choose a repository source."}
                {state === "ready" && "Repository source is ready for analysis."}
                {state === "scanning" && "ECDAT is analyzing the repository."}
                {state === "error" && "The scan did not complete."}
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

      <section className="mt-5 border border-[var(--border)] bg-[var(--accent)]/25 p-6">
        <div className="flex gap-4">
          <span className="mt-1 h-2 w-2 shrink-0 rounded-full bg-[var(--primary)]" />

          <div>
            <p className="font-mono text-[9px] uppercase tracking-[0.18em] text-[var(--primary)]">
              Analysis boundary
            </p>

            <p className="mt-3 max-w-4xl text-xs leading-5 text-[var(--muted-foreground)]">
              ECDAT currently performs source-code cryptographic discovery.
              Results describe the files and evidence available to the scanner;
              they are not a claim that every cryptographic dependency in an
              entire enterprise has been discovered.
            </p>
          </div>
        </div>
      </section>
    </main>
  );
}

function FolderSource({
  inputRef,
  onChange,
  fileName,
  fileCount,
  size,
  onChoose,
}: {
  inputRef: RefObject<HTMLInputElement | null>;
  onChange: (event: ChangeEvent<HTMLInputElement>) => void;
  fileName: string;
  fileCount: number;
  size: string;
  onChoose: () => void;
}) {
  return (
    <div>
      <input
        ref={inputRef}
        type="file"
        className="hidden"
        onChange={onChange}
        multiple
        onClick={(event) => {
          event.currentTarget.value = "";
        }}
      />

      <div
        role="button"
        tabIndex={0}
        onClick={onChoose}
        onKeyDown={(event) => {
          if (event.key === "Enter" || event.key === " ") {
            event.preventDefault();
            onChoose();
          }
        }}
        className="cursor-pointer rounded-md border border-dashed border-[var(--input)] bg-[var(--background)] px-6 py-8 text-center transition hover:border-[var(--primary)] hover:bg-[var(--primary)]/[0.02]"
      >
        <div className="mx-auto flex h-9 w-9 items-center justify-center rounded-full border border-[var(--border)] font-mono text-[10px] text-[var(--primary)]">
          {sourceIcon.folder}
        </div>

        <p className="mt-4 text-sm font-medium">
          Select repository folder
        </p>

        <p className="mt-1 text-xs text-[var(--muted-foreground)]">
          Choose the repository files you want ECDAT to analyze.
        </p>

        <span className="mt-5 inline-flex rounded-md border border-[var(--border)] px-4 py-2 font-mono text-[9px] uppercase tracking-[0.14em] text-[var(--primary)]">
          Choose folder
        </span>
      </div>

      {fileCount > 0 && (
        <SelectionSummary
          name={fileName}
          detail={`${fileCount.toLocaleString()} files · ${size}`}
        />
      )}
    </div>
  );
}

function ZipSource({
  inputRef,
  onChange,
  fileName,
  size,
  onChoose,
  onDrop,
}: {
  inputRef: RefObject<HTMLInputElement | null>;
  onChange: (event: ChangeEvent<HTMLInputElement>) => void;
  fileName: string;
  size: string;
  onChoose: () => void;
  onDrop: (file: File) => void;
}) {
  return (
    <div>
      <input
        ref={inputRef}
        type="file"
        accept=".zip,application/zip"
        className="hidden"
        onChange={onChange}
      />

      <div
        role="button"
        tabIndex={0}
        onClick={onChoose}
        onDragOver={(event) => event.preventDefault()}
        onDrop={(event) => {
          event.preventDefault();
          const file = event.dataTransfer.files?.[0];
          if (file) onDrop(file);
        }}
        onKeyDown={(event) => {
          if (event.key === "Enter" || event.key === " ") {
            event.preventDefault();
            onChoose();
          }
        }}
        className="cursor-pointer rounded-md border border-dashed border-[var(--input)] bg-[var(--background)] px-6 py-8 text-center transition hover:border-[var(--primary)] hover:bg-[var(--primary)]/[0.02]"
      >
        <div className="mx-auto flex h-9 w-9 items-center justify-center rounded-full border border-[var(--border)] font-mono text-[10px] text-[var(--primary)]">
          {sourceIcon.zip}
        </div>

        <p className="mt-4 text-sm font-medium">
          Upload repository ZIP
        </p>

        <p className="mt-1 text-xs text-[var(--muted-foreground)]">
          Drop a ZIP here, or choose one from your device.
        </p>

        <span className="mt-5 inline-flex rounded-md border border-[var(--border)] px-4 py-2 font-mono text-[9px] uppercase tracking-[0.14em] text-[var(--primary)]">
          Choose ZIP
        </span>
      </div>

      {zipFileNameExists(fileName) && (
        <SelectionSummary
          name={fileName}
          detail={size}
        />
      )}
    </div>
  );
}

function GithubSource({
  url,
  refValue,
  onUrlChange,
  onRefChange,
}: {
  url: string;
  refValue: string;
  onUrlChange: (value: string) => void;
  onRefChange: (value: string) => void;
}) {
  return (
    <div className="space-y-4">
      <div>
        <label
          htmlFor="github-url"
          className="block font-mono text-[11px] uppercase tracking-[0.18em] text-[var(--muted-foreground)]"
        >
          Repository URL
        </label>

        <input
          id="github-url"
          type="url"
          value={url}
          onChange={(event) => onUrlChange(event.target.value)}
          placeholder="https://github.com/owner/repository"
          className="mt-2 w-full rounded-md border border-[var(--input)] bg-[var(--background)] px-4 py-3 font-mono text-sm text-[var(--foreground)] outline-none placeholder:text-[var(--muted-foreground)] focus:border-[var(--primary)]"
        />
      </div>

      <div>
        <label
          htmlFor="github-ref"
          className="block font-mono text-[11px] uppercase tracking-[0.18em] text-[var(--muted-foreground)]"
        >
          Branch or tag
        </label>

        <input
          id="github-ref"
          type="text"
          value={refValue}
          onChange={(event) => onRefChange(event.target.value)}
          placeholder="main"
          className="mt-2 w-full rounded-md border border-[var(--input)] bg-[var(--background)] px-4 py-3 font-mono text-sm text-[var(--foreground)] outline-none placeholder:text-[var(--muted-foreground)] focus:border-[var(--primary)]"
        />
      </div>

      <p className="text-[10px] leading-5 text-[var(--muted-foreground)]">
        Public GitHub repositories are supported. Private repository
        authentication is intentionally not requested through this form.
      </p>
    </div>
  );
}

function SelectionSummary({
  name,
  detail,
}: {
  name: string;
  detail: string;
}) {
  return (
    <div className="mt-3 flex items-center justify-between gap-4 rounded-md border border-emerald-400/20 bg-emerald-400/[0.025] px-4 py-3">
      <div className="min-w-0">
        <p className="truncate font-mono text-[10px] text-emerald-300">
          ✓ {name}
        </p>
        <p className="mt-1 font-mono text-[9px] text-[var(--muted-foreground)]">
          {detail}
        </p>
      </div>
    </div>
  );
}

function PipelineStep({
  number,
  title,
  text,
  state,
  last = false,
}: {
  number: string;
  title: string;
  text: string;
  state: ScanState;
  last?: boolean;
}) {
  const index = Number(number);
  const completed = state === "success";
  const active =
    state === "scanning" && index === 1;
  const dimmed = state === "scanning" && index > 1;

  return (
    <div className="flex gap-4">
      <div className="flex flex-col items-center">
        <span
          className={`flex h-7 w-7 items-center justify-center rounded-full border font-mono text-[9px] ${
            completed
              ? "border-emerald-400/50 bg-emerald-400/[0.08] text-emerald-300"
              : active
                ? "border-[var(--primary)] bg-[var(--primary)] text-[var(--primary-foreground)]"
                : dimmed
                  ? "border-[var(--border)] text-[var(--muted-foreground)]"
                  : "border-[var(--border)] text-[var(--primary)]"
          }`}
        >
          {completed ? "✓" : number}
        </span>

        {!last && (
          <span className="mt-2 h-8 w-px bg-[var(--border)]" />
        )}
      </div>

      <div className="pb-6">
        <p className="text-sm font-medium">{title}</p>
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

      <p className="mt-3 font-mono text-2xl">{value}</p>
    </div>
  );
}

function zipFileNameExists(value: string) {
  return value.length > 0;
}

function formatBytes(bytes: number) {
  if (!bytes) return "0 B";

  const units = ["B", "KB", "MB", "GB"];
  const exponent = Math.min(
    Math.floor(Math.log(bytes) / Math.log(1024)),
    units.length - 1
  );

  return `${(bytes / 1024 ** exponent).toFixed(
    exponent === 0 ? 0 : 1
  )} ${units[exponent]}`;
}
