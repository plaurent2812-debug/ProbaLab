"""Tests : instrumentation provider health dans nhl_pipeline._fetch_json.

Master plan Phase 2.3 : chaque appel à la NHL API officielle (api-web.nhle.com)
doit produire UNE ligne dans ``provider_health_log`` via log_call. Une seule
ligne par appel (reflet du résultat final), même avec retries.

Conventions log_call attendues :

- provider = "nhl_api"
- sport = "nhl"
- endpoint = URL complète (NHL_API + endpoint argument)
- status_code = code HTTP final OU None si transport error final
- row_count = 1 si payload dict non vide, 0 si dict vide, None si abandon
- plan_label = "nhl_api_free" (la NHL API officielle est gratuite)
- empty_is_ok = True (un jour off / fin de saison renvoie un payload léger
  ou vide, c'est légitime)
- error = chaîne courte en cas d'échec
"""

from __future__ import annotations

from typing import Any

import pytest


class _FakeResp:
    def __init__(self, status_code: int, json_data: Any = None):
        self.status_code = status_code
        self._json = json_data
        self.text = ""

    def json(self):
        return self._json


@pytest.fixture
def captured_health_calls(monkeypatch):
    """Capture chaque appel à log_call sans toucher la DB."""
    from src.fetchers import nhl_pipeline
    from src.monitoring import provider_health as ph

    calls: list[dict[str, Any]] = []

    def fake_log_call(**kwargs):
        calls.append(kwargs)

    monkeypatch.setattr(ph, "log_call", fake_log_call)
    monkeypatch.setattr(nhl_pipeline, "log_call", fake_log_call, raising=False)
    return calls


def test_fetch_json_logs_success_dict_payload(monkeypatch, captured_health_calls):
    """Succès 200 + dict non vide → log_call(status=200, row_count=1)."""
    from src.fetchers import nhl_pipeline

    monkeypatch.setattr(
        nhl_pipeline.httpx,
        "get",
        lambda url, timeout=None, follow_redirects=None: _FakeResp(200, {"games": [1, 2]}),
    )
    monkeypatch.setattr(nhl_pipeline.time, "sleep", lambda s: None)

    result = nhl_pipeline._fetch_json("/schedule/now")

    assert result == {"games": [1, 2]}
    assert len(captured_health_calls) == 1
    call = captured_health_calls[0]
    assert call["provider"] == "nhl_api"
    assert call["sport"] == "nhl"
    assert call["status_code"] == 200
    assert call["row_count"] == 1
    assert call["plan_label"] == "nhl_api_free"
    assert call.get("empty_is_ok") is True
    assert "/schedule/now" in call["endpoint"]


def test_fetch_json_logs_success_empty_dict(monkeypatch, captured_health_calls):
    """200 + dict vide est un succès légitime (empty_is_ok=True)."""
    from src.fetchers import nhl_pipeline

    monkeypatch.setattr(
        nhl_pipeline.httpx,
        "get",
        lambda url, timeout=None, follow_redirects=None: _FakeResp(200, {}),
    )
    monkeypatch.setattr(nhl_pipeline.time, "sleep", lambda s: None)

    result = nhl_pipeline._fetch_json("/standings/now")

    assert result == {}
    assert len(captured_health_calls) == 1
    call = captured_health_calls[0]
    assert call["status_code"] == 200
    assert call["row_count"] == 0
    assert call.get("empty_is_ok") is True


def test_fetch_json_logs_terminal_4xx_failure(monkeypatch, captured_health_calls):
    """404 (non-retry) → 1 log avec status_code=404 et error set, return None."""
    from src.fetchers import nhl_pipeline

    monkeypatch.setattr(
        nhl_pipeline.httpx,
        "get",
        lambda url, timeout=None, follow_redirects=None: _FakeResp(404, None),
    )
    monkeypatch.setattr(nhl_pipeline.time, "sleep", lambda s: None)

    result = nhl_pipeline._fetch_json("/unknown")

    assert result is None
    assert len(captured_health_calls) == 1
    call = captured_health_calls[0]
    assert call["status_code"] == 404
    assert call.get("error") is not None


def test_fetch_json_logs_after_retries_then_success(monkeypatch, captured_health_calls):
    """500 puis succès → 1 SEUL log final (status=200), pas un log par retry."""
    from src.fetchers import nhl_pipeline

    attempts: list[int] = []

    def fake_get(url, timeout=None, follow_redirects=None):
        attempts.append(1)
        if len(attempts) < 3:
            return _FakeResp(500, None)
        return _FakeResp(200, {"ok": True})

    monkeypatch.setattr(nhl_pipeline.httpx, "get", fake_get)
    monkeypatch.setattr(nhl_pipeline.time, "sleep", lambda s: None)

    result = nhl_pipeline._fetch_json("/schedule/now")

    assert result == {"ok": True}
    assert len(attempts) == 3
    assert len(captured_health_calls) == 1
    assert captured_health_calls[0]["status_code"] == 200


def test_fetch_json_logs_after_max_retries_exhausted(monkeypatch, captured_health_calls):
    """3 retries 500 consécutifs → log(status=500, error set), return None."""
    from src.fetchers import nhl_pipeline

    monkeypatch.setattr(
        nhl_pipeline.httpx,
        "get",
        lambda url, timeout=None, follow_redirects=None: _FakeResp(500, None),
    )
    monkeypatch.setattr(nhl_pipeline.time, "sleep", lambda s: None)

    result = nhl_pipeline._fetch_json("/schedule/now")

    assert result is None
    assert len(captured_health_calls) == 1
    call = captured_health_calls[0]
    assert call["status_code"] == 500
    assert call.get("error") is not None


def test_fetch_json_logs_transport_error(monkeypatch, captured_health_calls):
    """Toutes tentatives transport-error → log(status=None, error set), return None."""
    from src.fetchers import nhl_pipeline

    def boom(url, timeout=None, follow_redirects=None):
        raise RuntimeError("dns failure")

    monkeypatch.setattr(nhl_pipeline.httpx, "get", boom)
    monkeypatch.setattr(nhl_pipeline.time, "sleep", lambda s: None)

    result = nhl_pipeline._fetch_json("/schedule/now")

    assert result is None
    assert len(captured_health_calls) == 1
    call = captured_health_calls[0]
    assert call["status_code"] is None
    assert (
        "dns" in (call.get("error") or "").lower() or "failure" in (call.get("error") or "").lower()
    )


def test_fetch_json_log_call_failure_does_not_break(monkeypatch):
    """log_call qui lève ne doit JAMAIS casser le fetch."""
    from src.fetchers import nhl_pipeline

    def boom_log(**kwargs):
        raise RuntimeError("monitoring on fire")

    monkeypatch.setattr(nhl_pipeline, "log_call", boom_log, raising=False)
    monkeypatch.setattr(
        nhl_pipeline.httpx,
        "get",
        lambda url, timeout=None, follow_redirects=None: _FakeResp(200, {"ok": True}),
    )

    result = nhl_pipeline._fetch_json("/schedule/now")
    assert result == {"ok": True}
