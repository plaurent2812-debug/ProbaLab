interface Props {
  lastUpdateUtc?: string;
  'data-testid'?: string;
}

export function ProofStrip({
  lastUpdateUtc,
  'data-testid': dataTestId = 'proof-strip',
}: Props) {
  const stamp = lastUpdateUtc ? `${lastUpdateUtc} UTC` : 'Mise à jour automatique en cours';

  return (
    <aside
      role="note"
      data-testid={dataTestId}
      aria-label="Transparence du modèle"
      className="rounded-2xl px-4 py-3 md:px-5 md:py-4"
      style={{
        border: '1px solid rgba(96,165,250,0.22)',
        background:
          'linear-gradient(180deg, rgba(96,165,250,0.08), rgba(15,23,42,0.6))',
      }}
    >
      <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
        <div className="space-y-1">
          <p
            className="text-[11px] font-bold uppercase tracking-[0.18em]"
            style={{ color: 'var(--primary)' }}
          >
            Modèle suivi en continu
          </p>
          <p
            data-testid="proof-strip-body"
            className="text-sm leading-relaxed"
            style={{ color: 'var(--text-muted)' }}
          >
            ROI 30J, précision, Brier 7J et bankroll sont recalculés automatiquement
            après chaque match résolu. Pas d'édition manuelle, pas de cherry-picking.
          </p>
        </div>
        <span
          className="shrink-0 rounded-full border px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.14em] tabular-nums"
          style={{
            borderColor: 'rgba(96,165,250,0.32)',
            color: 'var(--text)',
            background: 'rgba(15,23,42,0.6)',
          }}
        >
          {stamp}
        </span>
      </div>
    </aside>
  );
}

export default ProofStrip;
