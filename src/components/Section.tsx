import type { ReactNode } from 'react';

interface SectionProps {
  id?: string;
  index?: string;
  title: string;
  kicker?: string;
  headingId: string;
  children: ReactNode;
}

/** A numbered page section with the editorial heading and hairline divider used across the site. */
export function Section({ id, index, title, kicker, headingId, children }: SectionProps) {
  return (
    <section id={id} aria-labelledby={headingId} className="mx-auto max-w-7xl scroll-mt-24 px-6 py-20 lg:px-12">
      <div className="mb-12 flex flex-col justify-between gap-4 md:flex-row md:items-baseline">
        <div className="flex items-baseline gap-3">
          {index && <span className="font-mono text-sm text-ink-400">{index}</span>}
          <h2 id={headingId} className="font-serif text-3xl font-normal text-ink-900 md:text-4xl">
            {title}
          </h2>
        </div>
        {kicker && <p className="font-mono text-xs tracking-wider text-ink-500 uppercase">{kicker}</p>}
      </div>
      {children}
    </section>
  );
}

export function Hairline() {
  return (
    <div className="mx-auto max-w-7xl px-6 lg:px-12" aria-hidden="true">
      <div className="border-t border-ink-900/10" />
    </div>
  );
}
