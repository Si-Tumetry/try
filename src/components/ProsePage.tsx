import type { ReactNode } from 'react';

interface ProsePageProps {
  eyebrow?: string;
  title: string;
  intro?: string;
  notice?: string;
  children: ReactNode;
}

export function ProsePage({ eyebrow, title, intro, notice, children }: ProsePageProps) {
  return (
    <article className="mx-auto max-w-3xl px-6 py-16 lg:py-24">
      {eyebrow && <p className="mb-3 font-mono text-xs tracking-wider text-ink-500 uppercase">{eyebrow}</p>}
      <h1 className="font-serif text-4xl leading-tight font-normal text-ink-900 md:text-5xl">{title}</h1>
      {intro && <p className="mt-6 text-lg leading-relaxed text-ink-600">{intro}</p>}
      {notice && (
        <p role="note" className="mt-8 rounded-xl border border-ink-900/15 bg-cream-100 px-5 py-4 text-sm text-ink-700">
          {notice}
        </p>
      )}
      <div className="mt-12 space-y-10 text-[17px] leading-[1.7] text-ink-700">{children}</div>
    </article>
  );
}

export function ProseSection({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="space-y-4">
      <h2 className="font-serif text-2xl font-medium text-ink-900">{title}</h2>
      {children}
    </section>
  );
}
