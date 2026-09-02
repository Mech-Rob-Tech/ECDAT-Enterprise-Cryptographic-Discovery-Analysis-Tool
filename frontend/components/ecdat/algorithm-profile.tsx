interface AlgorithmProfileProps {
  algorithms: {
    name: string;
    count: number;
    percentage: number;
  }[];
}

export function AlgorithmProfile({
  algorithms,
}: AlgorithmProfileProps) {
  return (
    <section className="rounded-lg border border-white/[0.07] bg-card p-6">
      <div className="flex items-start justify-between">
        <div>
          <p className="font-mono text-[9px] uppercase tracking-[0.18em] text-muted-foreground">
            Algorithm profile
          </p>

          <h2 className="mt-2 font-display text-lg font-medium tracking-[-0.02em]">
            Detected technologies
          </h2>
        </div>

        <span className="font-mono text-[9px] uppercase tracking-[0.12em] text-muted-foreground">
          distribution
        </span>
      </div>

      <div className="mt-7 space-y-4">
        {algorithms.map((algorithm) => (
          <div key={algorithm.name}>
            <div className="mb-2 flex items-center justify-between">
              <span className="font-mono text-xs text-foreground">
                {algorithm.name}
              </span>

              <span className="font-mono text-[10px] text-muted-foreground">
                {algorithm.count}
              </span>
            </div>

            <div className="h-1 overflow-hidden rounded-full bg-white/[0.06]">
              <div
                className="h-full rounded-full bg-primary/70"
                style={{
                  width: `${algorithm.percentage}%`,
                }}
              />
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
