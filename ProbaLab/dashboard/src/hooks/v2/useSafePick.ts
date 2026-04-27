import { useQuery } from '@tanstack/react-query';
import { apiGet } from '@/lib/v2/apiClient';
import type { SafePick } from '@/types/v2/matches';

interface BackendSingleSafePick {
  type: 'single';
  fixture_id: string | number;
  odds: number;
  confidence: number;
  market?: string;
  selection?: string;
  kickoff_utc?: string;
  league_id?: string | number;
  league_name?: string;
  home_team?: string;
  away_team?: string;
}

interface BackendSafePickResponse {
  date: string;
  safe_pick: BackendSingleSafePick | { type: 'combo'; [key: string]: unknown } | null;
  fallback_message: string | null;
}

function isFiniteNumber(value: unknown): value is number {
  return typeof value === 'number' && Number.isFinite(value);
}

function adaptSafePick(response: BackendSafePickResponse): SafePick | null {
  const pick = response.safe_pick;
  if (!pick || pick.type !== 'single') return null;
  if (!isFiniteNumber(pick.odds) || !isFiniteNumber(pick.confidence)) return null;

  const homeName = pick.home_team ?? '';
  const awayName = pick.away_team ?? '';
  const matchup = [homeName, awayName].filter(Boolean).join(' vs ');
  const selection = pick.selection ? pick.selection.toUpperCase() : '';
  const market = pick.market ?? '';
  const betLabel =
    market === '1X2' && pick.selection === 'home' && homeName && awayName
      ? `${homeName} gagne vs ${awayName}`
      : market === '1X2' && pick.selection === 'away' && homeName && awayName
        ? `${awayName} gagne vs ${homeName}`
        : market === '1X2' && pick.selection === 'draw' && matchup
          ? `Match nul ${matchup}`
          : [selection, market].filter(Boolean).join(' · ') || matchup || 'Pronostic Safe';

  return {
    fixtureId: String(pick.fixture_id),
    league: {
      id: String(pick.league_id ?? 'unknown'),
      name: pick.league_name ?? '',
      country: '',
      color: '#10b981',
    },
    kickoffUtc: pick.kickoff_utc ?? '',
    home: { id: '', name: homeName, short: homeName },
    away: { id: '', name: awayName, short: awayName },
    betLabel,
    odd: pick.odds,
    probability: pick.confidence,
    justification: response.fallback_message ?? '',
  };
}

export function useSafePick(date: string) {
  return useQuery<BackendSafePickResponse, Error, SafePick | null>({
    queryKey: ['v2', 'safe-pick', date],
    queryFn: () => apiGet<BackendSafePickResponse>('/api/safe-pick', { date }),
    select: adaptSafePick,
    staleTime: 5 * 60 * 1000,
  });
}
