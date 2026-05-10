"""Per-pick Closing Line Value (CLV).

Master plan Phase 4.2 : for each recommended pick we want to know AFTER the
match :

- the bookmaker's CLOSING odds (more reflective of true probability);
- the OPENING odds (best effort — recorded by ``odds_ingestor``);
- how the displayed odds beat or lost vs. the closing line (CLV %).

Definition (industry standard, odds-ratio form):

    clv_pct = (displayed_odds / closing_odds_value - 1) * 100

Positive CLV → we recommended at better odds than where the line closed
(empirical mark of an edge). Negative CLV → the line moved against us.

The aggregated CLV-per-market lives in ``clv_engine.py`` (already shipped).
This module is the per-pick complement: it looks up the closing line in
``closing_odds`` and writes a small snapshot back to ``best_bets``.

Production safety:

- All Supabase access goes through ``client`` (default: ``src.config.supabase``).
- Read or write failures degrade silently to ``None`` — never raise.
- ``Pinnacle`` is preferred when multiple closing rows exist (sharpest line).
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)

_DEFAULT_BOOKMAKER_PREFERENCE: tuple[str, ...] = (
    "pinnacle",
    "betclic",
    "winamax",
    "unibet",
)


def compute_clv_pct(*, displayed_odds: float, closing_odds: float) -> float:
    """Return CLV % = (displayed / closing - 1) * 100.

    Both inputs must be decimal odds > 1.0. Raises ``ValueError`` otherwise.
    """
    if displayed_odds <= 1.0:
        raise ValueError(f"displayed_odds must be > 1.0, got {displayed_odds!r}")
    if closing_odds <= 1.0:
        raise ValueError(f"closing_odds must be > 1.0, got {closing_odds!r}")
    return (displayed_odds / closing_odds - 1.0) * 100.0


def _resolve_client(client: Any) -> Any:
    if client is not None:
        return client
    from src.config import supabase  # noqa: PLC0415

    return supabase


def _select_best_closing_row(
    rows: list[dict[str, Any]],
    preference: tuple[str, ...] | list[str],
) -> dict[str, Any] | None:
    """Pick the closing row that best reflects a fair price.

    Order of preference: explicit list (e.g. Pinnacle first), then the first
    non-empty row. Returns ``None`` when the list is empty.
    """
    if not rows:
        return None
    by_book = {row.get("bookmaker"): row for row in rows if row.get("bookmaker")}
    for book in preference:
        if book in by_book:
            return by_book[book]
    return rows[0]


def record_pick_clv(
    *,
    best_bet_id: int,
    fixture_id: str,
    market: str,
    selection: str,
    displayed_odds: float,
    bookmaker_preference: tuple[str, ...] | list[str] | None = None,
    client: Any = None,
) -> dict[str, Any] | None:
    """Look up the closing line and update ``best_bets`` with CLV details.

    Returns the payload that was written, or ``None`` when no closing line
    is found or any error occurs along the way. Never raises — callers
    (typically the bet resolver) plug this in without try/except.
    """
    preference = tuple(bookmaker_preference or _DEFAULT_BOOKMAKER_PREFERENCE)

    try:
        target = _resolve_client(client)
        result = (
            target.table("closing_odds")
            .select("fixture_id, market, selection, bookmaker, odds, snapshot_type")
            .eq("fixture_id", str(fixture_id))
            .eq("market", market)
            .eq("selection", selection)
            .eq("snapshot_type", "closing")
            .execute()
        )
        rows = list(result.data or [])
    except Exception:
        logger.warning(
            "pick_clv: closing_odds read failed (fixture=%s, market=%s)",
            fixture_id,
            market,
            exc_info=True,
        )
        return None

    chosen = _select_best_closing_row(rows, preference)
    if chosen is None:
        return None

    try:
        closing_value = float(chosen["odds"])
        clv_pct = compute_clv_pct(displayed_odds=displayed_odds, closing_odds=closing_value)
    except (KeyError, TypeError, ValueError):
        logger.warning(
            "pick_clv: invalid closing odds for fixture=%s row=%r",
            fixture_id,
            chosen,
        )
        return None

    payload = {
        "closing_odds_value": closing_value,
        "clv_pct": round(clv_pct, 2),
        "bookmaker_source": chosen.get("bookmaker"),
        "clv_recorded_at": datetime.now(timezone.utc).isoformat(),
    }

    try:
        target.table("best_bets").update(payload).eq("id", best_bet_id).execute()
    except Exception:
        logger.warning(
            "pick_clv: best_bets update failed (best_bet_id=%s)",
            best_bet_id,
            exc_info=True,
        )
        return None

    return payload
