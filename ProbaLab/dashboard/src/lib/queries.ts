import { useQuery } from '@tanstack/react-query'
import { api } from './api'

// ── Query key factory ──────────────────────────────────────────
// Centralised so cache invalidation is consistent across the app.
export const queryKeys = {
  predictions: (date?: string) => ['predictions', date] as const,
  predictionDetail: (fixtureId: number | string) =>
    ['prediction', fixtureId] as const,
  performance: (days: number, sport: string) =>
    ['performance', sport, days] as const,
  teamHistory: (teamName: string, limit: number) =>
    ['team-history', teamName, limit] as const,
  teamRoster: (teamName: string) => ['team-roster', teamName] as const,
  news: () => ['news'] as const,
  monitoring: () => ['monitoring'] as const,
  footballMetaAnalysis: (date?: string) =>
    ['football-meta-analysis', date] as const,
  nhlMetaAnalysis: (date?: string) => ['nhl-meta-analysis', date] as const,
  pipelineStatus: () => ['pipeline-status'] as const,
  playerProfile: (playerId: number | string) =>
    ['player-profile', playerId] as const,
  nhlMatchTopPlayers: (fixtureId: number | string) =>
    ['nhl-match-top-players', fixtureId] as const,
} as const

// ── Predictions ────────────────────────────────────────────────

export function usePredictions(date?: string) {
  return useQuery({
    queryKey: queryKeys.predictions(date),
    queryFn: () => api.getPredictions(date),
    staleTime: 5 * 60 * 1000, // 5 min — React Query refetches on next focus after stale
  })
}

export function usePredictionDetail(fixtureId: number | string) {
  return useQuery({
    queryKey: queryKeys.predictionDetail(fixtureId),
    queryFn: () => api.getPredictionDetail(fixtureId),
    staleTime: 5 * 60 * 1000,
    enabled: fixtureId != null,
  })
}

// ── Performance ────────────────────────────────────────────────

export function useFootballPerformance(days = 30) {
  return useQuery({
    queryKey: queryKeys.performance(days, 'football'),
    queryFn: () => api.getPerformance(days),
    staleTime: 10 * 60 * 1000, // 10 min — performance data changes rarely intraday
  })
}

export function useNHLPerformance(days = 30) {
  return useQuery({
    queryKey: queryKeys.performance(days, 'nhl'),
    queryFn: () => api.getNHLPerformance(days),
    staleTime: 10 * 60 * 1000,
  })
}

// ── Teams ──────────────────────────────────────────────────────

export function useTeamHistory(teamName: string, limit = 60) {
  return useQuery({
    queryKey: queryKeys.teamHistory(teamName, limit),
    queryFn: () => api.getTeamHistory(teamName, limit),
    staleTime: 10 * 60 * 1000,
    enabled: Boolean(teamName),
  })
}

export function useTeamRoster(teamName: string) {
  return useQuery({
    queryKey: queryKeys.teamRoster(teamName),
    queryFn: () => api.getTeamRoster(teamName),
    staleTime: 30 * 60 * 1000, // rosters change infrequently
    enabled: Boolean(teamName),
  })
}

// ── News / Monitoring ──────────────────────────────────────────

export function useNews() {
  return useQuery({
    queryKey: queryKeys.news(),
    queryFn: () => api.getNews(),
    staleTime: 60 * 60 * 1000, // 1 hour
  })
}

export function useMonitoring() {
  return useQuery({
    queryKey: queryKeys.monitoring(),
    queryFn: () => api.getMonitoring(),
    staleTime: 5 * 60 * 1000,
  })
}

// ── Meta-analysis ──────────────────────────────────────────────

export function useFootballMetaAnalysis(date?: string) {
  return useQuery({
    queryKey: queryKeys.footballMetaAnalysis(date),
    queryFn: () => api.getFootballMetaAnalysis(date),
    staleTime: 5 * 60 * 1000,
    // null is a valid "no analysis today" response — do not throw on it
    throwOnError: false,
  })
}

export function useNHLMetaAnalysis(date?: string) {
  return useQuery({
    queryKey: queryKeys.nhlMetaAnalysis(date),
    queryFn: () => api.getNHLMetaAnalysis(date),
    staleTime: 5 * 60 * 1000,
    throwOnError: false,
  })
}

// ── Admin ──────────────────────────────────────────────────────

export function usePipelineStatus(enabled = true) {
  return useQuery({
    queryKey: queryKeys.pipelineStatus(),
    queryFn: () => api.getPipelineStatus(),
    staleTime: 0, // always fetch fresh status
    refetchInterval: enabled ? 5000 : false, // poll every 5 s when enabled
    enabled,
  })
}

// ── Players ────────────────────────────────────────────────────

export function usePlayerProfile(playerId: number | string) {
  return useQuery({
    queryKey: queryKeys.playerProfile(playerId),
    queryFn: () => api.getPlayerProfile(playerId),
    staleTime: 10 * 60 * 1000,
    enabled: playerId != null,
  })
}

export function useNHLMatchTopPlayers(fixtureId: number | string) {
  return useQuery({
    queryKey: queryKeys.nhlMatchTopPlayers(fixtureId),
    queryFn: () => api.getNHLMatchTopPlayers(fixtureId),
    staleTime: 5 * 60 * 1000,
    enabled: fixtureId != null,
    throwOnError: false,
  })
}
