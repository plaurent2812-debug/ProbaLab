"""
Tests pour les endpoints /api/trigger/clv/* (H2-SS1 Trigger.dev integration).

Pattern : TestClient FastAPI + monkeypatch des fonctions H2-SS1 pour éviter
tout appel DB / réseau réel.
"""

from __future__ import annotations

import os
from unittest.mock import MagicMock

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


# ═══════════════════════════════════════════════════════════════
#  /api/trigger/clv/closing-tick
# ═══════════════════════════════════════════════════════════════


def _make_closing_tick_supabase_mock(
    *,
    football_rows: list[dict] | None = None,
    nhl_rows: list[dict] | None = None,
    already_snapshotted: list[dict] | None = None,
) -> MagicMock:
    """Construit un faux client Supabase pour le endpoint closing-tick.

    Le endpoint fait 3 requêtes :
      1. fixtures.select('id').gte('date', …).lt('date', …).execute()
      2. nhl_fixtures.select('game_id').gte('game_date', …).lt('game_date', …).execute()
      3. closing_odds.select('fixture_id').in_('fixture_id', …).eq('snapshot_type','closing').execute()
    """
    mock = MagicMock()

    def table_side_effect(name: str):
        chain = MagicMock()
        exec_res = MagicMock()
        if name == "fixtures":
            exec_res.data = football_rows or []
        elif name == "nhl_fixtures":
            exec_res.data = nhl_rows or []
        elif name == "closing_odds":
            exec_res.data = already_snapshotted or []
        else:
            exec_res.data = []
        # Chaque appel (.select / .gte / .lt / .in_ / .eq) renvoie le chain lui-même
        for method in ("select", "gte", "lt", "in_", "eq"):
            getattr(chain, method).return_value = chain
        chain.execute.return_value = exec_res
        return chain

    mock.table.side_effect = table_side_effect
    return mock


def test_clv_closing_tick_requires_auth(client):
    resp = client.post("/api/trigger/clv/closing-tick", json={})
    assert resp.status_code == 401


def test_clv_closing_tick_no_fixtures_in_window(client, auth_headers, monkeypatch):
    """Fenêtre vide → 200 avec snapshots=0, run_snapshot_for_fixtures pas appelé."""
    import api.routers.trigger as trigger_module
    from src.fetchers import odds_ingestor

    fake_supa = _make_closing_tick_supabase_mock()
    monkeypatch.setattr(trigger_module, "supabase", fake_supa)

    called_with: list[list[str]] = []

    def fake_run_for(fixture_ids: list[str]) -> int:
        called_with.append(fixture_ids)
        return 0

    monkeypatch.setattr(odds_ingestor, "run_snapshot_for_fixtures", fake_run_for)

    resp = client.post("/api/trigger/clv/closing-tick", headers=auth_headers, json={})
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["snapshots"] == 0
    assert called_with == []


def test_clv_closing_tick_snapshots_new_fixtures(client, auth_headers, monkeypatch):
    """2 fixtures football + 1 NHL en fenêtre, aucun déjà snapshotté → run_snapshot_for_fixtures(3 ids)."""
    import api.routers.trigger as trigger_module
    from src.fetchers import odds_ingestor

    fake_supa = _make_closing_tick_supabase_mock(
        football_rows=[{"id": 111}, {"id": 222}],
        nhl_rows=[{"game_id": 2026020500}],
        already_snapshotted=[],
    )
    monkeypatch.setattr(trigger_module, "supabase", fake_supa)

    called_with: list[list[str]] = []

    def fake_run_for(fixture_ids: list[str]) -> int:
        called_with.append(list(fixture_ids))
        return 18

    monkeypatch.setattr(odds_ingestor, "run_snapshot_for_fixtures", fake_run_for)

    resp = client.post("/api/trigger/clv/closing-tick", headers=auth_headers, json={})
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["snapshots"] == 18
    assert body["fixture_count"] == 3
    assert len(called_with) == 1
    assert set(called_with[0]) == {"111", "222", "2026020500"}


def test_clv_closing_tick_skips_already_snapshotted(client, auth_headers, monkeypatch):
    """2 fixtures, 1 déjà snapshotté → run_snapshot_for_fixtures n'appelle QUE l'autre."""
    import api.routers.trigger as trigger_module
    from src.fetchers import odds_ingestor

    fake_supa = _make_closing_tick_supabase_mock(
        football_rows=[{"id": 111}, {"id": 222}],
        nhl_rows=[],
        already_snapshotted=[{"fixture_id": "111"}],
    )
    monkeypatch.setattr(trigger_module, "supabase", fake_supa)

    called_with: list[list[str]] = []

    def fake_run_for(fixture_ids: list[str]) -> int:
        called_with.append(list(fixture_ids))
        return 6

    monkeypatch.setattr(odds_ingestor, "run_snapshot_for_fixtures", fake_run_for)

    resp = client.post("/api/trigger/clv/closing-tick", headers=auth_headers, json={})
    assert resp.status_code == 200
    body = resp.json()
    assert body["snapshots"] == 6
    assert body["fixture_count"] == 1
    assert called_with == [["222"]]


def test_clv_closing_tick_all_already_done_short_circuits(client, auth_headers, monkeypatch):
    """Toutes les fixtures déjà snapshottées → run_snapshot_for_fixtures PAS appelé."""
    import api.routers.trigger as trigger_module
    from src.fetchers import odds_ingestor

    fake_supa = _make_closing_tick_supabase_mock(
        football_rows=[{"id": 111}],
        nhl_rows=[],
        already_snapshotted=[{"fixture_id": "111"}],
    )
    monkeypatch.setattr(trigger_module, "supabase", fake_supa)

    called_with: list[list[str]] = []

    def fake_run_for(fixture_ids: list[str]) -> int:
        called_with.append(list(fixture_ids))
        return 0

    monkeypatch.setattr(odds_ingestor, "run_snapshot_for_fixtures", fake_run_for)

    resp = client.post("/api/trigger/clv/closing-tick", headers=auth_headers, json={})
    assert resp.status_code == 200
    body = resp.json()
    assert body["snapshots"] == 0
    assert body["already_done"] == 1
    assert called_with == []


