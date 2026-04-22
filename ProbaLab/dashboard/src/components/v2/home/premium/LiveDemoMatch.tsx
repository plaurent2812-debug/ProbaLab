import { useRef } from 'react';
import { motion, useInView } from 'framer-motion';
import { Lock, Zap } from 'lucide-react';
import { Link } from 'react-router-dom';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import type { MatchRowData } from '@/types/v2/matches';
import { EASE_OUT } from './animations';

function ProbBarAnimated({ home, draw, away }: { home: number; draw: number; away: number }) {
  const ref = useRef<HTMLDivElement>(null);
  const inView = useInView(ref, { once: true, margin: '-20%' });
  const pct = (v: number) => Math.round(v * 100);

  return (
    <div ref={ref} className="space-y-2">
      <div className="flex h-2.5 w-full overflow-hidden rounded-full bg-white/5">
        <motion.div
          className="h-full"
          style={{ background: '#10b981' }}
          initial={{ width: 0 }}
          animate={inView ? { width: `${pct(home)}%` } : { width: 0 }}
          transition={{ duration: 1, delay: 0.2, ease: EASE_OUT }}
        />
        <motion.div
          className="h-full"
          style={{ background: '#475569' }}
          initial={{ width: 0 }}
          animate={inView ? { width: `${pct(draw)}%` } : { width: 0 }}
          transition={{ duration: 1, delay: 0.35, ease: EASE_OUT }}
        />
        <motion.div
          className="h-full"
          style={{ background: '#334155' }}
          initial={{ width: 0 }}
          animate={inView ? { width: `${pct(away)}%` } : { width: 0 }}
          transition={{ duration: 1, delay: 0.5, ease: EASE_OUT }}
        />
      </div>
      <div className="flex justify-between text-xs text-slate-400" style={{ fontVariantNumeric: 'tabular-nums' }}>
        <span className="font-semibold text-emerald-400">{pct(home)}%</span>
        <span>{pct(draw)}%</span>
        <span>{pct(away)}%</span>
      </div>
    </div>
  );
}

// Curated fallback used when there is no featured match for the day
// (e.g. Monday mornings in summer). Keeps the landing section full.
const DEMO_FALLBACK = {
  home: { short: 'PSG', name: 'Paris Saint-Germain' },
  away: { short: 'NAN', name: 'Nantes' },
  league: { name: 'Ligue 1', color: '#1e40af' },
  kickoff: '19:00',
  prob: { home: 0.63, draw: 0.23, away: 0.14 },
  edge: 6.8,
  valueSide: 'home' as const,
} as const;

function formatKickoff(iso: string | undefined): string {
  if (!iso) return DEMO_FALLBACK.kickoff;
  const d = new Date(iso);
  return d.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' });
}

interface Props {
  // First interesting match of the day (highest edge). Optional: falls
  // back to a static PSG vs Nantes sample if the API is empty.
  match?: MatchRowData;
}

