/**
 * Shared API client for EmbedIQ frontend.
 * Automatically attaches the JWT Bearer token from localStorage on every request.
 */

// Use the Next.js proxy by default so browser requests work consistently in
// local development and deployed environments. A direct API URL remains
// available for explicit cross-origin deployments.
const API_BASE = process.env.NEXT_PUBLIC_API_URL || '';

export async function apiRequest<T>(
  path: string,
  options?: RequestInit & { noAuth?: boolean }
): Promise<T> {
  const token =
    typeof window !== 'undefined' ? localStorage.getItem('embediq_token') : null;

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options?.headers as Record<string, string>),
  };

  if (token && !options?.noAuth) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const { noAuth: _noAuth, ...fetchOptions } = options ?? {};

  const res = await fetch(`${API_BASE}${path}`, { ...fetchOptions, headers });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(
      err?.detail?.message || err?.detail || `HTTP ${res.status}`
    );
  }

  return res.json() as Promise<T>;
}
