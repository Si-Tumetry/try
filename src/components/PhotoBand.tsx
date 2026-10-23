import type { ReactNode } from 'react';

interface PhotoBandProps {
  /** Path under /public. Images are decorative, so the band is described by its text, not the picture. */
  image: string;
  children: ReactNode;
  className?: string;
  innerClassName?: string;
  /** Hero images load immediately; band images further down the page can wait. */
  priority?: boolean;
  /** 'strong' keeps text readable over busy images; 'soft' lets more of the photograph show. */
  tone?: 'strong' | 'soft';
}

/**
 * A full-width band with a photograph under a blue overlay. Keeps the page blue
 * even where the photograph is pale, so the text stays readable.
 */
const OVERLAYS = {
  strong: 'from-accent-navy/95 via-accent-navy/85 to-accent-blue/75',
  soft: 'from-accent-navy/80 via-accent-blue/60 to-accent-blue/40',
};

export function PhotoBand({
  image,
  children,
  className = '',
  innerClassName = '',
  priority = false,
  tone = 'strong',
}: PhotoBandProps) {
  return (
    <div className={`relative isolate overflow-hidden bg-accent-navy text-white ${className}`}>
      <img
        src={image}
        alt=""
        aria-hidden="true"
        className="absolute inset-0 -z-20 h-full w-full object-cover"
        loading={priority ? 'eager' : 'lazy'}
        decoding="async"
        fetchPriority={priority ? 'high' : 'auto'}
      />
      <div className={`absolute inset-0 -z-10 bg-linear-to-br ${OVERLAYS[tone]}`} aria-hidden="true" />
      <div className={`relative mx-auto max-w-7xl px-6 lg:px-12 ${innerClassName}`}>{children}</div>
    </div>
  );
}
