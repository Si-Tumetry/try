import { Link } from 'react-router';
import { SECTORS } from '../lib/sectors';
import { Wordmark } from './SiteHeader';

export function SiteFooter() {
  return (
    <footer className="w-full bg-accent-navy pt-16 pb-12 text-blue-100">
      <div className="mx-auto max-w-7xl px-6 lg:px-12">
        <div className="mb-16 grid grid-cols-1 gap-10 md:grid-cols-3">
          <div className="space-y-4">
            <Wordmark />
            <p className="text-xs leading-relaxed text-blue-200">
              Attachments, internships and entry-level roles from employers across Nigeria, South Africa, Kenya and
              Ghana. Every listing links to the employer&rsquo;s own posting.
            </p>
          </div>

          <div className="space-y-3">
            <h2 className="font-mono text-xs tracking-wider text-blue-200 uppercase">Directory</h2>
            <ul className="space-y-2 text-xs text-blue-100">
              {SECTORS.map((sector) => (
                <li key={sector.id}>
                  <Link className="rounded-sm transition-colors hover:text-white focus-visible:outline-blue-200" to={`/opportunities?sector=${sector.id}`}>
                    {sector.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          <div className="space-y-3">
            <h2 className="font-mono text-xs tracking-wider text-blue-200 uppercase">About NextStep</h2>
            <ul className="space-y-2 text-xs text-blue-100">
              <li>
                <Link className="rounded-sm transition-colors hover:text-white focus-visible:outline-blue-200" to="/standards">
                  How listings are checked
                </Link>
              </li>
              <li>
                <Link className="rounded-sm transition-colors hover:text-white focus-visible:outline-blue-200" to="/about">
                  About
                </Link>
              </li>
            </ul>
          </div>
        </div>

        <div className="flex flex-col items-center justify-between gap-4 border-t border-blue-300/25 pt-8 font-mono text-xs text-blue-200 sm:flex-row">
          <p>&copy; {new Date().getFullYear()} NextStep. Built for early career mobility across Africa.</p>
          <nav aria-label="Legal" className="flex items-center gap-6">
            <Link className="rounded-sm transition-colors hover:text-white focus-visible:outline-blue-200" to="/privacy">
              Privacy
            </Link>
            <Link className="rounded-sm transition-colors hover:text-white focus-visible:outline-blue-200" to="/terms">
              Terms
            </Link>
            <Link className="rounded-sm transition-colors hover:text-white focus-visible:outline-blue-200" to="/accessibility">
              Accessibility
            </Link>
          </nav>
        </div>
      </div>
    </footer>
  );
}
