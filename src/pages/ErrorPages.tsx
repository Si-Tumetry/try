import type { ReactNode } from 'react';
import { isRouteErrorResponse, Link, useRouteError } from 'react-router';
import { ArrowRightIcon } from '../components/Icon';
import { useDocumentTitle } from '../hooks/useDocumentTitle';

function Panel({ code, title, children }: { code: string; title: string; children: ReactNode }) {
  return (
    <div className="mx-auto max-w-2xl px-6 py-28 text-center">
      <p className="font-mono text-xs tracking-wider text-ink-500">{code}</p>
      <h1 className="mt-4 font-serif text-4xl leading-tight font-normal text-ink-900 md:text-5xl">{title}</h1>
      <div className="mt-6 text-ink-600">{children}</div>
      <div className="mt-10 flex flex-col items-center justify-center gap-3 sm:flex-row">
        <Link
          to="/"
          className="inline-flex items-center rounded-full bg-ink-900 px-6 py-3 text-sm font-semibold text-cream-50 transition-colors hover:bg-accent-blue"
        >
          Go home
        </Link>
        <Link
          to="/opportunities"
          className="inline-flex items-center gap-1 rounded-full border border-ink-900/15 px-6 py-3 text-sm font-semibold text-ink-900 transition-colors hover:bg-cream-100"
        >
          Browse opportunities <ArrowRightIcon aria-hidden="true" />
        </Link>
      </div>
    </div>
  );
}

export function NotFoundPage() {
  useDocumentTitle('Page not found');
  return (
    <Panel code="404" title="We could not find that page">
      <p>The link may be out of date, or the page may have moved.</p>
    </Panel>
  );
}

export function RouteErrorPage() {
  const error = useRouteError();
  useDocumentTitle('Something went wrong');

  if (isRouteErrorResponse(error) && error.status === 404) {
    return (
      <Panel code="404" title="We could not find that page">
        <p>The link may be out of date, or the page may have moved.</p>
      </Panel>
    );
  }

  if (import.meta.env.DEV) {
    console.error(error);
  }

  return (
    <Panel code="500" title="Something went wrong on our side">
      <p>Please try again. If the problem continues, come back in a little while.</p>
      <button
        type="button"
        onClick={() => window.location.reload()}
        className="mt-6 min-h-11 rounded-full border border-ink-900/15 px-5 text-sm font-semibold text-ink-900 hover:bg-cream-100"
      >
        Reload this page
      </button>
    </Panel>
  );
}
