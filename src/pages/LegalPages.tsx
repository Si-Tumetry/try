import { ProsePage, ProseSection } from '../components/ProsePage';
import { useDocumentTitle } from '../hooks/useDocumentTitle';

const DRAFT_NOTICE =
  'Draft. This text describes the current site and must be reviewed by counsel before it is relied on. Items in [square brackets] are still to be confirmed.';

export function PrivacyPage() {
  useDocumentTitle('Privacy');
  return (
    <ProsePage eyebrow="Legal" title="Privacy notice" notice={DRAFT_NOTICE}>
      <ProseSection title="What this site collects">
        <p>
          The directory does not yet have accounts, and no forms on this site send data to us. You can browse listings
          without signing in or giving your name, email or any other personal detail.
        </p>
        <p>
          Our hosting provider keeps standard server logs, which can include IP addresses and request times. We do not
          currently use analytics or advertising cookies.
        </p>
      </ProseSection>
      <ProseSection title="Listings">
        <p>
          The listings are employers’ own public postings. They are not personal data about you, and the employer
          remains responsible for its posting. When you apply, you apply on the employer’s site, and their privacy
          practices apply.
        </p>
      </ProseSection>
      <ProseSection title="Contact">
        <p>Questions about this notice: [contact address to be confirmed].</p>
      </ProseSection>
    </ProsePage>
  );
}

export function TermsPage() {
  useDocumentTitle('Terms');
  return (
    <ProsePage eyebrow="Legal" title="Terms of use" notice={DRAFT_NOTICE}>
      <ProseSection title="Using the directory">
        <p>
          NextStep lists opportunities from employers’ public postings so that people can find them. You may browse and
          share the directory for personal, non-commercial use.
        </p>
      </ProseSection>
      <ProseSection title="Listings and employers">
        <p>
          NextStep does not employ, interview or pay anyone listed here, and does not guarantee a role, a pay rate or
          a response. Details come from the employer’s posting, which may change or close at any time. Check the
          original posting before you apply.
        </p>
      </ProseSection>
      <ProseSection title="Changes">
        <p>We may change these terms. The date of the last change will be shown here: [date to be confirmed].</p>
      </ProseSection>
    </ProsePage>
  );
}

export function AccessibilityPage() {
  useDocumentTitle('Accessibility');
  return (
    <ProsePage eyebrow="Legal" title="Accessibility statement" notice={DRAFT_NOTICE}>
      <ProseSection title="Our commitment">
        <p>
          We aim to meet WCAG 2.2 Level AA. The site is built to work with a keyboard, with screen readers and with
          zoom, and it respects reduced-motion settings.
        </p>
      </ProseSection>
      <ProseSection title="Known limits">
        <p>
          We have not yet had an independent accessibility audit, and we have not yet tested every page with every
          assistive technology. Employers’ own job pages, which you reach from the listings, are outside our control.
        </p>
      </ProseSection>
      <ProseSection title="Report a barrier">
        <p>
          If something on this site is hard to use, tell us at [accessibility contact to be confirmed]. We will reply
          and tell you what we will do.
        </p>
      </ProseSection>
    </ProsePage>
  );
}
