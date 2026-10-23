import { useEffect, useState } from 'react';
import { Link } from 'react-router';
import { ScopeTag } from '../components/EligibilityTag';
import { ArrowRightIcon, ArrowUpRightIcon } from '../components/Icon';
import { PhotoBand } from '../components/PhotoBand';
import { useDocumentTitle } from '../hooks/useDocumentTitle';
import { ApiError, getMatches, type MatchesResponse, type MatchRow } from '../lib/api';
import { formatDate } from '../lib/format';
import { BAND_LABELS, CONFIDENCE_LABELS, MIN_SCORE_OPTIONS, formatScore } from '../lib/matching';
import { clearProfileToken, getProfileToken } from '../lib/session';
import type { Scope } from '../lib/opportunities';

const PAGE = 20;

const BAND_STYLES: Record<MatchRow['band'], string> = {
  strong: 'bg-accent-blue text-white',
  good: 'bg-blue-300 text-accent-navy',
  partial: 'bg-blue-200 text-accent-navy',
  weak: 'border border-accent-blue/30 text-ink-700',
};

function ScoreBlock({ row }: { row: MatchRow }) {
  return (
    <div className="flex shrink-0 flex-col items-start gap-2 md:w-40 md:items-end">
      <p className="font-serif text-5xl leading-none font-light text-accent-navy">
        {formatScore(row.score)}
        <span className="ml-1 font-sans text-sm font-normal text-ink-500">/100</span>
      </p>
      <div className="flex w-full gap-1" aria-hidden="true">
        {Array.from({ length: 10 }, (_, index) => (
          <span key={index} className={`h-1.5 flex-1 rounded-full ${index < Math.round(row.score / 10) ? 'bg-accent-blue' : 'bg-blue-200'}`} />
        ))}
      </div>
      <span className={`rounded-full px-2.5 py-1 text-xs font-semibold ${BAND_STYLES[row.band]}`}>{BAND_LABELS[row.band]}</span>
      <span className="font-mono text-[11px] text-ink-500">{CONFIDENCE_LABELS[row.confidence.label]}</span>
    </div>
  );
}

