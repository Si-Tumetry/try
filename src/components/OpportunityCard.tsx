import { SCOPE_LABELS, WORK_MODE_LABELS, type Opportunity } from '../lib/opportunities';

const dateFormat = new Intl.DateTimeFormat('en-GB', { day: 'numeric', month: 'short', year: 'numeric' });

function formatDate(value: string): string {
  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? value : dateFormat.format(parsed);
}

export function OpportunityCard({ opportunity }: { opportunity: Opportunity }) {
  const location = opportunity.location_text.trim();
  const countries = opportunity.eligible_countries.length > 0 ? opportunity.eligible_countries.join(', ') : null;

  return (
    <article className="card">
      <header className="card__header">
        <p className="card__employer">{opportunity.employer}</p>
        <h2 className="card__title">{opportunity.title.trim()}</h2>
      </header>

      {opportunity.description.trim() && <p className="card__excerpt">{opportunity.description.trim()}</p>}

      <ul className="card__tags" aria-label="Details">
        <li className="tag">{WORK_MODE_LABELS[opportunity.work_mode]}</li>
        <li className={`tag tag--${opportunity.scope}`}>{SCOPE_LABELS[opportunity.scope]}</li>
        {countries && <li className="tag tag--muted">{countries}</li>}
      </ul>

      <dl className="card__meta">
        {location && (
          <>
            <dt>Location</dt>
            <dd>{location}</dd>
          </>
        )}
        <dt>Updated</dt>
        <dd>
          <time dateTime={opportunity.updated_at}>{formatDate(opportunity.updated_at)}</time>
        </dd>
      </dl>

      <div className="card__footer">
        <a className="button" href={opportunity.source_url} target="_blank" rel="noopener noreferrer">
          View original posting
        </a>
        <span className="card__source">via {opportunity.employer}</span>
      </div>
    </article>
  );
}
