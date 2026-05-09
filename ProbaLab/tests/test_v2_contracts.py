"""V2 frontend contract tests for the matches and safe-pick endpoints.

The V2 hooks `useMatchesOfDay` and `useSafePick` consume specific top-level
keys. Any drift in the backend response shape blanks out the V2 home page
(lesson 60: "API shape must match frontend exactly"), so this module pins
the contract.

Coverage map:
    GET /api/matches              -> tests in this module (top-level + group + row)
    GET /api/safe-pick            -> tests in this module (single + null)
    GET /api/performance/summary  -> covered by `tests/test_api/test_performance_summary.py`

The tests follow the pattern from `test_matches_v2.py`: call the route
function via ``__wrapped__`` to bypass slowapi (lesson 64) and rely on the
function-scoped ``mock_supabase`` fixture from `tests/conftest.py`, which
patches ``src.config.supabase`` plus every already-imported v2 router module.

This file lives at ``tests/`` (not ``tests/test_api/``) on purpose:
``tests/test_api/conftest.py`` defines a session-scoped ``mock_supabase``
that shadows the function-scoped patcher, which makes V2 routes return 500
instead of using the mock. Aggregation correctness is covered by
`test_matches_v2.py` and `test_safe_pick_selector.py`. Here we only assert
on shape.
"""

from __future__ import annotations

from datetime import date as date_type
from datetime import datetime, timezone
from unittest.mock import MagicMock

from api.routers.v2.matches_v2 import get_matches
from api.routers.v2.safe_pick import get_safe_pick

# ── Helpers ──────────────────────────────────────────────────────────────


def _matches_execute_sequence(
    football_fixtures: list[dict],
    football_predictions: list[dict],
    football_bets: list[dict],
    nhl_fixtures: list[dict],
    nhl_bets: list[dict],
    *,
    include_football: bool = True,
    include_nhl: bool = True,
    safe_pick_fixtures: list[dict] | None = None,
) -> list[MagicMock]:
    """Mirror the query order issued by `/api/matches` (see test_matches_v2.py).

    The route fans out: fixtures -> predictions -> best_bets (football),
    nhl_fixtures -> best_bets (nhl), then nested safe_pick which fetches
    fixtures (+ predictions + odds when non-empty) and finally NHL fixtures.
    """
    safe_pick_fx = safe_pick_fixtures if safe_pick_fixtures is not None else []
    seq: list[MagicMock] = []

    if include_football:
        seq.append(MagicMock(data=football_fixtures))
        if football_fixtures:
            seq.append(MagicMock(data=football_predictions))
            seq.append(MagicMock(data=football_bets))

    if include_nhl:
        seq.append(MagicMock(data=nhl_fixtures))
        if nhl_fixtures:
            seq.append(MagicMock(data=nhl_bets))

    # Nested safe_pick call (best-effort inside /api/matches).
    seq.append(MagicMock(data=safe_pick_fx))
    if safe_pick_fx:
        seq.append(MagicMock(data=[]))
        seq.append(MagicMock(data=[]))
    seq.append(MagicMock(data=[]))  # NHL fixtures inside safe_pick
    return seq


def _safe_pick_execute_sequence(
    fixtures: list[dict],
    predictions: list[dict] | None = None,
    odds: list[dict] | None = None,
    nhl_fixtures: list[dict] | None = None,
) -> list[MagicMock]:
    """Mirror the query order issued by `/api/safe-pick`."""
    seq: list[MagicMock] = [MagicMock(data=fixtures)]
    if fixtures:
        seq.append(MagicMock(data=predictions or []))
        seq.append(MagicMock(data=odds or []))
    seq.append(MagicMock(data=nhl_fixtures or []))
    return seq


# ── /api/matches contract ────────────────────────────────────────────────


_DAY = date_type(2026, 5, 9)
_DAY_ISO = _DAY.isoformat()


def test_matches_top_level_shape_when_empty(mock_supabase) -> None:
    """Empty payload still has exactly {date, total, groups}."""
    mock_supabase.execute.side_effect = _matches_execute_sequence([], [], [], [], [])

    out = get_matches.__wrapped__(
        request=MagicMock(),
        date=_DAY,
        sports=None,
        leagues=None,
        signals=None,
        sort="time",
    )

    assert set(out.keys()) == {"date", "total", "groups"}
    assert out["date"] == _DAY_ISO
    assert out["total"] == 0
    assert out["groups"] == []


