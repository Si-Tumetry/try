import { SCOPE_LABELS, WORK_MODE_LABELS, type Opportunity, type Scope, type WorkMode } from '../lib/opportunities';

const SCOPE_STYLES: Record<Scope, string> = {
  in_region: 'bg-chip-blue-soft text-accent-navy',
  remote_in_region: 'bg-chip-blue-soft text-accent-navy',
  outside_region: 'bg-cream-200 text-ink-700',
  remote_outside_region: 'bg-cream-200 text-ink-700',
  unspecified: 'border border-ink-900/15 text-ink-600',
};

export function ScopeTag({ scope }: { scope: Scope }) {
  return (
    <span className={`rounded-full px-2.5 py-1 text-xs font-medium ${SCOPE_STYLES[scope]}`}>{SCOPE_LABELS[scope]}</span>
  );
}

export function WorkModeTag({ mode }: { mode: WorkMode }) {
  return (
    <span className="rounded-full border border-ink-900/10 bg-cream-100 px-2.5 py-1 text-xs text-ink-700">
      {WORK_MODE_LABELS[mode]}
    </span>
  );
}

export function CountryTags({ countries }: { countries: Opportunity['eligible_countries'] }) {
  if (countries.length === 0) {
    return null;
  }
  return (
    <span className="font-mono text-xs text-ink-500">{countries.join(' · ')}</span>
  );
}
