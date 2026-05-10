/**
 * Tests for validateEnv() boot-time fail-fast contract.
 *
 * The existing env.test.ts only tested envSchema (the Zod schema directly).
 * These tests exercise validateEnv() — the function called in main.tsx — to
 * protect the boot-time fail-fast contract against regressions.
 *
 * We reset the module between tests to clear the cachedEnv singleton, then
 * use vi.stubEnv to control import.meta.env per-test.
 */
import { describe, it, expect, beforeEach, vi } from 'vitest';

// We must re-import the module fresh each test to clear the cachedEnv cache.
// Use vi.resetModules() + dynamic import per-test.
describe('validateEnv()', () => {
  beforeEach(() => {
    vi.resetModules();
    vi.unstubAllEnvs();
  });

  it('throws when VITE_SUPABASE_URL is missing', async () => {
    vi.stubEnv('VITE_SUPABASE_URL', '');
    vi.stubEnv('VITE_SUPABASE_ANON_KEY', 'eyJlongenoughkey');
    vi.stubEnv('VITE_API_URL', 'http://localhost:8000');

    const { validateEnv } = await import('@/env');
    expect(() => validateEnv()).toThrow(/Invalid frontend env vars/);
  });

  it('throws when VITE_SUPABASE_URL is not a valid URL', async () => {
    vi.stubEnv('VITE_SUPABASE_URL', 'not-a-valid-url');
    vi.stubEnv('VITE_SUPABASE_ANON_KEY', 'eyJlongenoughkey');
    vi.stubEnv('VITE_API_URL', 'http://localhost:8000');

    const { validateEnv } = await import('@/env');
    expect(() => validateEnv()).toThrow(/Invalid frontend env vars/);
  });

  it('throws when VITE_SUPABASE_ANON_KEY is shorter than 10 characters', async () => {
    vi.stubEnv('VITE_SUPABASE_URL', 'https://test.supabase.co');
    vi.stubEnv('VITE_SUPABASE_ANON_KEY', 'short');
    vi.stubEnv('VITE_API_URL', 'http://localhost:8000');

    const { validateEnv } = await import('@/env');
    expect(() => validateEnv()).toThrow(/Invalid frontend env vars/);
  });

  it('returns the validated env object on happy path', async () => {
    vi.stubEnv('VITE_SUPABASE_URL', 'https://test.supabase.co');
    vi.stubEnv('VITE_SUPABASE_ANON_KEY', 'eyJlongenoughkey');
    vi.stubEnv('VITE_API_URL', 'http://localhost:8000');

    const { validateEnv } = await import('@/env');
    const env = validateEnv();

    expect(env.VITE_SUPABASE_URL).toBe('https://test.supabase.co');
    expect(env.VITE_SUPABASE_ANON_KEY).toBe('eyJlongenoughkey');
    expect(env.VITE_API_URL).toBe('http://localhost:8000');
  });

  it('returns cached result on second call without re-validating', async () => {
    vi.stubEnv('VITE_SUPABASE_URL', 'https://test.supabase.co');
    vi.stubEnv('VITE_SUPABASE_ANON_KEY', 'eyJlongenoughkey');
    vi.stubEnv('VITE_API_URL', 'http://localhost:8000');

    const { validateEnv } = await import('@/env');
    const first = validateEnv();
    const second = validateEnv();

    // Same object reference — the cache returned
    expect(first).toBe(second);
  });
});
