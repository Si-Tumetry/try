import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import App from './App';

const snapshot = {
  fetched_at: '2026-10-23T09:41:12+00:00',
  listings: Array.from({ length: 30 }, (_, index) => ({
    source_key: 'greenhouse-test',
    employer: index === 0 ? 'Moniepoint' : 'Jumia',
    external_id: String(index),
    title: index === 0 ? 'Payments Analyst' : `Role ${index}`,
    department: '',
    location_text: 'Lagos',
    eligible_countries: ['NG'],
    unmapped_locations: [],
    work_mode: 'onsite_or_hybrid',
    scope: 'in_region',
    source_url: `https://example.org/jobs/${index}`,
    updated_at: `2026-10-${String(10 + (index % 10)).padStart(2, '0')}T10:00:00+00:00`,
    expires_at: null,
    description: '<b>not html</b>',
    pay_ranges: [],
  })),
};

describe('App', () => {
  beforeEach(() => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async () => new Response(JSON.stringify(snapshot), { status: 200 })),
    );
  });

  afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
  });

  it('shows the first page of listings and a show-more control', async () => {
    render(<App />);

    expect(await screen.findByText('Showing 24 of 30 opportunities')).toBeInTheDocument();
    expect(screen.getAllByRole('article')).toHaveLength(24);
    expect(screen.getByRole('button', { name: 'Show more' })).toBeInTheDocument();
  });

  it('shows descriptions as plain text, not HTML', async () => {
    render(<App />);

    await screen.findAllByRole('article');
    expect(screen.getAllByText('<b>not html</b>').length).toBeGreaterThan(0);
  });

  it('filters by search text and offers a way to clear', async () => {
    render(<App />);
    await screen.findByText('Showing 24 of 30 opportunities');

    fireEvent.change(screen.getByRole('searchbox'), { target: { value: 'payments' } });

    expect(await screen.findByText('Showing 1 of 1 opportunity')).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Payments Analyst' })).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Show more' })).not.toBeInTheDocument();

    fireEvent.change(screen.getByRole('searchbox'), { target: { value: 'nothing matches this' } });
    expect(await screen.findByText(/No opportunities match these filters/)).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Clear filters' }));
    await waitFor(() => expect(screen.getByText('Showing 24 of 30 opportunities')).toBeInTheDocument());
  });

  it('shows an error when the data cannot be loaded', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => new Response('nope', { status: 500 })));
    render(<App />);

    expect(await screen.findByRole('alert')).toHaveTextContent('Could not load opportunities (HTTP 500)');
  });
});
