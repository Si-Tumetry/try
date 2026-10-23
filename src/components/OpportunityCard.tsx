import { Link } from 'react-router';
import { ArrowRightIcon } from './Icon';
import { CountryTags, ScopeTag, WorkModeTag } from './EligibilityTag';
import { formatDate } from '../lib/format';
import { listingId, type Opportunity } from '../lib/opportunities';

export function OpportunityCard({ opportunity }: { opportunity: Opportunity }) {
  const location = opportunity.location_text.trim();
  const id = listingId(opportunity);

  return (
    <article className="group relative flex flex-col gap-4 rounded-2xl border border-blue-300/60 bg-blue-50 p-6 transition-all hover:border-accent-blue/40 hover:bg-blue-200/50">
      <header className="space-y-2">
        <p className="text-xs font-medium text-ink-600">{opportunity.employer}</p>
        <h3 className="font-serif text-xl leading-snug font-medium text-ink-900 group-hover:text-accent-blue">
          <Link to={`/opportunities/${encodeURIComponent(id)}`} className="after:absolute after:inset-0">
            {opportunity.title.trim()}
          </Link>
        </h3>
      </header>

      <div className="flex flex-wrap gap-2">
        <WorkModeTag mode={opportunity.work_mode} />
        <ScopeTag scope={opportunity.scope} />
      </div>

      <dl className="grid grid-cols-[auto_1fr] gap-x-3 gap-y-1 font-mono text-xs text-ink-600">
        {location && (
          <>
            <dt className="text-ink-500">Where</dt>
            <dd>{location}</dd>
          </>
        )}
        <dt className="text-ink-500">Updated</dt>
        <dd>
          <time dateTime={opportunity.updated_at}>{formatDate(opportunity.updated_at)}</time>
        </dd>
      </dl>

      <div className="mt-auto flex items-center justify-between gap-3 pt-2">
        <CountryTags countries={opportunity.eligible_countries} />
        <span className="flex items-center gap-1 text-xs font-semibold text-ink-900 group-hover:text-accent-blue">
          View details
          <ArrowRightIcon className="transition-transform group-hover:translate-x-0.5" />
        </span>
      </div>
    </article>
  );
}
