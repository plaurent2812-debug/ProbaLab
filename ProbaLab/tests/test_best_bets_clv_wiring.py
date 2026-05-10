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


def _bet_row_unsupported_market() -> dict:
    """Marché non supporté côté CLV (closing_odds n'a pas de ligne pour ça)."""
    return {
        "id": 44,
        "bet_label": "PSG vs Lyon — Score exact 2-1",
        "market": "Score exact",
        "sport": "football",
        "fixture_id": "101",
        "odds": 8.50,
        "result": "PENDING",
    }


def _bet_row_btts_yes() -> dict:
    return {
        "id": 50,
        "bet_label": "PSG vs Lyon — BTTS Oui",
        "market": "BTTS Oui",
        "sport": "football",
        "fixture_id": "101",
        "odds": 1.80,
        "result": "PENDING",
    }


def _bet_row_over_25() -> dict:
    return {
        "id": 51,
        "bet_label": "PSG vs Lyon — Over 2.5 buts",
        "market": "Over 2.5 buts",
        "sport": "football",
        "fixture_id": "101",
        "odds": 1.90,
        "result": "PENDING",
    }


def _bet_row_under_15() -> dict:
    return {
        "id": 52,
        "bet_label": "PSG vs Lyon — Under 1.5 buts",
        "market": "Under 1.5 buts",
        "sport": "football",
        "fixture_id": "101",
        "odds": 4.20,
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


def test_record_pick_clv_safely_skips_unsupported_markets():
    """Marchés sans closing_odds mapping (Score exact, Double Chance…)
    → pas d'appel. Map exhaustive : 1X2, BTTS, Over/Under 1.5/2.5/3.5."""
    from api.routers import best_bets

    captured: list[dict] = []
    with patch.object(best_bets, "record_pick_clv", side_effect=lambda **kw: captured.append(kw)):
        best_bets._record_pick_clv_safely(_bet_row_unsupported_market(), result_val="WIN")

    assert captured == []


def test_record_pick_clv_safely_handles_btts_oui():
    from api.routers import best_bets

    captured: list[dict] = []
    with patch.object(best_bets, "record_pick_clv", side_effect=lambda **kw: captured.append(kw)):
        best_bets._record_pick_clv_safely(_bet_row_btts_yes(), result_val="WIN")

    assert len(captured) == 1
    call = captured[0]
    assert call["market"] == "btts"
    assert call["selection"] == "yes"
    assert call["displayed_odds"] == 1.80


def test_record_pick_clv_safely_handles_btts_non():
    from api.routers import best_bets

    bet = {**_bet_row_btts_yes(), "market": "BTTS Non", "id": 53}
    captured: list[dict] = []
    with patch.object(best_bets, "record_pick_clv", side_effect=lambda **kw: captured.append(kw)):
        best_bets._record_pick_clv_safely(bet, result_val="LOSS")

    assert len(captured) == 1
    assert captured[0]["market"] == "btts"
    assert captured[0]["selection"] == "no"


def test_record_pick_clv_safely_handles_over_25():
    from api.routers import best_bets

    captured: list[dict] = []
    with patch.object(best_bets, "record_pick_clv", side_effect=lambda **kw: captured.append(kw)):
        best_bets._record_pick_clv_safely(_bet_row_over_25(), result_val="WIN")

    assert len(captured) == 1
    call = captured[0]
    assert call["market"] == "over_2_5"
    assert call["selection"] == "over"


def test_record_pick_clv_safely_handles_under_15():
    """'Under 1.5 buts' → market='over_1_5' (même row closing), selection='under'."""
    from api.routers import best_bets

    captured: list[dict] = []
    with patch.object(best_bets, "record_pick_clv", side_effect=lambda **kw: captured.append(kw)):
        best_bets._record_pick_clv_safely(_bet_row_under_15(), result_val="WIN")

    assert len(captured) == 1
    call = captured[0]
    assert call["market"] == "over_1_5"
    assert call["selection"] == "under"


def test_record_pick_clv_safely_handles_over_35():
    """'Over 3.5 buts' → market='over_3_5', selection='over'."""
    from api.routers import best_bets

    bet = {**_bet_row_over_25(), "market": "Over 3.5 buts", "id": 54, "odds": 3.00}
    captured: list[dict] = []
    with patch.object(best_bets, "record_pick_clv", side_effect=lambda **kw: captured.append(kw)):
        best_bets._record_pick_clv_safely(bet, result_val="WIN")

    assert len(captured) == 1
    assert captured[0]["market"] == "over_3_5"
    assert captured[0]["selection"] == "over"


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
