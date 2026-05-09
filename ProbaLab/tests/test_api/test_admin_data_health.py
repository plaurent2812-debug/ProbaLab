"""Contract test for GET /api/admin/data-health.

Master plan Phase 2.4 : the admin must be able to tell, in 30 seconds, if
football or NHL data is healthy. The endpoint must:

- be auth-gated by ``verify_internal_auth`` (CRON_SECRET or admin JWT);
- return a stable shape so the future admin UI can pin its types;
- never crash when ``provider_health_log`` is unreachable — degrade to zeros.

The shape is fixed and small on purpose. We will extend it as the data
platform matures (fixtures today by sport, predictions today, odds coverage,
unresolved finished fixtures) — each addition gets its own test.
"""

from __future__ import annotations

from unittest.mock import patch

from fastapi.testclient import TestClient


def test_data_health_requires_auth(client: TestClient):
    res = client.get("/api/admin/data-health")
    assert res.status_code == 401


def test_data_health_with_cron_secret_returns_expected_shape(client: TestClient, auth_headers):
    """With a valid CRON_SECRET, the endpoint must return the contract shape."""
    fake_failures = [
        {
            "id": 1,
            "recorded_at": "2026-05-09T07:30:00+00:00",
            "provider": "api_football",
            "sport": "football",
            "endpoint": "/fixtures",
            "status_code": 500,
            "row_count": 0,
            "latency_ms": 320,
            "error": "internal",
            "is_success": False,
        }
    ]

    with patch(
        "api.routers.admin.recent_provider_failures",
        return_value=fake_failures,
    ):
        res = client.get("/api/admin/data-health", headers=auth_headers)

    assert res.status_code == 200, res.text
    body = res.json()

    # Top-level shape.
    assert set(body.keys()) == {
        "generated_at",
        "window_hours",
        "provider_failures",
        "summary",
    }

    # Provider failures forwarded as-is.
    assert body["provider_failures"] == fake_failures

    # Summary aggregates per provider.
    summary = body["summary"]
    assert "by_provider" in summary
    assert summary["by_provider"]["api_football"]["failure_count"] == 1
    assert summary["total_failures"] == 1


def test_data_health_returns_zero_summary_when_log_table_missing(client: TestClient, auth_headers):
    """If ``provider_health_log`` is unreachable, recent_provider_failures
    returns []. The endpoint must still return 200 with zeros, never 500."""
    with patch("api.routers.admin.recent_provider_failures", return_value=[]):
        res = client.get("/api/admin/data-health", headers=auth_headers)

    assert res.status_code == 200, res.text
    body = res.json()
    assert body["provider_failures"] == []
    assert body["summary"]["total_failures"] == 0
    assert body["summary"]["by_provider"] == {}


def test_data_health_accepts_window_hours_query_param(client: TestClient, auth_headers):
    with patch("api.routers.admin.recent_provider_failures", return_value=[]) as spy:
        res = client.get(
            "/api/admin/data-health",
            params={"window_hours": 6},
            headers=auth_headers,
        )

    assert res.status_code == 200, res.text
    body = res.json()
    assert body["window_hours"] == 6
    spy.assert_called_once()
    # The helper was called with the requested window.
    _, kwargs = spy.call_args
    assert kwargs.get("hours") == 6


def test_data_health_clamps_invalid_window_hours(client: TestClient, auth_headers):
    """Window hours must stay in [1, 168]. Anything outside is rejected by Pydantic."""
    res = client.get(
        "/api/admin/data-health",
        params={"window_hours": 999},
        headers=auth_headers,
    )
    assert res.status_code == 422
