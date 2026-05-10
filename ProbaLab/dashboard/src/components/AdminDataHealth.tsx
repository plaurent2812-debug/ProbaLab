import { useEffect, useState } from 'react';
import { supabase } from '@/lib/auth';
import { API_ROOT } from '@/lib/api';

interface ProviderFailure {
  id: number;
  recorded_at: string;
  provider: string;
  sport: string | null;
  endpoint: string;
  status_code: number | null;
  row_count: number | null;
  is_success: boolean;
  error?: string | null;
}

interface DataHealthResponse {
  generated_at: string;
  window_hours: number;
  provider_failures: ProviderFailure[];
  summary: {
    total_failures: number;
    by_provider: Record<string, { failure_count: number }>;
  };
}

interface Props {
  windowHours?: number;
}

export default function AdminDataHealth({ windowHours = 24 }: Props) {
  const [data, setData] = useState<DataHealthResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setLoading(true);
      setError(null);
      try {
        const session = await supabase.auth.getSession();
        const token = session.data?.session?.access_token;
        const res = await fetch(
          `${API_ROOT}/api/admin/data-health?window_hours=${windowHours}`,
          {
            headers: token ? { Authorization: `Bearer ${token}` } : {},
          },
        );
        if (!res.ok) {
          throw new Error(`HTTP ${res.status}`);
        }
        const body = (await res.json()) as DataHealthResponse;
        if (!cancelled) {
          setData(body);
        }
      } catch (e) {
        if (!cancelled) {
          setError(e instanceof Error ? e.message : 'unknown');
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, [windowHours]);

  if (loading && !data) {
    return (
      <section className="p-4">
        <p className="text-sm text-muted-foreground">Chargement…</p>
      </section>
    );
  }

  if (error && !data) {
    return (
      <section className="p-4 rounded-xl border border-amber-500/30 bg-amber-500/5">
        <h2 className="text-lg font-bold mb-2">Data Health</h2>
        <p className="text-sm">Données indisponibles ({error}).</p>
      </section>
    );
  }

  const providerEntries = Object.entries(data?.summary.by_provider ?? {});

  return (
    <section className="space-y-4">
      <header>
        <h2 className="text-lg font-bold tracking-tight">Data Health</h2>
        <p className="text-xs text-muted-foreground mt-1">
          Fenêtre : {data?.window_hours ?? windowHours} h · généré{' '}
          {data?.generated_at
            ? new Date(data.generated_at).toLocaleString('fr-FR', { timeZone: 'UTC' })
            : '—'}{' '}
          UTC
        </p>
      </header>

      <div className="grid grid-cols-2 gap-3 md:grid-cols-3">
        <div className="rounded-lg border border-border/40 bg-card p-3">
          <p className="text-xs uppercase tracking-wide text-muted-foreground">
            Total échecs
          </p>
          <p
            className="text-2xl font-black tabular-nums"
            data-testid="data-health-total-failures"
          >
            {data?.summary.total_failures ?? 0}
          </p>
        </div>
      </div>

      <div>
        <h3 className="text-sm font-bold mb-2">Échecs par provider</h3>
        {providerEntries.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            Aucun échec sur la fenêtre courante — tous les providers répondent.
          </p>
        ) : (
          <ul className="space-y-1 text-sm">
            {providerEntries.map(([provider, agg]) => (
              <li
                key={provider}
                className="flex items-center justify-between rounded-md border border-border/30 px-3 py-2"
              >
                <span className="font-mono">{provider}</span>
                <span className="font-bold tabular-nums">{agg.failure_count}</span>
              </li>
            ))}
          </ul>
        )}
      </div>

      {data?.provider_failures && data.provider_failures.length > 0 && (
        <div>
          <h3 className="text-sm font-bold mb-2">Détail des dernières erreurs</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead className="text-muted-foreground">
                <tr>
                  <th className="text-left p-2">Horodatage UTC</th>
                  <th className="text-left p-2">Provider</th>
                  <th className="text-left p-2">Sport</th>
                  <th className="text-left p-2">Endpoint</th>
                  <th className="text-left p-2">Status</th>
                  <th className="text-left p-2">Erreur</th>
                </tr>
              </thead>
              <tbody>
                {data.provider_failures.slice(0, 50).map((f) => (
                  <tr key={f.id} className="border-t border-border/30">
                    <td className="p-2 tabular-nums">{f.recorded_at}</td>
                    <td className="p-2 font-mono">{f.provider}</td>
                    <td className="p-2">{f.sport ?? '—'}</td>
                    <td className="p-2 font-mono truncate max-w-xs">{f.endpoint}</td>
                    <td className="p-2 tabular-nums">{f.status_code ?? '—'}</td>
                    <td className="p-2">{f.error ?? '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </section>
  );
}
