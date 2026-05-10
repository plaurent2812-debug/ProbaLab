"""Tests : instrumentation provider health pour API-Football.

Master plan Phase 2.3 bis : chaque appel à v3.football.api-sports.io doit
produire UNE ligne dans provider_health_log.

Modules instrumentés dans cette PR :
- src.fetchers.matches.get_fixtures_by_date
- src.fetchers.results.fetch_fixture_from_api

Conventions attendues :
- provider = "api_football"
- sport = "football"
- plan_label = "api_football_pro"
- empty_is_ok = True (un jour sans match est légitime pour fetch fixtures)
"""

from __future__ import annotations

from typing import Any

import pytest


class _FakeResp:
    def __init__(self, status_code: int = 200, json_data: Any = None):
        self.status_code = status_code
        self._json = json_data or {}

    def json(self):
        return self._json


@pytest.fixture
def captured_health_calls(monkeypatch):
    """Capture each log_call invocation without touching the DB."""
    from src.monitoring import provider_health as ph

    calls: list[dict[str, Any]] = []

    def fake_log_call(**kwargs):
        calls.append(kwargs)

    monkeypatch.setattr(ph, "log_call", fake_log_call)
    # Patch the local references in both fetcher modules.
    from src.fetchers import matches as matches_mod
    from src.fetchers import results as results_mod

    monkeypatch.setattr(matches_mod, "log_call", fake_log_call, raising=False)
    monkeypatch.setattr(results_mod, "log_call", fake_log_call, raising=False)
    return calls


# ── matches.get_fixtures_by_date ─────────────────────────────────────────


def test_get_fixtures_by_date_logs_success_with_row_count(monkeypatch, captured_health_calls):
    """Happy path: payload with N fixtures → log_call(status=200, row_count=N)."""
    from src.fetchers import matches as matches_mod

    payload = {"response": [{"fixture": {"id": 1}}, {"fixture": {"id": 2}}]}
    monkeypatch.setattr(
        matches_mod.requests,
        "get",
        lambda url, headers=None, params=None, timeout=None: _FakeResp(200, payload),
    )

    out = matches_mod.get_fixtures_by_date(61, "2026-05-10", "2026-05-11")

    assert len(out) == 2
    assert len(captured_health_calls) == 1
    call = captured_health_calls[0]
    assert call["provider"] == "api_football"
    assert call["sport"] == "football"
    assert call["status_code"] == 200
    assert call["row_count"] == 2
    assert call["plan_label"] == "api_football_pro"
    assert call.get("empty_is_ok") is True
    assert "api-sports.io" in call["endpoint"]


def test_get_fixtures_by_date_logs_success_for_empty_response(monkeypatch, captured_health_calls):
    """Empty response is legit (no match on that day for the given league)."""
    from src.fetchers import matches as matches_mod

    monkeypatch.setattr(
        matches_mod.requests,
        "get",
        lambda url, headers=None, params=None, timeout=None: _FakeResp(200, {"response": []}),
    )

    out = matches_mod.get_fixtures_by_date(61, "2026-05-10", "2026-05-11")

    assert out == []
    assert len(captured_health_calls) == 1
    call = captured_health_calls[0]
    assert call["status_code"] == 200
    assert call["row_count"] == 0
    assert call.get("empty_is_ok") is True


def test_get_fixtures_by_date_logs_transport_error(monkeypatch, captured_health_calls):
    """A raised exception → log_call(status=None, error set), return []."""
    from src.fetchers import matches as matches_mod

    def boom(url, headers=None, params=None, timeout=None):
        raise RuntimeError("dns failure")

    monkeypatch.setattr(matches_mod.requests, "get", boom)

    out = matches_mod.get_fixtures_by_date(61, "2026-05-10", "2026-05-11")

    assert out == []
    assert len(captured_health_calls) == 1
    call = captured_health_calls[0]
    assert call["status_code"] is None
    assert call.get("error") is not None


def test_get_fixtures_by_date_log_call_failure_does_not_break(monkeypatch):
    """log_call raising must not break the fetch path."""
    from src.fetchers import matches as matches_mod

    def boom_log(**kwargs):
        raise RuntimeError("monitoring on fire")

    monkeypatch.setattr(matches_mod, "log_call", boom_log, raising=False)
    monkeypatch.setattr(
        matches_mod.requests,
        "get",
        lambda url, headers=None, params=None, timeout=None: _FakeResp(
            200, {"response": [{"fixture": {"id": 1}}]}
        ),
    )

    out = matches_mod.get_fixtures_by_date(61, "2026-05-10", "2026-05-11")
    assert len(out) == 1


# ── results.fetch_fixture_from_api ───────────────────────────────────────


def test_fetch_fixture_from_api_logs_success_single_fixture(monkeypatch, captured_health_calls):
    """1 fixture returned → row_count=1."""
    from src.fetchers import results as results_mod

    payload = {"response": [{"fixture": {"id": 99}, "goals": {"home": 2, "away": 1}}]}
    monkeypatch.setattr(
        results_mod.requests,
        "get",
        lambda url, headers=None, params=None, timeout=None: _FakeResp(200, payload),
    )

    out = results_mod.fetch_fixture_from_api(99)

    assert out is not None
    assert len(captured_health_calls) == 1
    call = captured_health_calls[0]
    assert call["provider"] == "api_football"
    assert call["sport"] == "football"
    assert call["status_code"] == 200
    assert call["row_count"] == 1
    assert call["plan_label"] == "api_football_pro"


def test_fetch_fixture_from_api_logs_empty_response_as_success(monkeypatch, captured_health_calls):
    """response=[] is legit (fixture not found in API) — still success with row_count=0."""
    from src.fetchers import results as results_mod

    monkeypatch.setattr(
        results_mod.requests,
        "get",
        lambda url, headers=None, params=None, timeout=None: _FakeResp(200, {"response": []}),
    )

    out = results_mod.fetch_fixture_from_api(99)

    assert out is None
    assert len(captured_health_calls) == 1
    call = captured_health_calls[0]
    assert call["status_code"] == 200
    assert call["row_count"] == 0
    assert call.get("empty_is_ok") is True


def test_fetch_fixture_from_api_logs_transport_error(monkeypatch, captured_health_calls):
    from src.fetchers import results as results_mod

    def boom(url, headers=None, params=None, timeout=None):
        raise RuntimeError("connection timeout")

    monkeypatch.setattr(results_mod.requests, "get", boom)

    out = results_mod.fetch_fixture_from_api(99)

    assert out is None
    assert len(captured_health_calls) == 1
    call = captured_health_calls[0]
    assert call["status_code"] is None
    assert (
        "timeout" in (call.get("error") or "").lower()
        or "connection" in (call.get("error") or "").lower()
    )


def test_fetch_fixture_from_api_log_call_failure_does_not_break(monkeypatch):
    from src.fetchers import results as results_mod

    def boom_log(**kwargs):
        raise RuntimeError("monitoring on fire")

    monkeypatch.setattr(results_mod, "log_call", boom_log, raising=False)
    monkeypatch.setattr(
        results_mod.requests,
        "get",
        lambda url, headers=None, params=None, timeout=None: _FakeResp(
            200, {"response": [{"fixture": {"id": 99}}]}
        ),
    )

    out = results_mod.fetch_fixture_from_api(99)
    assert out is not None