function MatchCard({ row }: { row: MatchRow }) {
  const topGap = row.next_project;
  const missing = row.missing_skills.slice(0, 3);
  const matched = row.matched_skills.slice(0, 6);

  return (
    <article className="flex flex-col gap-6 rounded-2xl border border-blue-300/60 bg-blue-50 p-6 md:flex-row md:p-7">
      <div className="min-w-0 flex-1 space-y-4">
        <div className="space-y-2">
          <p className="text-xs font-medium text-ink-600">{row.employer ?? 'Employer not named'}</p>
          <h3 className="font-serif text-2xl leading-snug font-medium text-ink-900">
            <Link to={`/opportunities/${encodeURIComponent(row.listing_id)}`} className="hover:text-accent-blue">
              {row.title.trim()}
            </Link>
          </h3>
          <div className="flex flex-wrap items-center gap-2">
            {row.location && <span className="text-xs text-ink-600">{row.location}</span>}
            <ScopeTag scope={row.scope as Scope} />
            {!row.in_your_country && <span className="text-xs text-ink-500">Not open in your country</span>}
          </div>
        </div>

        {matched.length > 0 && (
          <div>
            <p className="mb-2 font-mono text-[11px] tracking-wider text-ink-500 uppercase">Your matching skills</p>
            <ul className="flex flex-wrap gap-2" aria-label="Matching skills">
              {matched.map((skill) => (
                <li key={skill.name} className="rounded-full bg-accent-blue px-2.5 py-1 text-xs text-white">
                  {skill.name}
                </li>
              ))}
            </ul>
          </div>
        )}

        {missing.length > 0 && (
          <div>
            <p className="mb-2 font-mono text-[11px] tracking-wider text-ink-500 uppercase">To raise this score</p>
            <ul className="flex flex-wrap gap-2" aria-label="Skills to add">
              {missing.map((skill) => (
                <li
                  key={skill.name}
                  className="rounded-full border border-accent-blue/30 px-2.5 py-1 text-xs text-accent-navy"
                >
                  {skill.name}
                  {skill.must_have ? ' · required' : ''}
                </li>
              ))}
            </ul>
            {topGap && (
              <p className="mt-3 text-sm text-ink-700">
                <span className="font-semibold">Next project:</span> {topGap.project}
              </p>
            )}
          </div>
        )}

        <div className="flex flex-wrap items-center gap-x-5 gap-y-2 pt-1 text-sm">
          <Link
            to={`/opportunities/${encodeURIComponent(row.listing_id)}`}
            className="inline-flex items-center gap-1 font-semibold text-accent-navy hover:text-accent-blue"
          >
            View listing <ArrowRightIcon aria-hidden="true" />
          </Link>
          {row.source_url && (
            <a
              href={row.source_url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1 text-ink-600 hover:text-accent-blue"
            >
              Employer’s posting <ArrowUpRightIcon aria-hidden="true" />
            </a>
          )}
          {row.expires_at && <span className="text-xs text-ink-500">Closes {formatDate(row.expires_at)}</span>}
          <span className="text-xs text-ink-500 capitalize">{row.type}</span>
        </div>
      </div>

      <ScoreBlock row={row} />
    </article>
  );
}

export function DashboardPage() {
  useDocumentTitle('My matches');
  const [token] = useState<string | null>(() => getProfileToken());
  const [minScore, setMinScore] = useState(0);
  const [data, setData] = useState<MatchesResponse | null>(null);
  const [rows, setRows] = useState<MatchRow[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sessionEnded, setSessionEnded] = useState(false);

  useEffect(() => {
    if (!token) return;
    const controller = new AbortController();
    setLoading(true);
    setError(null);
    getMatches(token, { limit: PAGE, minScore }, controller.signal)
      .then((response) => {
        setData(response);
        setRows(response.results);
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted) return;
        if (err instanceof ApiError && err.status === 401) {
          clearProfileToken();
          setSessionEnded(true);
        } else {
          setError(err instanceof ApiError ? err.message : 'Your matches could not be loaded. Try again.');
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [token, minScore]);

  async function loadMore() {
    if (!token || !data?.next_cursor) return;
    setLoading(true);
    try {
      const response = await getMatches(token, { limit: PAGE, minScore, cursor: data.next_cursor });
      setData(response);
      setRows((current) => [...current, ...response.results]);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'More matches could not be loaded. Try again.');
    } finally {
      setLoading(false);
    }
  }

  const noProfile = !token || sessionEnded;

  return (
    <>
      <PhotoBand image="/images/directory-laptop-dashboard.jpg" innerClassName="py-14 md:py-16">
        <p className="mb-3 font-mono text-xs tracking-wider text-blue-200 uppercase">Your matches</p>
        <h1 className="max-w-3xl font-serif text-4xl leading-tight font-normal text-white md:text-5xl">
          Jobs ranked by how well your CV fits
        </h1>
        <p className="mt-4 max-w-2xl text-base text-blue-100">
          Each score is out of 100, based on your skills, the skills each job asks for, and how sure we are of them.
        </p>
        {token && (
          <div className="mt-6 flex items-center gap-3">
            <Link
              to="/profile"
              className="inline-flex items-center gap-2 rounded-full bg-accent-navy px-4 py-2 text-sm font-semibold text-white hover:bg-ink-900"
            >
              Update CV <ArrowRightIcon aria-hidden="true" />
            </Link>
            <Link
              to="/dashboard"
              className="inline-flex items-center gap-2 rounded-full bg-blue-200 px-4 py-2 text-sm font-semibold text-accent-blue ring-1 ring-blue-200/40 transition-colors hover:bg-ink-900 focus-visible:outline-blue-200"
            >
              My dashboard
            </Link>
          </div>
        )}
      </PhotoBand>

      <div className="mx-auto max-w-6xl px-6 py-14 lg:px-12">
        {noProfile && (
          <div role={sessionEnded ? 'alert' : undefined} className="mx-auto max-w-2xl rounded-2xl border border-blue-300/60 bg-blue-50 p-8 text-center">
            <h2 className="font-serif text-2xl font-medium text-ink-900">
              {sessionEnded ? 'Your session has ended' : 'Upload your CV to see your matches'}
            </h2>
            <p className="mt-3 text-sm text-ink-600">
              {sessionEnded
                ? 'Your profile token is no longer valid, so create your profile again.'
                : 'We score every listing against the skills in your CV, so you can see where you stand before you apply.'}
            </p>
            <Link
              to="/profile"
              className="mt-6 inline-flex items-center gap-2 rounded-full bg-accent-navy px-6 py-3 text-sm font-semibold text-white hover:bg-ink-900"
            >
              {sessionEnded ? 'Create a profile' : 'Upload my CV'} <ArrowRightIcon aria-hidden="true" />
            </Link>
          </div>
        )}

        {!noProfile && (
          <>
            <div className="mb-8 flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
              <div aria-live="polite">
                <p className="font-semibold text-ink-900">
                  {data ? `${data.total_matching.toLocaleString('en-GB')} jobs matched` : 'Scoring jobs…'}
                </p>
                {data && rows.length < data.total_matching && (
                  <p className="mt-1 text-xs text-ink-500">Showing {rows.length} of {data.total_matching}</p>
                )}
              </div>
              <div className="flex flex-wrap items-center gap-3">
                <label className="flex items-center gap-2 text-sm text-ink-600">
                  Show
                  <select
                    value={minScore}
                    onChange={(event) => {
                      setData(null);
                      setRows([]);
                      setMinScore(Number(event.target.value));
                    }}
                    className="min-h-11 rounded-lg border border-accent-blue/30 bg-blue-50 px-3 text-sm text-ink-900"
                  >
                    {MIN_SCORE_OPTIONS.map((option) => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                </label>
                <Link to="/profile" className="text-sm font-semibold text-accent-navy hover:text-accent-blue">
                  Edit my CV and skills
                </Link>
              </div>
            </div>

            <p role="note" className="mb-6 rounded-lg border border-accent-blue/30 bg-blue-50 px-4 py-3 text-sm text-ink-700">
              Scores are provisional. The semantic-matching step is not switched on yet, so scores sit below the final
              scale and most jobs show as weak. The order still reflects which jobs fit your skills best.
            </p>

            {error && (
              <p role="alert" className="mb-6 rounded-lg border border-red-300 bg-red-50 px-4 py-3 text-sm text-red-900">
                {error}
              </p>
            )}

            {loading && rows.length === 0 && <p role="status" className="py-12 text-center text-sm text-ink-600">Scoring jobs against your CV…</p>}

            {!loading && data && rows.length === 0 && (
              <div className="rounded-2xl border border-blue-300/60 bg-blue-50 p-10 text-center">
                <p className="text-ink-800">No jobs reach this score yet.</p>
                <p className="mt-2 text-sm text-ink-600">Choose “All jobs” to see every listing and its gaps.</p>
              </div>
            )}

            <div className="space-y-5">
              {rows.map((row) => (
                <MatchCard key={row.listing_id} row={row} />
              ))}
            </div>

            {data?.next_cursor && (
              <div className="mt-10 flex justify-center">
                <button
                  type="button"
                  onClick={loadMore}
                  disabled={loading}
                  className="min-h-11 rounded-full border border-accent-blue/30 px-6 text-sm font-semibold text-accent-navy hover:bg-blue-200 disabled:opacity-50"
                >
                  {loading ? 'Loading…' : 'Show more'}
                </button>
              </div>
            )}
          </>
        )}
      </div>
    </>
  );
}
