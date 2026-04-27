import { useCallback, useEffect, useMemo, useState } from 'react';
import type { ReactNode } from 'react';
import { useSearchParams } from 'react-router-dom';
import { CalendarDays, ShieldCheck, Sparkles, Target } from 'lucide-react';
import { SportChips, type SportChipsValue } from '@/components/v2/matches/SportChips';
import { DateScroller } from '@/components/v2/matches/DateScroller';
import { ValueOnlyToggle } from '@/components/v2/matches/ValueOnlyToggle';
import { FilterSidebar } from '@/components/v2/matches/FilterSidebar';
import { MatchesTableDesktop } from '@/components/v2/matches/MatchesTableDesktop';
import { MatchesListMobile } from '@/components/v2/matches/MatchesListMobile';
import { Skeleton } from '@/components/ui/skeleton';
import { useMatchesOfDay } from '@/hooks/v2/useMatchesOfDay';
import type { League } from '@/types/v2/common';
import type { MatchRowData, MatchesFilters, SignalKind, Sport } from '@/types/v2/matches';

const DESKTOP_BREAKPOINT = 768;

function useIsDesktop(): boolean {
  const [isDesktop, setIsDesktop] = useState<boolean>(() =>
    typeof window !== 'undefined' ? window.innerWidth >= DESKTOP_BREAKPOINT : true,
  );
  useEffect(() => {
    const onResize = () => setIsDesktop(window.innerWidth >= DESKTOP_BREAKPOINT);
    window.addEventListener('resize', onResize);
    return () => window.removeEventListener('resize', onResize);
  }, []);
  return isDesktop;
}

function todayIso(): string {
  return new Date().toISOString().slice(0, 10);
}

function parseList<T extends string>(raw: string | null): T[] | undefined {
  if (!raw) return undefined;
  const list = raw.split(',').map((s) => s.trim()).filter(Boolean) as T[];
  return list.length > 0 ? list : undefined;
}

function sportChipsValue(sports: Sport[] | undefined): SportChipsValue {
  if (!sports || sports.length !== 1) return 'all';
  return sports[0];
}

function countMatchesWithSignal(matches: MatchRowData[], signal: SignalKind): number {
  return matches.filter((match) => match.signals.includes(signal)).length;
}

function findPriorityMatch(matches: MatchRowData[]): MatchRowData | null {
  return (
    matches.find((match) => match.signals.includes('safe')) ??
    [...matches]
      .filter((match) => match.topValueBet)
      .sort((a, b) => (b.topValueBet?.edgePct ?? 0) - (a.topValueBet?.edgePct ?? 0))[0] ??
    matches[0] ??
    null
  );
}

