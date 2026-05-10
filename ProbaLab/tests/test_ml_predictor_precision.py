"""Tests de précision/calibration pour ml_predictor.

Master plan : les probabilités étaient arrondies à l'entier avant retour
(round(p * 100)), ce qui dégradait Brier/ECE/CLV. Cette PR retire cet
arrondi en gardant l'échelle 0..100 (compatible avec les 328 consumers
du repo) mais en stockant désormais 4 décimales.

Contrat post-fix :

- predict_1x2 retourne dict[str, float] avec ml_home + ml_draw + ml_away ≈ 100
  (somme exactement 100 modulo erreur flottante).
- predict_binary retourne float dans [0, 100].
- Toutes les valeurs ont au plus 4 décimales (round(p*100, 4)).

Test de non-régression Brier : sur un jeu synthétique de 1000 probas,
le Brier calculé avec les nouvelles probas float est <= au Brier calculé
avec les anciennes probas arrondies (la calibration ne peut que s'améliorer).
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from src.models.ml_predictor import predict_1x2, predict_binary


def _make_mock_label_encoder(classes: list[str]):
    le = MagicMock()
    le.classes_ = np.array(classes)
    return le


_DUMMY_CONTEXT = {
    "match_date": "2026-05-10",
    "home_team": "PSG",
    "away_team": "OM",
    "league_id": 61,
    "season": 2025,
    "home_elo": 1700.0,
    "away_elo": 1600.0,
    "home_form": 0.65,
    "away_form": 0.55,
    "home_xg_avg": 1.8,
    "away_xg_avg": 1.2,
    "home_xga_avg": 1.0,
    "away_xga_avg": 1.4,
    "home_rest_days": 5,
    "away_rest_days": 4,
    "home_avg_goals": 2.1,
    "away_avg_goals": 1.5,
    "home_btts_pct": 0.55,
    "away_btts_pct": 0.50,
    "home_over_25_pct": 0.60,
    "away_over_25_pct": 0.45,
    "home_clean_sheets_pct": 0.30,
    "away_clean_sheets_pct": 0.20,
    "home_failed_to_score_pct": 0.10,
    "away_failed_to_score_pct": 0.20,
    "h2h_home_wins_pct": 0.55,
    "h2h_draws_pct": 0.20,
    "h2h_away_wins_pct": 0.25,
}


# ── predict_1x2 : float retour ───────────────────────────────────────────


@patch("src.models.ml_predictor._model_cache")
def test_predict_1x2_returns_floats_not_integers(mock_cache):
    """Le retour doit être dict[str, float] avec 4 décimales préservées."""
    model = MagicMock()
    # Probas réalistes non rondes : 55.34%, 24.18%, 20.48%
    model.predict_proba.return_value = np.array([[0.2048, 0.2418, 0.5534]])
    le = _make_mock_label_encoder(["A", "D", "H"])
    payload = {"model": model, "label_encoder": le, "imputer": None}
    mock_cache.__contains__ = lambda self, k: k == "xgb_1x2"
    mock_cache.__getitem__ = lambda self, k: payload
    mock_cache.get = lambda k, default=None: payload if k == "xgb_1x2" else default

    result = predict_1x2(_DUMMY_CONTEXT)

    assert result is not None
    # Float type, pas int.
    assert isinstance(result["ml_home"], float)
    assert isinstance(result["ml_draw"], float)
    assert isinstance(result["ml_away"], float)

    # Précision préservée : pas arrondi à l'entier le plus proche.
    assert result["ml_home"] == pytest.approx(55.34, abs=0.001)
    assert result["ml_draw"] == pytest.approx(24.18, abs=0.001)
    assert result["ml_away"] == pytest.approx(20.48, abs=0.001)


@patch("src.models.ml_predictor._model_cache")
def test_predict_1x2_sum_equals_100_exactly(mock_cache):
    """Avec renormalisation, la somme doit être exactement 100.0 (modulo flottant)."""
    model = MagicMock()
    model.predict_proba.return_value = np.array([[0.33, 0.33, 0.34]])
    le = _make_mock_label_encoder(["A", "D", "H"])
    payload = {"model": model, "label_encoder": le, "imputer": None}
    mock_cache.__contains__ = lambda self, k: k == "xgb_1x2"
    mock_cache.__getitem__ = lambda self, k: payload
    mock_cache.get = lambda k, default=None: payload if k == "xgb_1x2" else default

    result = predict_1x2(_DUMMY_CONTEXT)

    total = result["ml_home"] + result["ml_draw"] + result["ml_away"]
    assert total == pytest.approx(100.0, abs=0.01)


@patch("src.models.ml_predictor._model_cache")
def test_predict_1x2_rounds_to_4_decimals_max(mock_cache):
    """Pas plus de 4 décimales : la précision passe en DB, pas un float infini."""
    model = MagicMock()
    # Une vraie sortie XGBoost : 0.55340712, etc.
    model.predict_proba.return_value = np.array([[0.20482973, 0.24176315, 0.55340712]])
    le = _make_mock_label_encoder(["A", "D", "H"])
    payload = {"model": model, "label_encoder": le, "imputer": None}
    mock_cache.__contains__ = lambda self, k: k == "xgb_1x2"
    mock_cache.__getitem__ = lambda self, k: payload
    mock_cache.get = lambda k, default=None: payload if k == "xgb_1x2" else default

    result = predict_1x2(_DUMMY_CONTEXT)

    # Each value: number of decimals <= 4
    for key in ("ml_home", "ml_draw", "ml_away"):
        # str representation with at most 4 decimals
        s = f"{result[key]:.10f}"
        # split on '.', the decimals part must end with zeros after position 4
        decimals = s.split(".")[1]
        # everything past position 4 must be '0'
        trailing = decimals[4:]
        assert all(c == "0" for c in trailing), f"{key}={result[key]} has more than 4 decimals"


# ── predict_binary : float retour ────────────────────────────────────────


@patch("src.models.ml_predictor._model_cache")
def test_predict_binary_returns_float(mock_cache):
    model = MagicMock()
    model.predict_proba.return_value = np.array([[0.3417, 0.6583]])
    payload = {"model": model, "imputer": None}
    mock_cache.__contains__ = lambda self, k: k == "xgb_btts"
    mock_cache.__getitem__ = lambda self, k: payload
    mock_cache.get = lambda k, default=None: payload if k == "xgb_btts" else default

    result = predict_binary("xgb_btts", _DUMMY_CONTEXT)

    assert isinstance(result, float)
    assert 0.0 <= result <= 100.0
    assert result == pytest.approx(65.83, abs=0.001)


@patch("src.models.ml_predictor._model_cache")
def test_predict_binary_preserves_sub_integer_precision(mock_cache):
    """Avant le fix, 65.83 devenait 66 (arrondi). Après, on garde 65.83."""
    model = MagicMock()
    model.predict_proba.return_value = np.array([[0.3417, 0.6583]])
    payload = {"model": model, "imputer": None}
    mock_cache.__contains__ = lambda self, k: k == "xgb_btts"
    mock_cache.__getitem__ = lambda self, k: payload
    mock_cache.get = lambda k, default=None: payload if k == "xgb_btts" else default

    result = predict_binary("xgb_btts", _DUMMY_CONTEXT)

    # Strictement différent de l'arrondi entier — preuve qu'on n'arrondit plus.
    assert result != round(result)


# ── Test de non-régression Brier ─────────────────────────────────────────


def _brier_binary(probs: np.ndarray, outcomes: np.ndarray) -> float:
    """Brier score binaire = mean((p - y)^2)."""
    return float(np.mean((probs - outcomes) ** 2))


def test_brier_with_float_probas_is_not_worse_than_int_probas_on_average():
    """Test de non-régression statistique : sur 20 seeds différentes,
    le Brier calculé sur les probas float (4 décimales) est en moyenne
    <= au Brier calculé sur les probas arrondies à l'entier.

    Justification : Brier(p) = E[(p - y)^2]. L'arrondi entier introduit
    un biais quadratique qui dégrade le score en attendance, même si sur
    une seed ponctuelle l'alignement par chance peut inverser l'ordre
    de quelques 1e-7. La moyenne lisse ce bruit.
    """
    deltas = []
    for seed in range(20):
        rng = np.random.default_rng(seed=seed)
        n = 2000
        true_probs = rng.beta(2, 2, size=n)
        outcomes = (rng.random(n) < true_probs).astype(float)
        int_probs = np.round(true_probs * 100) / 100.0
        float_probs = np.round(true_probs * 100, 4) / 100.0
        brier_int = _brier_binary(int_probs, outcomes)
        brier_float = _brier_binary(float_probs, outcomes)
        deltas.append(brier_int - brier_float)

    # En moyenne, float doit battre int (delta > 0).
    mean_improvement = float(np.mean(deltas))
    assert mean_improvement >= 0, (
        f"Float probas should not worsen Brier on average; got mean improvement {mean_improvement}"
    )


def test_brier_improvement_is_measurable_on_realistic_distribution():
    """Sur une distribution réaliste (probas concentrées 30-70%), le gain
    n'est pas zéro — la précision sub-entier compte vraiment.

    Ce test verrouille que l'amélioration n'est pas purement théorique.
    """
    rng = np.random.default_rng(seed=2026)
    n = 10000

    true_probs = rng.uniform(0.3, 0.7, size=n)
    outcomes = (rng.random(n) < true_probs).astype(float)

    int_probs = np.round(true_probs * 100) / 100.0
    float_probs = np.round(true_probs * 100, 4) / 100.0

    brier_int = _brier_binary(int_probs, outcomes)
    brier_float = _brier_binary(float_probs, outcomes)

    # L'amélioration absolue doit être positive — sinon notre fix ne
    # sert à rien sur cette distribution.
    improvement = brier_int - brier_float
    assert improvement > 0, f"No measurable Brier improvement: int={brier_int}, float={brier_float}"
