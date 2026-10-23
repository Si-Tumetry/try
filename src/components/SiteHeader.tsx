import { Link, NavLink } from 'react-router';
import { MEMBER_PAGES_ENABLED } from '../lib/features';

const NAV = [
  { to: '/opportunities', label: 'Opportunities', index: '01' },
  { to: '/#how-it-works', label: 'How it works', index: '02' },
  { to: '/#sectors', label: 'Sectors', index: '03' },
  { to: '/about', label: 'About', index: '04' },
];

const MEMBER_NAV = [
  { to: '/dashboard', label: 'My matches', index: '05' },
];

export function Wordmark({ tone = 'light' }: { tone?: 'light' | 'dark' }) {
  const text = tone === 'light' ? 'text-white' : 'text-ink-900';
  const dot = tone === 'light' ? 'bg-blue-200' : 'bg-accent-blue';
  return (
    <Link
      to="/"
      className={`group flex items-center gap-3 rounded-sm focus-visible:outline-blue-200 ${text}`}
      aria-label="NextStep home"
    >
      <span className={`h-2.5 w-2.5 rounded-full ${dot}`} aria-hidden="true" />
      <span className="font-serif text-2xl font-medium tracking-tight italic">NextStep</span>
    </Link>
  );
}

export function SiteHeader() {
  return (
    <header className="sticky top-0 z-40 w-full bg-accent-blue text-white shadow-[0_1px_0_rgba(0,43,102,0.4)]">
      <div className="mx-auto flex h-20 max-w-7xl items-center justify-between gap-6 px-6 lg:px-12">
        <Wordmark />

        <nav aria-label="Main" className="hidden items-center gap-8 text-[13px] font-medium tracking-wide text-blue-100 md:flex">
          {[...NAV, { to: '/profile', label: 'Profile', index: '06' }, ...(MEMBER_PAGES_ENABLED ? MEMBER_NAV : [])].map((item) => (
            <NavLink
              key={item.label}
              to={item.to}
              className="flex items-center gap-1.5 rounded-sm transition-colors hover:text-white focus-visible:outline-blue-200"
            >
              <span className="font-mono text-[11px] text-blue-200/80">{item.index}</span>
              <span>{item.label}</span>
            </NavLink>
          ))}
        </nav>

        <Link
          to="/opportunities"
          className="inline-flex items-center justify-center rounded-full bg-accent-navy px-4 py-2 text-xs font-semibold tracking-wide text-white ring-1 ring-blue-200/40 transition-colors hover:bg-ink-900 focus-visible:outline-blue-200"
        >
          Explore directory
        </Link>

        {MEMBER_PAGES_ENABLED && (
          <Link
            to="/dashboard"
            className="inline-flex items-center justify-center rounded-full bg-blue-200 px-4 py-2 text-xs font-semibold tracking-wide text-accent-blue ring-1 ring-blue-200/40 transition-colors hover:bg-ink-900 focus-visible:outline-blue-200"
          >
            My dashboard
          </Link>
        )}
      </div>
    </header>
  );
}
