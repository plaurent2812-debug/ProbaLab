"""CLV engine — rigorous Closing Line Value computation per market.

Usage:
    from src.monitoring.clv_engine import run_daily_clv_snapshot
    run_daily_clv_snapshot()  # upsert model_health_log for yesterday

Design:
    - fair_prob_from_odds: decimal odds → raw implied (with vig)
    - remove_overround: list of odds for a closed market → fair probs (sum=1)
    - compute_clv: CLV = model_prob / closing_fair_prob - 1, clamped to [-1, +1]
    - aggregate_clv_by_market: joins predictions + closing_odds + results (Task 10)
    - run_daily_clv_snapshot: cron entrypoint (Task 11)
"""
from __future__ import annotations

import logging

logger = logging.getLogger("football_ia.clv_engine")


def fair_prob_from_odds(odds: float) -> float:
    """Décimal → proba implicite avec vig (pas encore dé-overroundée)."""
    if odds < 1.01:
        raise ValueError(f"Invalid decimal odds: {odds} (must be >= 1.01)")
    return 1.0 / odds


def remove_overround(odds_list: list[float]) -> list[float]:
    """Retire le vig d'un marché fermé (toutes les issues mutuellement exclusives).

    Normalisation proportionnelle (méthode la plus utilisée, équivalente à
    `margin_weights` de Shin 1993 quand overround est faible).

    Args:
        odds_list: cotes décimales de toutes les issues (ex: [home, draw, away])

    Returns:
        probas fair (sum=1). Liste vide si input vide.
    """
    if not odds_list:
        return []
    implied = [fair_prob_from_odds(o) for o in odds_list]
    overround = sum(implied)
    if overround <= 0:
        return []
    return [p / overround for p in implied]


def compute_clv(*, model_prob: float, closing_fair_prob: float) -> float:
    """CLV = (model_prob / closing_fair_prob) - 1, clampé à [-1, +1].

    - CLV > 0  → on battait la closing line (edge)
    - CLV = 0  → on matchait la closing line
    - CLV < 0  → closing line était meilleure que notre probs
    """
    if closing_fair_prob <= 0:
        return 1.0 if model_prob > 0 else -1.0
    raw = (model_prob / closing_fair_prob) - 1.0
    return max(-1.0, min(1.0, raw))
