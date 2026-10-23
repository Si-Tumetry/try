/**
 * Holds the profile token in this browser. This is a stand-in until sign-in exists (DESIGN.md §4.6):
 * the token is shown once when a profile is created, and clearing site data or a server restart loses it.
 */
const KEY = 'nextstep.profileToken';

export function getProfileToken(): string | null {
  try {
    return window.localStorage.getItem(KEY);
  } catch {
    return null;
  }
}

export function saveProfileToken(token: string): void {
  try {
    window.localStorage.setItem(KEY, token);
  } catch {
    // Storage can be unavailable in private modes. The user can still use this visit.
  }
}

export function clearProfileToken(): void {
  try {
    window.localStorage.removeItem(KEY);
  } catch {
    // Nothing to clear.
  }
}
