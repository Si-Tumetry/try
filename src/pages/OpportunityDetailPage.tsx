import { Link, useParams } from 'react-router';
import { CountryTags, ScopeTag, WorkModeTag } from '../components/EligibilityTag';
import { ArrowRightIcon, ArrowUpRightIcon } from '../components/Icon';
import { useDocumentTitle } from '../hooks/useDocumentTitle';
import { useOpportunities } from '../hooks/useOpportunities';
import { formatDate, formatDateTime } from '../lib/format';
import { findOpportunity, isExpired, type Opportunity } from '../lib/opportunities';

function sourceHost(url: string): string {
  try {
    return new URL(url).host;
  } catch {
    return 'the employer’s site';
  }
}

function Paragraphs({ text }: { text: string }) {
  const paragraphs = text
    .split(/\n\s*\n/)
    .map((part) => part.trim())
    .filter(Boolean);

  if (paragraphs.length === 0) {
    return <p className="text-ink-500">The employer has not provided a description. See the original posting for details.</p>;
  }

  return (
    <div className="space-y-5 text-[17px] leading-[1.7] text-ink-800">
      {paragraphs.map((paragraph, index) => (
        <p key={index} className="whitespace-pre-line">
          {paragraph}
        </p>
      ))}
    </div>
  );
}

function DetailView({ item }: { item: Opportunity }) {
  const expired = isExpired(item);
  const location = item.location_text.trim();

  return (
    <article className="mx-auto max-w-6xl px-6 py-14 lg:px-12">
      <nav aria-label="Breadcrumb" className="mb-8 flex flex-wrap items-center gap-2 text-xs text-ink-500">
        <Link to="/opportunities" className="hover:text-ink-900">
          Directory
        </Link>
        <span aria-hidden="true">›</span>
        <span className="line-clamp-1 text-ink-700">{item.title.trim()}</span>
      </nav>

      <div className="grid grid-cols-1 gap-12 lg:grid-cols-[minmax(0,1fr)_340px]">
        <div className="min-w-0">
          <p className="mb-3 font-mono text-xs tracking-wider text-ink-500 uppercase">{item.employer}</p>
          <h1 className="font-serif text-4xl leading-tight font-normal text-ink-900 md:text-5xl">{item.title.trim()}</h1>

          <div className="mt-6 flex flex-wrap items-center gap-2">
            <WorkModeTag mode={item.work_mode} />
            <ScopeTag scope={item.scope} />
            <CountryTags countries={item.eligible_countries} />
          </div>

          <div className="mt-12 border-t border-ink-900/10 pt-10">
            <h2 className="mb-6 font-serif text-2xl font-medium text-ink-900">About this role</h2>
            <Paragraphs text={item.description} />
          </div>
        </div>

        <aside aria-label="Listing details" className="space-y-6 lg:sticky lg:top-28 lg:self-start">
          {expired ? (
            <div role="status" className="rounded-2xl border border-ink-900/15 bg-cream-100 p-6">
              <p className="font-semibold text-ink-900">This posting has passed its expiry date.</p>
              <p className="mt-2 text-sm text-ink-600">
                The employer may have closed it. Check the original posting before you rely on this listing.
              </p>
              <Link to="/opportunities" className="mt-4 inline-flex items-center gap-1 text-sm font-semibold text-accent-blue">
                Back to the directory <ArrowRightIcon aria-hidden="true" />
              </Link>
            </div>
          ) : (
            <div className="rounded-2xl border border-ink-900/10 bg-white p-6">
              <a
                href={item.source_url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex w-full items-center justify-center gap-2 rounded-full bg-ink-900 px-6 py-3 text-sm font-semibold tracking-wide text-cream-50 transition-colors hover:bg-accent-blue"
              >
                Apply on the employer’s site
                <ArrowUpRightIcon aria-hidden="true" />
              </a>
              <p className="mt-3 text-xs leading-relaxed text-ink-500">
                NextStep does not take applications. The posting on {sourceHost(item.source_url)} is the source of truth.
              </p>
            </div>
          )}

          <dl className="space-y-5 rounded-2xl border border-ink-900/10 bg-cream-100/50 p-6 text-sm">
            {location && (
              <div>
                <dt className="font-mono text-xs text-ink-500">Location</dt>
                <dd className="mt-1 text-ink-900">{location}</dd>
              </div>
            )}
            {item.department.trim() && (
              <div>
                <dt className="font-mono text-xs text-ink-500">Department</dt>
                <dd className="mt-1 text-ink-900">{item.department.trim()}</dd>
              </div>
            )}
            <div>
              <dt className="font-mono text-xs text-ink-500">Open to</dt>
              <dd className="mt-1 text-ink-900">
                {item.eligible_countries.length > 0 ? item.eligible_countries.join(', ') : 'Not stated in the posting'}
              </dd>
            </div>
            <div>
              <dt className="font-mono text-xs text-ink-500">Pay</dt>
              <dd className="mt-1 text-ink-900">
                {item.pay_ranges.length > 0 ? 'See the posting' : 'Not stated in the posting'}
              </dd>
            </div>
            <div>
              <dt className="font-mono text-xs text-ink-500">Last updated</dt>
              <dd className="mt-1 text-ink-900">
                <time dateTime={item.updated_at}>{formatDate(item.updated_at)}</time>
              </dd>
            </div>
            {item.expires_at && (
              <div>
                <dt className="font-mono text-xs text-ink-500">Expires</dt>
                <dd className="mt-1 text-ink-900">
                  <time dateTime={item.expires_at}>{formatDateTime(item.expires_at)}</time>
                </dd>
              </div>
            )}
          </dl>
        </aside>
      </div>
    </article>
  );
}

export function OpportunityDetailPage() {
  const { id = '' } = useParams();
  const state = useOpportunities();

  const item = state.status === 'ready' ? findOpportunity(state.snapshot.listings, id) : undefined;
  useDocumentTitle(item ? item.title.trim() : 'Opportunity');

  if (state.status === 'loading') {
    return (
      <p role="status" className="py-24 text-center text-sm text-ink-500">
        Loading opportunity…
      </p>
    );
  }

  if (state.status === 'error') {
    return (
      <div role="alert" className="mx-auto max-w-2xl px-6 py-24 text-center">
        <p className="text-ink-700">{state.message}. Refresh the page to try again.</p>
      </div>
    );
  }

  if (!item) {
    return (
      <div className="mx-auto max-w-2xl px-6 py-24 text-center">
        <h1 className="font-serif text-4xl font-normal text-ink-900">Listing not found</h1>
        <p className="mt-4 text-ink-600">It may have been removed, or the link may be wrong.</p>
        <Link to="/opportunities" className="mt-8 inline-flex items-center gap-1 text-sm font-semibold text-accent-blue">
          Back to the directory <ArrowRightIcon aria-hidden="true" />
        </Link>
      </div>
    );
  }

  return <DetailView item={item} />;
}