def test_clv_closing_tick_continues_on_football_error(client, auth_headers, monkeypatch):
    """I2 regression — if football query raises, NHL processing still happens."""
    import api.routers.trigger as trigger_module
    from src.fetchers import odds_ingestor

    fake_supa = MagicMock()

    def table_side_effect(name: str):
        chain = MagicMock()
        if name == "fixtures":
            # Football fails: execute() raises
            chain.select.return_value = chain
            chain.gte.return_value = chain
            chain.lt.return_value = chain
            chain.execute.side_effect = RuntimeError("supabase 500 football")
            return chain
        # NHL succeeds with 1 fixture; dedup returns empty
        exec_res = MagicMock()
        if name == "nhl_fixtures":
            exec_res.data = [{"game_id": 2026020500}]
        elif name == "closing_odds":
            exec_res.data = []
        else:
            exec_res.data = []
        for m in ("select", "gte", "lt", "in_", "eq"):
            getattr(chain, m).return_value = chain
        chain.execute.return_value = exec_res
        return chain

    fake_supa.table.side_effect = table_side_effect
    monkeypatch.setattr(trigger_module, "supabase", fake_supa)

    called_with: list[list[str]] = []

    def fake_run_for(fixture_ids: list[str]) -> int:
        called_with.append(list(fixture_ids))
        return 6

    monkeypatch.setattr(odds_ingestor, "run_snapshot_for_fixtures", fake_run_for)

    resp = client.post("/api/trigger/clv/closing-tick", headers=auth_headers, json={})
    assert resp.status_code == 200
    body = resp.json()
    # Only NHL fixture survived
    assert body["fixture_count"] == 1
    assert called_with == [["2026020500"]]


def test_clv_closing_tick_continues_on_nhl_error(client, auth_headers, monkeypatch):
    """I2 regression — if NHL query raises, football processing still happens."""
    import api.routers.trigger as trigger_module
    from src.fetchers import odds_ingestor

    fake_supa = MagicMock()

    def table_side_effect(name: str):
        chain = MagicMock()
        if name == "nhl_fixtures":
            chain.select.return_value = chain
            chain.gte.return_value = chain
            chain.lt.return_value = chain
            chain.execute.side_effect = RuntimeError("supabase 500 nhl")
            return chain
        exec_res = MagicMock()
        if name == "fixtures":
            exec_res.data = [{"id": 777}]
        elif name == "closing_odds":
            exec_res.data = []
        else:
            exec_res.data = []
        for m in ("select", "gte", "lt", "in_", "eq"):
            getattr(chain, m).return_value = chain
        chain.execute.return_value = exec_res
        return chain

    fake_supa.table.side_effect = table_side_effect
    monkeypatch.setattr(trigger_module, "supabase", fake_supa)

    called_with: list[list[str]] = []

    def fake_run_for(fixture_ids: list[str]) -> int:
        called_with.append(list(fixture_ids))
        return 5

    monkeypatch.setattr(odds_ingestor, "run_snapshot_for_fixtures", fake_run_for)

    resp = client.post("/api/trigger/clv/closing-tick", headers=auth_headers, json={})
    assert resp.status_code == 200
    body = resp.json()
    assert body["fixture_count"] == 1
    assert called_with == [["777"]]


def test_clv_closing_tick_proceeds_without_dedup_on_dedup_failure(
    client, auth_headers, monkeypatch
):
    """I2+I3 regression — if dedup query fails, full fixture list is snapshotted
    AND a Telegram alert is fired."""
    import api.routers.trigger as trigger_module
    from src.fetchers import odds_ingestor

    fake_supa = MagicMock()

    def table_side_effect(name: str):
        chain = MagicMock()
        if name == "closing_odds":
            # Dedup fails
            chain.select.return_value = chain
            chain.in_.return_value = chain
            chain.eq.return_value = chain
            chain.execute.side_effect = RuntimeError("supabase 500 dedup")
            return chain
        exec_res = MagicMock()
        if name == "fixtures":
            exec_res.data = [{"id": 100}, {"id": 200}]
        elif name == "nhl_fixtures":
            exec_res.data = []
        else:
            exec_res.data = []
        for m in ("select", "gte", "lt", "in_", "eq"):
            getattr(chain, m).return_value = chain
        chain.execute.return_value = exec_res
        return chain

    fake_supa.table.side_effect = table_side_effect
    monkeypatch.setattr(trigger_module, "supabase", fake_supa)

    called_with: list[list[str]] = []

    def fake_run_for(fixture_ids: list[str]) -> int:
        called_with.append(list(fixture_ids))
        return 12

    monkeypatch.setattr(odds_ingestor, "run_snapshot_for_fixtures", fake_run_for)

    telegram_calls: list[str] = []

    def fake_send(msg: str) -> bool:
        telegram_calls.append(msg)
        return True

    monkeypatch.setattr(trigger_module, "send_telegram", fake_send, raising=False)

    resp = client.post("/api/trigger/clv/closing-tick", headers=auth_headers, json={})
    assert resp.status_code == 200
    body = resp.json()
    # Dedup failed → full list (2) goes to run_snapshot_for_fixtures
    assert body["fixture_count"] == 2
    assert called_with == [["100", "200"]]
    # I3 : Telegram alert sent
    assert len(telegram_calls) == 1
    assert "dedup query failed" in telegram_calls[0]
