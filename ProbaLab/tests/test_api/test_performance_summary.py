from __future__ import annotations

from fastapi.testclient import TestClient


def test_performance_summary_returns_frontend_contract(client: TestClient):
    res = client.get("/api/performance/summary", params={"window": 30})
    assert res.status_code == 200, res.text

    body = res.json()
    assert set(body) == {"roi30d", "accuracy", "brier7d", "bankroll"}

    for key in ("roi30d", "accuracy", "brier7d"):
        assert set(body[key]) == {"value", "deltaVs7d"}
        assert isinstance(body[key]["value"], int | float)
        assert isinstance(body[key]["deltaVs7d"], int | float)

    assert set(body["bankroll"]) == {"value", "currency"}
    assert isinstance(body["bankroll"]["value"], int | float)
    assert body["bankroll"]["currency"] == "EUR"


def test_performance_summary_accepts_only_supported_windows(client: TestClient):
    for window in (7, 30, 90):
        res = client.get("/api/performance/summary", params={"window": window})
        assert res.status_code == 200, f"window={window}: {res.text}"

    res = client.get("/api/performance/summary", params={"window": 500})
    assert res.status_code == 422
