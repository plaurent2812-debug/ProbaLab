"""Tests for the `/api/safe-pick` endpoint (Lot 2 · T02).

The route is a thin glue layer on top of `select_safe_pick`. These tests focus
on wiring (Supabase → selector → response shape) and bypass slowapi via
`__wrapped__` (lesson 64).
"""

from __future__ import annotations

from datetime import date as date_type
from unittest.mock import MagicMock

from api.routers.v2.safe_pick import get_safe_pick


def test_safe_pick_uses_selector(mock_supabase, fake_user) -> None:
    """A single-in-band candidate must be surfaced as a safe pick."""
    mock_supabase.execute.return_value = MagicMock(
        data=[
            {
                "fixture_id": "f1",
                "sport": "football",
                "market": "1X2",
                "selection": "H",
                "odds": 2.0,
                "confidence": 0.72,
            },
        ]
    )

    out = get_safe_pick.__wrapped__(
        request=MagicMock(),
        date=date_type(2026, 4, 21),
        user=fake_user,
    )

    assert out["safe_pick"] is not None
    assert out["safe_pick"]["type"] == "single"
    assert out["safe_pick"]["fixture_id"] == "f1"
    assert out["fallback_message"] is None


def test_safe_pick_empty_returns_message(mock_supabase, fake_user) -> None:
    """With no candidate, `safe_pick` must be None and a fallback message set."""
    mock_supabase.execute.return_value = MagicMock(data=[])

    out = get_safe_pick.__wrapped__(
        request=MagicMock(),
        date=date_type(2026, 4, 21),
        user=fake_user,
    )

    assert out["safe_pick"] is None
    assert out["fallback_message"]


def test_safe_pick_falls_back_to_combo(mock_supabase, fake_user) -> None:
    """Two low-odds candidates whose product ∈ band → combo payload."""
    mock_supabase.execute.return_value = MagicMock(
        data=[
            {
                "fixture_id": "f1",
                "sport": "football",
                "market": "1X2",
                "selection": "H",
                "odds": 1.40,
                "confidence": 0.82,
            },
            {
                "fixture_id": "f2",
                "sport": "football",
                "market": "OU",
                "selection": "O2.5",
                "odds": 1.45,
                "confidence": 0.78,
            },
        ]
    )

    out = get_safe_pick.__wrapped__(
        request=MagicMock(),
        date=date_type(2026, 4, 21),
        user=fake_user,
    )

    assert out["safe_pick"] is not None
    assert out["safe_pick"]["type"] == "combo"
    assert len(out["safe_pick"]["legs"]) == 2
