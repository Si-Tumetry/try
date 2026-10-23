import type { Opportunity } from './opportunities';

export type SectorId = 'software' | 'data' | 'finance' | 'operations';

export interface Sector {
  id: SectorId;
  label: string;
  /** Title and department words that place a listing in this sector. Matched as whole words. */
  keywords: string[];
}

/**
 * Sectors are derived from listing titles and departments, because the listing
 * data has no sector field yet. Counts are therefore approximate. Replace this with
 * the sector field once the listings API provides one.
 */
export const SECTORS: Sector[] = [
  {
    id: 'software',
    label: 'Software & Cloud',
    keywords: ['software', 'engineer', 'engineering', 'developer', 'frontend', 'backend', 'devops', 'cloud', 'qa'],
  },
  {
    id: 'data',
    label: 'Data & Analytics',
    keywords: ['data', 'analytics', 'machine learning', 'scientist'],
  },
  {
    id: 'finance',
    label: 'Finance & Fintech',
    keywords: ['finance', 'fintech', 'accounting', 'accountant', 'payments', 'credit', 'treasury', 'risk'],
  },
  {
    id: 'operations',
    label: 'Logistics & Operations',
    keywords: ['operations', 'logistics', 'supply', 'warehouse', 'procurement', 'fulfilment', 'fulfillment'],
  },
];

export function getSector(id: string): Sector | undefined {
  return SECTORS.find((sector) => sector.id === id);
}

export function matchesSector(item: Opportunity, id: SectorId): boolean {
  const sector = getSector(id);
  if (!sector) {
    return false;
  }
  const text = `${item.title} ${item.department}`.toLowerCase();
  return sector.keywords.some((keyword) => new RegExp(`\\b${keyword}\\b`).test(text));
}

export function sectorCount(items: Opportunity[], id: SectorId): number {
  return items.filter((item) => matchesSector(item, id)).length;
}

/** Decorative photograph for each sector. Chosen to contain no people. */
export const SECTOR_IMAGES: Record<SectorId, string> = {
  software: '/images/sector-software-laptop.jpg',
  data: '/images/sector-data-dashboard.jpg',
  finance: '/images/sector-finance-chart.jpg',
  operations: '/images/sector-operations-warehouse.jpg',
};

export const DEFAULT_LISTING_IMAGE = '/images/city-chicago.jpg';

/** The photograph for a listing: its first matching sector, or a neutral city image. */
export function imageForListing(item: Opportunity): string {
  const sector = SECTORS.find((candidate) => matchesSector(item, candidate.id));
  return sector ? SECTOR_IMAGES[sector.id] : DEFAULT_LISTING_IMAGE;
}
