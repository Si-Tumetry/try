import { describe, expect, it } from 'vitest';
import {
  EMPTY_FILTERS,
  countryOptions,
  directoryStats,
  filterOpportunities,
  findOpportunity,
  isExpired,
  listingId,
  sortOpportunities,
} from './opportunities';
import { sectorCount } from './sectors';
import { fixtureListings } from '../test/fixtures';

const byId = (items: { external_id: string }[]) => items.map((item) => item.external_id);

describe('filterOpportunities', () => {
  it('returns everything when no filter is set', () => {
    expect(filterOpportunities(fixtureListings, EMPTY_FILTERS)).toHaveLength(fixtureListings.length);
  });

  it('matches a country against any of the eligible countries', () => {
    const result = filterOpportunities(fixtureListings, { ...EMPTY_FILTERS, country: 'KE' });
    expect(byId(result)).toEqual(['102', '103']);
  });

  it('excludes listings with no eligible countries when a country is chosen', () => {
    const result = filterOpportunities(fixtureListings, { ...EMPTY_FILTERS, country: 'GH' });
    expect(result).toEqual([]);
  });

  it('filters by work mode and scope together', () => {
    const result = filterOpportunities(fixtureListings, {
      ...EMPTY_FILTERS,
      workMode: 'remote',
      scope: 'remote_in_region',
    });
    expect(byId(result)).toEqual(['102']);
  });

  it('filters by sector using whole words in the title', () => {
    expect(byId(filterOpportunities(fixtureListings, { ...EMPTY_FILTERS, sector: 'data' }))).toEqual(['103']);
    expect(byId(filterOpportunities(fixtureListings, { ...EMPTY_FILTERS, sector: 'finance' }))).toEqual(['101']);
  });

  it('requires every search term to match, ignoring case', () => {
    const hit = filterOpportunities(fixtureListings, { ...EMPTY_FILTERS, query: '  MONIE analyst ' });
    expect(byId(hit)).toEqual(['101']);

    const miss = filterOpportunities(fixtureListings, { ...EMPTY_FILTERS, query: 'monie intern' });
    expect(miss).toEqual([]);
  });
});

describe('sortOpportunities', () => {
  it('puts the most recently updated listing first without mutating the input', () => {
    const before = byId(fixtureListings);
    const sorted = sortOpportunities(fixtureListings, 'recent');
    expect(byId(sorted).slice(0, 3)).toEqual(['101', '102', '103']);
    expect(byId(fixtureListings)).toEqual(before);
  });

  it('sorts by employer name, then title', () => {
    const sorted = sortOpportunities(fixtureListings, 'employer');
    expect(sorted[0].employer).toBe('Jumia');
    expect(sorted[sorted.length - 1].employer).toBe('Moniepoint');
  });
});

describe('countryOptions', () => {
  it('lists each country code once, sorted', () => {
    expect(countryOptions(fixtureListings)).toEqual(['KE', 'NG', 'ZA']);
  });
});

describe('directoryStats', () => {
  it('counts listings, employers and listings open in a launch country', () => {
    expect(directoryStats(fixtureListings)).toEqual({
      listings: fixtureListings.length,
      employers: 2,
      openInLaunchCountries: 29,
    });
  });
});

describe('listing identity and expiry', () => {
  it('builds a stable id from the source and external id, and finds the listing by it', () => {
    const item = fixtureListings[0];
    expect(listingId(item)).toBe('greenhouse-test:101');
    expect(findOpportunity(fixtureListings, listingId(item))).toBe(item);
    expect(findOpportunity(fixtureListings, 'greenhouse-test:999')).toBeUndefined();
  });

  it('treats a listing as expired only after its expiry date', () => {
    const expired = fixtureListings.find((item) => item.external_id === '104')!;
    expect(isExpired(expired, new Date('2020-01-11T00:00:00Z'))).toBe(true);
    expect(isExpired(expired, new Date('2020-01-09T00:00:00Z'))).toBe(false);
    expect(isExpired(fixtureListings[0], new Date('2030-01-01T00:00:00Z'))).toBe(false);
  });
});

describe('sectorCount', () => {
  it('counts matching listings per sector', () => {
    expect(sectorCount(fixtureListings, 'software')).toBe(1);
    expect(sectorCount(fixtureListings, 'operations')).toBe(1);
  });
});
