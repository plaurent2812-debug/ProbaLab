"""Tests for src.monitoring.pick_clv.

Master plan Phase 4.2 : per-pick CLV. For each recommended pick, we want
to know the bookmaker's CLOSING odds, the OPENING odds (best effort), and
how the displayed odds compared to the closing line (CLV %).

Conventions:
    CLV % = (displayed_odds / closing_odds_value - 1) * 100

A POSITIVE CLV means we recommended at better odds than where the line
closed — that is the empirical mark of an edge. A negative CLV means
the line moved against us; the bookmaker priced in more probability
than we did.

We compute on the implied-probability domain when needed for sign
consistency with the existing clv_engine, but the displayed metric to
users is the odds-ratio form, which is the industry standard.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from src.monitoring import pick_clv

# ── compute_clv_pct ──────────────────────────────────────────────────────


def test_compute_clv_pct_positive_when_displayed_beats_closing():
    """Displayed 2.10, closing 2.00 → CLV = +5%."""
    assert pick_clv.compute_clv_pct(displayed_odds=2.10, closing_odds=2.00) == pytest.approx(5.0)


def test_compute_clv_pct_negative_when_closing_beats_displayed():
    """Displayed 1.90, closing 2.00 → CLV = -5%."""
    assert pick_clv.compute_clv_pct(displayed_odds=1.90, closing_odds=2.00) == pytest.approx(-5.0)


def test_compute_clv_pct_zero_at_equality():
    assert pick_clv.compute_clv_pct(displayed_odds=2.0, closing_odds=2.0) == pytest.approx(0.0)


def test_compute_clv_pct_rejects_invalid_closing():
    """Closing odds <= 1.0 makes the metric meaningless — raise rather than coerce."""
    with pytest.raises(ValueError):
        pick_clv.compute_clv_pct(displayed_odds=2.0, closing_odds=0.0)
    with pytest.raises(ValueError):
        pick_clv.compute_clv_pct(displayed_odds=2.0, closing_odds=1.0)


def test_compute_clv_pct_rejects_invalid_displayed():
    with pytest.raises(ValueError):
        pick_clv.compute_clv_pct(displayed_odds=0.0, closing_odds=2.0)


# ── record_pick_clv: lookup closing line + update best_bets ────────────


def _supabase_mock_for_closing(closing_rows: list[dict]):
    """Build a Supabase mock that returns ``closing_rows`` on select+execute."""
    mock = MagicMock()

    select_chain = MagicMock()
    select_result = MagicMock()
    select_result.data = closing_rows
    for method in (
        "select",
        "eq",
        "neq",
        "gte",
        "lte",
        "gt",
        "lt",
        "in_",
        "or_",
        "order",
        "limit",
        "single",
    ):
        getattr(select_chain, method).return_value = select_chain
    select_chain.execute.return_value = select_result

    update_chain = MagicMock()
    update_result = MagicMock()
    update_result.data = []
    for method in ("update", "eq", "execute"):
        getattr(update_chain, method).return_value = update_chain
    update_chain.execute.return_value = update_result

    # We need .table("closing_odds") to return select_chain
    # and .table("best_bets") to return update_chain.
    def table_router(name):
        if name == "closing_odds":
            return select_chain
        if name == "best_bets":
            return update_chain
        return MagicMock()

    mock.table.side_effect = table_router
    return mock, select_chain, update_chain


def test_record_pick_clv_updates_best_bet_with_closing_and_clv_pct():
    """Happy path : found a closing row, computed CLV %, updated best_bets."""
    mock, _, update_chain = _supabase_mock_for_closing(
        [
            {
                "fixture_id": "fx-001",
                "market": "1x2",
                "selection": "home",
                "bookmaker": "pinnacle",
                "odds": 1.95,
                "snapshot_type": "closing",
            }
        ]
    )

    out = pick_clv.record_pick_clv(
        best_bet_id=42,
        fixture_id="fx-001",
        market="1x2",
        selection="home",
        displayed_odds=2.10,
        bookmaker_preference=["pinnacle"],
        client=mock,
    )

    assert out is not None
    # CLV is rounded to 2 decimals for UI display — that is the contract.
    expected_clv = round((2.10 / 1.95 - 1.0) * 100.0, 2)
    assert out["clv_pct"] == expected_clv
    assert out["closing_odds_value"] == 1.95
    assert out["bookmaker_source"] == "pinnacle"

    # The update payload was written back.
    update_chain.update.assert_called_once()
    payload = update_chain.update.call_args[0][0]
    assert payload["clv_pct"] == expected_clv
    assert payload["closing_odds_value"] == 1.95
    assert payload["bookmaker_source"] == "pinnacle"
    assert "clv_recorded_at" in payload


def test_record_pick_clv_no_closing_row_returns_none():
    """No closing line found → no write, return None. Caller decides what to do."""
    mock, _, update_chain = _supabase_mock_for_closing([])

    out = pick_clv.record_pick_clv(
        best_bet_id=42,
        fixture_id="fx-999",
        market="1x2",
        selection="home",
        displayed_odds=2.10,
        client=mock,
    )

    assert out is None
    update_chain.update.assert_not_called()


def test_record_pick_clv_prefers_pinnacle_over_other_books():
    """When multiple closing rows exist, Pinnacle wins (sharpest line)."""
    mock, _, update_chain = _supabase_mock_for_closing(
        [
            {
                "fixture_id": "fx-001",
                "market": "1x2",
                "selection": "home",
                "bookmaker": "betclic",
                "odds": 2.10,
                "snapshot_type": "closing",
            },
            {
                "fixture_id": "fx-001",
                "market": "1x2",
                "selection": "home",
                "bookmaker": "pinnacle",
                "odds": 1.95,
                "snapshot_type": "closing",
            },
        ]
    )

    out = pick_clv.record_pick_clv(
        best_bet_id=42,
        fixture_id="fx-001",
        market="1x2",
        selection="home",
        displayed_odds=2.10,
        client=mock,
    )

    assert out["bookmaker_source"] == "pinnacle"
    assert out["closing_odds_value"] == 1.95


def test_record_pick_clv_falls_back_to_first_book_when_no_pinnacle():
    """No Pinnacle row → take the first available closing line, log the bookmaker."""
    mock, _, _ = _supabase_mock_for_closing(
        [
            {
                "fixture_id": "fx-001",
                "market": "1x2",
                "selection": "home",
                "bookmaker": "betclic",
                "odds": 2.05,
                "snapshot_type": "closing",
            }
        ]
    )

    out = pick_clv.record_pick_clv(
        best_bet_id=42,
        fixture_id="fx-001",
        market="1x2",
        selection="home",
        displayed_odds=2.10,
        client=mock,
    )

    assert out["bookmaker_source"] == "betclic"
    assert out["closing_odds_value"] == 2.05


def test_record_pick_clv_swallows_supabase_errors():
    """A read or write failure must not break the resolver pipeline."""
    mock = MagicMock()
    mock.table.side_effect = RuntimeError("supabase down")

    out = pick_clv.record_pick_clv(
        best_bet_id=42,
        fixture_id="fx-001",
        market="1x2",
        selection="home",
        displayed_odds=2.10,
        client=mock,
    )

    assert out is None
