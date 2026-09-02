import type { ScanResult } from "./types";

const STORAGE_KEY = "ecdat_scan_result";

export function getScanResult(): Promise<ScanResult> {
  return new Promise((resolve, reject) => {
    if (typeof window === "undefined") {
      reject(new Error("Scan results are only available in the browser."));
      return;
    }

    const stored = sessionStorage.getItem(STORAGE_KEY);

    if (!stored) {
      reject(
        new Error(
          "No scan result available. Import and scan a repository first."
        )
      );
      return;
    }

    try {
      const result = JSON.parse(stored) as ScanResult;

      if (
        !result ||
        typeof result !== "object" ||
        !result.target ||
        !Array.isArray(result.artifacts)
      ) {
        throw new Error("Stored scan result is invalid.");
      }

      resolve(result);
    } catch {
      reject(
        new Error(
          "The stored scan result is invalid. Run a new repository scan."
        )
      );
    }
  });
}
