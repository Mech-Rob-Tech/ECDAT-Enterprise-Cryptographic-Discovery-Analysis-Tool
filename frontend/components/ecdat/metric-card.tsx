interface MetricCardProps {
  label: string;
  value: string | number;
  detail?: string;
  accent?: boolean;
}

export function MetricCard({
  label,
  value,
  detail,
  accent = false,
}: MetricCardProps) {
  return (
    <section className="rounded-lg border border-white/[0.07] bg-card p-5">
      <div className="flex items-start justify-between">
        <p className="font-mono text-[9px] uppercase tracking-[0.18em] text-muted-foreground">
          {label}
        </p>

        {accent && (
          <span
            className="mt-0.5 h-1.5 w-1.5 rounded-full bg-primary"
            aria-hidden="true"
          />
        )}
      </div>

      <div className="mt-5 flex items-end justify-between gap-4">
        <p className="font-mono text-3xl font-medium tracking-[-0.04em] text-foreground">
          {value}
        </p>

        {detail && (
          <span className="pb-1 font-mono text-[9px] uppercase tracking-[0.1em] text-muted-foreground">
            {detail}
          </span>
        )}
      </div>
    </section>
  );
}
