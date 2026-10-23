import { Link } from 'react-router';
import { SECTORS } from '../lib/sectors';
import { Wordmark } from './SiteHeader';

export function SiteFooter() {
  return (
    <footer className="w-full border-t border-ink-900/10 bg-cream-50 pt-16 pb-12">
      <div className="mx-auto max-w-7xl px-6 lg:px-12">
        <div className="mb-16 grid grid-cols-1 gap-10 md:grid-cols-3">
          <div className="space-y-4">
            <Wordmark />
            <p className="text-xs leading-relaxed text-ink-500">
              Attachments, internships and entry-level roles from employers across Nigeria, South Africa, Kenya and
              Ghana. Every listing links to the employer&rsquo;s own posting.
            </p>
          </div>

          <div className="space-y-3">
            <h2 className="font-mono text-xs tracking-wider text-ink-500 uppercase">Directory</h2>
            <ul className="space-y-2 text-xs text-ink-600">
              {SECTORS.map((sector) => (
                <li key={sector.id}>
                  <Link className="transition-colors hover:text-ink-900" to={`/opportunities?sector=${sector.id}`}>
                    {sector.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          <div className="space-y-3">
            <h2 className="font-mono text-xs tracking-wider text-ink-500 uppercase">About NextStep</h2>
            <ul className="space-y-2 text-xs text-ink-600">
              <li>
                <Link className="transition-colors hover:text-ink-900" to="/standards">
                  How listings are checked
                </Link>
              </li>
              <li>
                <Link className="transition-colors hover:text-ink-900" to="/about">
                  About
                </Link>
              </li>
            </ul>
          </div>
        </div>

        <div className="flex flex-col items-center justify-between gap-4 border-t border-ink-900/10 pt-8 font-mono text-xs text-ink-500 sm:flex-row">
          <p>&copy; {new Date().getFullYear()} NextStep. Built for early career mobility across Africa.</p>
          <nav aria-label="Legal" className="flex items-center gap-6">
            <Link className="transition-colors hover:text-ink-900" to="/privacy">
              Privacy
            </Link>
            <Link className="transition-colors hover:text-ink-900" to="/terms">
              Terms
            </Link>
            <Link className="transition-colors hover:text-ink-900" to="/accessibility">
              Accessibility
            </Link>
          </nav>
        </div>
      </div>
    </footer>
  );
}
