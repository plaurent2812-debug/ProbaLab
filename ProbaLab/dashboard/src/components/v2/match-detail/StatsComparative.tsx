import type { ComparativeStat } from '../../../types/v2/match-detail';

export interface StatsComparativeProps {
  stats: ComparativeStat[];
  /**
   * Titre de la section. Absent = pas de heading rendu.
   */
  label?: string;
  'data-testid'?: string;
}

function format(value: number, unit?: string): string {
  return `${value}${unit ?? ''}`;
}

export function StatsComparative({
  stats,
  label,
  'data-testid': dataTestId = 'stats-comparative',
}: StatsComparativeProps) {
  return (
    <section
      data-testid={dataTestId}
      className="rounded-[22px] p-4"
      style={{ border: '1px solid var(--border)', background: 'var(--surface)' }}
    >
      {label && (
        <h3 className="mb-3 text-sm font-semibold" style={{ color: 'var(--text)' }}>{label}</h3>
      )}
      <ul className="space-y-3">
        {stats.map((s) => {
          const total = s.home_value + s.away_value;
          const homePct = total > 0 ? (s.home_value / total) * 100 : 50;
          const homeBest = s.home_value >= s.away_value;
          return (
            <li
              key={s.label}
              data-testid="stat-row"
              aria-label={`${s.label} : domicile ${format(
                s.home_value,
                s.unit,
              )}, extérieur ${format(s.away_value, s.unit)}`}
              className="flex items-center gap-3 text-xs"
            >
              <span
                className="w-10 text-right font-semibold tabular-nums"
                style={{ color: homeBest ? 'var(--primary)' : 'var(--text-muted)' }}
              >
                {format(s.home_value, s.unit)}
              </span>
              <div className="flex h-2 flex-1 overflow-hidden rounded-full" style={{ background: 'rgba(255,255,255,0.06)' }}>
                <div
                  style={{
                    width: `${homePct}%`,
                    background: homeBest ? 'var(--primary)' : 'rgba(148,163,184,0.7)',
                  }}
                />
                <div
                  style={{
                    width: `${100 - homePct}%`,
                    background: !homeBest ? 'var(--primary)' : 'rgba(148,163,184,0.7)',
                  }}
                />
              </div>
              <span
                className="w-10 text-left font-semibold tabular-nums"
                style={{ color: !homeBest ? 'var(--primary)' : 'var(--text-muted)' }}
              >
                {format(s.away_value, s.unit)}
              </span>
              <span className="ml-2 min-w-[120px]" style={{ color: 'var(--text-muted)' }}>
                {s.label}
              </span>
            </li>
          );
        })}
      </ul>
    </section>
  );
}

export default StatsComparative;
