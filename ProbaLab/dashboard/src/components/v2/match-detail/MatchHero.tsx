import { MapPin, UserCheck } from 'lucide-react';
import type {
  MatchHeader,
  MatchHeaderTeam,
} from '../../../types/v2/match-detail';
import { FormBadge } from './FormBadge';

export interface MatchHeroProps {
  header: MatchHeader;
  'data-testid'?: string;
}

function formatKickoff(iso: string): string {
  const d = new Date(iso);
  return new Intl.DateTimeFormat('fr-FR', {
    dateStyle: 'full',
    timeStyle: 'short',
    timeZone: 'Europe/Paris',
  }).format(d);
}

interface TeamBlockProps {
  team: MatchHeaderTeam;
  align: 'left' | 'right';
}

function TeamBlock({ team, align }: TeamBlockProps) {
  const flexClass =
    align === 'right'
      ? 'flex-row-reverse text-right'
      : 'flex-row text-left';
  const textAlign = align === 'right' ? 'text-right' : 'text-left';
  const formAlign = align === 'right' ? 'justify-end' : 'justify-start';

  return (
    <div className={`flex flex-1 items-center gap-4 ${flexClass}`}>
      <img
        src={team.logo_url}
        alt={`${team.name} logo`}
        width={64}
        height={64}
        className="h-16 w-16 shrink-0 object-contain"
      />
      <div className={`flex flex-col gap-1 ${textAlign}`}>
        <div className="text-lg font-black tracking-[-0.04em]" style={{ color: 'var(--text)' }}>
          {team.name}
        </div>
        {team.rank != null && (
          <div className="text-xs" style={{ color: 'var(--text-muted)' }}>
            #{team.rank}
          </div>
        )}
        <div className={`mt-1 flex ${formAlign}`}>
          <FormBadge form={team.form} />
        </div>
      </div>
    </div>
  );
}

export function MatchHero({
  header,
  'data-testid': dataTestId = 'match-hero',
}: MatchHeroProps) {
  const { home, away, kickoff_utc, stadium, referee, league_name } = header;
  return (
    <header
      data-testid={dataTestId}
      className="rounded-[28px] p-6"
      style={{
        border: '1px solid rgba(148,163,184,0.18)',
        background:
          'linear-gradient(180deg, rgba(255,255,255,0.045), rgba(255,255,255,0.012)), var(--surface)',
      }}
    >
      <div
        className="text-xs font-bold uppercase tracking-[0.18em]"
        style={{ color: 'var(--primary)' }}
      >
        {league_name}
      </div>
      <div className="mt-4 flex items-center justify-between gap-6">
        <TeamBlock team={home} align="right" />
        <div className="flex min-w-[160px] flex-col items-center gap-1 text-center">
          <div className="text-sm font-medium" style={{ color: 'var(--text)' }}>
            {formatKickoff(kickoff_utc)}
          </div>
          {stadium && (
            <div className="flex items-center gap-1 text-xs" style={{ color: 'var(--text-muted)' }}>
              <MapPin className="h-3 w-3" aria-hidden="true" />
              <span>{stadium}</span>
            </div>
          )}
          {referee && (
            <div className="flex items-center gap-1 text-xs" style={{ color: 'var(--text-muted)' }}>
              <UserCheck className="h-3 w-3" aria-hidden="true" />
              <span>{referee}</span>
            </div>
          )}
          <div className="mt-2 text-2xl font-black" style={{ color: 'var(--text-faint)' }}>
            VS
          </div>
        </div>
        <TeamBlock team={away} align="left" />
      </div>
    </header>
  );
}

export default MatchHero;
