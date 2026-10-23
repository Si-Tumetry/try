import { useEffect, useMemo, useState } from 'react';
import { useSearchParams } from 'react-router';
import { FilterBar } from '../components/FilterBar';
import { OpportunityCard } from '../components/OpportunityCard';
import { useDocumentTitle } from '../hooks/useDocumentTitle';
import { useOpportunities } from '../hooks/useOpportunities';
import { formatCount, formatDateTime } from '../lib/format';
import {
  EMPTY_FILTERS,
  SCOPE_LABELS,
  SORT_OPTIONS,
  WORK_MODE_LABELS,
  countryOptions,
  filterOpportunities,
  sortOpportunities,
  type OpportunityFilters,
  type Scope,
  type SortId,
  type WorkMode,
} from '../lib/opportunities';
import { getSector, type SectorId } from '../lib/sectors';

const PAGE_SIZE = 24;

function readFilters(params: URLSearchParams): OpportunityFilters {
  const workMode = params.get('workMode');
  const scope = params.get('scope');
  const sector = params.get('sector');
  return {
    query: params.get('q') ?? '',
    country: params.get('country') ?? '',
    workMode: workMode && workMode in WORK_MODE_LABELS ? (workMode as WorkMode) : '',
    scope: scope && scope in SCOPE_LABELS ? (scope as Scope) : '',
    sector: sector && getSector(sector) ? (sector as SectorId) : '',
  };
}

function readSort(params: URLSearchParams): SortId {
  const sort = params.get('sort');
  return SORT_OPTIONS.some((option) => option.id === sort) ? (sort as SortId) : 'recent';
}

export function OpportunitiesPage() {
  useDocumentTitle('Opportunities');
  const state = useOpportunities();
  const [params, setParams] = useSearchParams();
  const [visibleCount, setVisibleCount] = useState(PAGE_SIZE);

  const filters = useMemo(() => readFilters(params), [params]);
  const sort = readSort(params);

  const listings = state.status === 'ready' ? state.snapshot.listings : [];
  const countries = useMemo(() => countryOptions(listings), [listings]);
  const results = useMemo(
    () => sortOpportunities(filterOpportunities(listings, filters), sort),
    [listings, filters, sort],
  );

  const filterKey = [filters.query, filters.country, filters.workMode, filters.scope, filters.sector, sort].join('|');
  useEffect(() => {
    setVisibleCount(PAGE_SIZE);
  }, [filterKey]);

  function update(next: Partial<Record<string, string>>, replace = false) {
    setParams(
      (current) => {
        const merged = new URLSearchParams(current);
        for (const [key, value] of Object.entries(next)) {
          if (value) merged.set(key, value);
          else merged.delete(key);
        }
        return merged;
      },
      { replace },
    );
  }

  function setFilters(next: OpportunityFilters) {
    update(
      {
        q: next.query,
        country: next.country,
        workMode: next.workMode,
        scope: next.scope,
        sector: next.sector,
      },
      next.query !== filters.query,
    );
  }

  const shown = results.slice(0, visibleCount);

  return (
    <div className="mx-auto max-w-7xl px-6 py-14 lg:px-12">
      <header className="mb-10 max-w-3xl">
        <p className="mb-3 font-mono text-xs tracking-wider text-ink-500 uppercase">Directory</p>
        <h1 className="font-serif text-4xl leading-tight font-normal text-ink-900 md:text-5xl">Opportunities</h1>
        <p className="mt-4 text-base text-ink-600">
          Attachments, internships and entry-level roles. Each listing links to the employer&rsquo;s own posting.
        </p>
      </header>

      {state.status === 'loading' && (
        <p role="status" className="py-16 text-center text-sm text-ink-500">
          Loading opportunities…
        </p>
      )}

      {state.status === 'error' && (
        <div role="alert" className="rounded-2xl border border-ink-900/10 bg-white p-8 text-center">
          <p className="text-sm text-ink-700">{state.message}. Refresh the page to try again.</p>
        </div>
      )}

      {state.status === 'ready' && (
        <>
          <FilterBar filters={filters} countries={countries} onChange={setFilters} onReset={() => setFilters(EMPTY_FILTERS)} />

          <div className="mt-8 mb-6 flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
            <div aria-live="polite">
              <p className="font-semibold text-ink-900">
                Showing {shown.length} of {formatCount(results.length, 'opportunity')}
              </p>
              <p className="mt-1 font-mono text-xs text-ink-500">
                Listings last refreshed {formatDateTime(state.snapshot.fetched_at)}
              </p>
            </div>
            <label className="flex items-center gap-2 text-sm text-ink-600">
              Sort by
              <select
                value={sort}
                onChange={(event) => update({ sort: event.target.value === 'recent' ? '' : event.target.value })}
                className="min-h-11 rounded-lg border border-ink-900/15 bg-white px-3 text-sm text-ink-900"
              >
                {SORT_OPTIONS.map((option) => (
                  <option key={option.id} value={option.id}>
                    {option.label}
                  </option>
                ))}
              </select>
            </label>
          </div>

          {results.length === 0 ? (
            <div className="rounded-2xl border border-ink-900/10 bg-white p-10 text-center">
              <p className="text-ink-700">No opportunities match these filters.</p>
              <p className="mt-2 text-sm text-ink-500">Try clearing a filter or searching for a broader term.</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 xl:grid-cols-3">
              {shown.map((opportunity) => (
                <OpportunityCard key={`${opportunity.source_key}:${opportunity.external_id}`} opportunity={opportunity} />
              ))}
            </div>
          )}

          {visibleCount < results.length && (
            <div className="mt-10 flex justify-center">
              <button
                type="button"
                onClick={() => setVisibleCount((count) => count + PAGE_SIZE)}
                className="min-h-11 rounded-full border border-ink-900/15 px-6 text-sm font-semibold text-ink-900 transition-colors hover:bg-cream-100"
              >
                Show more
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
