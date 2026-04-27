import { Link } from 'react-router-dom';
import { Star } from 'lucide-react';
import type { SafePick } from '@/types/v2/matches';

interface Props {
  data: SafePick | null;
  'data-testid'?: string;
}

function isFiniteNumber(value: unknown): value is number {
  return typeof value === 'number' && Number.isFinite(value);
}

function formatOdd(value: unknown): string {
  return isFiniteNumber(value) ? value.toFixed(2) : '—';
}

function probabilityPercent(value: unknown): number {
  if (!isFiniteNumber(value)) return 0;
  return Math.round(Math.max(0, Math.min(1, value)) * 100);
}

export function SafeOfTheDayCard({ data, 'data-testid': dataTestId = 'safe-of-the-day-card' }: Props) {
  if (!data || !isFiniteNumber(data.odd) || typeof data.betLabel !== 'string') {
    return (
      <section
        data-testid={dataTestId}
        className="rounded-xl border border-border bg-surface p-6 text-center"
        style={{ border: '1px solid var(--border)', background: 'var(--surface)' }}
      >
        <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
          Pas de pronostic Safe aujourd'hui — privilégiez l'analyse des matchs du soir.
        </p>
      </section>
    );
  }
  const pct = probabilityPercent(data.probability);
  return (
    <section
      data-testid={dataTestId}
      className="rounded-[24px] p-5"
      style={{
        border: '1px solid rgba(96,165,250,0.24)',
        background:
          'radial-gradient(circle at 0% 0%, rgba(96,165,250,0.18), transparent 36%), linear-gradient(160deg, rgba(15,23,42,0.96), rgba(17,24,39,0.88))',
      }}
    >
      <div className="flex items-center justify-between mb-4">
        <span
          className="inline-flex items-center gap-1 text-xs font-medium tracking-wide"
          style={{ color: 'var(--primary)' }}
        >
          <Star aria-hidden="true" size={14} />
          PRONO · RECOMMANDÉ
        </span>
        <span
          className="rounded-full px-2 py-0.5 text-[11px] font-semibold"
          style={{
            border: '1px solid var(--border)',
            color: 'var(--text-muted)',
          }}
        >
          FREE
        </span>
      </div>
      <h3 className="text-lg font-semibold" style={{ color: 'var(--text)' }}>
        {data.betLabel}
      </h3>
      <div className="mt-3 flex items-baseline gap-4">
        <span
          className="font-bold tabular-nums"
          style={{ fontSize: 32, color: 'var(--primary)', fontVariantNumeric: 'tabular-nums' }}
        >
          {formatOdd(data.odd)}
        </span>
        <span className="text-sm" style={{ color: 'var(--text-muted)' }}>
          Probabilité {pct}%
        </span>
      </div>
      <div
        role="progressbar"
        aria-valuenow={pct}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label={`Probabilité ${data.betLabel} ${pct}%`}
        className="mt-2 h-1 w-full rounded-full overflow-hidden"
        style={{ background: 'var(--surface-2)' }}
      >
        <div
          className="h-full"
          style={{ width: `${pct}%`, background: 'var(--primary)' }}
        />
      </div>
      {data.justification && (
        <p className="mt-4 text-sm leading-relaxed" style={{ color: 'var(--text-muted)' }}>
          {data.justification}
        </p>
      )}
      <div className="mt-4 grid grid-cols-2 gap-2">
        <div
          className="rounded-xl p-3"
          style={{ border: '1px solid var(--border)', background: 'rgba(255,255,255,0.03)' }}
        >
          <span className="block text-[11px]" style={{ color: 'var(--text-muted)' }}>
            Niveau de risque
          </span>
          <strong className="mt-1 block text-sm" style={{ color: 'var(--primary)' }}>
            Prudent
          </strong>
        </div>
        <div
          className="rounded-xl p-3"
          style={{ border: '1px solid var(--border)', background: 'rgba(255,255,255,0.03)' }}
        >
          <span className="block text-[11px]" style={{ color: 'var(--text-muted)' }}>
            Confiance
          </span>
          <strong className="mt-1 block text-sm" style={{ color: 'var(--text)' }}>
            {pct}%
          </strong>
        </div>
      </div>
      <Link
        to={`/matchs/${data.fixtureId}`}
        className="mt-4 inline-block text-sm font-medium focus-visible:outline focus-visible:outline-2"
        style={{ color: 'var(--primary)' }}
      >
        Voir le match →
      </Link>
    </section>
  );
}

export default SafeOfTheDayCard;
