interface PageHeaderProps {
  eyebrow: string;
  title: string;
  description: string;
}

export function PageHeader({
  eyebrow,
  title,
  description,
}: PageHeaderProps) {
  return (
    <header>
      <p className="font-mono text-[9px] uppercase tracking-[0.2em] text-primary">
        {eyebrow}
      </p>

      <h1 className="mt-2 font-display text-3xl font-semibold tracking-[-0.045em] text-foreground md:text-4xl">
        {title}
      </h1>

      <p className="mt-3 max-w-2xl text-sm leading-6 text-muted-foreground">
        {description}
      </p>
    </header>
  );
}
