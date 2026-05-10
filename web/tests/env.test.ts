import { describe, it, expect } from 'vitest';
import { z } from 'zod';
import { envSchema } from '@/env';

describe('envSchema', () => {
  it('accepts a valid env object', () => {
    const result = envSchema.safeParse({
      VITE_SUPABASE_URL: 'https://test.supabase.co',
      VITE_SUPABASE_ANON_KEY: 'eyJtest123456',
      VITE_API_URL: 'http://localhost:8000',
    });
    expect(result.success).toBe(true);
  });

  it('rejects an env object missing VITE_SUPABASE_URL', () => {
    const result = envSchema.safeParse({
      VITE_SUPABASE_ANON_KEY: 'eyJtest123456',
      VITE_API_URL: 'http://localhost:8000',
    });
    expect(result.success).toBe(false);
  });

  it('rejects a non-URL VITE_SUPABASE_URL', () => {
    const result = envSchema.safeParse({
      VITE_SUPABASE_URL: 'not-a-url',
      VITE_SUPABASE_ANON_KEY: 'eyJtest123456',
      VITE_API_URL: 'http://localhost:8000',
    });
    expect(result.success).toBe(false);
  });

  it('exports the inferred Env type', () => {
    type Env = z.infer<typeof envSchema>;
    const e: Env = {
      VITE_SUPABASE_URL: 'https://x.co',
      VITE_SUPABASE_ANON_KEY: 'k',
      VITE_API_URL: 'http://l',
    };
    expect(e.VITE_API_URL).toBeDefined();
  });
});
