import { describe, expect, it } from 'vitest';
import {
  EMPTY_FILTERS,
  countryOptions,
  filterOpportunities,
  sortByUpdated,
  type Opportunity,
} from './opportunities';

function make(overrides: Partial<Opportunity>): Opportunity {
  return {
    source_key: 'greenhouse-test',
    employer: 'Test Employer',
    external_id: '1',
    title: 'Front Desk Intern',
    department: 'Lagos',
    location_text: 'Lagos, Nigeria',
    eligible_countries: ['NG'],
    unmapped_locations: [],
    work_mode: 'onsite_or_hybrid',
    scope: 'in_region',
    source_url: 'https://example.org/jobs/1',
    updated_at: '2026-10-01T10:00:00+00:00',
    expires_at: null,
    description: '',
    pay_ranges: [],
    ...overrides,
  };
}

const items = [
  make({ external_id: '1', title: 'Front Desk Intern', eligible_countries: ['NG'] }),
  make({
    external_id: '2',
    title: 'Data Analyst',
    employer: 'Moniepoint',
    eligible_countries: ['ZA', 'KE'],
    work_mode: 'remote',
    scope: 'remote_in_region',
    updated_at: '2026-10-05T10:00:00+00:00',
  }),
  make({
    external_id: '3',
    title: 'Sales Lead',
    eligible_countries: [],
    scope: 'unspecified',
    updated_at: '2026-09-01T10:00:00+00:00',
  }),
];

describe('filterOpportunities', () => {
  it('returns everything when no filter is set', () => {
    expect(filterOpportunities(items, EMPTY_FILTERS)).toHaveLength(3);
  });

  it('matches a country against any of the eligible countries', () => {
    const result = filterOpportunities(items, { ...EMPTY_FILTERS, country: 'KE' });
    expect(result.map((i) => i.external_id)).toEqual(['2']);
  });

  it('excludes listings with no eligible countries when a country is chosen', () => {
    const result = filterOpportunities(items, { ...EMPTY_FILTERS, country: 'NG' });
    expect(result.map((i) => i.external_id)).toEqual(['1']);
  });

  it('filters by work mode and scope together', () => {
    const result = filterOpportunities(items, {
      ...EMPTY_FILTERS,
      workMode: 'remote',
      scope: 'remote_in_region',
    });
    expect(result.map((i) => i.external_id)).toEqual(['2']);
  });

  it('requires every search term to match, ignoring case', () => {
    const hit = filterOpportunities(items, { ...EMPTY_FILTERS, query: '  MONIE analyst ' });
    expect(hit.map((i) => i.external_id)).toEqual(['2']);

    const miss = filterOpportunities(items, { ...EMPTY_FILTERS, query: 'monie intern' });
    expect(miss).toEqual([]);
  });
});

describe('sortByUpdated', () => {
  it('puts the most recently updated listing first without mutating the input', () => {
    const before = items.map((i) => i.external_id);
    const sorted = sortByUpdated(items).map((i) => i.external_id);
    expect(sorted).toEqual(['2', '1', '3']);
    expect(items.map((i) => i.external_id)).toEqual(before);
  });
});

describe('countryOptions', () => {
  it('lists each country code once, sorted', () => {
    expect(countryOptions(items)).toEqual(['KE', 'NG', 'ZA']);
  });
});
