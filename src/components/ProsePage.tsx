import type { ReactNode } from 'react';
import { PhotoBand } from './PhotoBand';

interface ProsePageProps {
  eyebrow?: string;
  title: string;
  intro?: string;
  notice?: string;
  /** When set, the title sits on a photograph band. */
  image?: string;
  children: ReactNode;
}

export function ProsePage({ eyebrow, title, intro, notice, image, children }: ProsePageProps) {
  const header = (
    <>
      {eyebrow && <p className={`mb-3 font-mono text-xs tracking-wider uppercase ${image ? 'text-blue-200' : 'text-ink-500'}`}>{eyebrow}</p>}
      <h1 className={`font-serif text-4xl leading-tight font-normal md:text-5xl ${image ? 'text-white' : 'text-ink-900'}`}>{title}</h1>
      {intro && <p className={`mt-6 max-w-3xl text-lg leading-relaxed ${image ? 'text-blue-100' : 'text-ink-600'}`}>{intro}</p>}
    </>
  );

  return (
    <article>
      {image ? (
        <PhotoBand image={image} innerClassName="py-20 md:py-24">
          <div className="max-w-3xl">{header}</div>
        </PhotoBand>
      ) : (
        <div className="mx-auto max-w-3xl px-6 pt-16 lg:pt-24">{header}</div>
      )}

      <div className="mx-auto max-w-3xl px-6 py-16">
        {notice && (
          <p role="note" className="mb-12 rounded-xl border border-accent-blue/30 bg-blue-50 px-5 py-4 text-sm text-ink-700">
            {notice}
          </p>
        )}
        <div className="space-y-10 text-[17px] leading-[1.7] text-ink-700">{children}</div>
      </div>
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
