"""Tests : instrumentation provider health dans fetch_odds.

Master plan Phase 2.2 : chaque appel à The Odds API doit produire UNE ligne
dans ``provider_health_log`` via ``src.monitoring.provider_health.log_call``,
quelle que soit l'issue (succès, retry-then-success, abandon, quota).

Ces tests vérifient l'instrumentation, pas la logique de fetch — celle-ci est
déjà couverte par tests/test_odds_ingestor.py::test_fetch_odds_*.

Conventions log_call attendues :

- provider = "the_odds_api"
- sport = "football" pour soccer_*, "nhl" pour icehockey_*
- endpoint = URL complète (les secrets sont strippés par log_call)
- status_code = code HTTP final OU None si transport error final
- row_count = len(payload) en cas de succès, sinon None
- plan_label = "the_odds_api_30_usd"
- empty_is_ok = True pour fetch_odds — un jour sans match est légitime
- error = chaîne courte en cas d'échec
"""

from __future__ import annotations

from typing import Any

import pytest

from src.fetchers.odds_ingestor import OddsAPIQuotaExhausted


class _FakeResp:
    def __init__(self, status_code: int, json_data: Any = None, headers: dict | None = None):
        self.status_code = status_code
        self._json = json_data
        self.headers = headers or {}
        self.text = ""

    def json(self):
        return self._json

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


@pytest.fixture
def captured_health_calls(monkeypatch):
    """Capture chaque appel à provider_health.log_call sans toucher la DB."""
    from src.monitoring import provider_health as ph

    calls: list[dict[str, Any]] = []

    def fake_log_call(**kwargs):
        calls.append(kwargs)

    monkeypatch.setattr(ph, "log_call", fake_log_call)
    # odds_ingestor importe via "from src.monitoring.provider_health import log_call"
    # → on patch aussi la référence locale si elle existe.
    from src.fetchers import odds_ingestor

    monkeypatch.setattr(odds_ingestor, "log_call", fake_log_call, raising=False)
    return calls


def test_fetch_odds_logs_success_with_row_count(monkeypatch, captured_health_calls):
    """Succès 200 + payload non vide → log_call(is_success implied, row_count>0)."""
    from src.fetchers import odds_ingestor

    payload = [{"id": "e1"}, {"id": "e2"}]
    monkeypatch.setattr(
        odds_ingestor.httpx,
        "get",
        lambda url, params=None, timeout=None: _FakeResp(
            200, json_data=payload, headers={"x-requests-remaining": "499"}
        ),
    )
    monkeypatch.setattr(odds_ingestor.time, "sleep", lambda s: None)

    result = odds_ingestor.fetch_odds(sport_key="soccer_epl", markets="h2h", api_key="FAKE")

    assert result == payload
    assert len(captured_health_calls) == 1
    call = captured_health_calls[0]
    assert call["provider"] == "the_odds_api"
    assert call["sport"] == "football"
    assert call["status_code"] == 200
    assert call["row_count"] == 2
    assert call["plan_label"] == "the_odds_api_30_usd"
    assert call["quota_remaining"] == 499
    assert call.get("empty_is_ok") is True


def test_fetch_odds_logs_success_for_empty_payload(monkeypatch, captured_health_calls):
    """200 + payload vide est un succès légitime (jour sans match)."""
    from src.fetchers import odds_ingestor

    monkeypatch.setattr(
        odds_ingestor.httpx,
        "get",
        lambda url, params=None, timeout=None: _FakeResp(
            200, json_data=[], headers={"x-requests-remaining": "500"}
        ),
    )
    monkeypatch.setattr(odds_ingestor.time, "sleep", lambda s: None)

    odds_ingestor.fetch_odds(sport_key="soccer_france_ligue_one", markets="h2h", api_key="FAKE")

    assert len(captured_health_calls) == 1
    call = captured_health_calls[0]
    assert call["status_code"] == 200
    assert call["row_count"] == 0
    assert call.get("empty_is_ok") is True


def test_fetch_odds_logs_429_as_quota_failure(monkeypatch, captured_health_calls):
    """429 → log_call(status_code=429, error='quota_exhausted'), PUIS raise."""
    from src.fetchers import odds_ingestor

    monkeypatch.setattr(
        odds_ingestor.httpx,
        "get",
        lambda url, params=None, timeout=None: _FakeResp(
            429, headers={"x-requests-remaining": "0"}
        ),
    )
    monkeypatch.setattr(odds_ingestor.time, "sleep", lambda s: None)

    with pytest.raises(OddsAPIQuotaExhausted):
        odds_ingestor.fetch_odds(sport_key="soccer_epl", markets="h2h", api_key="FAKE")

    assert len(captured_health_calls) == 1
    call = captured_health_calls[0]
    assert call["status_code"] == 429
    assert "quota" in (call.get("error") or "").lower()
    assert call.get("quota_remaining") == 0


