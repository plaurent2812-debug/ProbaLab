import { describe, it, expect } from 'vitest';
import type { PerformanceSummary } from '@/types/v2/performance';

const API = import.meta.env.VITE_API_URL ?? 'http://localhost:8000';

describe('MSW handlers', () => {
  it('GET /api/safe-pick returns the backend wrapper shape', async () => {
    const res = await fetch(`${API}/api/safe-pick?date=2026-04-21`);
    expect(res.status).toBe(200);
    const data = await res.json();
    expect(data.safe_pick.market).toBe('1X2');
    expect(data.safe_pick.odds).toBeGreaterThan(1);
    expect(data.safe_pick.confidence).toBeGreaterThan(0);
    expect(data.safe_pick.confidence).toBeLessThanOrEqual(1);
  });

  it('GET /api/matches returns backend groups + total', async () => {
    const res = await fetch(`${API}/api/matches?date=2026-04-21`);
    const data = await res.json();
    expect(data.total).toBe(3);
    expect(data.groups.flatMap((group: { matches: unknown[] }) => group.matches)).toHaveLength(3);
  });

  it('GET /api/matches?value_only=true filters to value signals', async () => {
    const res = await fetch(`${API}/api/matches?date=2026-04-21&value_only=true`);
    const data = await res.json();
    const matches = data.groups.flatMap((group: { matches: Array<{ signals: string[] }> }) => group.matches);
    expect(matches.length).toBeGreaterThan(0);
    expect(matches.every((m: { signals: string[] }) => m.signals.includes('value'))).toBe(true);
  });

  it('GET /api/performance/summary returns KPIs', async () => {
    const res = await fetch(`${API}/api/performance/summary?window=30`);
    const data = (await res.json()) as PerformanceSummary;
    expect(data.roi30d.value).toBeCloseTo(12.4);
    expect(data.bankroll.currency).toBe('EUR');
  });
});
