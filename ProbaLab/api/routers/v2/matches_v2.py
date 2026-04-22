"""api/routers/v2/matches_v2.py — Consolidated matches listing (Lot 2 · T03).

Replaces the ad-hoc aggregation previously done on the frontend by combining
several endpoints (/api/predictions + /api/best-bets). Returns matches grouped
by league, filtered by sport/league/signal query params, and sorted by the
chosen strategy.

The heavy lifting lives in `src.models.matches_aggregator.aggregate_matches`
so the route itself stays a thin glue layer (lesson 63) and is rate-limited
via the shared slowapi decorator (lesson 64).
"""

from __future__ import annotations

import logging
from datetime import date as date_type
from datetime import datetime, timezone
from typing import Any, Literal

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel, ConfigDict, Field

from api.auth import current_user
from api.rate_limit import _rate_limit
from src.config import supabase
from src.models.matches_aggregator import aggregate_matches

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["matches-v2"])


# Pydantic shapes ---------------------------------------------------------


class LeagueGroup(BaseModel):
    """One league's worth of matches. Extra fields on matches are allowed."""

    model_config = ConfigDict(extra="forbid")
    league_id: int | str
    league_name: str
    matches: list[dict[str, Any]]


class MatchesV2Response(BaseModel):
    """Route response: grouped match listings with totals."""

    model_config = ConfigDict(extra="forbid")
    date: str = Field(..., description="YYYY-MM-DD UTC (the requested day).")
    total: int = Field(..., ge=0, description="Total number of matches across all groups.")
    groups: list[LeagueGroup]


# Helpers -----------------------------------------------------------------


def _split_csv(raw: str | None) -> list[str] | None:
    """Split a comma-separated query param into a list, trimming whitespace.

    Returns ``None`` when ``raw`` is falsy so the caller can distinguish
    "no filter" from "empty filter".
    """
    if not raw:
        return None
    values = [p.strip() for p in raw.split(",") if p.strip()]
    return values or None


# Route -------------------------------------------------------------------


@router.get(
    "/matches",
    response_model=MatchesV2Response,
    summary="Consolidated football + NHL matches listing grouped by league.",
)
@_rate_limit("30/minute")
def get_matches(
    request: Request,
    date: date_type | None = Query(
        default=None,
        description="Target UTC date (YYYY-MM-DD). Defaults to today UTC.",
    ),
    sports: str | None = Query(
        default=None,
        description="CSV of sport keys ('football', 'nhl'). Omit for all.",
    ),
    leagues: str | None = Query(
        default=None,
        description="CSV of league_id filters (e.g. '39,61').",
    ),
    signals: str | None = Query(
        default=None,
        description="CSV of signal labels ('value', 'safe', 'confidence').",
    ),
    sort: Literal["time", "edge", "confidence"] = Query(
        default="time",
        description="Sort strategy applied inside each league group.",
    ),
    user: dict = Depends(current_user),
) -> dict[str, Any]:
    """Return the day's matches grouped by league, UTC timestamps preserved."""
    target = date if date is not None else datetime.now(timezone.utc).date()
    iso = target.isoformat()

    sport_filter = _split_csv(sports)
    league_filter_raw = _split_csv(leagues)
    signal_filter = _split_csv(signals)

    query = supabase.table("matches_v2_view").select("*").eq("match_date", iso)
    if sport_filter:
        query = query.in_("sport", sport_filter)
    if league_filter_raw:
        # Accept both int and str league IDs — cast when clearly numeric.
        league_ids: list[Any] = []
        for raw_id in league_filter_raw:
            league_ids.append(int(raw_id) if raw_id.lstrip("-").isdigit() else raw_id)
        query = query.in_("league_id", league_ids)

    try:
        rows = query.execute().data or []
    except Exception:
        logger.exception("matches_v2: failed to fetch rows for date=%s", iso)
        rows = []

    # fixture_id is stored as TEXT across the stack (lesson 48).
    normalized: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        row = dict(row)
        if row.get("fixture_id") is not None:
            row["fixture_id"] = str(row["fixture_id"])
        normalized.append(row)

    groups = aggregate_matches(normalized, signals=signal_filter, sort=sort)
    total = sum(len(g["matches"]) for g in groups)
    return {"date": iso, "total": total, "groups": groups}
