import { useId } from 'react';
import { Zap, Star, TrendingUp } from 'lucide-react';
import type { League } from '@/types/v2/common';
import type { MatchesFilters, SignalKind, Sport } from '@/types/v2/matches';

type MatchesSort = NonNullable<MatchesFilters['sort']>;

interface Props {
  filters: MatchesFilters;
  onChange: (f: MatchesFilters) => void;
  matchesByLeague?: Partial<Record<League, number>>;
  'data-testid'?: string;
}

const SPORTS: { key: Sport; label: string }[] = [
  { key: 'football', label: 'Football' },
  { key: 'nhl', label: 'NHL' },
];

const LEAGUES: { key: League; label: string }[] = [
  { key: 'L1', label: 'Ligue 1' },
  { key: 'L2', label: 'Ligue 2' },
  { key: 'PL', label: 'Premier League' },
  { key: 'LaLiga', label: 'La Liga' },
  { key: 'SerieA', label: 'Serie A' },
  { key: 'Bundesliga', label: 'Bundesliga' },
  { key: 'UCL', label: 'UCL' },
  { key: 'UEL', label: 'UEL' },
];

const SIGNALS: { key: SignalKind; label: string; Icon: typeof Zap }[] = [
  { key: 'value', label: 'Signal modèle fort', Icon: Zap },
  { key: 'safe', label: 'Safe du jour', Icon: Star },
  { key: 'high_confidence', label: 'Confiance élevée', Icon: TrendingUp },
];

const SORTS: { key: MatchesSort; label: string }[] = [
  { key: 'kickoff', label: 'Heure' },
  { key: 'edge', label: 'Signal' },
  { key: 'confidence', label: 'Confiance' },
  { key: 'league', label: 'Ligue' },
];

function toggle<T>(arr: T[] | undefined, value: T): T[] {
  const list = arr ?? [];
  return list.includes(value) ? list.filter((v) => v !== value) : [...list, value];
}

export function FilterSidebar({
  filters,
  onChange,
  matchesByLeague,
  'data-testid': dataTestId = 'filter-sidebar',
}: Props) {
  const sortId = useId();

  const onSportToggle = (s: Sport) =>
    onChange({ ...filters, sports: toggle(filters.sports, s) });
  const onLeagueToggle = (l: League) =>
    onChange({ ...filters, leagues: toggle(filters.leagues, l) });
  const onSignalToggle = (sig: SignalKind) =>
    onChange({ ...filters, signals: toggle(filters.signals, sig) });

  const sportCount = (s: Sport): number | undefined => {
    if (!matchesByLeague) return undefined;
    if (s === 'nhl') return matchesByLeague.NHL ?? 0;
    const footballKeys: League[] = [
      'L1',
      'L2',
      'PL',
      'LaLiga',
      'SerieA',
      'Bundesliga',
      'UCL',
      'UEL',
    ];
    return footballKeys.reduce((acc, k) => acc + (matchesByLeague[k] ?? 0), 0);
  };

  return (
    <aside
      data-testid={dataTestId}
      aria-label="Filtres"
      className="flex w-full flex-col gap-5 rounded-[26px] p-4 md:w-[260px]"
      style={{
        color: 'var(--text)',
        border: '1px solid rgba(148,163,184,0.18)',
        background:
          'linear-gradient(180deg, rgba(255,255,255,0.045), rgba(255,255,255,0.018)), var(--surface)',
      }}
    >
      <div>
        <div className="text-sm font-black tracking-[-0.04em]" style={{ color: 'var(--text)' }}>
          Affiner la sélection
        </div>
        <p className="mt-1 text-xs leading-5" style={{ color: 'var(--text-muted)' }}>
          Filtre les matchs utiles sans perdre la synthèse principale.
        </p>
      </div>
      <section>
        <h3 className="mb-2 text-xs font-semibold uppercase tracking-wider" style={{ color: 'var(--text-muted)' }}>
          Sport
        </h3>
        <ul className="space-y-1.5">
          {SPORTS.map(({ key, label }) => {
            const count = sportCount(key);
            return (
              <li key={key}>
                <label className="flex cursor-pointer items-center gap-2 text-sm">
                  <input
                    type="checkbox"
                    checked={filters.sports?.includes(key) ?? false}
                    onChange={() => onSportToggle(key)}
                  />
                  <span>{label}</span>
                  {count !== undefined && (
                    <span className="ml-auto text-xs tabular-nums" style={{ color: 'var(--text-muted)' }}>
                      {count}
                    </span>
                  )}
                </label>
              </li>
            );
          })}
        </ul>
      </section>

      <section>
        <h3 className="mb-2 text-xs font-semibold uppercase tracking-wider" style={{ color: 'var(--text-muted)' }}>
          Ligue
        </h3>
        <ul className="space-y-1.5">
          {LEAGUES.map(({ key, label }) => {
            const count = matchesByLeague?.[key];
            return (
              <li key={key}>
                <label className="flex cursor-pointer items-center gap-2 text-sm">
                  <input
                    type="checkbox"
                    aria-label={label}
                    checked={filters.leagues?.includes(key) ?? false}
                    onChange={() => onLeagueToggle(key)}
                  />
                  <span>{label}</span>
                  {count !== undefined && (
                    <span className="ml-auto text-xs tabular-nums" style={{ color: 'var(--text-muted)' }}>
                      {count}
                    </span>
                  )}
                </label>
              </li>
            );
          })}
        </ul>
      </section>

      <section>
        <h3 className="mb-2 text-xs font-semibold uppercase tracking-wider" style={{ color: 'var(--text-muted)' }}>
          Signaux
        </h3>
        <ul className="space-y-1.5">
          {SIGNALS.map(({ key, label, Icon }) => (
            <li key={key}>
              <label className="flex cursor-pointer items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={filters.signals?.includes(key) ?? false}
                  onChange={() => onSignalToggle(key)}
                />
                <Icon aria-hidden="true" size={14} />
                <span>{label}</span>
              </label>
            </li>
          ))}
        </ul>
      </section>

      <section>
        <h3 id={sortId} className="mb-2 text-xs font-semibold uppercase tracking-wider" style={{ color: 'var(--text-muted)' }}>
          Tri
        </h3>
        <select
          aria-labelledby={sortId}
          value={filters.sort ?? 'kickoff'}
          onChange={(e) =>
            onChange({ ...filters, sort: e.target.value as MatchesSort })
          }
          className="w-full rounded-md px-2 py-1.5 text-sm"
          style={{ border: '1px solid var(--border)', background: 'var(--surface)', color: 'var(--text)' }}
        >
          {SORTS.map(({ key, label }) => (
            <option key={key} value={key}>
              {label}
            </option>
          ))}
        </select>
      </section>
    </aside>
  );
}

export default FilterSidebar;
