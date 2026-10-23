import { Link } from 'react-router';
import { ProsePage, ProseSection } from '../components/ProsePage';
import { useDocumentTitle } from '../hooks/useDocumentTitle';
import { useOpportunities } from '../hooks/useOpportunities';
import { formatDateTime } from '../lib/format';
import { LAUNCH_COUNTRIES, COUNTRY_NAMES, directoryStats } from '../lib/opportunities';

export function AboutPage() {
  useDocumentTitle('About');
  const state = useOpportunities();
  const stats = state.status === 'ready' ? directoryStats(state.snapshot.listings) : null;

  return (
    <ProsePage
      eyebrow="About"
      title="A first step into work"
      intro="NextStep helps young people find attachments, internships and entry-level roles, and shows them clearly who each role is open to. It is part of Youth Yellow Pages, a directory for early career mobility across Africa."
    >
      <ProseSection title="What it is today">
        <p>
          A directory of opportunities from employers’ own public postings, filtered by sector, country, work mode and
          eligibility. Each listing links to the employer’s posting, and applications go to the employer directly.
        </p>
        <p>
          Matching candidates to roles, verifying skills, and tracking placements are planned. They are not part of this
          version.
        </p>
      </ProseSection>

      <ProseSection title="Where we operate">
        <p>
          Our launch countries are {LAUNCH_COUNTRIES.map((code) => COUNTRY_NAMES[code]).join(', ')}. Listings from other
          countries may appear, and they are labelled as not open in your country.
        </p>
      </ProseSection>

      <ProseSection title="The directory right now">
        {stats ? (
          <>
            <ul className="space-y-2">
              <li>{stats.listings.toLocaleString('en-GB')} listings</li>
              <li>{stats.employers.toLocaleString('en-GB')} employers</li>
              <li>{stats.openInLaunchCountries.toLocaleString('en-GB')} listings open in a launch country</li>
            </ul>
            {state.status === 'ready' && (
              <p className="text-sm text-ink-500">Snapshot taken {formatDateTime(state.snapshot.fetched_at)}.</p>
            )}
          </>
        ) : (
          <p>Figures appear once the listings load.</p>
        )}
      </ProseSection>

      <p className="text-sm text-ink-500">
        Read how listings are checked on the{' '}
        <Link className="text-accent-blue underline underline-offset-4" to="/standards">
          standards page
        </Link>
        .
      </p>
    </ProsePage>
  );
}
