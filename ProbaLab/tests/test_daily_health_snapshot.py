"""Tests : pipeline de snapshot quotidien dans model_health_log.

Master plan Phase 3 : orchestrateur qui agrège les sorties de
- brier_monitor.run() : Brier 1X2 / log_loss / ECE / drift / health_score
- provider_health.recent_failures() : data completeness, ml_fallback_rate

et insère UNE row par sport dans model_health_log par jour.

Le module clv_engine.run_daily_clv_snapshot() écrit déjà ses propres
colonnes CLV — l'orchestrateur ne les recalcule PAS. Les deux écritures
sont indépendantes et peuvent tourner dans le même cron sans conflit.

Conventions row insérée (colonnes existantes dans model_health_log
après migration 050) :
  sport, recorded_at, brier_7d, brier_30d, log_loss_30d, ece_30d,
  drift_detected, data_completeness_pct, prediction_volume_today,
  alert_count, ml_fallback_rate, notes
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch


def _brier_run_result(
    *,
    n: int = 100,
    brier: float | None = 0.19,
    ece: float | None = 0.04,
    drift: bool = False,
    health: int = 8,
) -> dict:
    return {
        "status": "OK",
        "n_matches": n,
        "brier_1x2": {"brier": brier, "n": n, "grade": "GOOD"},
        "log_loss_1x2": {"log_loss": 0.85, "n": n},
        "ece": {"ece": ece, "grade": "GOOD"},
        "binary_markets": {},
        "drift": {"drift_detected": drift, "delta": 0.005, "threshold": 0.03},
        "health_score": health,
    }


def test_snapshot_inserts_one_row_per_sport_with_required_columns():
    """L'orchestrateur insère 1 row par sport ('football' au minimum) avec
    les colonnes attendues par migration 050."""
    from src.monitoring import daily_health_snapshot as dhs

    mock_supabase = MagicMock()
    chain = MagicMock()
    mock_supabase.table.return_value = chain
    chain.insert.return_value = chain
    chain.execute.return_value = MagicMock(data=[{"id": 1}])

    with (
        patch.object(dhs, "_run_brier_monitor", return_value=_brier_run_result()),
        patch.object(dhs, "_count_recent_failures", return_value=0),
        patch.object(dhs, "_count_predictions_today", return_value=42),
    ):
        result = dhs.run_daily_snapshot(client=mock_supabase)

    assert result["status"] == "OK"
    assert result["rows_inserted"] == 1
    assert mock_supabase.table.call_count == 1
    assert mock_supabase.table.call_args_list[0][0][0] == "model_health_log"
    chain.insert.assert_called_once()
    row = chain.insert.call_args[0][0]
    assert row["sport"] == "football"
    assert row["brier_7d"] == 0.19
    assert row["log_loss_30d"] == 0.85
    assert row["ece_30d"] == 0.04
    assert row["drift_detected"] is False
    assert row["prediction_volume_today"] == 42
    assert row["alert_count"] == 0
    assert "recorded_at" in row


def test_snapshot_marks_drift_when_brier_run_reports_drift():
    from src.monitoring import daily_health_snapshot as dhs

    mock_supabase = MagicMock()
    chain = MagicMock()
    mock_supabase.table.return_value = chain
    chain.insert.return_value = chain
    chain.execute.return_value = MagicMock(data=[{"id": 1}])

    drift_result = _brier_run_result(drift=True, health=6)
    with (
        patch.object(dhs, "_run_brier_monitor", return_value=drift_result),
        patch.object(dhs, "_count_recent_failures", return_value=2),
        patch.object(dhs, "_count_predictions_today", return_value=42),
    ):
        dhs.run_daily_snapshot(client=mock_supabase)

    row = chain.insert.call_args[0][0]
    assert row["drift_detected"] is True
    assert row["alert_count"] == 2


def test_snapshot_handles_no_data_status_gracefully():
    """Si brier_monitor renvoie NO_DATA, on insère quand même une row avec
    les colonnes Brier à None et un note explicite."""
    from src.monitoring import daily_health_snapshot as dhs

    mock_supabase = MagicMock()
    chain = MagicMock()
    mock_supabase.table.return_value = chain
    chain.insert.return_value = chain
    chain.execute.return_value = MagicMock(data=[{"id": 1}])

    with (
        patch.object(dhs, "_run_brier_monitor", return_value={"status": "NO_DATA"}),
        patch.object(dhs, "_count_recent_failures", return_value=0),
        patch.object(dhs, "_count_predictions_today", return_value=0),
    ):
        result = dhs.run_daily_snapshot(client=mock_supabase)

    assert result["status"] == "OK"
    row = chain.insert.call_args[0][0]
    assert row["brier_7d"] is None
    assert row["log_loss_30d"] is None
    assert row["ece_30d"] is None
    assert row["prediction_volume_today"] == 0
    # Note explicite.
    assert "no" in (row.get("notes") or "").lower() or "data" in (row.get("notes") or "").lower()


def test_snapshot_returns_error_status_when_insert_fails_but_does_not_raise():
    """Un échec d'écriture Supabase ne doit pas casser le cron. Le caller
    récupère un status='ERROR' pour pouvoir alerter."""
    from src.monitoring import daily_health_snapshot as dhs

    mock_supabase = MagicMock()
    mock_supabase.table.side_effect = RuntimeError("supabase down")

    with (
        patch.object(dhs, "_run_brier_monitor", return_value=_brier_run_result()),
        patch.object(dhs, "_count_recent_failures", return_value=0),
        patch.object(dhs, "_count_predictions_today", return_value=10),
    ):
        result = dhs.run_daily_snapshot(client=mock_supabase)

    assert result["status"] == "ERROR"
    assert result["rows_inserted"] == 0


def test_snapshot_records_data_completeness_from_failures_count():
    """data_completeness_pct = max(0, 100 - 10 * recent_failures)."""
    from src.monitoring import daily_health_snapshot as dhs

    mock_supabase = MagicMock()
    chain = MagicMock()
    mock_supabase.table.return_value = chain
    chain.insert.return_value = chain
    chain.execute.return_value = MagicMock(data=[{"id": 1}])

    with (
        patch.object(dhs, "_run_brier_monitor", return_value=_brier_run_result()),
        patch.object(dhs, "_count_recent_failures", return_value=3),
        patch.object(dhs, "_count_predictions_today", return_value=42),
    ):
        dhs.run_daily_snapshot(client=mock_supabase)

    row = chain.insert.call_args[0][0]
    assert row["data_completeness_pct"] == 70.0  # 100 - 10*3


def test_snapshot_data_completeness_clamped_to_zero():
    from src.monitoring import daily_health_snapshot as dhs

    mock_supabase = MagicMock()
    chain = MagicMock()
    mock_supabase.table.return_value = chain
    chain.insert.return_value = chain
    chain.execute.return_value = MagicMock(data=[{"id": 1}])

    with (
        patch.object(dhs, "_run_brier_monitor", return_value=_brier_run_result()),
        patch.object(dhs, "_count_recent_failures", return_value=20),
        patch.object(dhs, "_count_predictions_today", return_value=42),
    ):
        dhs.run_daily_snapshot(client=mock_supabase)

    row = chain.insert.call_args[0][0]
    assert row["data_completeness_pct"] == 0.0
