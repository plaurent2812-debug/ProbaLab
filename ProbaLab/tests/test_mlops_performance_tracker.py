from datetime import datetime, timezone
from types import SimpleNamespace

from pytest import approx

from src.mlops.performance_tracker import (
    build_performance_snapshot_from_rows,
    compute_market_metrics,
    persist_daily_performance_snapshots,
)


class FakeSupabaseQuery:
    def __init__(self, client, table_name: str):
        self.client = client
        self.table_name = table_name
        self.insert_payload = None

    @property
    def not_(self):
        return self

    def select(self, *_args, **_kwargs):
        return self

    def is_(self, *_args, **_kwargs):
        return self

    def gte(self, *_args, **_kwargs):
        return self

    def eq(self, *_args, **_kwargs):
        return self

    def insert(self, payload):
        self.insert_payload = payload
        return self

    def execute(self):
        if self.insert_payload is not None:
            self.client.inserted.setdefault(self.table_name, []).extend(self.insert_payload)
            return SimpleNamespace(data=self.insert_payload)
        return SimpleNamespace(data=self.client.rows_by_table.get(self.table_name, []))


class FakeSupabase:
    def __init__(self, rows_by_table: dict[str, list[dict]]):
        self.rows_by_table = rows_by_table
        self.inserted: dict[str, list[dict]] = {}

    def table(self, table_name: str):
        return FakeSupabaseQuery(self, table_name)


def test_compute_1x2_metrics_from_prediction_results_rows():
    rows = [
        {
            "pred_home": 60,
            "pred_draw": 25,
            "pred_away": 15,
            "actual_result": "H",
            "stake": 10,
            "profit": 8,
            "clv_pct": 0.03,
        },
        {
            "pred_home": 40,
            "pred_draw": 30,
            "pred_away": 30,
            "actual_result": "A",
            "stake": 10,
            "profit": -10,
            "clv_pct": -0.01,
        },
        {
            "pred_home": 20,
            "pred_draw": 30,
            "pred_away": 50,
            "actual_result": "A",
            "stake": 10,
            "profit": 9,
            "clv_pct": 0.02,
        },
    ]

    metrics = compute_market_metrics(rows, market="1x2")

    assert metrics["sample_size"] == 3
    assert metrics["accuracy"] == approx(2 / 3)
    assert metrics["brier"] == approx(0.151667, abs=1e-6)
    assert metrics["log_loss"] == approx(0.802649, abs=1e-6)
    assert metrics["roi"] == approx(23.333333, abs=1e-6)
    assert metrics["clv_mean"] == approx(0.013333, abs=1e-6)


def test_ece_requires_enough_samples():
    rows = [
        {"pred_home": 60, "pred_draw": 25, "pred_away": 15, "actual_result": "H"},
        {"pred_home": 20, "pred_draw": 30, "pred_away": 50, "actual_result": "A"},
    ]

    metrics = compute_market_metrics(rows, market="1x2")

    assert metrics["sample_size"] == 2
    assert metrics["ece"] is None


def test_compute_binary_metrics_for_btts():
    rows = [
        {"pred_btts": 70, "actual_btts": True},
        {"pred_btts": 40, "actual_btts": False},
        {"pred_btts": 55, "actual_btts": False},
    ]

    metrics = compute_market_metrics(rows, market="btts")

    assert metrics["sample_size"] == 3
    assert metrics["accuracy"] == approx(2 / 3)
    assert metrics["brier"] == approx(0.184167, abs=1e-6)
    assert metrics["log_loss"] == approx(0.555336, abs=1e-6)


def test_empty_metrics_are_explicit():
    metrics = compute_market_metrics([], market="1x2")

    assert metrics == {
        "sample_size": 0,
        "accuracy": None,
        "brier": None,
        "log_loss": None,
        "ece": None,
        "roi": None,
        "clv_mean": None,
        "clv_positive_pct": None,
        "fallback_rate": None,
    }


def test_build_performance_snapshot_from_rows_includes_identity_and_metrics():
    rows = [
        {"pred_home": 60, "pred_draw": 25, "pred_away": 15, "actual_result": "H"},
        {"pred_home": 20, "pred_draw": 30, "pred_away": 50, "actual_result": "A"},
    ]

    snapshot = build_performance_snapshot_from_rows(
        rows,
        sport="football",
        market="1x2",
        model_name="xgb_1x2",
        model_version="xgb_1x2_v1",
        window_days=7,
    )

    assert snapshot["sport"] == "football"
    assert snapshot["market"] == "1x2"
    assert snapshot["model_name"] == "xgb_1x2"
    assert snapshot["model_version"] == "xgb_1x2_v1"
    assert snapshot["window_days"] == 7
    assert snapshot["sample_size"] == 2
    assert snapshot["brier"] == approx(0.104167, abs=1e-6)
    assert snapshot["metrics"]["accuracy"] == 1.0


def test_persist_daily_performance_snapshots_inserts_computed_rows():
    fake_supabase = FakeSupabase(
        {
            "prediction_results": [
                {"pred_home": 60, "pred_draw": 25, "pred_away": 15, "actual_result": "H"},
                {"pred_home": 20, "pred_draw": 30, "pred_away": 50, "actual_result": "A"},
            ]
        }
    )

    result = persist_daily_performance_snapshots(
        supabase_client=fake_supabase,
        windows=[7],
        now=datetime(2026, 4, 26, tzinfo=timezone.utc),
        trackers=[
            {
                "sport": "football",
                "market": "1x2",
                "model_name": "xgb_1x2",
                "model_version": "xgb_1x2_v1",
            }
        ],
    )

    inserted = fake_supabase.inserted["model_performance_snapshots"]
    assert result == {
        "inserted": 1,
        "windows": [7],
        "markets": [{"sport": "football", "market": "1x2", "sample_size": 2}],
    }
    assert inserted[0]["model_name"] == "xgb_1x2"
    assert inserted[0]["window_days"] == 7
    assert inserted[0]["sample_size"] == 2
    assert inserted[0]["accuracy"] == 1.0