function MatchesDayOverview({
  matches,
  date,
}: {
  matches: MatchRowData[];
  date: string;
}) {
  const priorityMatch = findPriorityMatch(matches);
  const recommendedCount = countMatchesWithSignal(matches, 'safe');
  const signalCount = matches.filter((match) => match.topValueBet || match.signals.includes('value')).length;
  const highConfidenceCount = countMatchesWithSignal(matches, 'high_confidence');
  const priorityLabel = priorityMatch
    ? `${priorityMatch.home.short} vs ${priorityMatch.away.short}`
    : 'Aucun match prioritaire';

  return (
    <section
      data-testid="matches-day-overview"
      aria-labelledby="matches-day-overview-title"
      className="relative overflow-hidden rounded-[32px] p-5 md:p-6"
      style={{
        border: '1px solid rgba(96,165,250,0.24)',
        background:
          'radial-gradient(circle at 0% 0%, rgba(96,165,250,0.20), transparent 34%), radial-gradient(circle at 100% 0%, rgba(34,211,238,0.10), transparent 30%), linear-gradient(145deg, rgba(7,17,31,0.98), rgba(15,23,42,0.92))',
        boxShadow: '0 24px 80px rgba(0,0,0,0.25)',
      }}
    >
      <div className="grid gap-5 lg:grid-cols-[minmax(0,1fr)_390px] lg:items-end">
        <div>
          <div className="flex flex-wrap items-center gap-2 text-xs font-bold uppercase tracking-[0.16em]" style={{ color: 'var(--primary)' }}>
            <Sparkles className="h-4 w-4" aria-hidden="true" />
            Lecture du jour
            <span aria-hidden="true">·</span>
            <span>{date}</span>
          </div>
          <h1
            id="matches-day-overview-title"
            className="mt-3 text-4xl font-black tracking-[-0.07em] md:text-5xl"
            style={{ color: 'var(--text)' }}
          >
            Matchs à analyser
          </h1>
          <p className="mt-3 max-w-2xl text-sm leading-6" style={{ color: 'var(--text-muted)' }}>
            Sélectionne vite les affiches utiles : probabilités, signaux du modèle et pronos éventuels sont résumés avant l'analyse complète.
          </p>
        </div>

        <div className="grid grid-cols-2 gap-2">
          <OverviewMetric icon={<CalendarDays className="h-4 w-4" aria-hidden="true" />} label="Matchs suivis" value={`${matches.length}`} />
          <OverviewMetric icon={<ShieldCheck className="h-4 w-4" aria-hidden="true" />} label="Pronos recommandés" value={`${recommendedCount}`} />
          <OverviewMetric icon={<Target className="h-4 w-4" aria-hidden="true" />} label="Signaux modèle" value={`${signalCount}`} />
          <OverviewMetric icon={<Sparkles className="h-4 w-4" aria-hidden="true" />} label="Confiance élevée" value={`${highConfidenceCount}`} />
        </div>
      </div>

      <div
        className="mt-5 flex flex-wrap items-center gap-3 rounded-2xl p-4"
        style={{ border: '1px solid var(--border)', background: 'rgba(255,255,255,0.035)' }}
      >
        <span className="text-[11px] font-bold uppercase tracking-[0.16em]" style={{ color: 'var(--text-muted)' }}>
          Match prioritaire
        </span>
        <strong className="text-lg font-black tracking-[-0.04em]" style={{ color: 'var(--text)' }}>
          {priorityLabel}
        </strong>
        {priorityMatch?.topValueBet && (
          <span className="rounded-full px-2.5 py-1 text-xs font-bold" style={{ background: 'rgba(251,191,36,0.12)', color: 'var(--value)' }}>
            Signal +{priorityMatch.topValueBet.edgePct.toFixed(1)}%
          </span>
        )}
      </div>
    </section>
  );
}

function OverviewMetric({
  icon,
  label,
  value,
}: {
  icon: ReactNode;
  label: string;
  value: string;
}) {
  return (
    <div
      className="rounded-2xl p-3"
      style={{ border: '1px solid var(--border)', background: 'rgba(255,255,255,0.04)' }}
    >
      <div className="flex items-center gap-2 text-[11px] font-semibold" style={{ color: 'var(--text-muted)' }}>
        {icon}
        {label}
      </div>
      <strong className="mt-2 block text-2xl font-black tabular-nums" style={{ color: 'var(--text)' }}>
        {value}
      </strong>
    </div>
  );
}

