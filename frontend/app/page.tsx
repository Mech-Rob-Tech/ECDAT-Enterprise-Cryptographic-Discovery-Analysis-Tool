const navigation = [
  {
    label: "DISCOVER",
    items: ["Overview", "Inventory"],
  },
  {
    label: "ASSESS",
    items: ["Quantum", "Mosca"],
  },
  {
    label: "PLAN",
    items: ["Migration"],
  },
  {
    label: "REPORT",
    items: ["Reports"],
  },
];

export default function Home() {
  return (
    <main className="relative min-h-screen overflow-hidden bg-background text-foreground">
      {/* Landing atmosphere */}
      <div
        className="ecdat-dot-field"
        aria-hidden="true"
      />

      <div
        className="ecdat-atmosphere"
        aria-hidden="true"
      />

      {/* Content */}
      <div className="relative z-10 min-h-screen">
        {/* Top micro header */}
        <header className="flex items-center justify-between px-6 py-5 md:px-10">
	<div className="flex items-center gap-3 font-mono text-[10px] uppercase tracking-[0.28em] text-primary">
  <span
    className="h-px w-8 bg-primary"
    aria-hidden="true"
  />
  <span>SIH26-26164 / NTRO</span>
</div>
          <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-muted-foreground">
            ECDAT
          </div>
        </header>

        {/* Hero */}
        <section className="flex min-h-[calc(100vh-80px)] items-center justify-center px-6">
          <div className="w-full max-w-5xl text-center">

            <p className="mb-7 font-mono text-[11px] uppercase tracking-[0.32em] text-muted-foreground">
              Cryptographic visibility / post-quantum readiness
            </p>

            <h1 className="text-balance font-display text-[clamp(4.5rem,13vw,10rem)] font-bold leading-[0.78] tracking-[-0.075em] text-foreground">
              ECDAT
            </h1>

            <div className="mt-10 flex flex-wrap items-baseline justify-center gap-x-3 gap-y-1">
              <span className="font-display text-2xl font-medium tracking-[-0.035em] text-foreground md:text-4xl">
                Enterprise Cryptographic
              </span>

              <span className="font-editorial text-2xl text-primary md:text-4xl">
                Discovery &amp; Analysis
              </span>
            </div>

            <p className="mx-auto mt-7 max-w-2xl text-sm leading-7 text-muted-foreground md:text-base">
              Discover cryptographic usage. Trace evidence. Assess quantum
              exposure. Plan migration.
            </p>

            <div className="mt-10 flex justify-center">
              <a
                href="/overview"
                className="
                  group
                  inline-flex
                  h-12
                  items-center
                  gap-5
                  rounded-md
                  bg-primary
                  px-7
                  font-mono
                  text-[11px]
                  font-semibold
                  uppercase
                  tracking-[0.12em]
                  text-primary-foreground
                  transition-all
                  duration-200
                  hover:-translate-y-0.5
                  hover:shadow-[0_12px_40px_rgba(244,196,48,0.16)]
                  active:translate-y-0
                "
              >
                Enter ECDAT

                <span
                  aria-hidden="true"
                  className="
                    transition-transform
                    duration-200
                    group-hover:translate-x-1
                  "
                >
                  →
                </span>
              </a>
            </div>

            {/* Divider */}
            <div className="mx-auto mt-12 h-px w-10 bg-primary/60" />

            {/* Product promise */}
            <div className="mt-5 font-mono text-[9px] uppercase tracking-[0.25em] text-muted-foreground">
              Discovery / Evidence / Risk / Migration
            </div>
          </div>
        </section>
      </div>
    </main>
  );
}

