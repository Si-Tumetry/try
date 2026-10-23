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
}

export const EMPTY_FILTERS: OpportunityFilters = {
  query: '',
  country: '',
  workMode: '',
  scope: '',
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

export function filterOpportunities(
  items: Opportunity[],
  filters: OpportunityFilters,
): Opportunity[] {
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
    if (terms.length > 0) {
      const haystack = [item.title, item.employer, item.department, item.location_text]
        .join(' ')
        .toLowerCase();
      return terms.every((term) => haystack.includes(term));
    }
    return true;
  });
}

export function sortByUpdated(items: Opportunity[]): Opportunity[] {
  return [...items].sort((a, b) => Date.parse(b.updated_at) - Date.parse(a.updated_at));
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

export async function loadOpportunities(url: string, signal?: AbortSignal): Promise<OpportunitySnapshot> {
  const response = await fetch(url, { signal });
  if (!response.ok) {
    throw new Error(`Could not load opportunities (HTTP ${response.status})`);
  }
  const snapshot = (await response.json()) as OpportunitySnapshot;
  if (!Array.isArray(snapshot.listings)) {
    throw new Error('Opportunity data is in an unexpected format');
  }
  return snapshot;
}
