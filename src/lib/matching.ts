import type { MatchRow } from './api';

export const BAND_LABELS: Record<MatchRow['band'], string> = {
  strong: 'Strong match',
  good: 'Good match',
  partial: 'Partial match',
  weak: 'Weak match',
};

export const CONFIDENCE_LABELS: Record<MatchRow['confidence']['label'], string> = {
  high: 'High confidence',
  medium: 'Medium confidence',
  low: 'Low confidence',
};

export const AVAILABILITY_OPTIONS = [
  { value: 'now', label: 'Available now' },
  { value: 'within_30_days', label: 'Within 30 days' },
  { value: 'flexible', label: 'Flexible' },
] as const;

export const COUNTRY_OPTIONS = [
  { value: 'NG', label: 'Nigeria' },
  { value: 'ZA', label: 'South Africa' },
  { value: 'KE', label: 'Kenya' },
  { value: 'GH', label: 'Ghana' },
] as const;

/** Thresholds on the 0 to 100 score. 0 shows everything, so every job is listed with its score. */
export const MIN_SCORE_OPTIONS = [
  { value: 0, label: 'All jobs' },
  { value: 40, label: 'Partial match and above' },
  { value: 60, label: 'Good match and above' },
  { value: 80, label: 'Strong matches only' },
] as const;

export function formatScore(score: number): string {
  return String(Math.round(score));
}
