import { Link } from 'react-router';
import { ProsePage, ProseSection } from '../components/ProsePage';
import { useDocumentTitle } from '../hooks/useDocumentTitle';
import { SCOPE_LABELS } from '../lib/opportunities';

const SCOPE_MEANINGS: Record<keyof typeof SCOPE_LABELS, string> = {
  in_region: 'Onsite or hybrid in Nigeria, South Africa, Kenya or Ghana, or open to people in those countries.',
  remote_in_region: 'Remote, and the posting names one of the four launch countries.',
  outside_region: 'Onsite or hybrid in another country. Shown, and labelled as not open in your country.',
  remote_outside_region: 'Remote, and the posting names only other countries. Shown, and labelled.',
  unspecified: 'The posting does not say who it is open to. Shown, and labelled as unclear.',
};

export function StandardsPage() {
  useDocumentTitle('How listings are checked');

  return (
    <ProsePage
      image="/images/sector-data-dashboard.jpg"
      eyebrow="Standards"
      title="How listings are checked"
      intro="NextStep shows opportunities from employers’ own public postings. This page explains where they come from, what we label, and what we have not yet put in place."
    >
      <ProseSection title="Where listings come from">
        <p>
          Each listing is copied from an employer’s public job board, with the employer’s name, title, location and
          description. HTML is removed from the description, and the text is shown as plain text. The original posting
          is always linked, and it is the source of truth. If a listing and its posting disagree, the posting wins.
        </p>
        <p>Listings are refreshed from those boards when the snapshot is updated. The date of the last refresh is shown on the directory.</p>
      </ProseSection>

      <ProseSection title="Eligibility labels">
        <p>Every listing carries one of five eligibility labels. We use these exact words everywhere.</p>
        <dl className="space-y-4">
          {(Object.keys(SCOPE_LABELS) as (keyof typeof SCOPE_LABELS)[]).map((scope) => (
            <div key={scope} className="rounded-xl border border-blue-300/60 bg-blue-50 p-5">
              <dt className="font-semibold text-ink-900">{SCOPE_LABELS[scope]}</dt>
              <dd className="mt-1 text-[15px] text-ink-600">{SCOPE_MEANINGS[scope]}</dd>
            </div>
          ))}
        </dl>
      </ProseSection>

      <ProseSection title="What we will not use">
        <p>
          When matching features are built, they will not use names, photographs, gender, age, national ID numbers or
          school names. These fields are not collected for ranking. Matching is not live in this version, so nothing
          on this site ranks people today.
        </p>
      </ProseSection>

      <ProseSection title="Not yet in place">
        <p>We do not yet offer these, and we will not describe them as available until they are:</p>
        <ul className="list-disc space-y-2 pl-6">
          <li>A verified employer seal. The process for checking an employer is still being defined.</li>
          <li>A placement guarantee. Any guarantee will be published only after its terms are written and reviewed.</li>
          <li>Measured outcomes such as placements or retention. These will be published only once they are recorded and verified.</li>
        </ul>
      </ProseSection>

      <p className="text-sm text-ink-500">
        Questions about a listing? Use the link on the listing to contact the employer, or read the{' '}
        <Link className="text-accent-blue underline underline-offset-4" to="/privacy">
          privacy notice
        </Link>{' '}
        for how we handle data.
      </p>
    </ProsePage>
  );
}
