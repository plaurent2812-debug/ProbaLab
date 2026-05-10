"""Daily health snapshot writer.

Master plan Phase 3 : orchestrateur quotidien qui consolide les sorties
de ``brier_monitor`` + ``provider_health.recent_failures`` et insère UNE
row dans ``model_health_log`` par sport.

Pas de recalcul de CLV : ``clv_engine.run_daily_clv_snapshot`` écrit déjà
ses propres colonnes (clv_vs_pinnacle_*, clv_vs_fr_avg_*) — les deux
écritures sont indépendantes et compatibles dans le même cron.

Design :

- ``_run_brier_monitor`` : indirection patch-friendly pour les tests.
- ``_count_recent_failures`` : agrège ``provider_health.recent_failures``
  (24h, tous providers confondus côté football) en un compteur entier.
- ``_count_predictions_today`` : SELECT count(*) sur la table predictions
  pour la date du jour UTC. Pour le sport NHL, on changera la table dans
  une PR ultérieure.
- ``run_daily_snapshot`` : entrypoint. Insère une row par sport, retourne
  un dict ``{status, rows_inserted, sports}`` sans jamais lever.

Cron : à brancher dans ``api/routers/trigger.py`` ou via une route admin
``POST /api/admin/run-daily-health`` (gated CRON_SECRET). Pas dans cette PR
pour limiter le blast radius — le module est testable et invocable
manuellement via ``python -m src.monitoring.daily_health_snapshot``.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)

_TABLE = "model_health_log"


# ── Indirection helpers (patchable in tests) ─────────────────────────────


def _run_brier_monitor() -> dict[str, Any]:
    """Wrap ``brier_monitor.run`` so tests can patch this thin layer."""
    from src.monitoring.brier_monitor import run

    return run()


def _resolve_client(client: Any) -> Any:
    if client is not None:
        return client
    from src.config import supabase  # noqa: PLC0415

    return supabase


def _count_recent_failures(*, sport: str = "football", hours: int = 24, client: Any = None) -> int:
    """Count provider_health rows where is_success=false in the last ``hours``.

    Used to derive ``data_completeness_pct`` and ``alert_count``. Reads
    swallow Supabase errors and return 0 to avoid breaking the snapshot.
    """
    from src.monitoring.provider_health import recent_failures

    try:
        rows = recent_failures(hours=hours, client=client)
    except Exception:
        logger.warning("daily_health: recent_failures read failed", exc_info=True)
        return 0
    # Filter by sport when the column is set (None means meta-call, count anyway).
    return sum(1 for r in rows if (r.get("sport") in (sport, None)))


def _count_predictions_today(*, sport: str = "football", client: Any = None) -> int:
    """SELECT count(*) for today's predictions. Football table for now."""
    try:
        target = _resolve_client(client)
        today_iso = datetime.now(timezone.utc).date().isoformat()
        result = (
            target.table("predictions" if sport == "football" else "nhl_predictions")
            .select("id", count="exact")
            .gte("created_at", f"{today_iso}T00:00:00Z")
            .lt("created_at", f"{today_iso}T23:59:59Z")
            .execute()
        )
        return int(result.count or 0) if hasattr(result, "count") else len(result.data or [])
    except Exception:
        logger.warning("daily_health: predictions count failed", exc_info=True)
        return 0


# ── Row builders ─────────────────────────────────────────────────────────


def _build_football_row(brier: dict[str, Any], failures: int, volume: int) -> dict[str, Any]:
    """Map brier_monitor.run() output to a model_health_log row.

    Columns set:
      sport, recorded_at, brier_7d, log_loss_30d, ece_30d,
      drift_detected, data_completeness_pct, prediction_volume_today,
      alert_count, notes.

    Unset (left None): brier_30d, clv_best_mean_30d, ml_fallback_rate.
    They are owned by other writers (clv_engine) or future fills.
    """
    if brier.get("status") == "NO_DATA":
        return {
            "sport": "football",
            "recorded_at": datetime.now(timezone.utc).isoformat(),
            "brier_7d": None,
            "log_loss_30d": None,
            "ece_30d": None,
            "drift_detected": False,
            "data_completeness_pct": max(0.0, 100.0 - 10.0 * failures),
            "prediction_volume_today": volume,
            "alert_count": failures,
            "notes": "no data: no evaluated predictions in window",
        }

    brier_1x2 = brier.get("brier_1x2") or {}
    log_loss = brier.get("log_loss_1x2") or {}
    ece = brier.get("ece") or {}
    drift = brier.get("drift") or {}

    return {
        "sport": "football",
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "brier_7d": brier_1x2.get("brier"),
        "log_loss_30d": log_loss.get("log_loss"),
        "ece_30d": ece.get("ece"),
        "drift_detected": bool(drift.get("drift_detected", False)),
        "data_completeness_pct": max(0.0, 100.0 - 10.0 * failures),
        "prediction_volume_today": volume,
        "alert_count": failures,
        "notes": None,
    }


# ── Public entrypoint ────────────────────────────────────────────────────


def run_daily_snapshot(*, client: Any = None) -> dict[str, Any]:
    """Compute today's health row and insert into ``model_health_log``.

    Returns a status dict; never raises. The caller (cron / admin route)
    can alert on ``status='ERROR'`` if needed.
    """
    try:
        brier = _run_brier_monitor()
    except Exception:
        logger.warning("daily_health: brier_monitor failed", exc_info=True)
        brier = {"status": "NO_DATA"}

    failures = _count_recent_failures(sport="football", client=client)
    volume = _count_predictions_today(sport="football", client=client)

    row = _build_football_row(brier, failures, volume)

    try:
        target = _resolve_client(client)
        target.table(_TABLE).insert(row).execute()
        return {
            "status": "OK",
            "rows_inserted": 1,
            "sports": ["football"],
            "row": row,
        }
    except Exception:
        logger.warning("daily_health: insert failed", exc_info=True)
        return {
            "status": "ERROR",
            "rows_inserted": 0,
            "sports": [],
            "row": row,
        }


if __name__ == "__main__":  # pragma: no cover - manual invocation
    logging.basicConfig(level=logging.INFO)
    out = run_daily_snapshot()
    print(out)
