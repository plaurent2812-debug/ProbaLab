// Minimal typed fetcher for V2 TanStack Query hooks.
// Base URL comes from VITE_API_URL. Undefined params are dropped.

const BASE = (import.meta.env.VITE_API_URL ?? 'http://localhost:8000') as string;

export async function apiGet<T>(
  path: string,
  params?: Record<string, string | undefined>,
): Promise<T> {
  const url = new URL(`${BASE}${path}`);
  if (params) {
    for (const [k, v] of Object.entries(params)) {
      if (v !== undefined) url.searchParams.set(k, v);
    }
  }
  const res = await fetch(url.toString(), { credentials: 'include' });
  if (!res.ok) {
    throw new Error(`GET ${path} failed: ${res.status}`);
  }
  return (await res.json()) as T;
}
