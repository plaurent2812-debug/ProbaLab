import { useEffect, useState } from 'react';
import { useV2User } from '@/hooks/v2/useV2User';
import { useSafePick } from '@/hooks/v2/useSafePick';
import { useMatchesOfDay } from '@/hooks/v2/useMatchesOfDay';
import { usePerformanceSummary } from '@/hooks/v2/usePerformanceSummary';
import { PreviewBlurMatches } from '@/components/v2/home/PreviewBlurMatches';
import { StatStrip } from '@/components/v2/home/StatStrip';
import { ProofStrip } from '@/components/v2/home/ProofStrip';
import { SafeOfTheDayCard } from '@/components/v2/home/SafeOfTheDayCard';
import { MatchesList } from '@/components/v2/home/MatchesList';
import { ValueBetsTeaser } from '@/components/v2/home/ValueBetsTeaser';
import { PremiumCTA } from '@/components/v2/home/PremiumCTA';
// Premium landing sections (visitor-only) — shadcn + framer-motion.
import { Hero } from '@/components/v2/home/premium/Hero';
import { StatStripPremium } from '@/components/v2/home/premium/StatStripPremium';
import { LiveDemoMatch } from '@/components/v2/home/premium/LiveDemoMatch';
import { HowItWorks } from '@/components/v2/home/premium/HowItWorks';
import { TrackRecord } from '@/components/v2/home/premium/TrackRecord';
import { FinalCTA } from '@/components/v2/home/premium/FinalCTA';
import type { MatchRowData } from '@/types/v2/matches';

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

function todayIso(): string {
  return new Date().toISOString().slice(0, 10);
}

function lastUpdateUtc(): string {
  return new Date().toISOString().slice(11, 16);
}

/**
 * Pick the match most worth showing on the public landing:
 *   1. highest edge from topValueBet, then
 *   2. fall back to first match of the day.
 * Returns undefined when there are no matches — LiveDemoMatch then
 * renders its own curated fallback (PSG vs Nantes).
 */
function pickFeaturedMatch(matches: MatchRowData[] | undefined): MatchRowData | undefined {
  if (!matches || matches.length === 0) return undefined;
  const byEdge = [...matches].sort(
    (a, b) => (b.topValueBet?.edgePct ?? 0) - (a.topValueBet?.edgePct ?? 0),
  );
  return byEdge[0];
}

