import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { createMemoryRouter, RouterProvider } from 'react-router';
import { routes } from './routes';
import { clearOpportunityCache } from './lib/opportunities';
import { fixtureSnapshot } from './test/fixtures';

function renderAt(path: string) {
  const router = createMemoryRouter(routes, { initialEntries: [path] });
  return render(<RouterProvider router={router} />);
}

function stubSnapshotFetch() {
  vi.stubGlobal(
    'fetch',
    vi.fn(async () => new Response(JSON.stringify(fixtureSnapshot), { status: 200 })),
  );
}

describe('site routes', () => {
  beforeEach(() => {
    clearOpportunityCache();
    stubSnapshotFetch();
  });

  afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
  });

  describe('landing page', () => {
    it('shows the hero, live directory counts and featured roles', async () => {
      renderAt('/');

      expect(await screen.findByRole('heading', { level: 1, name: /step into work/i })).toBeInTheDocument();
      expect(await screen.findByText(/2 employers · /)).toBeInTheDocument();
      expect(screen.getByRole('heading', { name: 'Payments Analyst' })).toBeInTheDocument();
    });

    it('sends a hero search to the directory with the query', async () => {
      renderAt('/');
      await screen.findByText(/2 employers · /);

      fireEvent.change(screen.getByLabelText('Search by role, employer or place'), { target: { value: 'python' } });
      fireEvent.submit(screen.getByRole('search', { name: 'Search opportunities' }));

      expect(await screen.findByRole('heading', { level: 1, name: 'Opportunities' })).toBeInTheDocument();
      expect(screen.getByText('No opportunities match these filters.')).toBeInTheDocument();
    });

    it('does not show unverified figures', async () => {
      renderAt('/');
      await screen.findByText(/2 employers · /);

      expect(screen.queryByText(/94\.6/)).not.toBeInTheDocument();
      expect(screen.queryByText(/1,420/)).not.toBeInTheDocument();
      expect(screen.queryByText(/48 hrs/)).not.toBeInTheDocument();
    });
  });

  describe('directory', () => {
    it('shows the first page of listings and a show-more control', async () => {
      renderAt('/opportunities');

      expect(await screen.findByText('Showing 24 of 30 opportunities')).toBeInTheDocument();
      expect(screen.getAllByRole('heading', { level: 3 })).toHaveLength(24);

      fireEvent.click(screen.getByRole('button', { name: 'Show more' }));
      expect(await screen.findByText('Showing 30 of 30 opportunities')).toBeInTheDocument();
    });

    it('applies the sector in the URL', async () => {
      renderAt('/opportunities?sector=data');

      expect(await screen.findByText('Showing 1 of 1 opportunity')).toBeInTheDocument();
      expect(screen.getByRole('heading', { name: 'Data Analyst' })).toBeInTheDocument();
    });

    it('filters by search text and clears back to everything', async () => {
      renderAt('/opportunities');
      await screen.findByText('Showing 24 of 30 opportunities');

      fireEvent.change(screen.getByRole('searchbox'), { target: { value: 'payments' } });
      expect(await screen.findByText('Showing 1 of 1 opportunity')).toBeInTheDocument();
      expect(screen.queryByRole('button', { name: 'Show more' })).not.toBeInTheDocument();

      fireEvent.click(screen.getByRole('button', { name: 'Clear filters' }));
      await waitFor(() => expect(screen.getByText('Showing 24 of 30 opportunities')).toBeInTheDocument());
    });

    it('links each card to its detail page', async () => {
      renderAt('/opportunities?sector=software');
      const card = await screen.findByRole('heading', { name: 'Software Engineer Intern' });

      expect(within(card).getByRole('link')).toHaveAttribute(
        'href',
        '/opportunities/greenhouse-test%3A102',
      );
    });

    it('shows an error when the listings cannot be loaded', async () => {
      clearOpportunityCache();
      vi.stubGlobal('fetch', vi.fn(async () => new Response('nope', { status: 500 })));
      renderAt('/opportunities');

      expect(await screen.findByRole('alert')).toHaveTextContent('Could not load listings (HTTP 500)');
    });
  });

  describe('opportunity detail', () => {
    it('shows the posting as plain text with a link to the employer', async () => {
      renderAt('/opportunities/greenhouse-test%3A101');

      expect(await screen.findByRole('heading', { level: 1, name: 'Payments Analyst' })).toBeInTheDocument();
      expect(screen.getByText('You will learn how the business runs day to day.')).toBeInTheDocument();

      const apply = screen.getByRole('link', { name: /apply on the employer/i });
      expect(apply).toHaveAttribute('href', 'https://jobs.example.org/101');
      expect(apply).toHaveAttribute('target', '_blank');
      expect(apply).toHaveAttribute('rel', 'noopener noreferrer');
    });

    it('explains an expired posting and hides the apply button', async () => {
      renderAt('/opportunities/greenhouse-test%3A104');

      expect(await screen.findByText('This posting has passed its expiry date.')).toBeInTheDocument();
      expect(screen.queryByRole('link', { name: /apply on the employer/i })).not.toBeInTheDocument();
    });

    it('says when the listing does not exist', async () => {
      renderAt('/opportunities/greenhouse-test%3A999');

      expect(await screen.findByRole('heading', { name: 'Listing not found' })).toBeInTheDocument();
    });
  });

  describe('standing pages', () => {
    it('renders the standards page with the eligibility labels', async () => {
      renderAt('/standards');

      expect(await screen.findByRole('heading', { level: 1, name: 'How listings are checked' })).toBeInTheDocument();
      expect(screen.getByText('Eligibility unclear')).toBeInTheDocument();
    });

    it('marks the legal pages as drafts', async () => {
      renderAt('/privacy');

      expect(await screen.findByRole('note')).toHaveTextContent('Draft.');
    });

    it('keeps member pages out of navigation until they are switched on', async () => {
      renderAt('/');

      await screen.findByRole('heading', { level: 1, name: /step into work/i });
      expect(screen.queryByRole('link', { name: 'My matches' })).not.toBeInTheDocument();
      expect(screen.queryByRole('link', { name: /upload my cv/i })).not.toBeInTheDocument();
    });

    it('renders a not-found page for unknown addresses', async () => {
      renderAt('/no-such-page');

      expect(await screen.findByRole('heading', { name: 'We could not find that page' })).toBeInTheDocument();
    });
  });
});
