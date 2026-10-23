export class ApiError extends Error {
  readonly status: number;
  readonly code: string;

  constructor(status: number, code: string, message: string) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.code = code;
  }
}

export interface ProfileSkill {
  skill_id: string;
  name: string;
  level: number;
}

export interface Profile {
  profile_id: string;
  country: string;
  availability: 'now' | 'within_30_days' | 'flexible' | null;
  searchable: boolean;
  skills: ProfileSkill[];
}

export interface SkillRow {
  name: string;
  must_have: boolean;
  required_level: number;
  level: number;
  coverage: number;
}

export interface NextProject {
  for_skill: string;
  project: string;
}

export interface MatchRow {
  listing_id: string;
  title: string;
  type: string;
  employer: string | null;
  location: string | null;
  eligible_countries: string[];
  scope: string;
  in_your_country: boolean;
  source: string | null;
  source_url: string | null;
  demo: boolean;
  expires_at: string | null;
  score: number;
  band: 'strong' | 'good' | 'partial' | 'weak';
  confidence: { value: number; label: 'high' | 'medium' | 'low' };
  matched_skills: SkillRow[];
  missing_skills: SkillRow[];
  next_project: NextProject | null;
}

export interface MatchesResponse {
  results: MatchRow[];
  total_matching: number;
  next_cursor: string | null;
}

export interface SkillGap {
  listing_id: string;
  score: number;
  band: string;
  matched_skills: SkillRow[];
  missing_skills: SkillRow[];
  projects: NextProject[];
}

export interface CreatedProfile {
  token: string;
  profile: Profile;
}

export interface MatchQuery {
  limit?: number;
  minScore?: number;
  cursor?: string | null;
}

const BASE = '/v1';

async function request<T>(
  path: string,
  options: { method?: string; token?: string; body?: FormData; signal?: AbortSignal } = {},
): Promise<T> {
  const headers: Record<string, string> = {};
  if (options.token) {
    headers.authorization = `Bearer ${options.token}`;
  }

  const response = await fetch(`${BASE}${path}`, {
    method: options.method ?? 'GET',
    headers,
    body: options.body,
    signal: options.signal,
  });

  if (response.status === 204) {
    return undefined as T;
  }

  const data = (await response.json().catch(() => null)) as { error?: { code?: string; message?: string } } | null;
  if (!response.ok) {
    throw new ApiError(
      response.status,
      data?.error?.code ?? 'error',
      data?.error?.message ?? `Something went wrong (HTTP ${response.status})`,
    );
  }
  return data as T;
}

export function createProfile(form: FormData): Promise<CreatedProfile> {
  return request<CreatedProfile>('/profiles', { method: 'POST', body: form });
}

export async function getProfile(token: string): Promise<Profile> {
  const body = await request<{ profile: Profile }>('/me/profile', { token });
  return body.profile;
}

export async function updateProfile(token: string, form: FormData): Promise<Profile> {
  const body = await request<{ profile: Profile }>('/me/profile', { method: 'PUT', token, body: form });
  return body.profile;
}

export function deleteProfile(token: string): Promise<void> {
  return request<void>('/me/profile', { method: 'DELETE', token });
}

export function getMatches(token: string, query: MatchQuery = {}, signal?: AbortSignal): Promise<MatchesResponse> {
  const params = new URLSearchParams();
  params.set('limit', String(query.limit ?? 20));
  if (query.minScore !== undefined) params.set('min_score', String(query.minScore));
  if (query.cursor) params.set('cursor', query.cursor);
  return request<MatchesResponse>(`/me/matches?${params.toString()}`, { token, signal });
}

export function getSkillGap(token: string, listingId: string): Promise<SkillGap> {
  return request<SkillGap>(`/me/matches/${encodeURIComponent(listingId)}`, { token });
}
