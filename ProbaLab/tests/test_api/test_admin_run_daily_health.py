"""Contract tests for POST /api/admin/run-daily-health.

Master plan Phase 3 (wiring) : expose ``daily_health_snapshot.run_daily_snapshot``
as an authenticated admin endpoint that a cron (Trigger.dev, APScheduler,
GitHub Actions schedule) can hit once a day.

Endpoint contract:
- POST /api/admin/run-daily-health
- Auth: verify_internal_auth (CRON_SECRET via Authorization: Bearer
  OR via X-Cron-Secret header, OR admin Supabase JWT).
- Response: {ok: bool, status: "OK"|"ERROR", rows_inserted: int, sports: list[str]}
- Never 500s: the underlying writer swallows its own errors and returns
  status="ERROR" rather than raising. The route just forwards.
"""

from __future__ import annotations

from unittest.mock import patch

from fastapi.testclient import TestClient


def test_run_daily_health_requires_auth(client: TestClient):
    res = client.post("/api/admin/run-daily-health")
    assert res.status_code == 401


def test_run_daily_health_with_cron_secret_forwards_writer_result(client: TestClient, auth_headers):
    """Happy path : auth OK, writer renvoie status='OK' avec une row insérée."""
    fake_result = {
        "status": "OK",
        "rows_inserted": 1,
        "sports": ["football"],
        "row": {"sport": "football"},
    }

    with patch(
        "api.routers.admin.run_daily_health_snapshot",
        return_value=fake_result,
    ) as spy:
        res = client.post("/api/admin/run-daily-health", headers=auth_headers)

    assert res.status_code == 200, res.text
    body = res.json()
    assert body["ok"] is True
    assert body["status"] == "OK"
    assert body["rows_inserted"] == 1
    assert body["sports"] == ["football"]
    spy.assert_called_once()


def test_run_daily_health_returns_503_when_writer_reports_error(client: TestClient, auth_headers):
    """Writer status='ERROR' (DB down) → on retourne 503 mais sans 500.

    FastAPI wraps HTTPException(detail=...) payloads under {"detail": ...},
    so we read the structured body from there.
    """
    err_result = {
        "status": "ERROR",
        "rows_inserted": 0,
        "sports": [],
        "row": {"sport": "football"},
    }

    with patch(
        "api.routers.admin.run_daily_health_snapshot",
        return_value=err_result,
    ):
        res = client.post("/api/admin/run-daily-health", headers=auth_headers)

    assert res.status_code == 503, res.text
    detail = res.json()["detail"]
    assert detail["ok"] is False
    assert detail["status"] == "ERROR"
    assert detail["rows_inserted"] == 0


def test_run_daily_health_never_500_even_if_writer_raises(client: TestClient, auth_headers):
    """Le writer ne devrait jamais raise — mais s'il le fait, on dégrade
    en 503 pour permettre au cron de retry, pas 500 qui pollue les logs."""
    with patch(
        "api.routers.admin.run_daily_health_snapshot",
        side_effect=RuntimeError("unexpected"),
    ):
        res = client.post("/api/admin/run-daily-health", headers=auth_headers)

    assert res.status_code == 503, res.text
    detail = res.json()["detail"]
    assert detail["ok"] is False
    assert detail["status"] == "ERROR"


def test_run_daily_health_rejects_bad_auth(client: TestClient, bad_auth_headers):
    res = client.post("/api/admin/run-daily-health", headers=bad_auth_headers)
    assert res.status_code in (401, 403)
