/**
 * Auth helper functions for EmbedIQ.
 * JWT token is stored as 'embediq_token' in localStorage.
 */

/** Retrieve the stored JWT token, or null if not available. */
export function getToken(): string | null {
  return typeof window !== 'undefined'
    ? localStorage.getItem('embediq_token')
    : null;
}

/** Persist a JWT token to localStorage. */
export function setToken(token: string): void {
  localStorage.setItem('embediq_token', token);
}

/** Remove the JWT token from localStorage (logout). */
export function clearToken(): void {
  localStorage.removeItem('embediq_token');
}

/** Returns true when a token is present (does not validate expiry). */
export function isAuthenticated(): boolean {
  return !!getToken();
}
