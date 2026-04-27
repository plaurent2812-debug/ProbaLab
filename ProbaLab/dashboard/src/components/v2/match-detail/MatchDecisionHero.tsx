import { ArrowRight, CalendarClock, MapPin, ShieldCheck, Target } from 'lucide-react';
import type {
  MatchHeader,
  MarketProb,
  Recommendation,
} from '@/types/v2/match-detail';

export interface MatchDecisionHeroProps {
  header: MatchHeader;
  probs: { home: number; draw: number; away: number };
  recommendation: Recommendation | null;
  recommendedMarket: MarketProb | null;
  analysisAvailable: boolean;
  'data-testid'?: string;
}

function pct(value: number): string {
  return `${Math.round(value * 100)}%`;
}

function odds(value: number | null | undefined): string {
  return typeof value === 'number' && Number.isFinite(value) ? value.toFixed(2) : '—';
}

function formatKickoff(iso: string): string {
  return new Intl.DateTimeFormat('fr-FR', {
    weekday: 'short',
    day: '2-digit',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
    timeZone: 'Europe/Paris',
  }).format(new Date(iso));
}

function leadingScenario(
  probs: MatchDecisionHeroProps['probs'],
  homeName: string,
  awayName: string,
): string {
  const entries = [
    { key: 'home', label: `${homeName} devant`, value: probs.home },
    { key: 'draw', label: 'Match serré', value: probs.draw },
    { key: 'away', label: `${awayName} devant`, value: probs.away },
  ].sort((a, b) => b.value - a.value);
  const [first, second] = entries;

  if (first.key === 'draw') {
    return `Le nul pèse lourd dans la lecture du match : ${pct(first.value)} contre ${pct(second.value)} pour l'option suivante.`;
  }

  return `${first.label} selon le modèle (${pct(first.value)}), avec ${second.label.toLowerCase()} comme scénario à surveiller.`;
}

function ProbabilityCard({
  label,
  value,
  active,
}: {
  label: string;
  value: number;
  active: boolean;
}) {
  return (
    <div
      className="rounded-2xl p-3"
      style={{
        border: active ? '1px solid rgba(96,165,250,0.44)' : '1px solid var(--border)',
        background: active ? 'rgba(96,165,250,0.11)' : 'rgba(255,255,255,0.035)',
      }}
    >
      <span className="block text-[11px] font-semibold" style={{ color: 'var(--text-muted)' }}>
        {label}
      </span>
      <strong className="mt-1 block text-2xl font-black tabular-nums" style={{ color: active ? '#93c5fd' : 'var(--text)' }}>
        {pct(value)}
      </strong>
    </div>
  );
}

