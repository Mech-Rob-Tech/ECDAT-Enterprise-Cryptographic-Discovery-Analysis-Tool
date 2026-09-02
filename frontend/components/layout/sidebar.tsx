"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const navigation = [
  {
    label: "DISCOVER",
    items: [
      { name: "Overview", href: "/overview" },
      { name: "Inventory", href: "/inventory" },
      { name: "Artifacts", href: "/artifacts" },
    ],
  },
  {
    label: "ASSESS",
    items: [
      { name: "Quantum Risk", href: "/quantum" },
      { name: "Mosca Analysis", href: "/mosca" },
    ],
  },
  {
    label: "PLAN",
    items: [
      { name: "Migration", href: "/migration" },
    ],
  },
  {
    label: "REPORT",
    items: [
      { name: "Reports", href: "/reports" },
    ],
  },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="fixed inset-y-0 left-0 z-40 hidden w-[248px] border-r border-white/[0.07] bg-[#101927] lg:flex lg:flex-col">
      {/* Brand */}
      <div className="px-6 pb-7 pt-7">
        <Link href="/overview" className="block">
          <div className="flex items-center gap-3">
            <span
              className="h-5 w-[3px] bg-primary"
              aria-hidden="true"
            />

            <div>
              <div className="font-display text-lg font-bold tracking-[-0.04em] text-foreground">
                ECDAT
              </div>

              <div className="mt-0.5 font-mono text-[8px] uppercase tracking-[0.16em] text-muted-foreground">
                Cryptographic Analysis
              </div>
            </div>
          </div>
        </Link>
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto px-3 pb-6">
        {navigation.map((section) => (
          <div key={section.label} className="mb-7">
            <div className="mb-2 px-3 font-mono text-[9px] font-medium tracking-[0.2em] text-[#66748A]">
              {section.label}
            </div>

            <div className="space-y-0.5">
              {section.items.map((item) => {
                const active = pathname === item.href;

                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={`
                      group
                      relative
                      flex
                      h-9
                      items-center
                      rounded-md
                      px-3
                      text-sm
                      transition-colors
                      duration-150
                      ${
                        active
                          ? "bg-white/[0.045] text-foreground"
                          : "text-[#8793A6] hover:bg-white/[0.025] hover:text-foreground"
                      }
                    `}
                  >
                    {active && (
                      <span
                        className="absolute left-0 h-4 w-[2px] rounded-full bg-primary"
                        aria-hidden="true"
                      />
                    )}

                    <span
                      className={
                        active
                          ? "font-medium"
                          : "font-normal"
                      }
                    >
                      {item.name}
                    </span>
                  </Link>
                );
              })}
            </div>
          </div>
        ))}
      </nav>

      {/* Import */}
      <div className="px-3 pb-4">
        <Link
          href="/import"
          className={`
            flex
            h-10
            items-center
            rounded-md
            border
            border-white/[0.07]
            px-3
            font-mono
            text-[10px]
            uppercase
            tracking-[0.12em]
            transition-colors
            ${
              pathname === "/import"
                ? "border-primary/30 bg-primary/[0.06] text-primary"
                : "text-[#8793A6] hover:border-white/[0.12] hover:text-foreground"
            }
          `}
        >
          Import Scan
        </Link>
      </div>

      {/* Footer */}
      <div className="border-t border-white/[0.07] px-6 py-4">
        <div className="flex items-center justify-between">
          <span className="font-mono text-[8px] uppercase tracking-[0.15em] text-[#566276]">
            Local Prototype
          </span>

          <span className="font-mono text-[8px] text-[#566276]">
            v0.2
          </span>
        </div>
      </div>
    </aside>
  );
}
