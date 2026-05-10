import { describe, it, expect, vi, beforeEach } from 'vitest';
import { apiFetch, ApiError } from '@/lib/api';

const getSessionMock = vi.fn();
vi.mock('@/lib/supabase', () => ({
  getSupabase: () => ({
    auth: {
      getSession: getSessionMock,
    },
  }),
}));

vi.mock('@/env', () => ({
  validateEnv: () => ({
    VITE_API_URL: 'http://api.test',
    VITE_SUPABASE_URL: 'http://sb.test',
    VITE_SUPABASE_ANON_KEY: 'anon',
  }),
}));

describe('apiFetch', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    getSessionMock.mockReset();
  });

  it('attaches Authorization header when session exists', async () => {
    getSessionMock.mockResolvedValue({ data: { session: { access_token: 'jwt-abc' } } });
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(JSON.stringify({ ok: true }), { status: 200, headers: { 'content-type': 'application/json' } })
    );

    const data = await apiFetch<{ ok: boolean }>('/api/v2/home');

    expect(data).toEqual({ ok: true });
    expect(fetchMock).toHaveBeenCalledWith(
      'http://api.test/api/v2/home',
      expect.objectContaining({
        headers: expect.objectContaining({ Authorization: 'Bearer jwt-abc' }),
      })
    );
  });

  it('omits Authorization when no session', async () => {
    getSessionMock.mockResolvedValue({ data: { session: null } });
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(JSON.stringify({ ok: true }), { status: 200, headers: { 'content-type': 'application/json' } })
    );

    await apiFetch('/api/v2/home');

    const call = fetchMock.mock.calls[0];
    const headers = call[1]?.headers as Record<string, string>;
    expect(headers.Authorization).toBeUndefined();
  });

  it('throws ApiError with status on non-2xx response', async () => {
    getSessionMock.mockResolvedValue({ data: { session: null } });
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(JSON.stringify({ detail: 'Not found' }), {
        status: 404,
        headers: { 'content-type': 'application/json' },
      })
    );

    await expect(apiFetch('/api/v2/match/x')).rejects.toMatchObject({
      name: 'ApiError',
      status: 404,
    });
  });

  it('returns text when content-type is not JSON', async () => {
    getSessionMock.mockResolvedValue({ data: { session: null } });
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response('plain text', { status: 200, headers: { 'content-type': 'text/plain' } })
    );

    const data = await apiFetch<string>('/api/healthz');
    expect(data).toBe('plain text');
  });

  it('ApiError class is thrown correctly', async () => {
    getSessionMock.mockResolvedValue({ data: { session: null } });
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response('{}', { status: 500, headers: { 'content-type': 'application/json' } })
    );

    try {
      await apiFetch('/api/x');
      expect.fail('Should have thrown');
    } catch (e) {
      expect(e).toBeInstanceOf(ApiError);
      expect((e as ApiError).status).toBe(500);
    }
  });
});
