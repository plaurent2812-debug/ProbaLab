import type { ReactNode } from 'react';
import type { LeagueRef } from '@/types/v2/matches';

interface Props {
  league: LeagueRef;
  count: number;
  children: ReactNode;
  'data-testid'?: string;
}

export function LeagueGroup({
  league,
  count,
  children,
  'data-testid': dataTestId = 'league-group',
}: Props) {
  return (
    <section
      data-testid={dataTestId}
      className="overflow-hidden rounded-[26px]"
      style={{
        border: '1px solid rgba(148,163,184,0.18)',
        background:
          'linear-gradient(180deg, rgba(255,255,255,0.045), rgba(255,255,255,0.018)), var(--surface)',
      }}
    >
      <h3
        className="flex items-center gap-2 px-4 py-3 text-xs font-bold uppercase tracking-[0.16em]"
        style={{
          background: `linear-gradient(90deg, ${league.color}55, rgba(15,23,42,0.40))`,
          color: 'var(--text)',
          borderBottom: '1px solid var(--border)',
        }}
      >
        {league.name}
        <span className="ml-auto text-[11px]" style={{ opacity: 0.8 }}>
          {count}
        </span>
      </h3>
      <div>{children}</div>
    </section>
  );
}

export default LeagueGroup;
