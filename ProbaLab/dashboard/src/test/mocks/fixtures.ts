import type { LeagueRef, MatchRowData, SafePick } from '@/types/v2/matches';
import type { PerformanceSummary } from '@/types/v2/performance';

export const leagueL1: LeagueRef = {
  id: 'fr-l1',
  name: 'Ligue 1',
  country: 'FR',
  color: '#2563eb',
};

export const leaguePL: LeagueRef = {
  id: 'en-pl',
  name: 'Premier League',
  country: 'EN',
  color: '#7c3aed',
};

export const leagueSA: LeagueRef = {
  id: 'it-sa',
  name: 'Serie A',
  country: 'IT',
  color: '#0ea5e9',
};

export const mockMatches: MatchRowData[] = [
  {
    fixtureId: 'fx-1',
    sport: 'football',
    league: leagueL1,
    kickoffUtc: '2026-04-21T19:00:00Z',
    home: { id: 't-psg', name: 'Paris Saint-Germain', short: 'PSG' },
    away: { id: 't-len', name: 'RC Lens', short: 'LEN' },
    prob1x2: { home: 0.58, draw: 0.24, away: 0.18 },
    signals: ['safe'],
    topValueBet: undefined,
  },
  {
    fixtureId: 'fx-2',
    sport: 'football',
    league: leaguePL,
    kickoffUtc: '2026-04-21T18:30:00Z',
    home: { id: 't-ars', name: 'Arsenal', short: 'ARS' },
    away: { id: 't-che', name: 'Chelsea', short: 'CHE' },
    prob1x2: { home: 0.51, draw: 0.26, away: 0.23 },
    signals: ['value', 'high_confidence'],
    topValueBet: {
      market: 'Over 2.5',
      edgePct: 5.4,
      bestOdd: 1.85,
      bestBook: 'Unibet',
      kellyPct: 1.7,
    },
  },
  {
    fixtureId: 'fx-3',
    sport: 'football',
    league: leagueSA,
    kickoffUtc: '2026-04-21T20:45:00Z',
    home: { id: 't-int', name: 'Inter Milan', short: 'INT' },
    away: { id: 't-mil', name: 'AC Milan', short: 'MIL' },
    prob1x2: { home: 0.42, draw: 0.27, away: 0.31 },
    signals: ['value'],
    topValueBet: {
      market: 'Over 2.5',
      edgePct: 7.2,
      bestOdd: 1.92,
      bestBook: 'Pinnacle',
      kellyPct: 2.4,
    },
  },
];

export const mockSafePick: SafePick = {
  fixtureId: 'fx-1',
  league: leagueL1,
  kickoffUtc: '2026-04-21T19:00:00Z',
  home: mockMatches[0].home,
  away: mockMatches[0].away,
  betLabel: 'PSG gagne vs Lens',
  odd: 1.85,
  probability: 0.58,
  justification:
    "PSG enchaîne 5 victoires à domicile avec xG moyen 2.3. Lens absent de ses 3 cadres défensifs. Valeur cote 1.85 vs proba 58% → edge 7.3%.",
};

export const mockPerformance: PerformanceSummary = {
  roi30d: { value: 12.4, deltaVs7d: 0.8 },
  accuracy: { value: 54.2, deltaVs7d: -0.3 },
  brier7d: { value: 0.189, deltaVs7d: -0.004 },
  bankroll: { value: 1240, currency: 'EUR' },
};
