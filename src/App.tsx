import { useEffect, useMemo, useState } from 'react';
import { FilterBar } from './components/FilterBar';
import { OpportunityCard } from './components/OpportunityCard';
import {
  EMPTY_FILTERS,
  countryOptions,
  filterOpportunities,
  loadOpportunities,
  sortByUpdated,
  type OpportunityFilters,
  type OpportunitySnapshot,
} from './lib/opportunities';

const DATA_URL = `${import.meta.env.BASE_URL}data/opportunities.json`;
const PAGE_SIZE = 24;

type LoadState =
  | { status: 'loading' }
  | { status: 'error'; message: string }
  | { status: 'ready'; snapshot: OpportunitySnapshot };

const refreshedFormat = new Intl.DateTimeFormat('en-GB', {
  day: 'numeric',
  month: 'short',
  year: 'numeric',
  hour: '2-digit',
  minute: '2-digit',
});

export default function App() {
  const [state, setState] = useState<LoadState>({ status: 'loading' });
  const [filters, setFilters] = useState<OpportunityFilters>(EMPTY_FILTERS);
  const [visibleCount, setVisibleCount] = useState(PAGE_SIZE);

  useEffect(() => {
    const controller = new AbortController();
    loadOpportunities(DATA_URL, controller.signal)
      .then((snapshot) => setState({ status: 'ready', snapshot }))
      .catch((error: unknown) => {
        if (controller.signal.aborted) return;
        const message = error instanceof Error ? error.message : 'Something went wrong';
        setState({ status: 'error', message });
      });
    return () => controller.abort();
  }, []);

  const listings = state.status === 'ready' ? state.snapshot.listings : [];

  const countries = useMemo(() => countryOptions(listings), [listings]);
  const results = useMemo(
    () => sortByUpdated(filterOpportunities(listings, filters)),
    [listings, filters],
  );

  useEffect(() => {
    setVisibleCount(PAGE_SIZE);
  }, [filters]);

  const shown = results.slice(0, visibleCount);
  const refreshed =
    state.status === 'ready' ? refreshedFormat.format(new Date(state.snapshot.fetched_at)) : null;

  return (
    <div className="app">
      <header className="site-header">
        <div className="container">
          <h1 className="site-title">Youth Yellow Pages</h1>
          <p className="site-tagline">Opportunities for young people across Nigeria, South Africa, Kenya and Ghana</p>
        </div>
      </header>

      <main className="container">
        {state.status === 'loading' && <p className="status" role="status">Loading opportunities…</p>}

        {state.status === 'error' && (
          <div className="status status--error" role="alert">
            <p>{state.message}. Please refresh the page to try again.</p>
          </div>
        )}

        {state.status === 'ready' && (
          <>
            <FilterBar
              filters={filters}
              countries={countries}
              onChange={setFilters}
              onReset={() => setFilters(EMPTY_FILTERS)}
            />

            <div className="results-meta" aria-live="polite">
              <p>
                Showing {shown.length} of {results.length} {results.length === 1 ? 'opportunity' : 'opportunities'}
              </p>
              {refreshed && <p className="results-meta__source">Listings last refreshed {refreshed}</p>}
            </div>

            {results.length === 0 ? (
              <p className="status">No opportunities match these filters. Try clearing some of them.</p>
            ) : (
              <div className="grid">
                {shown.map((opportunity) => (
                  <OpportunityCard key={`${opportunity.source_key}:${opportunity.external_id}`} opportunity={opportunity} />
                ))}
              </div>
            )}

            {visibleCount < results.length && (
              <div className="load-more">
                <button
                  type="button"
                  className="button button--ghost"
                  onClick={() => setVisibleCount((count) => count + PAGE_SIZE)}
                >
                  Show more
                </button>
              </div>
            )}
          </>
        )}
      </main>

      <footer className="site-footer">
        <div className="container">
          <p>
            Each listing links to the employer’s original posting, which is the source of truth. Youth Yellow Pages
            does not hold or apply to these roles.
          </p>
        </div>
      </footer>
    </div>
  );
}