export function HomeV2() {
  const user = useV2User();
  const date = todayIso();
  const safe = useSafePick(date);
  const matches = useMatchesOfDay({ date });
  const perf = usePerformanceSummary();
  const isDesktop = useIsDesktop();

  // ── Visitor landing (public marketing page) ───────────────────────
  // Dark premium layout with hero, live stats, a real match preview,
  // "how it works", track record, and final CTA. All sections use
  // framer-motion reveals and shadcn primitives.
  if (user.isVisitor) {
    return (
      <main
        data-testid="home-landing"
        aria-label="Accueil ProbaLab"
        // Force dark premium background regardless of theme — this is
        // the public face of the product.
        className="min-h-screen"
        style={{ background: '#0a0e1a', color: '#e5e7eb' }}
      >
        <Hero />
        <StatStripPremium data={perf.data} />
        <LiveDemoMatch match={pickFeaturedMatch(matches.data?.matches)} />
        {/* Keeps a secondary "here are more matches, blurred" teaser so
            visitors see the breadth of our coverage before committing. */}
        {matches.data && matches.data.matches.length > 1 && (
          <section className="mx-auto max-w-6xl px-4 pb-8 md:px-8">
            <PreviewBlurMatches matches={matches.data.matches} />
          </section>
        )}
        <HowItWorks />
        <TrackRecord />
        <FinalCTA />
      </main>
    );
  }

  // ── Connected dashboard (free/trial/premium/admin) ────────────────
  const gating: 'free' | 'trial' | 'premium' =
    user.role === 'free' ? 'free' : user.role === 'trial' ? 'trial' : 'premium';

  const showPremiumCTA = user.role !== 'premium' && user.role !== 'admin';
  const matchCount = matches.data?.matches.length ?? 0;
  const signalCount = matches.data?.matches.filter((match) => match.topValueBet).length ?? 0;
  const daySummary = matches.isLoading
    ? 'Chargement des analyses'
    : matches.isError
      ? 'Analyses indisponibles'
      : `${matchCount} matchs analysés · ${signalCount} signaux forts`;

  return (
    <main
      data-testid="home-v2"
      aria-label="Tableau de bord ProbaLab"
      className="mx-auto max-w-7xl px-4 md:px-8 py-6 space-y-6"
    >
      <section
        aria-labelledby="analysis-heading"
        className="overflow-hidden rounded-[28px] p-5 md:p-7"
        style={{
          border: '1px solid rgba(96,165,250,0.24)',
          background:
            'radial-gradient(circle at 12% 0%, rgba(96,165,250,0.18), transparent 34%), radial-gradient(circle at 86% 12%, rgba(34,211,238,0.12), transparent 28%), linear-gradient(135deg, rgba(7,17,31,0.98), rgba(15,23,42,0.92))',
          boxShadow: '0 24px 80px rgba(0,0,0,0.28)',
        }}
      >
        <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_360px] lg:items-end">
          <div>
            <p
              className="mb-3 text-xs font-bold uppercase tracking-[0.22em]"
              style={{ color: 'var(--primary)' }}
            >
              Centre d'analyse ProbaLab
            </p>
            <h1
              id="analysis-heading"
              className="max-w-3xl text-4xl font-black leading-[0.95] tracking-[-0.06em] md:text-6xl"
              style={{ color: 'var(--text)' }}
            >
              Analyses et probabilités sportives
            </h1>
            <p
              className="mt-4 max-w-2xl text-sm leading-6 md:text-base"
              style={{ color: 'var(--text-muted)' }}
            >
              Les matchs du jour, les probabilités clés et les signaux du modèle pour décider plus vite.
            </p>
            <div className="mt-5 flex flex-wrap gap-2">
              {['Probabilités 1X2', 'Scénarios modèles', 'Pronos recommandés'].map((label) => (
                <span
                  key={label}
                  className="rounded-full px-3 py-1 text-[11px] font-bold uppercase tracking-[0.12em]"
                  style={{
                    border: '1px solid rgba(96,165,250,0.26)',
                    background: 'rgba(96,165,250,0.08)',
                    color: 'var(--text)',
                  }}
                >
                  {label}
                </span>
              ))}
            </div>
          </div>
          <aside
            aria-label="Résumé de journée"
            className="rounded-2xl p-4"
            style={{
              border: '1px solid var(--border)',
              background: 'rgba(15,23,42,0.78)',
            }}
          >
            <p
              className="text-xs font-bold uppercase tracking-[0.18em]"
              style={{ color: 'var(--text-faint)' }}
            >
              Résumé de journée
            </p>
            <p className="mt-3 text-2xl font-black tracking-[-0.05em]" style={{ color: 'var(--text)' }}>
              {daySummary}
            </p>
            <div className="mt-4 grid grid-cols-2 gap-2">
              <div
                className="rounded-xl p-3"
                style={{ border: '1px solid var(--border)', background: 'var(--surface)' }}
              >
                <span className="block text-[11px]" style={{ color: 'var(--text-muted)' }}>
                  Confiance modèle
                </span>
                <strong className="mt-1 block text-sm" style={{ color: '#60a5fa' }}>
                  Analyse active
                </strong>
              </div>
              <div
                className="rounded-xl p-3"
                style={{ border: '1px solid var(--border)', background: 'var(--surface)' }}
              >
                <span className="block text-[11px]" style={{ color: 'var(--text-muted)' }}>
                  Dernière mise à jour UTC
                </span>
                <strong className="mt-1 block text-sm tabular-nums" style={{ color: 'var(--text)' }}>
                  {lastUpdateUtc()}
                </strong>
              </div>
            </div>
          </aside>
        </div>
      </section>
      <StatStrip data={perf.data} loading={perf.isLoading} />
      <ProofStrip lastUpdateUtc={lastUpdateUtc()} />
      <div className="grid gap-6 lg:grid-cols-[1fr_360px]">
        <div className="space-y-6">
          {!isDesktop && <SafeOfTheDayCard data={safe.data ?? null} />}
          <section>
            <h2
              className="mb-3 text-lg font-semibold"
              style={{ color: 'var(--text)' }}
            >
              Au programme
            </h2>
            {matches.isLoading ? (
              <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
                Chargement des matchs...
              </p>
            ) : matches.isError ? (
              <p className="text-sm" style={{ color: 'var(--danger, #ef4444)' }}>
                Impossible de charger les matchs du jour.
              </p>
            ) : (
              <MatchesList matches={matches.data?.matches ?? []} />
            )}
          </section>
        </div>
        <aside
          data-testid="home-right-col"
          data-layout={isDesktop ? 'sticky' : 'inline'}
          className={isDesktop ? 'sticky top-5 space-y-4 self-start' : 'space-y-4'}
        >
          {isDesktop && <SafeOfTheDayCard data={safe.data ?? null} />}
          {matches.data && matches.data.matches.length > 0 && (
            <ValueBetsTeaser matches={matches.data.matches} gating={gating} />
          )}
          {showPremiumCTA && <PremiumCTA />}
        </aside>
      </div>
    </main>
  );
}

export default HomeV2;