export function LiveDemoMatch({ match }: Props) {
  const home = match?.home.short ?? DEMO_FALLBACK.home.short;
  const away = match?.away.short ?? DEMO_FALLBACK.away.short;
  const leagueName = match?.league.name ?? DEMO_FALLBACK.league.name;
  const leagueColor = match?.league.color ?? DEMO_FALLBACK.league.color;
  const kickoff = formatKickoff(match?.kickoffUtc);
  const prob = match?.prob1x2 ?? DEMO_FALLBACK.prob;
  const edge = match?.topValueBet?.edgePct ?? DEMO_FALLBACK.edge;

  // Identify the dominant side (biggest probability) to highlight as
  // the "value" column visually.
  const maxProb = Math.max(prob.home, prob.draw, prob.away);
  const dominantSide: 'home' | 'draw' | 'away' =
    prob.home === maxProb ? 'home' : prob.away === maxProb ? 'away' : 'draw';

  return (
    <section className="mx-auto max-w-6xl px-4 py-12 md:px-8">
      <div className="mb-8 text-center">
        <motion.h2
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
          className="text-3xl font-bold tracking-tight text-white md:text-4xl"
        >
          Voyez par vous-même
        </motion.h2>
        <motion.p
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5, delay: 0.1 }}
          className="mt-3 text-slate-400"
        >
          Un match du jour, probabilités calibrées, value bet repéré.
        </motion.p>
      </div>

      <motion.div
        initial={{ opacity: 0, y: 20, scale: 0.98 }}
        whileInView={{ opacity: 1, y: 0, scale: 1 }}
        viewport={{ once: true, margin: '-10%' }}
        transition={{ duration: 0.6, ease: EASE_OUT }}
      >
        <Card className="relative overflow-hidden border-white/5 bg-gradient-to-br from-white/[0.04] to-white/[0.01] p-6 backdrop-blur md:p-8">
          <div
            aria-hidden
            className="pointer-events-none absolute -right-20 -top-20 h-72 w-72 rounded-full opacity-20 blur-3xl"
            style={{ background: '#10b981' }}
          />

          <div className="relative mb-6 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div
                className="h-2 w-2 rounded-full"
                style={{ background: leagueColor, boxShadow: `0 0 12px ${leagueColor}` }}
              />
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                {leagueName}
              </span>
              <Badge variant="outline" className="border-white/10 bg-white/5 text-[10px] text-slate-400">
                {kickoff}
              </Badge>
            </div>
            <Badge className="gap-1 border-amber-500/30 bg-amber-500/10 text-amber-400">
              <Zap className="h-3 w-3" />
              Value bet · +{edge.toFixed(1)}%
            </Badge>
          </div>

          <div className="relative mb-6 flex items-center justify-between">
            <div className="flex-1 text-left">
              <div className="text-2xl font-bold text-white md:text-3xl">{home}</div>
              <div className="mt-1 text-xs text-slate-500">Domicile</div>
            </div>
            <div className="px-4 text-sm text-slate-600">vs</div>
            <div className="flex-1 text-right">
              <div className="text-2xl font-bold text-white md:text-3xl">{away}</div>
              <div className="mt-1 text-xs text-slate-500">Extérieur</div>
            </div>
          </div>

          <ProbBarAnimated home={prob.home} draw={prob.draw} away={prob.away} />

          <div className="relative mt-6 grid grid-cols-3 gap-2">
            {(['home', 'draw', 'away'] as const).map((side, i) => {
              const labels = { home, draw: 'Nul', away };
              const implOdd = 1 / Math.max(prob[side], 0.01);
              const isValue = side === dominantSide;
              return (
                <motion.div
                  key={side}
                  initial={{ opacity: 0, y: 10 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.4, delay: 0.6 + i * 0.1 }}
                  className={`rounded-lg border p-3 text-center transition-all ${
                    isValue
                      ? 'border-emerald-500/40 bg-emerald-500/5 shadow-[0_0_0_1px_rgba(16,185,129,0.15)]'
                      : 'border-white/5 bg-white/[0.02]'
                  }`}
                >
                  <div className="text-[10px] font-semibold uppercase tracking-wider text-slate-500">
                    {labels[side]}
                  </div>
                  <div
                    className={`mt-1 text-lg font-bold ${isValue ? 'text-emerald-400' : 'text-white'}`}
                    style={{ fontVariantNumeric: 'tabular-nums' }}
                  >
                    {implOdd.toFixed(2)}
                  </div>
                  {isValue && (
                    <div className="mt-1 text-[10px] font-semibold text-emerald-400">
                      +{edge.toFixed(1)}%
                    </div>
                  )}
                </motion.div>
              );
            })}
          </div>

          <div className="relative mt-6 flex items-center justify-between rounded-lg border border-white/5 bg-white/[0.02] px-4 py-3">
            <div className="flex items-center gap-3">
              <div className="flex h-8 w-8 items-center justify-center rounded-full bg-emerald-500/10">
                <Lock className="h-3.5 w-3.5 text-emerald-400" />
              </div>
              <div>
                <div className="text-sm font-semibold text-white">
                  Kelly fraction · Stats avancées · Alerte
                </div>
                <div className="text-xs text-slate-500">Réservé aux comptes Premium</div>
              </div>
            </div>
            <Button asChild size="sm" className="bg-emerald-500 text-black hover:bg-emerald-400">
              <Link to="/premium">Débloquer</Link>
            </Button>
          </div>
        </Card>
      </motion.div>
    </section>
  );
}