export function MatchDecisionHero({
  header,
  probs,
  recommendation,
  recommendedMarket,
  analysisAvailable,
  'data-testid': dataTestId = 'match-decision-hero',
}: MatchDecisionHeroProps) {
  const { home, away } = header;
  const maxProb = Math.max(probs.home, probs.draw, probs.away);
  const recommendedText = recommendation?.market_label ?? 'Aucun prono recommandé';
  const confidence = recommendation ? pct(recommendation.confidence) : '—';
  const signal = recommendation ? `+${pct(recommendation.edge)}` : '—';

  return (
    <section
      data-testid={dataTestId}
      aria-labelledby="match-decision-title"
      className="relative overflow-hidden rounded-[32px] p-5 md:p-7"
      style={{
        border: '1px solid rgba(96,165,250,0.28)',
        background:
          'radial-gradient(circle at 8% 8%, rgba(96,165,250,0.22), transparent 32%), radial-gradient(circle at 88% 8%, rgba(34,211,238,0.14), transparent 28%), linear-gradient(145deg, rgba(7,17,31,0.99), rgba(15,23,42,0.94))',
        boxShadow: '0 28px 90px rgba(0,0,0,0.32)',
      }}
    >
      <div
        aria-hidden="true"
        className="pointer-events-none absolute inset-x-8 top-0 h-px"
        style={{ background: 'linear-gradient(90deg, transparent, rgba(147,197,253,0.8), transparent)' }}
      />

      <div className="grid gap-6 lg:grid-cols-[minmax(0,1.25fr)_minmax(330px,0.75fr)] lg:items-stretch">
        <div className="flex flex-col justify-between gap-6">
          <div>
            <div className="flex flex-wrap items-center gap-2 text-xs font-bold uppercase tracking-[0.16em]" style={{ color: 'var(--primary)' }}>
              <span>{header.league_name}</span>
              <span aria-hidden="true">·</span>
              <span className="inline-flex items-center gap-1">
                <CalendarClock className="h-3.5 w-3.5" aria-hidden="true" />
                {formatKickoff(header.kickoff_utc)}
              </span>
              {header.stadium && (
                <>
                  <span aria-hidden="true">·</span>
                  <span className="inline-flex items-center gap-1">
                    <MapPin className="h-3.5 w-3.5" aria-hidden="true" />
                    {header.stadium}
                  </span>
                </>
              )}
            </div>

            <h1
              id="match-decision-title"
              className="mt-4 text-4xl font-black leading-[0.95] tracking-[-0.07em] md:text-6xl"
              style={{ color: 'var(--text)' }}
            >
              Décision du match
            </h1>
            <p className="mt-3 max-w-2xl text-sm leading-6 md:text-base" style={{ color: 'var(--text-muted)' }}>
              Une lecture claire du scénario, des probabilités et du prono éventuel avant de descendre dans les détails.
            </p>
          </div>

          <div className="grid gap-4 md:grid-cols-[1fr_auto_1fr] md:items-center">
            <TeamIdentity name={home.name} logo={home.logo_url} rank={home.rank} align="left" />
            <div className="hidden rounded-full px-4 py-2 text-xs font-black md:block" style={{ color: 'var(--text-faint)', border: '1px solid var(--border)' }}>
              VS
            </div>
            <TeamIdentity name={away.name} logo={away.logo_url} rank={away.rank} align="right" />
          </div>

          <div>
            <div className="mb-2 text-[11px] font-bold uppercase tracking-[0.16em]" style={{ color: 'var(--text-muted)' }}>
              Probabilités clés
            </div>
            <div className="grid gap-3 sm:grid-cols-3">
              <ProbabilityCard label={home.name} value={probs.home} active={probs.home === maxProb} />
              <ProbabilityCard label="Nul" value={probs.draw} active={probs.draw === maxProb} />
              <ProbabilityCard label={away.name} value={probs.away} active={probs.away === maxProb} />
            </div>
          </div>
        </div>

        <div
          className="rounded-[26px] p-4 md:p-5"
          style={{
            border: '1px solid rgba(148,163,184,0.18)',
            background: 'rgba(2,6,23,0.46)',
            boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.05)',
          }}
        >
          <div className="flex items-center gap-2 text-[11px] font-bold uppercase tracking-[0.16em]" style={{ color: 'var(--primary)' }}>
            <ShieldCheck className="h-4 w-4" aria-hidden="true" />
            Prono recommandé
          </div>
          <div className="mt-3 rounded-2xl p-4" style={{ background: 'rgba(96,165,250,0.10)', border: '1px solid rgba(96,165,250,0.24)' }}>
            <strong className="block text-xl font-black tracking-[-0.04em]" style={{ color: 'var(--text)' }}>
              {recommendedText}
            </strong>
            {recommendation ? (
              <div className="mt-2 flex flex-wrap items-end gap-3">
                <span className="text-4xl font-black tabular-nums" style={{ color: 'var(--primary)' }}>
                  {recommendation.odds.toFixed(2)}
                </span>
                <span className="pb-1 text-xs" style={{ color: 'var(--text-muted)' }}>
                  chez {recommendation.book_name}
                </span>
              </div>
            ) : (
              <p className="mt-2 text-sm leading-6" style={{ color: 'var(--text-muted)' }}>
                Le modèle ne force pas de pari si le signal n'est pas assez clair.
              </p>
            )}
          </div>

          <div className="mt-4 grid grid-cols-3 gap-2 text-center">
            <MiniMetric label="Confiance" value={confidence} />
            <MiniMetric label="Cote modèle" value={odds(recommendedMarket?.fair_odds)} />
            <MiniMetric label="Signal" value={signal} accent />
          </div>

          <div className="mt-4 rounded-2xl p-4" style={{ border: '1px solid var(--border)', background: 'rgba(255,255,255,0.035)' }}>
            <div className="flex items-center gap-2 text-[11px] font-bold uppercase tracking-[0.14em]" style={{ color: 'var(--text-muted)' }}>
              <Target className="h-3.5 w-3.5" aria-hidden="true" />
              À surveiller
            </div>
            <p className="mt-2 text-sm leading-6" style={{ color: 'var(--text)' }}>
              {leadingScenario(probs, home.name, away.name)}
            </p>
          </div>

          <div className="mt-4 flex flex-wrap gap-2">
            {analysisAvailable && (
              <a
                href="#analyse-ia"
                className="inline-flex items-center gap-1 rounded-full px-3 py-2 text-xs font-bold"
                style={{ background: 'var(--primary)', color: '#061014' }}
              >
                Voir l'analyse
                <ArrowRight className="h-3.5 w-3.5" aria-hidden="true" />
              </a>
            )}
            <a
              href="#marches"
              className="inline-flex items-center gap-1 rounded-full px-3 py-2 text-xs font-bold"
              style={{ border: '1px solid var(--border)', color: 'var(--text)' }}
            >
              Tous les marchés
              <ArrowRight className="h-3.5 w-3.5" aria-hidden="true" />
            </a>
          </div>
        </div>
      </div>
    </section>
  );
}

function TeamIdentity({
  name,
  logo,
  rank,
  align,
}: {
  name: string;
  logo: string;
  rank?: number;
  align: 'left' | 'right';
}) {
  const reverse = align === 'right';
  return (
    <div className={`flex items-center gap-3 ${reverse ? 'justify-end text-right' : 'justify-start text-left'}`}>
      {!reverse && <img src={logo} alt={`${name} logo`} className="h-14 w-14 object-contain md:h-16 md:w-16" />}
      <div>
        <div className="text-xl font-black tracking-[-0.05em] md:text-2xl" style={{ color: 'var(--text)' }}>
          {name}
        </div>
        {rank != null && (
          <div className="mt-1 text-xs font-semibold" style={{ color: 'var(--text-muted)' }}>
            Classement #{rank}
          </div>
        )}
      </div>
      {reverse && <img src={logo} alt={`${name} logo`} className="h-14 w-14 object-contain md:h-16 md:w-16" />}
    </div>
  );
}

function MiniMetric({
  label,
  value,
  accent = false,
}: {
  label: string;
  value: string;
  accent?: boolean;
}) {
  return (
    <div className="rounded-xl p-2" style={{ background: 'rgba(255,255,255,0.035)', border: '1px solid var(--border)' }}>
      <span className="block text-[10px]" style={{ color: 'var(--text-muted)' }}>
        {label}
      </span>
      <strong className="mt-1 block text-sm tabular-nums" style={{ color: accent ? 'var(--value, #fbbf24)' : 'var(--text)' }}>
        {value}
      </strong>
    </div>
  );
}

export default MatchDecisionHero;
