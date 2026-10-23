import type { ReactNode } from 'react';

interface SectionProps {
  id?: string;
  index?: string;
  title: string;
  kicker?: string;
  headingId: string;
  /** 'blue' gives a solid accent-blue band with white text. */
  tone?: 'page' | 'blue';
  children: ReactNode;
}

/** A numbered page section with the editorial heading used across the site. */
export function Section({ id, index, title, kicker, headingId, tone = 'page', children }: SectionProps) {
  const band = tone === 'blue' ? 'bg-accent-blue text-white' : '';
  const indexClass = tone === 'blue' ? 'text-blue-200' : 'text-ink-500';
  const kickerClass = tone === 'blue' ? 'text-blue-200' : 'text-ink-500';

  return (
    <section id={id} aria-labelledby={headingId} className={`scroll-mt-24 ${band}`}>
      <div className="mx-auto max-w-7xl px-6 py-20 lg:px-12">
        <div className="mb-12 flex flex-col justify-between gap-4 md:flex-row md:items-baseline">
          <div className="flex items-baseline gap-3">
            {index && <span className={`font-mono text-sm ${indexClass}`}>{index}</span>}
            <h2 id={headingId} className="font-serif text-3xl font-normal md:text-4xl">
              {title}
            </h2>
          </div>
          {kicker && <p className={`font-mono text-xs tracking-wider uppercase ${kickerClass}`}>{kicker}</p>}
        </div>
        {children}
      </div>
    </section>
  );
}

export function Hairline() {
  return (
    <div className="mx-auto max-w-7xl px-6 lg:px-12" aria-hidden="true">
      <div className="border-t border-blue-300/70" />
    </div>
  );
}
