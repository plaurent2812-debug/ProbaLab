"""
Tests pour les endpoints /api/trigger/clv/* (H2-SS1 Trigger.dev integration).

Pattern : TestClient FastAPI + monkeypatch des fonctions H2-SS1 pour éviter
tout appel DB / réseau réel.
"""

from __future__ import annotations

import os

# ── Env vars requis AVANT toute import projet ───────────────────
os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
os.environ.setdefault("SUPABASE_KEY", "test-key")
os.environ.setdefault("CRON_SECRET", "test-cron-secret")
os.environ.setdefault("ALLOWED_ORIGINS", "http://localhost:5173")

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    from api.main import app

    return TestClient(app)


@pytest.fixture
def auth_headers():
    return {"Authorization": "Bearer test-cron-secret"}


# ═══════════════════════════════════════════════════════════════
#  /api/trigger/clv/opening
# ═══════════════════════════════════════════════════════════════


def test_clv_opening_requires_auth(client):
    """Endpoint sans header → 401."""
    resp = client.post("/api/trigger/clv/opening", json={})
    assert resp.status_code == 401


def test_clv_opening_rejects_bad_token(client):
    """Token incorrect → 403."""
    resp = client.post(
        "/api/trigger/clv/opening",
        headers={"Authorization": "Bearer WRONG"},
        json={},
    )
    assert resp.status_code == 403


def test_clv_opening_calls_run_snapshot(client, auth_headers, monkeypatch):
    """Happy path : appelle run_snapshot(snapshot_type='opening') et
    retourne rows_submitted + duration_ms."""
    from src.fetchers import odds_ingestor

    called_with: dict = {}

    def fake_run(*, snapshot_type: str) -> int:
        called_with["snapshot_type"] = snapshot_type
        return 42

    monkeypatch.setattr(odds_ingestor, "run_snapshot", fake_run)

    resp = client.post("/api/trigger/clv/opening", headers=auth_headers, json={})
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["rows_submitted"] == 42
    assert called_with["snapshot_type"] == "opening"
    assert isinstance(body["duration_ms"], int)
    assert body["duration_ms"] >= 0


# ═══════════════════════════════════════════════════════════════
#  /api/trigger/clv/daily-snapshot
# ═══════════════════════════════════════════════════════════════


def test_clv_daily_snapshot_requires_auth(client):
    resp = client.post("/api/trigger/clv/daily-snapshot", json={})
    assert resp.status_code == 401


def test_clv_daily_snapshot_returns_payload(client, auth_headers, monkeypatch):
    """Happy path : appelle run_daily_clv_snapshot() et renvoie le résultat
    encapsulé sous 'payload'."""
    from src.monitoring import clv_engine

    fake_payload = {
        "sport": "football",
        "n_matches_clv": 12,
        "clv_vs_pinnacle_1x2": 0.018,
        "variant_id": "baseline",
    }

    def fake_run_daily() -> dict:
        return fake_payload

    monkeypatch.setattr(clv_engine, "run_daily_clv_snapshot", fake_run_daily)

    resp = client.post("/api/trigger/clv/daily-snapshot", headers=auth_headers, json={})
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["payload"] == fake_payload


def test_clv_daily_snapshot_500_on_exception(client, auth_headers, monkeypatch):
    """Si run_daily_clv_snapshot lève, renvoyer 500."""
    from src.monitoring import clv_engine

    def fake_run_daily() -> dict:
        raise RuntimeError("boom")

    monkeypatch.setattr(clv_engine, "run_daily_clv_snapshot", fake_run_daily)

    resp = client.post("/api/trigger/clv/daily-snapshot", headers=auth_headers, json={})
    assert resp.status_code == 500


# ═══════════════════════════════════════════════════════════════
#  /api/trigger/clv/drift
# ═══════════════════════════════════════════════════════════════


def test_clv_drift_requires_auth(client):
    resp = client.post("/api/trigger/clv/drift", json={})
    assert resp.status_code == 401


def test_clv_drift_no_alert_below_threshold(client, auth_headers, monkeypatch):
    """Si drift_result_to_alert renvoie None, send_telegram ne doit pas être appelé."""
    from src.monitoring import feature_drift

    def fake_run(*, alpha: float, window_days: int) -> dict:
        return {"n_drifted": 2, "n_features": 43, "per_feature": {}}

    monkeypatch.setattr(feature_drift, "run_feature_drift_check", fake_run)
    monkeypatch.setattr(feature_drift, "drift_result_to_alert", lambda _r, **_kw: None)

    telegram_calls: list[str] = []
    import api.routers.trigger as trigger_module

    def fake_send(msg: str) -> bool:
        telegram_calls.append(msg)
        return True

    monkeypatch.setattr(trigger_module, "send_telegram", fake_send, raising=False)

    resp = client.post("/api/trigger/clv/drift", headers=auth_headers, json={})
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["n_drifted"] == 2
    assert body["alert_sent"] is False
    assert telegram_calls == []


def test_clv_drift_sends_telegram_when_threshold_exceeded(client, auth_headers, monkeypatch):
    """Si drift_result_to_alert renvoie un message, send_telegram doit être appelé 1 fois."""
    from src.monitoring import feature_drift

    def fake_run(*, alpha: float, window_days: int) -> dict:
        return {"n_drifted": 7, "n_features": 43, "per_feature": {}}

    monkeypatch.setattr(feature_drift, "run_feature_drift_check", fake_run)
    monkeypatch.setattr(
        feature_drift,
        "drift_result_to_alert",
        lambda _r, **_kw: "\u26a0 drift alert",
    )

    telegram_calls: list[str] = []
    import api.routers.trigger as trigger_module

    def fake_send(msg: str) -> bool:
        telegram_calls.append(msg)
        return True

    monkeypatch.setattr(trigger_module, "send_telegram", fake_send, raising=False)

    resp = client.post("/api/trigger/clv/drift", headers=auth_headers, json={})
    assert resp.status_code == 200
    body = resp.json()
    assert body["n_drifted"] == 7
    assert body["alert_sent"] is True
    assert len(telegram_calls) == 1
