import {
  SCOPE_LABELS,
  WORK_MODE_LABELS,
  type OpportunityFilters,
  type Scope,
  type WorkMode,
} from '../lib/opportunities';

interface FilterBarProps {
  filters: OpportunityFilters;
  countries: string[];
  onChange: (next: OpportunityFilters) => void;
  onReset: () => void;
}

export function FilterBar({ filters, countries, onChange, onReset }: FilterBarProps) {
  const isDirty = filters.query !== '' || filters.country !== '' || filters.workMode !== '' || filters.scope !== '';

  return (
    <form className="filters" role="search" onSubmit={(event) => event.preventDefault()}>
      <label className="field field--wide">
        <span>Search</span>
        <input
          type="search"
          placeholder="Role, employer or place"
          value={filters.query}
          onChange={(event) => onChange({ ...filters, query: event.target.value })}
        />
      </label>

      <label className="field">
        <span>Country</span>
        <select
          value={filters.country}
          onChange={(event) => onChange({ ...filters, country: event.target.value })}
        >
          <option value="">All countries</option>
          {countries.map((code) => (
            <option key={code} value={code}>
              {code}
            </option>
          ))}
        </select>
      </label>

      <label className="field">
        <span>Work mode</span>
        <select
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

      <label className="field">
        <span>Eligibility</span>
        <select
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

      <button type="button" className="button button--ghost" onClick={onReset} disabled={!isDirty}>
        Clear filters
      </button>
    </form>
  );
}
