import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { ChevronLeft } from 'lucide-react';
import { useMatchDetail } from '@/hooks/v2/useMatchDetail';
import { useAnalysis } from '@/hooks/v2/useAnalysis';
import { useV2User } from '@/hooks/v2/useV2User';
import {
  MatchDecisionHero,
  StatsComparative,
  H2HSection,
  AIAnalysis,
  CompositionsSection,
  AllMarketsGrid,
  RecoCard,
  BookOddsList,
  ValueBetsList,
  StickyActions,
} from '@/components/v2/match-detail';
import { ProbBar } from '@/components/v2/system/ProbBar';
import { Skeleton } from '@/components/ui/skeleton';
import type { FixtureId } from '@/types/v2/common';
import type {
  AnalysisPayload,
  BookOdd,
  MarketProb,
  Recommendation,
} from '@/types/v2/match-detail';

const DESKTOP_BREAKPOINT = 1024;

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

/**
 * Dérive une liste minimale de cotes bookmaker à partir de la reco principale.
 * Tant que le Lot 4 ne livre pas `useOddsComparison`, on affiche au moins le
 * meilleur prix connu pour maintenir la section dans la colonne droite.
 */
function deriveBookOdds(
  recommendation: Recommendation | null,
  kickoffUtc: string,
): BookOdd[] {
  if (!recommendation) return [];
  return [
    {
      bookmaker: recommendation.book_name,
      odds: recommendation.odds,
      is_best: true,
      updated_at: kickoffUtc,
    },
  ];
}

function fmtPct(value: number): string {
  return `${Math.round(value * 100)}%`;
}

function fmtOdds(value: number | null | undefined): string {
  return typeof value === 'number' && Number.isFinite(value) ? value.toFixed(2) : '—';
}

function fmtUtcTime(value: string | undefined): string {
  if (!value) return '—';
  return new Intl.DateTimeFormat('fr-FR', {
    hour: '2-digit',
    minute: '2-digit',
    timeZone: 'UTC',
  }).format(new Date(value));
}

function findRecommendationMarket(
  markets: MarketProb[],
  recommendation: Recommendation | null,
): MarketProb | null {
  if (!recommendation) return null;
  return markets.find((market) => market.market_key === recommendation.market_key) ?? null;
}

function DecisionMetric({
  label,
  value,
  tone = 'neutral',
}: {
  label: string;
  value: string;
  tone?: 'neutral' | 'positive' | 'warning';
}) {
  const color =
    tone === 'positive'
      ? 'var(--primary)'
      : tone === 'warning'
        ? 'var(--value, #fbbf24)'
        : 'var(--text)';
  return (
    <div
      className="rounded-xl p-3"
      style={{ border: '1px solid var(--border)', background: 'rgba(255,255,255,0.03)' }}
    >
      <span className="block text-[11px]" style={{ color: 'var(--text-muted)' }}>
        {label}
      </span>
      <strong className="mt-1 block text-sm tabular-nums" style={{ color }}>
        {value}
      </strong>
    </div>
  );
}

