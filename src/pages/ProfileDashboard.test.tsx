import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { createMemoryRouter, RouterProvider } from 'react-router';
import { routes } from '../routes';
import { clearProfileToken, saveProfileToken, getProfileToken } from '../lib/session';

const TOKEN = 'token-abc';

const profile = {
  profile_id: 'p-1',
  country: 'NG',
  availability: 'now',
  searchable: false,
  skills: [
    { skill_id: 's-py', name: 'Python', level: 3 },
    { skill_id: 's-sql', name: 'SQL', level: 2 },
  ],
};

function match(overrides: Record<string, unknown>) {
  return {
    listing_id: 'greenhouse-test:1',
    title: 'Data Analyst',
    type: 'job',
    employer: 'Moniepoint',
    location: 'Lagos',
    eligible_countries: ['NG'],
    scope: 'in_region',
    in_your_country: true,
    source: 'greenhouse-test',
    source_url: 'https://jobs.example.org/1',
    demo: true,
    expires_at: null,
    score: 52.4,
    band: 'good',
    confidence: { value: 0.5, label: 'medium' },
    matched_skills: [{ name: 'Python', must_have: true, required_level: 3, level: 3, coverage: 1 }],
    missing_skills: [{ name: 'Power BI', must_have: false, required_level: 2, level: 0, coverage: 0 }],
    next_project: { for_skill: 'Power BI', project: 'Build a sales dashboard from a public dataset' },
    ...overrides,
  };
}

const matches = {
  results: [
    match({ listing_id: 'greenhouse-test:1', title: 'Data Analyst', score: 72.8, band: 'good' }),
    match({ listing_id: 'greenhouse-test:2', title: 'Warehouse Lead', score: 31.2, band: 'partial' }),
  ],
  total_matching: 2,
  next_cursor: null,
};

function jsonResponse(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), { status, headers: { 'content-type': 'application/json' } });
}

function renderAt(path: string) {
  const router = createMemoryRouter(routes, { initialEntries: [path] });
  return render(<RouterProvider router={router} />);
}

describe('dashboard', () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
  });

  it('asks for a CV when there is no profile token', async () => {
    renderAt('/dashboard');

    expect(await screen.findByRole('heading', { name: 'Upload your CV to see your matches' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /upload my cv/i })).toHaveAttribute('href', '/profile');
  });

  it('keeps the server order, highest score first, and shows each score and its gaps', async () => {
    saveProfileToken(TOKEN);
    const fetchMock = vi.fn(async () => jsonResponse(matches));
    vi.stubGlobal('fetch', fetchMock);

    renderAt('/dashboard');

    const titles = await screen.findAllByRole('heading', { level: 3 });
    expect(titles.map((heading) => heading.textContent)).toEqual(['Data Analyst', 'Warehouse Lead']);

    const first = titles[0].closest('article') as HTMLElement;
    expect(within(first).getByText('73')).toBeInTheDocument();
    expect(within(first).getByText('Good match')).toBeInTheDocument();
    expect(within(first).getByText('Build a sales dashboard from a public dataset')).toBeInTheDocument();
    expect(within(first).getByRole('list', { name: 'Matching skills' })).toHaveTextContent('Python');
  });

  it('sends the token and the chosen minimum score', async () => {
    saveProfileToken(TOKEN);
    const fetchMock = vi.fn(async () => jsonResponse(matches));
    vi.stubGlobal('fetch', fetchMock);

    renderAt('/dashboard');
    await screen.findAllByRole('heading', { level: 3 });

    const [url, init] = fetchMock.mock.calls[0] as unknown as [string, RequestInit];
    expect(url).toBe('/v1/me/matches?limit=20&min_score=0');
    expect((init.headers as Record<string, string>).authorization).toBe(`Bearer ${TOKEN}`);

    fireEvent.change(screen.getByRole('combobox'), { target: { value: '60' } });

    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(2));
    expect((fetchMock.mock.calls[1] as unknown as [string])[0]).toBe('/v1/me/matches?limit=20&min_score=60');
  });

  it('ends the session and asks for a new profile when the token is rejected', async () => {
    saveProfileToken(TOKEN);
    vi.stubGlobal(
      'fetch',
      vi.fn(async () =>
        jsonResponse({ error: { code: 'unauthenticated', message: 'sign in again' } }, 401),
      ),
    );

    renderAt('/dashboard');

    expect(await screen.findByRole('heading', { name: 'Your session has ended' })).toBeInTheDocument();
    expect(getProfileToken()).toBeNull();
  });

  it('shows the empty state when no job reaches the chosen score', async () => {
    saveProfileToken(TOKEN);
    vi.stubGlobal('fetch', vi.fn(async () => jsonResponse({ results: [], total_matching: 0, next_cursor: null })));

    renderAt('/dashboard');

    expect(await screen.findByText('No jobs reach this score yet.')).toBeInTheDocument();
  });
});

describe('profile', () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  afterEach(() => {
    cleanup();
    clearProfileToken();
    vi.unstubAllGlobals();
  });

  it('creates a profile, keeps the token, and shows the skills found', async () => {
    const fetchMock = vi.fn(async () => jsonResponse({ token: 'new-token', profile }, 201));
    vi.stubGlobal('fetch', fetchMock);

    renderAt('/profile');
    const submit = await screen.findByRole('button', { name: 'Create my profile' });
    fireEvent.submit(submit.closest('form') as HTMLFormElement);

    expect(await screen.findByRole('list', { name: 'Skills' })).toHaveTextContent('Python');
    expect(getProfileToken()).toBe('new-token');
    expect(fetchMock.mock.calls[0]).toEqual(expect.arrayContaining(['/v1/profiles']));
  });

  it('shows the server message when the CV is rejected', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async () =>
        jsonResponse(
          { error: { code: 'validation_error', message: 'we did not find any skills we recognise in this CV.' } },
          422,
        ),
      ),
    );

    renderAt('/profile');
    fireEvent.submit((await screen.findByRole('button', { name: 'Create my profile' })).closest('form') as HTMLFormElement);

    expect(await screen.findByRole('alert')).toHaveTextContent('we did not find any skills we recognise');
    expect(getProfileToken()).toBeNull();
  });

  it('shows the saved skills when a token already exists', async () => {
    saveProfileToken(TOKEN);
    vi.stubGlobal('fetch', vi.fn(async () => jsonResponse({ profile })));

    renderAt('/profile');

    expect(await screen.findByRole('list', { name: 'Skills' })).toHaveTextContent('SQL');
    expect(screen.getByRole('link', { name: /see my matches/i })).toHaveAttribute('href', '/dashboard');
  });
});
