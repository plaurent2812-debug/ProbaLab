import { Users } from 'lucide-react';
import type {
  CompositionsPayload,
  CompositionsStatus,
  Lineup,
} from '../../../types/v2/match-detail';

export interface CompositionsSectionProps {
  compositions: CompositionsPayload;
  homeName: string;
  awayName: string;
  'data-testid'?: string;
}

const STATUS_LABEL: Record<CompositionsStatus, string> = {
  confirmed: 'Confirmée',
  probable: 'Probable',
  unavailable: 'Indisponible',
};

const STATUS_BG: Record<CompositionsStatus, string> = {
  confirmed: 'rgba(16,185,129,0.14)',
  probable: 'rgba(251,191,36,0.14)',
  unavailable: 'rgba(148,163,184,0.12)',
};

const STATUS_COLOR: Record<CompositionsStatus, string> = {
  confirmed: '#34d399',
  probable: '#fbbf24',
  unavailable: 'var(--text-muted)',
};

function TeamLineup({ name, lineup }: { name: string; lineup: Lineup }) {
  return (
    <div>
      <div className="mb-2 flex items-center justify-between">
        <span className="text-xs font-semibold" style={{ color: 'var(--text)' }}>{name}</span>
        <span className="rounded px-2 py-0.5 text-[10px] font-medium tabular-nums" style={{ background: 'rgba(255,255,255,0.06)', color: 'var(--text-muted)' }}>
          {lineup.formation}
        </span>
      </div>
      <ul className="space-y-1 text-xs" style={{ color: 'var(--text)' }}>
        {lineup.starters.map((p) => (
          <li
            key={p.number}
            className="flex items-center gap-2"
            data-testid="lineup-player"
          >
            <span className="inline-block w-6 text-right tabular-nums" style={{ color: 'var(--text-muted)' }}>
              {p.number}
            </span>
            <span className="font-medium">{p.name}</span>
            <span style={{ color: 'var(--text-faint)' }}>{p.position}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

export function CompositionsSection({
  compositions,
  homeName,
  awayName,
  'data-testid': dataTestId = 'compositions-section',
}: CompositionsSectionProps) {
  const { status, home, away } = compositions;
  const unavailable = status === 'unavailable' || (!home && !away);

  return (
    <section
      data-testid={dataTestId}
      className="rounded-[22px] p-4"
      style={{ border: '1px solid var(--border)', background: 'var(--surface)' }}
    >
      <div className="mb-3 flex items-center justify-between">
        <h3 className="flex items-center gap-2 text-sm font-semibold" style={{ color: 'var(--text)' }}>
          <Users className="h-4 w-4" style={{ color: 'var(--text-muted)' }} aria-hidden="true" />
          Compositions
        </h3>
        <span
          data-testid="compositions-status"
          className="rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide"
          style={{ background: STATUS_BG[status], color: STATUS_COLOR[status] }}
        >
          {STATUS_LABEL[status]}
        </span>
      </div>
      {unavailable ? (
        <p className="text-xs" style={{ color: 'var(--text-muted)' }}>
          Compositions non communiquées.
        </p>
      ) : (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          {home && <TeamLineup name={homeName} lineup={home} />}
          {away && <TeamLineup name={awayName} lineup={away} />}
        </div>
      )}
    </section>
  );
}

export default CompositionsSection;
