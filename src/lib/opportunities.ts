import { matchesSector, type SectorId } from './sectors';

export type WorkMode = 'remote' | 'onsite_or_hybrid';

export type Scope =
  | 'in_region'
  | 'remote_in_region'
  | 'outside_region'
  | 'remote_outside_region'
  | 'unspecified';

export interface Opportunity {
  source_key: string;
  employer: string;
  external_id: string;
  title: string;
  department: string;
  location_text: string;
  eligible_countries: string[];
  unmapped_locations: string[];
  work_mode: WorkMode;
  scope: Scope;
  source_url: string;
  updated_at: string;
  expires_at: string | null;
  description: string;
  pay_ranges: unknown[];
}

export interface OpportunitySnapshot {
  fetched_at: string;
  listings: Opportunity[];
}

export interface OpportunityFilters {
  query: string;
  country: string;
  workMode: '' | WorkMode;
  scope: '' | Scope;
  sector: '' | SectorId;
}

export const EMPTY_FILTERS: OpportunityFilters = {
  query: '',
  country: '',
  workMode: '',
  scope: '',
  sector: '',
};

/** The four countries NextStep launches in (README, Youth Yellow Pages scope). */
export const LAUNCH_COUNTRIES = ['NG', 'ZA', 'KE', 'GH'] as const;

export const COUNTRY_NAMES: Record<string, string> = {
  NG: 'Nigeria',
  ZA: 'South Africa',
  KE: 'Kenya',
  GH: 'Ghana',
};

export const WORK_MODE_LABELS: Record<WorkMode, string> = {
  remote: 'Remote',
  onsite_or_hybrid: 'On-site or hybrid',
};

export const SCOPE_LABELS: Record<Scope, string> = {
  in_region: 'In your region',
  remote_in_region: 'Remote, in your region',
  outside_region: 'Not in your country',
  remote_outside_region: 'Remote, not in your country',
  unspecified: 'Eligibility unclear',
};

export const SORT_OPTIONS = [
  { id: 'recent', label: 'Most recent' },
  { id: 'employer', label: 'Employer A to Z' },
] as const;

export type SortId = (typeof SORT_OPTIONS)[number]['id'];

/** Stable identifier used in detail URLs. Source key and external id together are unique. */
export function listingId(item: Opportunity): string {
  return `${item.source_key}:${item.external_id}`;
}

export function findOpportunity(items: Opportunity[], id: string): Opportunity | undefined {
  return items.find((item) => listingId(item) === id);
}

export function filterOpportunities(items: Opportunity[], filters: OpportunityFilters): Opportunity[] {
  const terms = filters.query.trim().toLowerCase().split(/\s+/).filter(Boolean);

  return items.filter((item) => {
    if (filters.country && !item.eligible_countries.includes(filters.country)) {
      return false;
    }
    if (filters.workMode && item.work_mode !== filters.workMode) {
      return false;
    }
    if (filters.scope && item.scope !== filters.scope) {
      return false;
    }
    if (filters.sector && !matchesSector(item, filters.sector)) {
      return false;
    }
    if (terms.length > 0) {
      const haystack = [item.title, item.employer, item.department, item.location_text].join(' ').toLowerCase();
      return terms.every((term) => haystack.includes(term));
    }
    return true;
  });
}

export function sortOpportunities(items: Opportunity[], sort: SortId): Opportunity[] {
  const copy = [...items];
  if (sort === 'employer') {
    return copy.sort((a, b) => a.employer.localeCompare(b.employer) || a.title.localeCompare(b.title));
  }
  return copy.sort((a, b) => Date.parse(b.updated_at) - Date.parse(a.updated_at));
}

export function countryOptions(items: Opportunity[]): string[] {
  const codes = new Set<string>();
  for (const item of items) {
    for (const code of item.eligible_countries) {
      codes.add(code);
    }
  }
  return [...codes].sort();
}

export function isOpenInLaunchCountries(item: Opportunity): boolean {
  return item.eligible_countries.some((code) => (LAUNCH_COUNTRIES as readonly string[]).includes(code));
}

export interface DirectoryStats {
  listings: number;
  employers: number;
  openInLaunchCountries: number;
}

export function directoryStats(items: Opportunity[]): DirectoryStats {
  return {
    listings: items.length,
    employers: new Set(items.map((item) => item.employer)).size,
    openInLaunchCountries: items.filter(isOpenInLaunchCountries).length,
  };
}

export function isExpired(item: Opportunity, now: Date = new Date()): boolean {
  return item.expires_at !== null && Date.parse(item.expires_at) < now.getTime();
}

export async function loadOpportunities(url: string, signal?: AbortSignal): Promise<OpportunitySnapshot> {
  const response = await fetch(url, { signal });
  if (!response.ok) {
    throw new Error(`Could not load listings (HTTP ${response.status})`);
  }
  const snapshot = (await response.json()) as OpportunitySnapshot;
  if (!Array.isArray(snapshot.listings)) {
    throw new Error('Listing data is in an unexpected format');
  }
  return snapshot;
}

let cached: Promise<OpportunitySnapshot> | null = null;

/** Loads the snapshot once per page session. A failed load is not cached, so a retry can succeed. */
export function getOpportunitySnapshot(url: string): Promise<OpportunitySnapshot> {
  if (!cached) {
    cached = loadOpportunities(url).catch((error: unknown) => {
      cached = null;
      throw error;
    });
  }
  return cached;
}

/** Test helper: forget the cached snapshot. */
export function clearOpportunityCache(): void {
  cached = null;
}
