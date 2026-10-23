import type { Opportunity, OpportunitySnapshot } from '../lib/opportunities';

function make(overrides: Partial<Opportunity> & Pick<Opportunity, 'external_id' | 'title'>): Opportunity {
  return {
    source_key: 'greenhouse-test',
    employer: 'Test Employer',
    department: '',
    location_text: 'Lagos, Nigeria',
    eligible_countries: ['NG'],
    unmapped_locations: [],
    work_mode: 'onsite_or_hybrid',
    scope: 'in_region',
    source_url: `https://jobs.example.org/${overrides.external_id}`,
    updated_at: '2026-10-05T10:00:00+00:00',
    expires_at: null,
    description: 'Support the team.\n\nYou will learn how the business runs day to day.',
    pay_ranges: [],
    ...overrides,
  };
}

const named: Opportunity[] = [
  make({
    external_id: '101',
    title: 'Payments Analyst',
    employer: 'Moniepoint',
    location_text: 'Lagos',
    updated_at: '2026-10-20T10:00:00+00:00',
  }),
  make({
    external_id: '102',
    title: 'Software Engineer Intern',
    employer: 'Moniepoint',
    work_mode: 'remote',
    scope: 'remote_in_region',
    eligible_countries: ['KE'],
    location_text: 'Remote',
    updated_at: '2026-10-18T10:00:00+00:00',
  }),
  make({
    external_id: '103',
    title: 'Data Analyst',
    employer: 'Jumia',
    eligible_countries: ['ZA', 'KE'],
    scope: 'in_region',
    updated_at: '2026-10-15T10:00:00+00:00',
  }),
  make({
    external_id: '104',
    title: 'Warehouse Supervisor',
    employer: 'Jumia',
    eligible_countries: [],
    scope: 'unspecified',
    location_text: 'Accra',
    updated_at: '2026-10-01T10:00:00+00:00',
    expires_at: '2020-01-10T10:00:00+00:00',
  }),
];

const generated: Opportunity[] = Array.from({ length: 26 }, (_, index) =>
  make({
    external_id: String(200 + index),
    title: `Graduate Trainee ${index + 1}`,
    employer: 'Jumia',
    updated_at: `2026-09-${String((index % 28) + 1).padStart(2, '0')}T10:00:00+00:00`,
  }),
);

export const fixtureListings: Opportunity[] = [...named, ...generated];

export const fixtureSnapshot: OpportunitySnapshot = {
  fetched_at: '2026-10-23T09:41:12+00:00',
  listings: fixtureListings,
};