export function MatchesV2() {
  const [searchParams, setSearchParams] = useSearchParams();
  const isDesktop = useIsDesktop();

  const date = searchParams.get('date') ?? todayIso();
  const sports = parseList<Sport>(searchParams.get('sport'));
  const leagues = parseList<League>(searchParams.get('league'));
  const signals = parseList<SignalKind>(searchParams.get('signals'));
  const valueOnly = searchParams.get('value_only') === 'true';
  const sort = (searchParams.get('sort') as MatchesFilters['sort']) ?? undefined;

  const filters: MatchesFilters = useMemo(
    () => ({ date, sports, leagues, signals, valueOnly: valueOnly || undefined, sort }),
    [date, sports, leagues, signals, valueOnly, sort],
  );

  const { data, isLoading, isError } = useMatchesOfDay(filters);

  const updateParams = useCallback(
    (mutator: (p: URLSearchParams) => void) => {
      const next = new URLSearchParams(searchParams);
      mutator(next);
      setSearchParams(next, { replace: false });
    },
    [searchParams, setSearchParams],
  );

  const onDateChange = (iso: string) => {
    updateParams((p) => {
      p.set('date', iso);
    });
  };

  const onSportChipsChange = (v: SportChipsValue) => {
    updateParams((p) => {
      if (v === 'all') p.delete('sport');
      else p.set('sport', v);
    });
  };

  const onFiltersChange = (next: MatchesFilters) => {
    updateParams((p) => {
      if (next.sports?.length) p.set('sport', next.sports.join(','));
      else p.delete('sport');
      if (next.leagues?.length) p.set('league', next.leagues.join(','));
      else p.delete('league');
      if (next.signals?.length) p.set('signals', next.signals.join(','));
      else p.delete('signals');
      if (next.valueOnly) p.set('value_only', 'true');
      else p.delete('value_only');
      if (next.sort) p.set('sort', next.sort);
      else p.delete('sort');
    });
  };

  const onValueOnlyChange = (v: boolean) => {
    updateParams((p) => {
      if (v) p.set('value_only', 'true');
      else p.delete('value_only');
    });
  };

  const matches = data?.matches ?? [];
  const isEmpty = !isLoading && !isError && matches.length === 0;

  return (
    <main
      data-testid="matches-v2-page"
      data-date={date}
      data-sport={sports?.join(',') ?? 'all'}
      data-leagues={leagues?.join(',') ?? ''}
      aria-label="Matchs du jour"
      className="mx-auto max-w-7xl px-4 md:px-8 py-4 md:py-6 space-y-4"
    >
      {!isDesktop && (
        <>
          <header className="flex items-center justify-between">
            <h1 className="text-lg font-semibold" style={{ color: 'var(--text)' }}>
              Matchs
            </h1>
          </header>
          <SportChips
            value={sportChipsValue(sports)}
            onChange={onSportChipsChange}
            counts={
              data
                ? {
                    all: data.counts.total,
                    football: data.counts.bySport.football,
                    nhl: data.counts.bySport.nhl,
                  }
                : undefined
            }
          />
          <DateScroller value={date} onChange={onDateChange} />
          <div className="flex items-center justify-between">
            <ValueOnlyToggle value={valueOnly} onChange={onValueOnlyChange} />
          </div>
          {isLoading && (
            <div className="space-y-2" data-testid="matches-loading">
              <Skeleton className="h-16 w-full" />
              <Skeleton className="h-16 w-full" />
              <Skeleton className="h-16 w-full" />
            </div>
          )}
          {isError && (
            <p
              data-testid="matches-error"
              className="rounded-lg p-6 text-center text-sm"
              style={{
                border: '1px solid var(--border)',
                background: 'var(--surface)',
                color: 'var(--danger, #ef4444)',
              }}
            >
              Impossible de charger les matchs. Réessayez dans un instant.
            </p>
          )}
          {isEmpty && (
            <p
              data-testid="matches-empty"
              className="rounded-lg p-6 text-center text-sm"
              style={{
                border: '1px solid var(--border)',
                background: 'var(--surface)',
                color: 'var(--text-muted)',
              }}
            >
              Pas de match ce jour.
            </p>
          )}
          {!isLoading && !isError && !isEmpty && <MatchesListMobile matches={matches} />}
        </>
      )}

      {isDesktop && (
        <>
          <MatchesDayOverview matches={matches} date={date} />
          <DateScroller value={date} onChange={onDateChange} />
          <div className="grid gap-6 md:grid-cols-[260px_1fr]">
            <FilterSidebar
              filters={filters}
              onChange={onFiltersChange}
              matchesByLeague={
                data
                  ? (Object.fromEntries(
                      Object.entries(data.counts.byLeague),
                    ) as Partial<Record<League, number>>)
                  : undefined
              }
            />
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <SportChips
                  value={sportChipsValue(sports)}
                  onChange={onSportChipsChange}
                  counts={
                    data
                      ? {
                          all: data.counts.total,
                          football: data.counts.bySport.football,
                          nhl: data.counts.bySport.nhl,
                        }
                      : undefined
                  }
                />
                <ValueOnlyToggle value={valueOnly} onChange={onValueOnlyChange} />
              </div>
              {isLoading && (
                <div className="space-y-2" data-testid="matches-loading">
                  <Skeleton className="h-12 w-full" />
                  <Skeleton className="h-12 w-full" />
                  <Skeleton className="h-12 w-full" />
                  <Skeleton className="h-12 w-full" />
                </div>
              )}
              {isError && (
                <p
                  data-testid="matches-error"
                  className="rounded-lg p-6 text-center text-sm"
                  style={{
                    border: '1px solid var(--border)',
                    background: 'var(--surface)',
                    color: 'var(--danger, #ef4444)',
                  }}
                >
                  Impossible de charger les matchs. Réessayez dans un instant.
                </p>
              )}
              {isEmpty && (
                <p
                  data-testid="matches-empty"
                  className="rounded-lg p-6 text-center text-sm"
                  style={{
                    border: '1px solid var(--border)',
                    background: 'var(--surface)',
                    color: 'var(--text-muted)',
                  }}
                >
                  Pas de match ce jour.
                </p>
              )}
              {!isLoading && !isError && !isEmpty && <MatchesTableDesktop matches={matches} />}
            </div>
          </div>
        </>
      )}
    </main>
  );
}

export default MatchesV2;
