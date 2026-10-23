import type { ReactNode } from 'react';
import { isRouteErrorResponse, Link, useRouteError } from 'react-router';
import { ArrowRightIcon } from '../components/Icon';
import { PhotoBand } from '../components/PhotoBand';
import { useDocumentTitle } from '../hooks/useDocumentTitle';

function Panel({ code, title, children }: { code: string; title: string; children: ReactNode }) {
  return (
    <PhotoBand image="/images/city-chicago.jpg" className="flex min-h-[70vh] items-center" innerClassName="py-28 text-center">
      <div className="mx-auto max-w-2xl">
        <p className="font-mono text-xs tracking-wider text-blue-200">{code}</p>
        <h1 className="mt-4 font-serif text-4xl leading-tight font-normal text-white md:text-5xl">{title}</h1>
        <div className="mt-6 text-blue-100">{children}</div>
        <div className="mt-10 flex flex-col items-center justify-center gap-3 sm:flex-row">
          <Link
            to="/"
            className="inline-flex items-center rounded-full bg-blue-50 px-6 py-3 text-sm font-semibold text-accent-navy transition-colors hover:bg-blue-200 focus-visible:outline-blue-200"
          >
            Go home
          </Link>
          <Link
            to="/opportunities"
            className="inline-flex items-center gap-1 rounded-full border border-blue-200/60 px-6 py-3 text-sm font-semibold text-white transition-colors hover:bg-white/10 focus-visible:outline-blue-200"
          >
            Browse opportunities <ArrowRightIcon aria-hidden="true" />
          </Link>
        </div>
      </div>
    </PhotoBand>
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
        className="mt-6 min-h-11 rounded-full border border-blue-200/60 px-5 text-sm font-semibold text-white hover:bg-white/10"
      >
        Reload this page
      </button>
    </Panel>
  );
}