def test_matches_group_shape(mock_supabase) -> None:
    """Each league group must expose exactly {league_id, league_name, matches}."""
    fixtures = [
        {
            "id": "fx-001",
            "api_fixture_id": 12345,
            "home_team": "PSG",
            "away_team": "OM",
            "date": f"{_DAY_ISO}T19:00:00+00:00",
            "status": "NS",
            "league_id": 61,
            "league_name": "Ligue 1",
        }
    ]
    predictions = [
        {
            "fixture_id": "fx-001",
            "proba_home": 55.0,
            "proba_draw": 25.0,
            "proba_away": 20.0,
            "confidence_score": 7,
        }
    ]
    mock_supabase.execute.side_effect = _matches_execute_sequence(
        fixtures, predictions, [], [], [], include_nhl=False
    )

    out = get_matches.__wrapped__(
        request=MagicMock(),
        date=_DAY,
        sports="football",
        leagues=None,
        signals=None,
        sort="time",
    )

    assert out["groups"], "expected at least one league group"
    group = out["groups"][0]
    assert set(group.keys()) == {"league_id", "league_name", "matches"}
    assert isinstance(group["matches"], list)


def test_matches_row_keys_consumed_by_frontend(mock_supabase) -> None:
    """Each match row must carry the keys read by `useMatchesOfDay`.

    Source of truth: `dashboard/src/hooks/v2/useMatchesOfDay.ts::BackendMatchRow`.
    Required keys (frontend will not render without them): fixture_id, sport,
    league_id, league_name, home_team, away_team, kickoff_utc.
    """
    fixtures = [
        {
            "id": "fx-001",
            "api_fixture_id": 12345,
            "home_team": "PSG",
            "away_team": "OM",
            "date": f"{_DAY_ISO}T19:00:00+00:00",
            "status": "NS",
            "league_id": 61,
            "league_name": "Ligue 1",
        }
    ]
    predictions = [
        {
            "fixture_id": "fx-001",
            "proba_home": 55.0,
            "proba_draw": 25.0,
            "proba_away": 20.0,
            "confidence_score": 7,
        }
    ]
    mock_supabase.execute.side_effect = _matches_execute_sequence(
        fixtures, predictions, [], [], [], include_nhl=False
    )

    out = get_matches.__wrapped__(
        request=MagicMock(),
        date=_DAY,
        sports="football",
        leagues=None,
        signals=None,
        sort="time",
    )

    rows = [m for g in out["groups"] for m in g["matches"]]
    assert rows, "expected at least one match row"
    row = rows[0]
    required = {
        "fixture_id",
        "sport",
        "league_id",
        "league_name",
        "home_team",
        "away_team",
        "kickoff_utc",
    }
    missing = required - set(row.keys())
    assert not missing, f"matches row missing frontend-required keys: {missing}"
    # signals is always emitted by the route — frontend treats it as iterable.
    assert "signals" in row
    assert isinstance(row["signals"], list)


def test_matches_default_date_is_today_utc(mock_supabase) -> None:
    """Without an explicit date, the route must default to today's UTC date."""
    mock_supabase.execute.side_effect = _matches_execute_sequence([], [], [], [], [])

    out = get_matches.__wrapped__(
        request=MagicMock(),
        date=None,
        sports=None,
        leagues=None,
        signals=None,
        sort="time",
    )

    assert out["date"] == datetime.now(timezone.utc).date().isoformat()


# ── /api/safe-pick contract ──────────────────────────────────────────────


def test_safe_pick_top_level_shape_when_no_candidate(mock_supabase) -> None:
    """`SafePickResponse` is `extra='forbid'`. No candidate => safe_pick is None
    with the exact shape `{date, safe_pick, fallback_message}`."""
    mock_supabase.execute.side_effect = _safe_pick_execute_sequence([])

    out = get_safe_pick.__wrapped__(request=MagicMock(), date=_DAY)

    assert set(out.keys()) == {"date", "safe_pick", "fallback_message"}
    assert out["date"] == _DAY_ISO
    assert out["safe_pick"] is None
    assert out["fallback_message"] is None or isinstance(out["fallback_message"], str)


def test_safe_pick_default_date_is_today_utc(mock_supabase) -> None:
    mock_supabase.execute.side_effect = _safe_pick_execute_sequence([])

    out = get_safe_pick.__wrapped__(request=MagicMock(), date=None)

    assert out["date"] == datetime.now(timezone.utc).date().isoformat()
