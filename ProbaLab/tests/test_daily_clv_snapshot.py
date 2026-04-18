"""Tests end-to-end pour le daily CLV snapshot cron job."""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from unittest.mock import MagicMock


def test_run_daily_clv_snapshot_upserts_model_health_log(monkeypatch):
    from src.monitoring import clv_engine

    target = (datetime.now(timezone.utc) - timedelta(days=1)).date()

    # Fake predictions on 2 matches with closing Pinnacle + Betclic
    predictions = [
        {"fixture_id": "fx1", "sport": "football", "league_id": 61,
         "pred_home": 60.0, "pred_draw": 25.0, "pred_away": 15.0,
         "actual_result": "H"},
        {"fixture_id": "fx2", "sport": "football", "league_id": 61,
         "pred_home": 30.0, "pred_draw": 30.0, "pred_away": 40.0,
         "actual_result": "A"},
    ]
    closing_rows = [
        {"fixture_id": "fx1", "bookmaker": "pinnacle", "market": "1x2",
         "selection": "home", "odds": 1.80, "line": None},
        {"fixture_id": "fx1", "bookmaker": "pinnacle", "market": "1x2",
         "selection": "draw", "odds": 3.60, "line": None},
        {"fixture_id": "fx1", "bookmaker": "pinnacle", "market": "1x2",
         "selection": "away", "odds": 4.80, "line": None},
        {"fixture_id": "fx2", "bookmaker": "pinnacle", "market": "1x2",
         "selection": "home", "odds": 3.00, "line": None},
        {"fixture_id": "fx2", "bookmaker": "pinnacle", "market": "1x2",
         "selection": "draw", "odds": 3.40, "line": None},
        {"fixture_id": "fx2", "bookmaker": "pinnacle", "market": "1x2",
         "selection": "away", "odds": 2.50, "line": None},
    ]

    monkeypatch.setattr(
        clv_engine, "_load_predictions_for_date", lambda d: predictions
    )
    monkeypatch.setattr(
        clv_engine, "_load_closing_odds_for_date", lambda d: closing_rows
    )

    upserted: list[dict] = []

    class _Exec:
        def __init__(self, store, row):
            self._store = store
            self._row = row
        def execute(self):
            self._store.append(self._row)
            return MagicMock(data=[self._row])

    class FakeSupabase:
        def table(self, name):
            assert name == "model_health_log"
            mock = MagicMock()
            mock.upsert = lambda row, on_conflict=None: _Exec(upserted, row)
            mock.insert = lambda row: _Exec(upserted, row)
            return mock

    monkeypatch.setattr(clv_engine, "supabase", FakeSupabase())

    out = clv_engine.run_daily_clv_snapshot(target_date=target)
    assert out["n_matches_clv"] > 0
    assert len(upserted) == 1
    row = upserted[0]
    assert row["sport"] == "football"
    assert row["variant_id"] is not None
    assert "clv_vs_pinnacle_1x2" in row


def test_run_daily_clv_snapshot_no_predictions_noop(monkeypatch):
    from src.monitoring import clv_engine

    monkeypatch.setattr(clv_engine, "_load_predictions_for_date", lambda d: [])
    monkeypatch.setattr(clv_engine, "_load_closing_odds_for_date", lambda d: [])

    called = []

    class FakeSupabase:
        def table(self, name):
            called.append(name)
            raise AssertionError("should not insert when no predictions")

    monkeypatch.setattr(clv_engine, "supabase", FakeSupabase())

    out = clv_engine.run_daily_clv_snapshot(target_date=date(2026, 4, 10))
    assert out["n_matches_clv"] == 0
    assert called == []
