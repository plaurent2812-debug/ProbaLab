"""Tests for src.odds_math.

Master plan Phase 4.1 : standardize edge / EV / implied_prob across the
codebase. This module is the single source of truth for all three.

Conventions (see master plan):

    implied_prob = 1 / odds                        (decimal odds)
    edge         = model_prob - implied_prob       (probability domain)
    ev           = model_prob * odds - 1           (return domain, per stake unit)

Where ``model_prob`` and ``implied_prob`` are in [0, 1] (NOT percent).
"""

from __future__ import annotations

import math

import pytest

from src import odds_math

# ── implied_prob ──────────────────────────────────────────────────────────


def test_implied_prob_simple():
    assert odds_math.implied_prob(2.0) == pytest.approx(0.5)
    assert odds_math.implied_prob(4.0) == pytest.approx(0.25)
    assert odds_math.implied_prob(1.5) == pytest.approx(0.6667, abs=1e-3)


def test_implied_prob_rejects_invalid_odds():
    """Decimal odds must be > 1.0 (a stake of 1 unit must return more than 1)."""
    for bad in (0.0, 1.0, 0.5, -2.0):
        with pytest.raises(ValueError):
            odds_math.implied_prob(bad)


def test_implied_prob_at_lowest_realistic_odds():
    """1.01 is the floor we accept — heavy favourites still in the realm of value betting."""
    assert odds_math.implied_prob(1.01) == pytest.approx(1 / 1.01)


# ── edge ─────────────────────────────────────────────────────────────────


def test_edge_positive_when_model_higher_than_market():
    # Model says 60%, market implies 50% (odds 2.0) → edge = +10pp.
    assert odds_math.edge(model_prob=0.6, odds=2.0) == pytest.approx(0.10)


def test_edge_negative_when_market_higher_than_model():
    # Model says 40%, market implies 50% → edge = -10pp.
    assert odds_math.edge(model_prob=0.4, odds=2.0) == pytest.approx(-0.10)


def test_edge_zero_at_fair_price():
    assert odds_math.edge(model_prob=0.5, odds=2.0) == pytest.approx(0.0)


def test_edge_rejects_invalid_inputs():
    with pytest.raises(ValueError):
        odds_math.edge(model_prob=1.2, odds=2.0)
    with pytest.raises(ValueError):
        odds_math.edge(model_prob=-0.1, odds=2.0)
    with pytest.raises(ValueError):
        odds_math.edge(model_prob=0.5, odds=0.9)


# ── ev (expected value) ──────────────────────────────────────────────────


def test_ev_positive_when_model_higher_than_market():
    # Model 60%, odds 2.0 → ev = 0.6 * 2.0 - 1 = 0.20 (20% per unit staked).
    assert odds_math.ev(model_prob=0.6, odds=2.0) == pytest.approx(0.20)


def test_ev_zero_at_fair_price():
    assert odds_math.ev(model_prob=0.5, odds=2.0) == pytest.approx(0.0)


def test_ev_negative_when_market_higher_than_model():
    assert odds_math.ev(model_prob=0.4, odds=2.0) == pytest.approx(-0.20)


def test_ev_consistent_with_edge():
    """EV and edge agree on sign and zero-crossing — different magnitudes is fine."""
    for model_prob, odds in [(0.6, 2.0), (0.4, 2.0), (0.5, 2.0), (0.7, 1.5)]:
        e = odds_math.edge(model_prob=model_prob, odds=odds)
        v = odds_math.ev(model_prob=model_prob, odds=odds)
        assert math.copysign(1, e) == math.copysign(1, v) or (
            math.isclose(e, 0, abs_tol=1e-9) and math.isclose(v, 0, abs_tol=1e-9)
        )


# ── Percent helpers (for legacy call sites) ──────────────────────────────


def test_edge_pct_returns_percentage_form():
    """The frontend reads edge_pct as a percent (e.g. 5.0 means 5%)."""
    assert odds_math.edge_pct(model_prob=0.6, odds=2.0) == pytest.approx(10.0)
    assert odds_math.edge_pct(model_prob=0.4, odds=2.0) == pytest.approx(-10.0)


def test_implied_prob_pct():
    assert odds_math.implied_prob_pct(2.0) == pytest.approx(50.0)
    assert odds_math.implied_prob_pct(4.0) == pytest.approx(25.0)


# ── Migration helper for legacy code paths ───────────────────────────────


def test_edge_from_percent_proba_handles_percent_inputs():
    """Existing callsites store proba in 0..100 form. The helper translates
    them transparently so we can migrate them without touching their tests."""
    # 60% model, odds 2.0 → edge = 0.10 in [0,1] form.
    assert odds_math.edge_from_percent_proba(60.0, 2.0) == pytest.approx(0.10)


def test_edge_from_percent_proba_returns_zero_for_invalid():
    """Legacy ticket_generator returns 0.0 (not raise) on invalid inputs to
    skip a row silently. We preserve that contract for drop-in replacement.
    """
    assert odds_math.edge_from_percent_proba(0.0, 2.0) == 0.0
    assert odds_math.edge_from_percent_proba(60.0, 1.0) == 0.0
    assert odds_math.edge_from_percent_proba(60.0, 0.5) == 0.0
