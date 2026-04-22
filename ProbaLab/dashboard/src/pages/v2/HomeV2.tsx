import { useEffect, useState } from 'react';
import { useV2User } from '@/hooks/v2/useV2User';
import { useSafePick } from '@/hooks/v2/useSafePick';
import { useMatchesOfDay } from '@/hooks/v2/useMatchesOfDay';
import { usePerformanceSummary } from '@/hooks/v2/usePerformanceSummary';
import { PreviewBlurMatches } from '@/components/v2/home/PreviewBlurMatches';
import { StatStrip } from '@/components/v2/home/StatStrip';
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

  return (
    <main
      data-testid="home-v2"
      aria-label="Tableau de bord ProbaLab"
      className="mx-auto max-w-7xl px-4 md:px-8 py-6 space-y-6"
    >
      <StatStrip data={perf.data} loading={perf.isLoading} />
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
