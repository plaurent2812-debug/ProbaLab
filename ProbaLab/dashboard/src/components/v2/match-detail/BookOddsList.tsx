import { BookOpen } from 'lucide-react';
import type { BookOdd } from '../../../types/v2/match-detail';
import { OddsChip } from '../system/OddsChip';

export interface BookOddsListProps {
  bookOdds: BookOdd[];
  /**
   * Index (dans `bookOdds`) à mettre en évidence comme "meilleur prix".
   * Si non fourni, on cherche d'abord le premier item avec `is_best=true`,
   * puis on retombe sur le plus haut `odds`.
   */
  bestIndex?: number;
  'data-testid'?: string;
}

function resolveBestIndex(
  bookOdds: BookOdd[],
  override: number | undefined,
): number {
  if (override != null && override >= 0 && override < bookOdds.length) {
    return override;
  }
  const flagged = bookOdds.findIndex((b) => b.is_best);
  if (flagged !== -1) return flagged;
  let maxIdx = 0;
  let maxOdds = -Infinity;
  for (let i = 0; i < bookOdds.length; i++) {
    if (bookOdds[i].odds > maxOdds) {
      maxOdds = bookOdds[i].odds;
      maxIdx = i;
    }
  }
  return maxIdx;
}

export function BookOddsList({
  bookOdds,
  bestIndex,
  'data-testid': dataTestId = 'book-odds-list',
}: BookOddsListProps) {
  const heading = (
    <h3 className="mb-3 flex items-center gap-2 text-sm font-semibold" style={{ color: 'var(--text)' }}>
      <BookOpen className="h-4 w-4" style={{ color: 'var(--text-muted)' }} aria-hidden="true" />
      Cotes bookmakers
    </h3>
  );

  if (bookOdds.length === 0) {
    return (
      <section
        data-testid={dataTestId}
        className="rounded-[22px] p-4"
        style={{ border: '1px solid var(--border)', background: 'var(--surface)' }}
      >
        {heading}
        <p className="text-xs" style={{ color: 'var(--text-muted)' }}>
          Aucune cote disponible pour le moment.
        </p>
      </section>
    );
  }

  const bestIdx = resolveBestIndex(bookOdds, bestIndex);

  return (
    <section
      data-testid={dataTestId}
      className="rounded-[22px] p-4"
      style={{ border: '1px solid var(--border)', background: 'var(--surface)' }}
    >
      {heading}
      <ul
        aria-label="Comparateur de cotes par bookmaker"
        className="flex flex-col gap-2"
      >
        {bookOdds.map((b, i) => {
          const isBest = i === bestIdx;
          const rowTestId = isBest ? 'book-odds-item-best' : 'book-odds-item';
          return (
            <li
              key={b.bookmaker}
              data-testid={rowTestId}
              data-best={isBest}
              aria-label={`${b.bookmaker}, cote ${b.odds.toFixed(2)}`}
              className="flex items-center gap-3 rounded-xl border p-3 text-sm"
              style={{
                borderColor: isBest ? 'var(--primary)' : 'var(--border)',
                background: isBest ? 'rgba(16,185,129,0.08)' : 'rgba(255,255,255,0.03)',
              }}
            >
              <span
                className="flex-1"
                style={{ color: isBest ? 'var(--text)' : 'var(--text-muted)', fontWeight: isBest ? 700 : 500 }}
              >
                {b.bookmaker}
              </span>
              <OddsChip value={b.odds} highlight={isBest} />
            </li>
          );
        })}
      </ul>
    </section>
  );
}

export { resolveBestIndex };
export default BookOddsList;