function MatchReadingPanel({
  recommendation,
  recommendedMarket,
  probs,
  bookOdds,
  homeName,
  awayName,
}: {
  recommendation: Recommendation | null;
  recommendedMarket: MarketProb | null;
  probs: { home: number; draw: number; away: number };
  bookOdds: BookOdd[];
  homeName: string;
  awayName: string;
}) {
  const latestBookOdd = bookOdds[0];
  const confidencePct = recommendation ? fmtPct(recommendation.confidence) : '—';
  const edgePct = recommendation ? fmtPct(recommendation.edge) : '—';
  const riskLabel =
    recommendation && recommendation.kelly_fraction <= 0.015
      ? 'Prudent'
      : recommendation && recommendation.kelly_fraction <= 0.04
        ? 'Modéré'
        : 'Élevé';

  return (
    <section
      aria-labelledby="match-reading-heading"
      className="rounded-[26px] p-5"
      style={{
        border: '1px solid rgba(96,165,250,0.24)',
        background:
          'radial-gradient(circle at 0% 0%, rgba(96,165,250,0.18), transparent 36%), radial-gradient(circle at 100% 0%, rgba(34,211,238,0.10), transparent 32%), linear-gradient(160deg, rgba(7,17,31,0.98), rgba(15,23,42,0.92))',
      }}
    >
      <p
        className="mb-2 text-xs font-bold uppercase tracking-[0.2em]"
        style={{ color: 'var(--primary)' }}
      >
        Analyse du match
      </p>
      <h2
        id="match-reading-heading"
        className="text-2xl font-black tracking-[-0.06em]"
        style={{ color: 'var(--text)' }}
      >
        Lecture du match
      </h2>
      <p className="mt-2 text-sm leading-6" style={{ color: 'var(--text-muted)' }}>
        Les probabilités du modèle résument le scénario le plus probable et les points de décision.
      </p>

      <div className="mt-5">
        <ProbBar
          home={probs.home}
          draw={probs.draw}
          away={probs.away}
          homeLabel={homeName}
          awayLabel={awayName}
        />
        <div
          className="mt-2 flex justify-between text-[11px] tabular-nums"
          style={{ color: 'var(--text-muted)' }}
        >
          <span>{fmtPct(probs.home)}</span>
          <span>{fmtPct(probs.draw)}</span>
          <span>{fmtPct(probs.away)}</span>
        </div>
      </div>

      <div
        className="mt-4 rounded-xl p-3 text-sm"
        style={{
          border: '1px solid var(--border)',
          background: 'rgba(255,255,255,0.03)',
          color: 'var(--text)',
        }}
      >
        <span
          className="block text-[11px] font-semibold uppercase tracking-[0.12em]"
          style={{ color: 'var(--text-muted)' }}
        >
          Scénario probable
        </span>
        <strong className="mt-1 block">
          {homeName} favori selon le modèle, nul à surveiller.
        </strong>
      </div>

      <div className="mt-5 grid grid-cols-2 gap-2">
        <DecisionMetric label="Niveau de risque" value={riskLabel} tone="positive" />
        <DecisionMetric label="Confiance modèle" value={confidencePct} />
        <DecisionMetric label="Cote juste modèle" value={fmtOdds(recommendedMarket?.fair_odds)} />
        <DecisionMetric label="Signal modèle" value={edgePct} tone="warning" />
        <DecisionMetric label="Meilleure cote" value={fmtOdds(latestBookOdd?.odds)} tone="positive" />
        <DecisionMetric label="Dernière cote UTC" value={fmtUtcTime(latestBookOdd?.updated_at)} />
      </div>
    </section>
  );
}

const EMPTY_ANALYSIS: AnalysisPayload = {
  paragraphs: [],
  generated_at: '',
};

