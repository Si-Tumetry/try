import { SCOPE_LABELS, WORK_MODE_LABELS, type Opportunity, type Scope, type WorkMode } from '../lib/opportunities';

const SCOPE_STYLES: Record<Scope, string> = {
  in_region: 'bg-accent-blue text-white',
  remote_in_region: 'bg-accent-blue text-white',
  outside_region: 'bg-blue-200 text-accent-navy',
  remote_outside_region: 'bg-blue-200 text-accent-navy',
  unspecified: 'border border-accent-blue/40 text-accent-navy',
};

export function ScopeTag({ scope }: { scope: Scope }) {
  return (
    <span className={`rounded-full px-2.5 py-1 text-xs font-medium ${SCOPE_STYLES[scope]}`}>{SCOPE_LABELS[scope]}</span>
  );
}

export function WorkModeTag({ mode }: { mode: WorkMode }) {
  return (
    <span className="rounded-full border border-accent-blue/25 bg-blue-50 px-2.5 py-1 text-xs text-accent-navy">
      {WORK_MODE_LABELS[mode]}
    </span>
  );
}

export function CountryTags({ countries }: { countries: Opportunity['eligible_countries'] }) {
  if (countries.length === 0) {
    return null;
  }
  return <span className="font-mono text-xs text-ink-500">{countries.join(' · ')}</span>;
}
