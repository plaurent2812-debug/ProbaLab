import { TrendingUp } from 'lucide-react';
import type { Recommendation } from '../../../types/v2/match-detail';

export interface RecoCardProps {
  recommendation: Recommendation | null;
  'data-testid'?: string;
}

export function RecoCard({
  recommendation,
  'data-testid': dataTestId = 'reco-card',
}: RecoCardProps) {
  if (!recommendation) return null;

  const confidencePct = Math.round(recommendation.confidence * 100);
  const kellyPct = (recommendation.kelly_fraction * 100).toFixed(1);
  const edgePct = Math.round(recommendation.edge * 100);

  const ariaLabel = `Recommandation : ${recommendation.market_label} à cote ${recommendation.odds.toFixed(2)} chez ${recommendation.book_name}, confiance ${confidencePct}%, mise prudente ${kellyPct}%, signal +${edgePct}%`;

  return (
    <section
      data-testid={dataTestId}
      aria-label={ariaLabel}
      className="rounded-[22px] p-5"
      style={{
        border: '1px solid rgba(96,165,250,0.22)',
        background:
          'linear-gradient(180deg, rgba(96,165,250,0.08), rgba(255,255,255,0.015)), var(--surface)',
      }}
    >
      <div
        className="flex items-center gap-1.5 text-[10px] font-bold uppercase tracking-[0.16em]"
        style={{ color: 'var(--primary)' }}
      >
        <TrendingUp className="h-3 w-3" aria-hidden="true" />
        Prono recommandé
      </div>
      <div className="mt-1 text-base font-semibold" style={{ color: 'var(--text)' }}>
        {recommendation.market_label}
      </div>
      <div
        data-testid="reco-odds"
        className="mt-2 text-[34px] font-black leading-none tabular-nums"
        style={{ color: 'var(--primary)' }}
      >
        {recommendation.odds.toFixed(2)}
      </div>
      <div className="mt-1 text-xs" style={{ color: 'var(--text-muted)' }}>
        chez {recommendation.book_name}
      </div>
      <dl className="mt-4 grid grid-cols-3 gap-2 text-center text-xs">
        <div>
          <dt style={{ color: 'var(--text-muted)' }}>Confiance</dt>
          <dd className="mt-0.5 font-semibold tabular-nums" style={{ color: 'var(--text)' }}>
            {confidencePct}%
          </dd>
        </div>
        <div>
          <dt style={{ color: 'var(--text-muted)' }}>Mise prudente</dt>
          <dd className="mt-0.5 font-semibold tabular-nums" style={{ color: 'var(--text)' }}>
            {kellyPct}%
          </dd>
        </div>
        <div>
          <dt style={{ color: 'var(--text-muted)' }}>Signal</dt>
          <dd className="mt-0.5 font-semibold tabular-nums" style={{ color: 'var(--value)' }}>
            +{edgePct}%
          </dd>
        </div>
      </dl>
    </section>
  );
}

export default RecoCard;
