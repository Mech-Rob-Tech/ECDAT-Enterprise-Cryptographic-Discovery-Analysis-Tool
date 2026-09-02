import type { RiskLevel } from "@/lib/types";

interface RiskBadgeProps {
  level: RiskLevel;
}

const styles: Record<RiskLevel, string> = {
  CRITICAL:
    "border-red-400/25 bg-red-400/[0.08] text-red-300",
  HIGH:
    "border-orange-300/25 bg-orange-300/[0.07] text-orange-200",
  MEDIUM:
    "border-yellow-300/25 bg-yellow-300/[0.07] text-yellow-200",
  LOW:
    "border-emerald-300/25 bg-emerald-300/[0.07] text-emerald-200",
};

export function RiskBadge({ level }: RiskBadgeProps) {
  return (
    <span
      className={`inline-flex items-center rounded-full border px-2 py-1 font-mono text-[9px] uppercase tracking-[0.12em] ${styles[level]}`}
    >
      {level}
    </span>
  );
}
