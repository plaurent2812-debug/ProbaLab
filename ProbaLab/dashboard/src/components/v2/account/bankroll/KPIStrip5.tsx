import { StatTile } from '@/components/v2/system/StatTile';
import type { StatTone } from '@/components/v2/system/StatTile';
import type { BankrollSummary } from '@/hooks/v2/useBankroll';

const euro = new Intl.NumberFormat('fr-FR', {
  style: 'currency',
  currency: 'EUR',
});

// Signed integer delta in euros — we keep it integer to avoid cents
// noise ("+284€" reads much cleaner than "+284.00€" for a hero tile).
function formatDelta(current: number, initial: number): string {
  const diff = Math.round(current - initial);
  return `${diff >= 0 ? '+' : ''}${diff}€`;
}

function toneForSigned(value: number): StatTone {
  if (value > 0) return 'positive';
  if (value < 0) return 'negative';
  return 'neutral';
}

interface Props {
  bankroll: BankrollSummary;
  'data-testid'?: string;
}

/**
 * Bankroll hero row — five KPI tiles summarising the user's tracked capital.
 *
 * Responsive: 2 columns on mobile, 5 columns from `lg`. Uses the
 * shared StatTile primitive so the tones + typography stay aligned
 * with the rest of the dashboard.
 */
export function KPIStrip5({
  bankroll,
  'data-testid': dataTestId = 'kpi-strip-5',
}: Props) {
  const roiTone = toneForSigned(bankroll.roi_30d);
  // Drawdown is always <= 0 by definition — non-zero means a loss,
  // so we flag it negative whenever the user actually hit one.
  const drawdownTone: StatTone =
    bankroll.drawdown_max_pct < 0 ? 'negative' : 'neutral';

  return (
    <div
      data-testid={dataTestId}
      className="grid gap-3 grid-cols-2 lg:grid-cols-5"
    >
      <StatTile
        data-testid="tile-bankroll"
        label="Capital suivi"
        value={euro.format(bankroll.current_balance)}
        delta={formatDelta(bankroll.current_balance, bankroll.initial_balance)}
        tone={toneForSigned(bankroll.current_balance - bankroll.initial_balance)}
      />
      <StatTile
        data-testid="tile-roi-30d"
        label="Résultat 30J"
        value={`${bankroll.roi_30d >= 0 ? '+' : ''}${bankroll.roi_30d.toFixed(1)}%`}
        delta="30 derniers jours"
        tone={roiTone}
      />
      <StatTile
        data-testid="tile-win-rate"
        label="Taux de réussite"
        value={`${bankroll.win_rate.toFixed(1)}%`}
        delta={`${bankroll.wins} gagnés / ${bankroll.losses} perdus`}
        tone="neutral"
      />
      <StatTile
        data-testid="tile-drawdown"
        label="Baisse max"
        value={`${bankroll.drawdown_max_pct.toFixed(1)}%`}
        delta="Max"
        tone={drawdownTone}
      />
      <StatTile
        data-testid="tile-kelly"
        label="Mise auto"
        value={bankroll.kelly_fraction_active.toFixed(2)}
        delta="Niveau"
        tone="neutral"
      />
    </div>
  );
}

export default KPIStrip5;
