import type { ReactNode } from 'react';

export type StatTone = 'neutral' | 'positive' | 'negative';

export interface StatTileProps {
  label: string;
  value: ReactNode;
  delta?: string;
  tone?: StatTone;
  'data-testid'?: string;
}

function toneColor(tone: StatTone): string {
  if (tone === 'positive') return 'var(--primary)';
  if (tone === 'negative') return 'var(--danger)';
  return 'var(--text-muted)';
}

export function StatTile({
  label,
  value,
  delta,
  tone = 'neutral',
  'data-testid': dataTestId = 'stat-tile',
}: StatTileProps) {
  return (
    <div
      role="group"
      data-testid={dataTestId}
      aria-label={`${label}: ${typeof value === 'string' ? value : ''}`}
      style={{
        display: 'flex',
        flexDirection: 'column',
        gap: 'var(--space-1)',
        minHeight: 92,
        padding: 'var(--space-4)',
        background:
          'linear-gradient(180deg, rgba(255,255,255,0.035), rgba(255,255,255,0.012)), var(--surface)',
        border: '1px solid rgba(148,163,184,0.18)',
        borderRadius: 'var(--radius-lg)',
      }}
    >
      <span
        style={{
          fontSize: 12,
          color: 'var(--text-faint)',
          textTransform: 'uppercase',
          letterSpacing: '0.12em',
          fontWeight: 800,
        }}
      >
        {label}
      </span>
      <span
        style={{
          fontSize: 24,
          fontWeight: 900,
          color: 'var(--text)',
          fontVariantNumeric: 'tabular-nums',
          letterSpacing: '-0.04em',
        }}
      >
        {value}
      </span>
      {delta && (
        <span
          data-tone={tone}
          style={{ fontSize: 12, color: toneColor(tone), fontVariantNumeric: 'tabular-nums' }}
        >
          {delta}
        </span>
      )}
    </div>
  );
}

export default StatTile;
