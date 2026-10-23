import { SearchIcon } from './Icon';
import { COUNTRY_NAMES, SCOPE_LABELS, WORK_MODE_LABELS, type OpportunityFilters, type Scope, type WorkMode } from '../lib/opportunities';
import { SECTORS, type SectorId } from '../lib/sectors';

interface FilterBarProps {
  filters: OpportunityFilters;
  countries: string[];
  onChange: (next: OpportunityFilters) => void;
  onReset: () => void;
}

const selectClass =
  'min-h-11 rounded-lg border border-accent-blue/30 bg-blue-50 px-3 py-2 text-sm text-ink-900 focus:border-accent-blue';

export function FilterBar({ filters, countries, onChange, onReset }: FilterBarProps) {
  const isDirty = Object.values(filters).some((value) => value !== '');

  return (
    <form
      role="search"
      aria-label="Filter opportunities"
      className="grid grid-cols-1 gap-3 rounded-2xl border border-blue-300/60 bg-blue-50 p-4 sm:grid-cols-2 lg:grid-cols-6"
      onSubmit={(event) => event.preventDefault()}
    >
      <label className="flex flex-col gap-1.5 text-xs font-semibold text-ink-500 sm:col-span-2">
        Search
        <span className="relative flex items-center">
          <SearchIcon className="pointer-events-none absolute left-3 text-ink-400" />
          <input
            type="search"
            placeholder="Role, employer or place"
            value={filters.query}
            onChange={(event) => onChange({ ...filters, query: event.target.value })}
            className="min-h-11 w-full rounded-lg border border-accent-blue/30 bg-blue-50 py-2 pr-3 pl-9 text-sm font-normal text-ink-900 placeholder:text-ink-400 focus:border-accent-blue"
          />
        </span>
      </label>

      <label className="flex flex-col gap-1.5 text-xs font-semibold text-ink-500">
        Sector
        <select
          className={selectClass}
          value={filters.sector}
          onChange={(event) => onChange({ ...filters, sector: event.target.value as '' | SectorId })}
        >
          <option value="">All sectors</option>
          {SECTORS.map((sector) => (
            <option key={sector.id} value={sector.id}>
              {sector.label}
            </option>
          ))}
        </select>
      </label>

      <label className="flex flex-col gap-1.5 text-xs font-semibold text-ink-500">
        Country
        <select className={selectClass} value={filters.country} onChange={(event) => onChange({ ...filters, country: event.target.value })}>
          <option value="">All countries</option>
          {countries.map((code) => (
            <option key={code} value={code}>
              {COUNTRY_NAMES[code] ?? code}
            </option>
          ))}
        </select>
      </label>

      <label className="flex flex-col gap-1.5 text-xs font-semibold text-ink-500">
        Work mode
        <select
          className={selectClass}
          value={filters.workMode}
          onChange={(event) => onChange({ ...filters, workMode: event.target.value as '' | WorkMode })}
        >
          <option value="">Any</option>
          {(Object.keys(WORK_MODE_LABELS) as WorkMode[]).map((mode) => (
            <option key={mode} value={mode}>
              {WORK_MODE_LABELS[mode]}
            </option>
          ))}
        </select>
      </label>

      <label className="flex flex-col gap-1.5 text-xs font-semibold text-ink-500">
        Eligibility
        <select
          className={selectClass}
          value={filters.scope}
          onChange={(event) => onChange({ ...filters, scope: event.target.value as '' | Scope })}
        >
          <option value="">Any</option>
          {(Object.keys(SCOPE_LABELS) as Scope[]).map((scope) => (
            <option key={scope} value={scope}>
              {SCOPE_LABELS[scope]}
            </option>
          ))}
        </select>
      </label>

      <div className="flex items-end sm:col-span-2 lg:col-span-6 lg:justify-end">
        <button
          type="button"
          onClick={onReset}
          disabled={!isDirty}
          className="min-h-11 rounded-full px-4 text-sm font-semibold text-accent-blue transition-colors hover:text-ink-900 disabled:cursor-not-allowed disabled:opacity-40"
        >
          Clear filters
        </button>
      </div>
    </form>
  );
}
