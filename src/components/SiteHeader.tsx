import { Link, NavLink } from 'react-router';

const NAV = [
  { to: '/opportunities', label: 'Opportunities', index: '01' },
  { to: '/#how-it-works', label: 'How it works', index: '02' },
  { to: '/#sectors', label: 'Sectors', index: '03' },
  { to: '/about', label: 'About', index: '04' },
];

export function Wordmark() {
  return (
    <Link to="/" className="group flex items-center gap-3" aria-label="NextStep home">
      <span className="h-2.5 w-2.5 rounded-full bg-accent-blue" aria-hidden="true" />
      <span className="font-serif text-2xl font-medium tracking-tight text-ink-900 italic">NextStep</span>
    </Link>
  );
}

export function SiteHeader() {
  return (
    <header className="sticky top-0 z-40 w-full border-b border-ink-900/10 bg-cream-50/95 backdrop-blur-md">
      <div className="mx-auto flex h-20 max-w-7xl items-center justify-between gap-6 px-6 lg:px-12">
        <Wordmark />

        <nav aria-label="Main" className="hidden items-center gap-8 text-[13px] font-medium tracking-wide text-ink-600 md:flex">
          {NAV.map((item) => (
            <NavLink
              key={item.label}
              to={item.to}
              className="flex items-center gap-1.5 transition-colors hover:text-ink-900"
            >
              <span className="font-mono text-[11px] text-ink-400">{item.index}</span>
              <span>{item.label}</span>
            </NavLink>
          ))}
        </nav>

        <Link
          to="/opportunities"
          className="inline-flex items-center justify-center rounded-full bg-ink-900 px-4 py-2 text-xs font-semibold tracking-wide text-cream-50 transition-colors hover:bg-accent-blue"
        >
          Explore directory
        </Link>
      </div>
    </header>
  );
}