export function MatchDetailV2() {
  const params = useParams<{ fixtureId: FixtureId }>();
  const fixtureId = params.fixtureId ?? null;
  const { role } = useV2User();
  const isDesktop = useIsDesktop();

  const match = useMatchDetail(fixtureId);
  const analysis = useAnalysis(fixtureId);

  if (match.isLoading) {
    return (
      <main
        data-testid="match-detail-loading"
        aria-label="Chargement du match"
        className="mx-auto max-w-7xl px-4 md:px-8 py-6 space-y-4"
      >
        <Skeleton className="h-6 w-48" />
        <Skeleton className="h-40 w-full" />
        <div className="grid gap-4 lg:grid-cols-[1fr_360px]">
          <div className="space-y-4">
            <Skeleton className="h-32 w-full" />
            <Skeleton className="h-32 w-full" />
            <Skeleton className="h-32 w-full" />
          </div>
          <div className="space-y-4">
            <Skeleton className="h-48 w-full" />
            <Skeleton className="h-32 w-full" />
          </div>
        </div>
      </main>
    );
  }

  if (match.isError || !match.data) {
    return (
      <main
        data-testid="match-detail-error"
        aria-label="Erreur chargement match"
        className="mx-auto max-w-3xl px-4 md:px-8 py-10 text-center"
      >
        <p className="text-sm text-rose-600">
          Impossible de charger le match. Réessaie dans un instant.
        </p>
        <Link
          to="/matchs"
          className="mt-4 inline-flex items-center gap-1 text-sm font-medium text-slate-700 hover:text-slate-900"
        >
          <ChevronLeft className="h-4 w-4" aria-hidden="true" />
          Retour aux matchs
        </Link>
      </main>
    );
  }

  const d = match.data;
  const matchTitle = `${d.header.home.name} vs ${d.header.away.name}`;
  const analysisPayload: AnalysisPayload = analysis.data ?? EMPTY_ANALYSIS;
  const hasAnalysis = analysisPayload.paragraphs.length > 0;
  const bookOdds = deriveBookOdds(d.recommendation, d.header.kickoff_utc);
  const recommendedMarket = findRecommendationMarket(d.all_markets, d.recommendation);
  const canUseSticky = role === 'trial' || role === 'premium' || role === 'admin';
  const canAddToBankroll = canUseSticky && d.recommendation !== null;

  const breadcrumb = (
    <nav
      data-testid="match-detail-breadcrumb"
      aria-label="Fil d'Ariane"
      className="flex items-center gap-1 text-xs text-slate-500"
    >
      <Link
        to="/matchs"
        className="inline-flex items-center gap-1 hover:text-slate-800"
      >
        <ChevronLeft className="h-3 w-3" aria-hidden="true" />
        Matchs
      </Link>
      <span className="mx-1" aria-hidden="true">
        /
      </span>
      <span className="truncate text-slate-700">{d.header.league_name}</span>
      <span className="mx-1" aria-hidden="true">
        /
      </span>
      <span className="truncate font-medium text-slate-900">{matchTitle}</span>
    </nav>
  );

  if (!isDesktop) {
    // Mobile-first — ordre A (décision rapide) :
    // 1. Breadcrumb / back
    // 2. MatchDecisionHero
    // 3. RecoCard
    // 4. Lecture du match
    // 5. ValueBetsList
    // 6. StatsComparative
    // 7. AIAnalysis
    // 8. AllMarketsGrid
    // 9. CompositionsSection
    return (
      <main
        data-testid="match-detail-v2"
        data-fixture-id={fixtureId ?? ''}
        data-layout="mobile"
        aria-label={`Détail du match ${matchTitle}`}
        className="mx-auto max-w-3xl px-4 py-4 space-y-4"
      >
        {breadcrumb}
        <MatchDecisionHero
          header={d.header}
          probs={d.probs_1x2}
          recommendation={d.recommendation}
          recommendedMarket={recommendedMarket}
          analysisAvailable={hasAnalysis}
        />
        <MatchReadingPanel
          recommendation={d.recommendation}
          recommendedMarket={recommendedMarket}
          probs={d.probs_1x2}
          bookOdds={bookOdds}
          homeName={d.header.home.name}
          awayName={d.header.away.name}
        />
        <RecoCard recommendation={d.recommendation} />
        <ValueBetsList
          valueBets={d.value_bets}
          userRole={role}
          matchTitle={matchTitle}
        />
        {canAddToBankroll && d.recommendation && (
          <StickyActions
            fixtureId={fixtureId ?? ''}
            recommendation={d.recommendation}
          />
        )}
        <StatsComparative
          stats={d.stats}
          label="Stats comparées (5 derniers)"
        />
        {hasAnalysis && (
          <div id="analyse-ia">
            <AIAnalysis analysis={analysisPayload} userRole={role} />
          </div>
        )}
        <div id="marches">
          <AllMarketsGrid markets={d.all_markets} userRole={role} />
        </div>
        <CompositionsSection
          compositions={d.compositions}
          homeName={d.header.home.name}
          awayName={d.header.away.name}
        />
      </main>
    );
  }

  // Desktop — 2 colonnes sticky
  return (
    <main
      data-testid="match-detail-v2"
      data-fixture-id={fixtureId ?? ''}
      data-layout="desktop"
      aria-label={`Détail du match ${matchTitle}`}
      className="mx-auto max-w-7xl px-4 md:px-8 py-6 space-y-5"
    >
      {breadcrumb}
      <MatchDecisionHero
        header={d.header}
        probs={d.probs_1x2}
        recommendation={d.recommendation}
        recommendedMarket={recommendedMarket}
        analysisAvailable={hasAnalysis}
      />
      <div className="grid gap-7 lg:grid-cols-[1fr_360px]">
        <div className="space-y-5">
          <StatsComparative
            stats={d.stats}
            label="Stats comparées (5 derniers)"
          />
          <H2HSection
            h2h={d.h2h}
            homeName={d.header.home.name}
            awayName={d.header.away.name}
          />
          {hasAnalysis && (
            <div id="analyse-ia">
              <AIAnalysis analysis={analysisPayload} userRole={role} />
            </div>
          )}
          <CompositionsSection
            compositions={d.compositions}
            homeName={d.header.home.name}
            awayName={d.header.away.name}
          />
          <div id="marches">
            <AllMarketsGrid markets={d.all_markets} userRole={role} />
          </div>
        </div>
        <aside
          data-testid="match-detail-right-col"
          className="sticky top-5 space-y-4 self-start"
        >
          <MatchReadingPanel
            recommendation={d.recommendation}
            recommendedMarket={recommendedMarket}
            probs={d.probs_1x2}
            bookOdds={bookOdds}
            homeName={d.header.home.name}
            awayName={d.header.away.name}
          />
          <RecoCard recommendation={d.recommendation} />
          <BookOddsList bookOdds={bookOdds} />
          <ValueBetsList
            valueBets={d.value_bets}
            userRole={role}
            matchTitle={matchTitle}
          />
          {canAddToBankroll && d.recommendation && (
            <StickyActions
              fixtureId={fixtureId ?? ''}
              recommendation={d.recommendation}
            />
          )}
        </aside>
      </div>
    </main>
  );
}

export default MatchDetailV2;
