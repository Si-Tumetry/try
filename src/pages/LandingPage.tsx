import { useState, type FormEvent } from 'react';
import { Link, useNavigate } from 'react-router';
import { CountryTags, ScopeTag, WorkModeTag } from '../components/EligibilityTag';
import { ArrowRightIcon, SearchIcon } from '../components/Icon';
import { PhotoBand } from '../components/PhotoBand';
import { Section } from '../components/Section';
import { useDocumentTitle } from '../hooks/useDocumentTitle';
import { useOpportunities } from '../hooks/useOpportunities';
import { formatCount, formatDate, formatDateTime } from '../lib/format';
import {
  LAUNCH_COUNTRIES,
  directoryStats,
  isOpenInLaunchCountries,
  sortOpportunities,
  type Opportunity,
} from '../lib/opportunities';
import { SECTORS, SECTOR_IMAGES, sectorCount } from '../lib/sectors';

const QUICK_SEARCHES = [
  { label: 'Internships', query: 'intern' },
  { label: 'Junior roles', query: 'junior' },
  { label: 'Engineering', query: 'engineer' },
];


const STEPS = [
  {
    title: 'Browse listings',
    body: 'Each listing comes from the employer’s own posting, with the work mode and country it names.',
  },
  {
    title: 'Check who it is open to',
    body: 'Every listing says whether it is open in your country. When the posting does not say, it is labelled as unclear.',
  },
  {
    title: 'Apply on the employer’s site',
    body: 'NextStep does not take applications. You apply directly, and the employer’s posting remains the source of truth.',
  },
];

function firstSentence(text: string): string {
  const cleaned = text.replace(/\s+/g, ' ').trim();
  const match = cleaned.match(/^.{20,200}?[.!?](\s|$)/);
  if (match) return match[0].trim();
  return cleaned.length > 180 ? `${cleaned.slice(0, 177).trimEnd()}…` : cleaned;
}

function FeaturedRole({ item }: { item: Opportunity }) {
  const location = item.location_text.trim();
  return (
    <article className="group relative flex flex-col gap-4 rounded-2xl border border-blue-300/60 bg-blue-50 p-7 transition-all hover:border-accent-blue/40 hover:bg-blue-200/50 md:flex-row md:items-center md:justify-between md:gap-6 md:p-8">
      <div className="max-w-2xl space-y-2">
        <div className="flex flex-wrap items-center gap-x-2.5 gap-y-1 font-mono text-xs text-ink-500">
          <span className="font-medium text-ink-900">{item.employer}</span>
          {location && (
            <>
              <span className="text-blue-300" aria-hidden="true">·</span>
              <span>{location}</span>
            </>
          )}
          <span className="text-blue-300" aria-hidden="true">·</span>
          <span>Updated {formatDate(item.updated_at)}</span>
          {item.eligible_countries.length > 0 && (
            <>
              <span className="text-blue-300" aria-hidden="true">·</span>
              <CountryTags countries={item.eligible_countries} />
            </>
          )}
        </div>
        <h3 className="font-serif text-2xl leading-snug font-medium text-ink-900 transition-colors group-hover:text-accent-blue md:text-3xl">
          <Link
            to={`/opportunities/${encodeURIComponent(`${item.source_key}:${item.external_id}`)}`}
            className="after:absolute after:inset-0"
          >
            {item.title.trim()}
          </Link>
        </h3>
        <p className="line-clamp-2 text-sm text-ink-600">
          {firstSentence(item.description) || 'See the employer’s posting for details.'}
        </p>
      </div>

      <div className="flex shrink-0 flex-row items-center justify-between gap-4 border-t border-blue-300/60 pt-4 md:flex-col md:items-end md:justify-center md:border-t-0 md:pt-0">
        <div className="flex flex-wrap gap-2 md:justify-end">
          <WorkModeTag mode={item.work_mode} />
          <ScopeTag scope={item.scope} />
        </div>
        <span className="flex items-center gap-1 text-xs font-semibold text-accent-navy underline decoration-accent-blue/40 underline-offset-4 group-hover:text-accent-blue group-hover:decoration-accent-blue">
          View details <ArrowRightIcon aria-hidden="true" />
        </span>
      </div>
    </article>
  );
}

