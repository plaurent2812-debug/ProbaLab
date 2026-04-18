"""Tests pour odds_ingestor — client The Odds API Dev."""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from src.fetchers.odds_ingestor import (
    OddsAPIQuotaExhausted,
    parse_odds_response,
    to_implied_prob,
)


def test_to_implied_prob_basic():
    assert to_implied_prob(2.0) == 0.5
    assert to_implied_prob(1.50) == pytest.approx(0.6667, abs=1e-3)


def test_to_implied_prob_rejects_sub_unity():
    with pytest.raises(ValueError):
        to_implied_prob(0.95)


def test_parse_1x2_response_returns_rows():
    """Sample 1X2 extrait de la doc v4 The Odds API."""
    sample = [
        {
            "id": "event_abc123",
            "sport_key": "soccer_france_ligue_one",
            "commence_time": "2026-04-20T19:00:00Z",
            "home_team": "Paris Saint-Germain",
            "away_team": "Olympique de Marseille",
            "bookmakers": [
                {
                    "key": "pinnacle",
                    "title": "Pinnacle",
                    "last_update": "2026-04-19T10:00:00Z",
                    "markets": [
                        {
                            "key": "h2h",
                            "outcomes": [
                                {"name": "Paris Saint-Germain", "price": 1.50},
                                {"name": "Olympique de Marseille", "price": 7.00},
                                {"name": "Draw", "price": 4.50},
                            ],
                        }
                    ],
                }
            ],
        }
    ]
    rows = parse_odds_response(
        sample,
        sport="football",
        snapshot_type="opening",
        source_request_id="req-1",
    )
    assert len(rows) == 3
    # Row canonique : sport, fixture_id, bookmaker, market, selection, odds, implied_prob
    home_row = next(r for r in rows if r["selection"] == "home")
    assert home_row["bookmaker"] == "pinnacle"
    assert home_row["market"] == "1x2"
    assert home_row["odds"] == 1.50
    assert home_row["implied_prob"] == pytest.approx(0.6667, abs=1e-3)
    assert home_row["sport"] == "football"
    assert home_row["fixture_id"] == "event_abc123"
    assert home_row["snapshot_type"] == "opening"
    assert home_row["source_request_id"] == "req-1"
    assert isinstance(home_row["match_start"], datetime)
    assert home_row["match_start"].tzinfo == timezone.utc
    # Overround présent et > 1
    assert home_row["overround"] > 1.0


def test_parse_skips_unknown_bookmakers():
    sample = [
        {
            "id": "event_xxx",
            "sport_key": "soccer_epl",
            "commence_time": "2026-04-20T15:00:00Z",
            "home_team": "Arsenal",
            "away_team": "Chelsea",
            "bookmakers": [
                {
                    "key": "random_book_not_in_registry",
                    "title": "Random",
                    "last_update": "2026-04-19T10:00:00Z",
                    "markets": [
                        {
                            "key": "h2h",
                            "outcomes": [
                                {"name": "Arsenal", "price": 1.80},
                                {"name": "Chelsea", "price": 4.50},
                                {"name": "Draw", "price": 3.60},
                            ],
                        }
                    ],
                }
            ],
        }
    ]
    rows = parse_odds_response(sample, sport="football", snapshot_type="opening",
                               source_request_id="req-2")
    assert rows == []


def test_quota_exhausted_is_an_exception():
    assert issubclass(OddsAPIQuotaExhausted, Exception)
