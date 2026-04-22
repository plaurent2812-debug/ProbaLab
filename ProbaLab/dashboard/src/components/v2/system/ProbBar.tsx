export interface ProbBarProps {
  home: number;
  draw: number;
  away: number;
  homeLabel: string;
  awayLabel: string;
  'data-testid'?: string;
}

function pct(n: number): number {
  return Math.round(n * 100);
}

export function ProbBar({
  home,
  draw,
  away,
  homeLabel,
  awayLabel,
  'data-testid': dataTestId = 'prob-bar',
}: ProbBarProps) {
  // Tolerate missing probabilities (e.g. NHL fixtures without a prediction yet).
  // Normalize small rounding errors silently; treat sum=0 as a neutral bar.
  const rawSum = home + draw + away;
  if (rawSum <= 0) {
    return (
      <div
        role="img"
        aria-label="Probabilités non disponibles"
        data-testid={dataTestId}
        className="flex h-2 w-full rounded overflow-hidden"
        style={{ background: 'var(--surface-2)' }}
      />
    );
  }
  // Normalize if off from 1 (rounding) by renormalizing proportionally.
  const normHome = home / rawSum;
  const normDraw = draw / rawSum;
  const normAway = away / rawSum;
  home = normHome;
  draw = normDraw;
  away = normAway;
  const max = Math.max(home, draw, away);
  const dominant = home === max ? 'home' : draw === max ? 'draw' : 'away';
  const label = `${homeLabel} ${pct(home)}%, Nul ${pct(draw)}%, ${awayLabel} ${pct(away)}%`;

  const bg = (isDom: boolean, muted: boolean): string => {
    if (isDom) return 'var(--primary)';
    return muted ? 'var(--surface-2)' : '#334155';
  };

  return (
    <div
      role="img"
      data-testid={dataTestId}
      aria-label={label}
      style={{
        display: 'flex',
        width: '100%',
        height: 8,
        borderRadius: 'var(--radius-sm)',
        overflow: 'hidden',
        background: 'var(--surface-2)',
      }}
    >
      <span
        data-segment="home"
        data-testid="segment-home"
        data-dominant={dominant === 'home'}
        style={{ width: `${pct(home)}%`, background: bg(dominant === 'home', false) }}
      />
      <span
        data-segment="draw"
        data-testid="segment-draw"
        data-dominant={dominant === 'draw'}
        style={{ width: `${pct(draw)}%`, background: bg(dominant === 'draw', true) }}
      />
      <span
        data-segment="away"
        data-testid="segment-away"
        data-dominant={dominant === 'away'}
        style={{ width: `${pct(away)}%`, background: bg(dominant === 'away', false) }}
      />
    </div>
  );
}

export default ProbBar;
