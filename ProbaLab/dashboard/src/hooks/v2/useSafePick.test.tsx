import { describe, it, expect } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import type { ReactNode } from 'react';
import { useSafePick } from './useSafePick';

function wrapper({ children }: { children: ReactNode }) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
}

describe('useSafePick', () => {
  it('returns a flat SafePick when the backend wraps it in {date, safe_pick, fallback_message}', async () => {
    const { result } = renderHook(() => useSafePick('2026-04-21'), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    // Hook must unwrap and adapt to the SafePick shape used by components.
    expect(result.current.data?.betLabel).toBeDefined();
    expect(result.current.data?.odd).toBe(1.85);
    expect(result.current.data?.probability).toBeCloseTo(0.58, 2);
    expect(result.current.data?.fixtureId).toBe('fx-1');
  });

  it('returns null when the backend payload has safe_pick: null', async () => {
    const { result } = renderHook(() => useSafePick('2026-04-22-empty'), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toBeNull();
  });
});
