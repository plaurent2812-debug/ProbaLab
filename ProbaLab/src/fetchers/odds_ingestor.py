"""Client The Odds API Dev — ingestion cotes bookmakers FR + Pinnacle.

Responsabilités :
    - fetch /v4/sports/{sport}/odds avec retry + circuit breaker
    - parsing JSON → rows canoniques (one row par bookmaker × marché × selection)
    - dedup via UNIQUE constraint on closing_odds
    - quota tracking (x-requests-remaining header)

Module pur (parsing + helpers) + fonctions I/O (fetch, upsert).
Les fonctions I/O utilisent supabase + httpx ; les helpers sont testables sans réseau.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from src.fetchers.bookmaker_registry import get_bookmaker_from_api_key

logger = logging.getLogger("football_ia.odds_ingestor")


class OddsAPIQuotaExhausted(Exception):  # noqa: N818 — nom contractuel (cf. spec H2-SS1)
    """Levée quand The Odds API signale le quota mensuel dépassé."""


def to_implied_prob(odds: float) -> float:
    """Décimal → proba implicite (sans retrait overround)."""
    if odds < 1.01:
        raise ValueError(f"Invalid decimal odds: {odds} (must be >= 1.01)")
    return 1.0 / odds


def _parse_h2h_market(
    outcomes: list[dict], home_team: str, away_team: str
) -> list[tuple[str, float]]:
    """Retourne [(selection, odds), ...] pour un marché h2h (1X2 foot)."""
    out: list[tuple[str, float]] = []
    for o in outcomes:
        name = o["name"]
        price = float(o["price"])
        if name == home_team:
            out.append(("home", price))
        elif name == away_team:
            out.append(("away", price))
        elif name.lower() == "draw":
            out.append(("draw", price))
    return out


def parse_odds_response(
    events: list[dict],
    *,
    sport: str,
    snapshot_type: str,
    source_request_id: str,
) -> list[dict]:
    """Parse la réponse JSON The Odds API → rows canoniques pour closing_odds.

    Args:
        events: liste d'events telle que retournée par /v4/sports/{sport}/odds
        sport: "football" | "nhl"
        snapshot_type: "opening" | "closing" | "intraday"
        source_request_id: identifiant idempotent (UUID ou composite)

    Returns:
        Liste de dicts insérables dans closing_odds. Bookmakers inconnus sont skippés.
    """
    rows: list[dict] = []
    for event in events:
        fixture_id = str(event["id"])
        home_team = event.get("home_team", "")
        away_team = event.get("away_team", "")
        raw_commence = event["commence_time"]
        parsed_commence = datetime.fromisoformat(raw_commence.replace("Z", "+00:00"))
        if parsed_commence.tzinfo is None:
            raise ValueError(
                f"commence_time must be timezone-aware: {raw_commence!r}"
            )
        match_start = parsed_commence.astimezone(timezone.utc)

        for bk_block in event.get("bookmakers", []):
            bk = get_bookmaker_from_api_key(bk_block["key"])
            if bk is None:
                continue  # skip bookmakers hors registre
            for market_block in bk_block.get("markets", []):
                mkey = market_block["key"]
                outcomes = market_block.get("outcomes", [])
                if mkey == "h2h" and sport == "football":
                    parsed = _parse_h2h_market(outcomes, home_team, away_team)
                    if len(parsed) != 3:
                        continue
                    overround = sum(to_implied_prob(p) for _, p in parsed)
                    for selection, odds in parsed:
                        rows.append(
                            {
                                "sport": sport,
                                "fixture_id": fixture_id,
                                "match_start": match_start,
                                "bookmaker": bk,
                                "market": "1x2",
                                "selection": selection,
                                "line": None,
                                "odds": odds,
                                "implied_prob": to_implied_prob(odds),
                                "overround": overround,
                                "snapshot_type": snapshot_type,
                                "source_request_id": source_request_id,
                            }
                        )
                # Marchés BTTS / Over / NHL seront ajoutés Task 5.
    return rows
