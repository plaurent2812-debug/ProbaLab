import { StatTile } from '@/components/v2/system/StatTile';
import type { PerformanceSummary } from '@/types/v2/performance';

interface Props {
  data?: PerformanceSummary;
  loading?: boolean;
  'data-testid'?: string;
}

// Defensive helpers: API may return partial/invalid payloads (404 fallback,
// empty DB, schema drift). We never call .toFixed on possibly-undefined values.
function isNum(v: unknown): v is number {
  return typeof v === 'number' && Number.isFinite(v);
}

function fmtPct(v: unknown, digits = 1): string {
  return isNum(v) ? `${(v as number).toFixed(digits)}%` : '—';
}

function fmtBrier(v: unknown): string {
  return isNum(v) ? (v as number).toFixed(3) : '—';
}

function fmtBankroll(v: unknown): string {
  if (!isNum(v)) return '—';
  return `${(v as number).toLocaleString('fr-FR').replace(/\u202f/g, ' ')} €`;
}

function fmtDelta(v: unknown, suffix = '%'): string | undefined {
  if (!isNum(v)) return undefined;
  const n = v as number;
  const sign = n >= 0 ? '+' : '';
  return `${sign}${n.toFixed(1)}${suffix} vs 7j`;
}

export function StatStrip({ data, loading, 'data-testid': dataTestId = 'stat-strip' }: Props) {
  if (loading) {
    return (
      <div
        data-testid={dataTestId}
        className="grid grid-cols-2 md:grid-cols-4 gap-3"
      >
        {[0, 1, 2, 3].map((i) => (
          <div
            key={i}
            data-testid="stat-tile-skeleton"
            className="h-20 rounded-lg bg-surface-2 animate-pulse"
            style={{ background: 'var(--surface-2)' }}
          />
        ))}
      </div>
    );
  }

  // Safe accessors - every field is optional and guarded.
  const roi = data?.roi30d;
  const acc = data?.accuracy;
  const brier = data?.brier7d;
  const bank = data?.bankroll;

  const roiValue = roi?.value;
  const accValue = acc?.value;
  const brierDelta = brier?.deltaVs7d;

  return (
    <div
      data-testid={dataTestId}
      className="grid grid-cols-2 md:grid-cols-4 gap-3"
    >
      <StatTile
        label="ROI 30J"
        value={fmtPct(roiValue)}
        delta={fmtDelta(roi?.deltaVs7d)}
        tone={isNum(roiValue) ? (roiValue >= 0 ? 'positive' : 'negative') : undefined}
      />
      <StatTile
        label="Accuracy"
        value={fmtPct(accValue)}
        delta={fmtDelta(acc?.deltaVs7d)}
      />
      <StatTile
        label="Brier 7J"
        value={fmtBrier(brier?.value)}
        delta={fmtDelta(brierDelta, '')}
        tone={isNum(brierDelta) ? (brierDelta <= 0 ? 'positive' : 'negative') : undefined}
      />
      <StatTile label="Bankroll" value={fmtBankroll(bank?.value)} />
    </div>
  );
}

export default StatStrip;