export function LandingPage() {
  useDocumentTitle();
  const state = useOpportunities();
  const navigate = useNavigate();
  const [query, setQuery] = useState('');

  const listings = state.status === 'ready' ? state.snapshot.listings : [];
  const stats = directoryStats(listings);
  const featured = sortOpportunities(listings.filter(isOpenInLaunchCountries), 'recent').slice(0, 3);

  function submitSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const q = query.trim();
    navigate(q ? `/opportunities?q=${encodeURIComponent(q)}` : '/opportunities');
  }

  return (
    <>
      <PhotoBand image="/images/hero-towers.jpg" priority innerClassName="py-20 md:py-28">
        <div className="max-w-3xl">
          <p className="mb-6 inline-flex items-center gap-2 border-b border-blue-200/40 pb-1 font-mono text-xs tracking-wider text-blue-200 uppercase">
            <span>Youth Yellow Pages</span>
            <span className="text-blue-300" aria-hidden="true">·</span>
            <span>Attachments, internships &amp; entry-level roles</span>
          </p>

          <h1 id="hero-heading" className="mb-8 font-serif text-5xl leading-[1.08] tracking-[-0.03em] font-normal text-white sm:text-6xl md:text-7xl">
            Find your first <br className="hidden sm:inline" />
            <span className="font-light text-blue-200 italic">step into work.</span>
          </h1>

          <p className="mb-12 max-w-2xl text-lg leading-relaxed text-blue-100 md:text-xl">
            Opportunities from employers across Nigeria, South Africa, Kenya and Ghana. Every listing links to the
            employer&rsquo;s own posting, and says who it is open to.
          </p>

          <form className="mb-5 max-w-2xl" role="search" aria-label="Search opportunities" onSubmit={submitSearch}>
            <div className="flex items-center gap-2 rounded-full border border-blue-200/60 bg-blue-50 p-1.5 shadow-lg shadow-accent-navy/20 transition-all focus-within:border-white">
              <SearchIcon className="ml-4 shrink-0 text-xl text-accent-blue" aria-hidden="true" />
              <label htmlFor="hero-search" className="sr-only">
                Search by role, employer or place
              </label>
              <input
                id="hero-search"
                type="search"
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="Describe what you do (e.g. Python, data analysis, Nairobi)"
                className="w-full min-w-0 border-0 bg-transparent px-2 py-2.5 font-sans text-sm text-ink-900 placeholder:text-ink-500 focus:ring-0 focus:outline-none md:text-base"
              />
              <button
                type="submit"
                className="shrink-0 rounded-full bg-accent-navy px-6 py-2.5 text-xs font-semibold tracking-wide text-white transition-colors hover:bg-ink-900 md:text-sm"
              >
                Search
              </button>
            </div>
          </form>

          <div className="flex max-w-2xl flex-wrap items-center justify-between gap-x-6 gap-y-4 pt-2 text-xs">
            <div className="flex flex-wrap items-center gap-2">
              <span className="font-mono text-[11px] text-blue-200">Quick search:</span>
              {QUICK_SEARCHES.map((item) => (
                <Link
                  key={item.label}
                  to={`/opportunities?q=${encodeURIComponent(item.query)}`}
                  className="rounded-full border border-blue-200/40 bg-white/10 px-3 py-1 text-white transition-colors hover:bg-white/20 focus-visible:outline-blue-200"
                >
                  {item.label}
                </Link>
              ))}
            </div>
            <p className="font-mono text-[11px] tracking-tight text-blue-200" aria-live="polite">
              {state.status === 'ready' &&
                `${formatCount(stats.listings, 'listing')} · ${formatCount(stats.employers, 'employer')} · ${stats.openInLaunchCountries.toLocaleString('en-GB')} open in NG, ZA, KE or GH`}
              {state.status === 'loading' && 'Loading listings…'}
              {state.status === 'error' && 'Listings are unavailable right now'}
            </p>
          </div>
        </div>
      </PhotoBand>

      <Section id="sectors" index="01" title="Sectors" headingId="sectors-heading" kicker="Matching titles in the current listings">
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {SECTORS.map((sector, position) => (
            <Link
              key={sector.id}
              to={`/opportunities?sector=${sector.id}`}
              className="group relative flex flex-col overflow-hidden rounded-2xl border border-blue-300/60 bg-blue-50 transition-all hover:border-accent-blue/40 hover:shadow-lg hover:shadow-accent-navy/10"
            >
              <div className="relative h-40 overflow-hidden">
                <img
                  src={SECTOR_IMAGES[sector.id]}
                  alt=""
                  decoding="async"
                  className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-105"
                />
                <div className="absolute inset-0 bg-accent-blue/45 mix-blend-multiply" aria-hidden="true" />
              </div>
              <div className="flex flex-1 flex-col justify-between gap-4 p-5">
                <div className="flex items-center justify-between">
                  <span className="font-mono text-xs text-ink-500">0{position + 1}</span>
                  <ArrowRightIcon className="-rotate-45 text-accent-blue transition-all group-hover:translate-x-0.5" aria-hidden="true" />
                </div>
                <div>
                  <h3 className="mb-1 font-sans text-base font-semibold text-ink-900">{sector.label}</h3>
                  <p className="font-mono text-xs text-ink-500">
                    {state.status === 'ready' ? formatCount(sectorCount(listings, sector.id), 'listing') : '—'}
                  </p>
                </div>
              </div>
            </Link>
          ))}
        </div>
      </Section>

      <Section
        id="opportunities"
        index="02"
        title="Featured roles"
        headingId="featured-heading"
        kicker="Most recently updated, open in launch countries"
      >
        {state.status === 'loading' && <p className="text-sm text-ink-500">Loading roles…</p>}
        {state.status === 'error' && (
          <p className="text-sm text-ink-500">Featured roles are unavailable right now. You can still browse the directory.</p>
        )}
        {state.status === 'ready' && (
          <div className="space-y-4">
            {featured.map((item) => (
              <FeaturedRole key={`${item.source_key}:${item.external_id}`} item={item} />
            ))}
          </div>
        )}
        {state.status === 'ready' && (
          <Link
            to="/opportunities"
            className="mt-8 inline-flex items-center gap-1 text-sm font-semibold text-accent-navy hover:text-accent-blue"
          >
            Browse all {stats.listings} listings <ArrowRightIcon aria-hidden="true" />
          </Link>
        )}
      </Section>

      <Section id="how-it-works" index="03" title="How it works" headingId="how-heading" kicker="What you can count on today" tone="blue">
        <div className="grid grid-cols-1 gap-10 md:grid-cols-3 lg:gap-14">
          {STEPS.map((step, position) => (
            <div key={step.title} className="space-y-4">
              <span className="block border-b border-blue-200/40 pb-2 font-mono text-xs text-blue-200">0{position + 1}</span>
              <h3 className="font-serif text-2xl font-medium text-white">{step.title}</h3>
              <p className="text-sm leading-relaxed text-blue-100">{step.body}</p>
            </div>
          ))}
        </div>
      </Section>

      <PhotoBand image="/images/city-chicago.jpg" tone="soft" className="py-20" innerClassName="">
        <div className="mb-12 flex flex-col justify-between gap-4 md:flex-row md:items-baseline">
          <div className="flex items-baseline gap-3">
            <span className="font-mono text-sm text-blue-200">04</span>
            <h2 id="numbers-heading" className="font-serif text-3xl font-normal text-white md:text-4xl">
              In the directory
            </h2>
          </div>
          <p className="font-mono text-xs tracking-wider text-blue-200 uppercase">From the current listings</p>
        </div>

        {state.status === 'ready' ? (
          <>
            <dl className="grid grid-cols-2 gap-8 md:gap-12 lg:grid-cols-4">
              {[
                { value: stats.listings, label: 'Listings in the directory' },
                { value: stats.employers, label: 'Employers listing' },
                { value: stats.openInLaunchCountries, label: 'Open in our four launch countries' },
                { value: LAUNCH_COUNTRIES.length, label: 'Launch countries' },
              ].map((figure) => (
                <div key={figure.label} className="flex flex-col gap-2">
                  <dt className="order-2 font-mono text-xs text-blue-200">{figure.label}</dt>
                  <dd className="font-serif text-4xl font-light tracking-tight text-white sm:text-5xl lg:text-6xl">
                    {figure.value.toLocaleString('en-GB')}
                  </dd>
                </div>
              ))}
            </dl>
            <p className="mt-10 max-w-2xl text-xs text-blue-200">
              Counts come from the listings snapshot taken {formatDateTime(state.snapshot.fetched_at)}. Placement outcomes
              will be shown here once they are measured and verified.
            </p>
          </>
        ) : (
          <p className="text-sm text-blue-100">Figures appear once the listings load.</p>
        )}
      </PhotoBand>

      <PhotoBand image="/images/cta-mountains.jpg" tone="soft" className="py-24 md:py-32" innerClassName="">
        <div className="max-w-2xl">
          <p className="mb-4 font-mono text-xs text-blue-200">05 · Get started</p>
          <h2 id="cta-heading" className="mb-4 font-serif text-4xl leading-tight font-normal text-white sm:text-5xl">
            Your first opportunity <br className="hidden sm:inline" />
            <span className="font-light text-blue-200 italic">starts today.</span>
          </h2>
          <p className="mb-8 text-base text-blue-100">
            No fees to browse. Start with the directory, and check each listing’s eligibility before you apply.
          </p>
          <div className="flex flex-col gap-3 sm:flex-row">
            <Link
              to="/opportunities"
              className="inline-flex items-center justify-center rounded-full bg-blue-50 px-6 py-3 text-sm font-semibold tracking-wide text-accent-navy transition-colors hover:bg-blue-200 focus-visible:outline-blue-200"
            >
              Browse listings
            </Link>
            <Link
              to="/standards"
              className="inline-flex items-center justify-center rounded-full border border-blue-200/60 px-6 py-3 text-sm font-semibold text-white transition-colors hover:bg-white/10 focus-visible:outline-blue-200"
            >
              How listings are checked
            </Link>
          </div>
        </div>
      </PhotoBand>
    </>
  );
}
