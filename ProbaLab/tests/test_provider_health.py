"""Tests for src.monitoring.provider_health.

Master plan Phase 2.1: provider health logging. The writer must be:
- pure: build a row from explicit args, never reach for globals;
- safe: never raise on Supabase errors (logging must not break the pipeline);
- explicit: HTTP 200 with row_count=0 IS a failure unless the caller says so;
- idempotent for tests: a fully chainable mock is enough.

We do not test the SQL schema here (that lives in the migration). We pin the
Python contract so the rest of the codebase can rely on it.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from src.monitoring import provider_health

# ── Pure builder ──────────────────────────────────────────────────────────


def test_build_row_marks_http_500_as_failure():
    row = provider_health.build_row(
        provider="api_football",
        sport="football",
        endpoint="/fixtures",
        status_code=500,
        row_count=0,
        latency_ms=120,
    )
    assert row["is_success"] is False
    assert row["status_code"] == 500
    assert row["provider"] == "api_football"
    assert row["sport"] == "football"
    assert row["endpoint"] == "/fixtures"
    assert row["row_count"] == 0


def test_build_row_marks_http_200_with_zero_rows_as_failure():
    """A provider returning 200 with an empty payload is NOT a success.
    Lesson: the UI silently shows 'no matches' otherwise.
    """
    row = provider_health.build_row(
        provider="the_odds_api",
        sport="football",
        endpoint="/sports/soccer/odds",
        status_code=200,
        row_count=0,
        latency_ms=80,
    )
    assert row["is_success"] is False


def test_build_row_marks_http_200_with_rows_as_success():
    row = provider_health.build_row(
        provider="api_football",
        sport="football",
        endpoint="/fixtures",
        status_code=200,
        row_count=42,
        latency_ms=150,
    )
    assert row["is_success"] is True


def test_build_row_marks_transport_error_as_failure():
    """When status_code is None (timeout, DNS failure…), mark failure."""
    row = provider_health.build_row(
        provider="api_football",
        sport="football",
        endpoint="/fixtures",
        status_code=None,
        row_count=None,
        latency_ms=30000,
        error="ConnectionTimeout",
    )
    assert row["is_success"] is False
    assert row["error"] == "ConnectionTimeout"


def test_build_row_allow_explicit_empty_success():
    """Some endpoints legitimately return zero rows (e.g. NHL on a non-game day).
    The caller can opt into success when the empty result is expected.
    """
    row = provider_health.build_row(
        provider="nhl_api",
        sport="nhl",
        endpoint="/schedule",
        status_code=200,
        row_count=0,
        latency_ms=90,
        empty_is_ok=True,
    )
    assert row["is_success"] is True


def test_build_row_redacts_query_string_secrets():
    """We must never persist API keys or secrets in the endpoint column."""
    row = provider_health.build_row(
        provider="api_football",
        sport="football",
        endpoint="/fixtures?api_key=SECRET&league=39",
        status_code=200,
        row_count=10,
        latency_ms=120,
    )
    assert "SECRET" not in row["endpoint"]
    assert "api_key" not in row["endpoint"]


# ── log_call: write to Supabase, never raise ────────────────────────────


def test_log_call_writes_to_provider_health_log_table():
    mock_client = MagicMock()
    chain = MagicMock()
    mock_client.table.return_value = chain
    chain.insert.return_value = chain
    chain.execute.return_value = MagicMock(data=[{"id": 1}])

    provider_health.log_call(
        provider="api_football",
        sport="football",
        endpoint="/fixtures",
        status_code=200,
        row_count=10,
        latency_ms=100,
        client=mock_client,
    )

    mock_client.table.assert_called_once_with("provider_health_log")
    chain.insert.assert_called_once()
    inserted = chain.insert.call_args[0][0]
    assert inserted["provider"] == "api_football"
    assert inserted["row_count"] == 10
    assert inserted["is_success"] is True


def test_log_call_swallows_supabase_errors():
    """A monitoring failure must never break the pipeline."""
    mock_client = MagicMock()
    mock_client.table.side_effect = RuntimeError("supabase exploded")

    # Must not raise.
    provider_health.log_call(
        provider="api_football",
        sport="football",
        endpoint="/fixtures",
        status_code=500,
        row_count=0,
        latency_ms=80,
        client=mock_client,
    )


def test_log_call_returns_none_on_success_and_on_failure():
    """The contract is: log_call has no observable return value.

    We assert it returns None in both branches so callers do not accidentally
    rely on a row id (which would couple them to the Supabase response shape).
    """
    success_client = MagicMock()
    success_client.table.return_value.insert.return_value.execute.return_value = MagicMock(
        data=[{"id": 7}]
    )
    assert (
        provider_health.log_call(
            provider="api_football",
            sport="football",
            endpoint="/fixtures",
            status_code=200,
            row_count=10,
            latency_ms=100,
            client=success_client,
        )
        is None
    )

    fail_client = MagicMock()
    fail_client.table.side_effect = RuntimeError("boom")
    assert (
        provider_health.log_call(
            provider="api_football",
            sport="football",
            endpoint="/fixtures",
            status_code=500,
            row_count=0,
            latency_ms=200,
            client=fail_client,
        )
        is None
    )


# ── Recent failures helper ───────────────────────────────────────────────


def test_recent_failures_filters_to_is_success_false():
    """The admin endpoint will reuse this helper; it must restrict to failures."""
    mock_client = MagicMock()
    chain = MagicMock()
    mock_client.table.return_value = chain
    for method in ("select", "eq", "gte", "order", "limit"):
        getattr(chain, method).return_value = chain
    chain.execute.return_value = MagicMock(
        data=[
            {"id": 1, "provider": "api_football", "is_success": False},
            {"id": 2, "provider": "the_odds_api", "is_success": False},
        ]
    )

    rows = provider_health.recent_failures(hours=24, client=mock_client)
    assert len(rows) == 2
    chain.eq.assert_any_call("is_success", False)


def test_recent_failures_returns_empty_on_supabase_error():
    """Same swallow-and-log discipline for reads."""
    mock_client = MagicMock()
    mock_client.table.side_effect = RuntimeError("read failed")
    rows = provider_health.recent_failures(hours=24, client=mock_client)
    assert rows == []


# ── Sport / provider validation ──────────────────────────────────────────


def test_build_row_rejects_unknown_sport():
    with pytest.raises(ValueError):
        provider_health.build_row(
            provider="api_football",
            sport="cricket",  # not in {'football','nhl', None}
            endpoint="/fixtures",
            status_code=200,
            row_count=10,
            latency_ms=100,
        )


def test_build_row_accepts_none_sport_for_provider_meta_calls():
    """Quota / health pings may not be sport-scoped."""
    row = provider_health.build_row(
        provider="the_odds_api",
        sport=None,
        endpoint="/quota",
        status_code=200,
        row_count=1,
        latency_ms=50,
    )
    assert row["sport"] is None
    assert row["is_success"] is True