def test_fetch_odds_logs_terminal_failure_after_max_retries(monkeypatch, captured_health_calls):
    """3 retries 500 consécutifs → 1 log_call(failure, status_code=500), PUIS RuntimeError."""
    from src.fetchers import odds_ingestor

    monkeypatch.setattr(
        odds_ingestor.httpx,
        "get",
        lambda url, params=None, timeout=None: _FakeResp(500),
    )
    monkeypatch.setattr(odds_ingestor.time, "sleep", lambda s: None)

    with pytest.raises(RuntimeError):
        odds_ingestor.fetch_odds(sport_key="soccer_epl", markets="h2h", api_key="FAKE")

    assert len(captured_health_calls) == 1
    call = captured_health_calls[0]
    assert call["status_code"] == 500
    assert call.get("error") is not None


def test_fetch_odds_logs_transport_error_with_none_status(monkeypatch, captured_health_calls):
    """Toutes les tentatives lèvent (transport) → log_call(status_code=None, error set)."""
    from src.fetchers import odds_ingestor

    def boom(url, params=None, timeout=None):
        raise RuntimeError("connection reset")

    monkeypatch.setattr(odds_ingestor.httpx, "get", boom)
    monkeypatch.setattr(odds_ingestor.time, "sleep", lambda s: None)

    with pytest.raises(RuntimeError):
        odds_ingestor.fetch_odds(sport_key="icehockey_nhl", markets="h2h", api_key="FAKE")

    assert len(captured_health_calls) == 1
    call = captured_health_calls[0]
    assert call["status_code"] is None
    assert call["sport"] == "nhl"
    assert (
        "connection" in (call.get("error") or "").lower()
        or "reset" in (call.get("error") or "").lower()
    )


def test_fetch_odds_logs_only_once_even_with_retries(monkeypatch, captured_health_calls):
    """Le log doit refléter le résultat FINAL, pas une ligne par tentative."""
    from src.fetchers import odds_ingestor

    attempts: list[int] = []

    def fake_get(url, params=None, timeout=None):
        attempts.append(1)
        if len(attempts) < 3:
            return _FakeResp(500)
        return _FakeResp(200, json_data=[{"id": "x"}], headers={"x-requests-remaining": "100"})

    monkeypatch.setattr(odds_ingestor.httpx, "get", fake_get)
    monkeypatch.setattr(odds_ingestor.time, "sleep", lambda s: None)

    odds_ingestor.fetch_odds(sport_key="soccer_epl", markets="h2h", api_key="FAKE")

    assert len(attempts) == 3
    # 1 seul log final, pas 3.
    assert len(captured_health_calls) == 1
    assert captured_health_calls[0]["status_code"] == 200
    assert captured_health_calls[0]["row_count"] == 1


def test_fetch_odds_log_call_failure_does_not_break_fetch(monkeypatch):
    """Si log_call lève (ne devrait jamais, mais par sécurité) → le fetch passe quand même."""
    from src.fetchers import odds_ingestor

    def boom_log(**kwargs):
        raise RuntimeError("monitoring is on fire")

    monkeypatch.setattr(odds_ingestor, "log_call", boom_log, raising=False)
    monkeypatch.setattr(
        odds_ingestor.httpx,
        "get",
        lambda url, params=None, timeout=None: _FakeResp(
            200, json_data=[{"id": "x"}], headers={"x-requests-remaining": "100"}
        ),
    )

    # Ne doit pas lever.
    out = odds_ingestor.fetch_odds(sport_key="soccer_epl", markets="h2h", api_key="FAKE")
    assert out == [{"id": "x"}]


def test_sport_from_key_resolves_soccer_and_nhl():
    """Le helper qui mappe sport_key → sport doit être public et testable."""
    from src.fetchers.odds_ingestor import _sport_from_key

    assert _sport_from_key("soccer_epl") == "football"
    assert _sport_from_key("soccer_france_ligue_one") == "football"
    assert _sport_from_key("icehockey_nhl") == "nhl"
    # Sport inconnu → None plutôt que raise (log_call accepte None).
    assert _sport_from_key("basketball_nba") is None
