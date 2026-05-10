"""Tests : record_pick_clv est invoqué quand un best_bet football 1X2 est résolu.

Master plan : wiring du module pick_clv (livré dans PR #21) dans la
résolution football WIN/LOSS. Scope limité au 1X2 dans cette PR — c'est
le marché le plus fréquent et le mieux servi par Pinnacle.

Approach: mock supabase + spy sur api.routers.best_bets._record_pick_clv_safely
pour vérifier que la résolution déclenche le call avec la bonne shape.
"""

from __future__ import annotations

from unittest.mock import patch


def _bet_row_1x2_home_win() -> dict:
    """Best bet : PSG vs Lyon, Victoire domicile, odds 2.10."""
    return {
        "id": 42,
        "bet_label": "PSG vs Lyon — Victoire domicile",
        "market": "Victoire domicile",
        "sport": "football",
        "fixture_id": "101",
        "odds": 2.10,
        "result": "PENDING",
    }


def _bet_row_1x2_away_win() -> dict:
    return {
        "id": 43,
        "bet_label": "PSG vs Lyon — Victoire extérieur",
        "market": "Victoire extérieur",
        "sport": "football",
        "fixture_id": "101",
        "odds": 3.20,
        "result": "PENDING",
    }


def _bet_row_other_market() -> dict:
    """Marché hors 1X2 (BTTS) — pas wired dans cette PR."""
    return {
        "id": 44,
        "bet_label": "PSG vs Lyon — BTTS Oui",
        "market": "BTTS",
        "sport": "football",
        "fixture_id": "101",
        "odds": 1.85,
        "result": "PENDING",
    }


# ── Helper module-level testable directement ─────────────────────────────


def test_record_pick_clv_safely_handles_1x2_home_win():
    """Un pick 1X2 'Victoire domicile' déclenche record_pick_clv avec
    market='1x2' et selection='home'."""
    from api.routers import best_bets

    captured: list[dict] = []

    def fake_record(**kwargs):
        captured.append(kwargs)
        return {"clv_pct": 5.0}

    with patch.object(best_bets, "record_pick_clv", side_effect=fake_record):
        best_bets._record_pick_clv_safely(_bet_row_1x2_home_win(), result_val="WIN")

    assert len(captured) == 1
    call = captured[0]
    assert call["best_bet_id"] == 42
    assert call["fixture_id"] == "101"
    assert call["market"] == "1x2"
    assert call["selection"] == "home"
    assert call["displayed_odds"] == 2.10


def test_record_pick_clv_safely_handles_1x2_away_win():
    from api.routers import best_bets

    captured: list[dict] = []
    with patch.object(best_bets, "record_pick_clv", side_effect=lambda **kw: captured.append(kw)):
        best_bets._record_pick_clv_safely(_bet_row_1x2_away_win(), result_val="WIN")

    assert len(captured) == 1
    assert captured[0]["selection"] == "away"


def test_record_pick_clv_safely_skips_non_1x2_markets_in_this_pr():
    """BTTS / Over / Double Chance → pas wired ici, donc pas d'appel."""
    from api.routers import best_bets

    captured: list[dict] = []
    with patch.object(best_bets, "record_pick_clv", side_effect=lambda **kw: captured.append(kw)):
        best_bets._record_pick_clv_safely(_bet_row_other_market(), result_val="WIN")

    assert captured == []


def test_record_pick_clv_safely_skips_void_and_pending():
    """VOID / PENDING → pas de signal CLV utile."""
    from api.routers import best_bets

    captured: list[dict] = []
    with patch.object(best_bets, "record_pick_clv", side_effect=lambda **kw: captured.append(kw)):
        for result_val in ("VOID", "PENDING"):
            best_bets._record_pick_clv_safely(_bet_row_1x2_home_win(), result_val=result_val)

    assert captured == []


def test_record_pick_clv_safely_skips_when_required_fields_missing():
    """Si fixture_id ou odds manque → on ne tente même pas l'appel."""
    from api.routers import best_bets

    captured: list[dict] = []
    with patch.object(best_bets, "record_pick_clv", side_effect=lambda **kw: captured.append(kw)):
        bet_no_fixture = {**_bet_row_1x2_home_win(), "fixture_id": None}
        best_bets._record_pick_clv_safely(bet_no_fixture, result_val="WIN")
        bet_no_odds = {**_bet_row_1x2_home_win(), "odds": None}
        best_bets._record_pick_clv_safely(bet_no_odds, result_val="WIN")
        bet_zero_odds = {**_bet_row_1x2_home_win(), "odds": 0.0}
        best_bets._record_pick_clv_safely(bet_zero_odds, result_val="WIN")

    assert captured == []


def test_record_pick_clv_safely_swallows_record_errors():
    """record_pick_clv déjà swallow ses erreurs, mais on ajoute une seconde
    couche : si elle lève quand même, le resolver doit continuer."""
    from api.routers import best_bets

    def boom(**kwargs):
        raise RuntimeError("clv pipeline on fire")

    with patch.object(best_bets, "record_pick_clv", side_effect=boom):
        # Doit retourner sans lever.
        best_bets._record_pick_clv_safely(_bet_row_1x2_home_win(), result_val="WIN")


def test_record_pick_clv_safely_handles_int_fixture_id():
    """fixture_id peut être int en DB — on le stringifie pour le lookup."""
    from api.routers import best_bets

    captured: list[dict] = []
    with patch.object(best_bets, "record_pick_clv", side_effect=lambda **kw: captured.append(kw)):
        bet = {**_bet_row_1x2_home_win(), "fixture_id": 101}
        best_bets._record_pick_clv_safely(bet, result_val="LOSS")

    assert len(captured) == 1
    assert captured[0]["fixture_id"] == "101"  # stringifié
