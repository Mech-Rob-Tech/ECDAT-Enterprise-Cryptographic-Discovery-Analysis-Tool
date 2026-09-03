"use client";

import { usePathname } from "next/navigation";

const pageNames: Record<string, string> = {
  "/overview": "Overview",
  "/inventory": "Inventory",
  "/artifacts": "Artifacts",
  "/analysis": "Analysis Tools",
  "/topology": "Cryptographic Topology",
  "/quantum": "Quantum Risk",
  "/mosca": "MOSCA Analysis",
  "/migration": "Migration",
  "/reports": "Reports",
  "/import": "Import Scan",
};

export function Topbar() {
  const pathname = usePathname();

  const pageName =
    pageNames[pathname] ?? "ECDAT";

  return (
    <header className="flex h-16 items-center justify-between border-b border-white/[0.07] px-6 md:px-8">
      {/* Left */}
      <div className="flex items-center gap-3">
        <span className="font-display text-sm font-medium text-foreground">
          {pageName}
        </span>

        <span className="text-[#566276]">
          /
        </span>

        <span className="font-mono text-[9px] uppercase tracking-[0.15em] text-muted-foreground">
          ECDAT
        </span>
      </div>

      {/* Right */}
      <div className="flex items-center gap-5">
        <div className="hidden items-center gap-2 sm:flex">
          <span className="font-mono text-[9px] uppercase tracking-[0.12em] text-[#66748A]">
            Scan
          </span>

          <span className="font-mono text-[10px] text-foreground">
            demo_repo
          </span>
        </div>

        <div className="h-4 w-px bg-white/[0.08]" />

        <div className="flex items-center gap-2">
          <span
            className="h-1.5 w-1.5 rounded-full bg-success"
            aria-hidden="true"
          />

          <span className="font-mono text-[9px] uppercase tracking-[0.14em] text-success">
            Ready
          </span>
        </div>
      </div>
    </header>
  );
}
