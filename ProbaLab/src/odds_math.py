"""Standardized odds math primitives.

Master plan Phase 4.1: a single source of truth for the three numbers that
the rest of the codebase (and the UI) reads constantly. Definitions:

    implied_prob = 1 / odds                        # decimal odds
    edge         = model_prob - implied_prob       # probability domain
    ev           = model_prob * odds - 1           # return per unit staked

Conventions:

- ``odds`` are decimal (Continental). They MUST satisfy ``odds > 1.0``.
  We accept down to 1.01 (heavy favourite floor used by the value-betting
  module). Values <= 1.0 raise ``ValueError`` to surface bugs early.
- ``model_prob`` and ``implied_prob`` are in [0, 1]. Anything in 0..100 is
  considered a percent and is rejected by the strict primitives — use the
  ``*_pct`` helpers or ``edge_from_percent_proba`` for legacy paths.
- ``edge`` and ``ev`` are returned in their own native unit. ``edge_pct``
  multiplies by 100 for UI display.

Why both ``edge`` and ``ev``? They answer different questions:

- ``edge``: "by how many percentage points does my probability beat the
  market?" — used to gate which picks we surface.
- ``ev``: "for each euro staked, how many euros do I expect to walk away
  with on average?" — used to size stakes (Kelly).

Master plan note: the UI must never display the two interchangeably.
"""

from __future__ import annotations

_MIN_ODDS = 1.01


def implied_prob(odds: float) -> float:
    """Return the bookmaker-implied probability (no overround stripping).

    Raises ``ValueError`` if ``odds < 1.01``.
    """
    if odds < _MIN_ODDS:
        raise ValueError(f"odds must be >= {_MIN_ODDS}, got {odds!r}")
    return 1.0 / odds


def implied_prob_pct(odds: float) -> float:
    """Implied probability in 0..100 percent form (UI helper)."""
    return implied_prob(odds) * 100.0


def edge(*, model_prob: float, odds: float) -> float:
    """Edge in probability units: ``model_prob - 1/odds``.

    Both inputs are validated:

    - ``model_prob`` must be in [0, 1].
    - ``odds`` must be >= 1.01.

    Returns a signed float in [-1, 1].
    """
    if not 0.0 <= model_prob <= 1.0:
        raise ValueError(f"model_prob must be in [0, 1], got {model_prob!r}")
    return model_prob - implied_prob(odds)


def edge_pct(*, model_prob: float, odds: float) -> float:
    """Edge expressed in percent form (e.g. 10.0 = +10pp). UI helper."""
    return edge(model_prob=model_prob, odds=odds) * 100.0


def ev(*, model_prob: float, odds: float) -> float:
    """Expected value per unit staked: ``model_prob * odds - 1``.

    Same validation as ``edge``.
    """
    if not 0.0 <= model_prob <= 1.0:
        raise ValueError(f"model_prob must be in [0, 1], got {model_prob!r}")
    if odds < _MIN_ODDS:
        raise ValueError(f"odds must be >= {_MIN_ODDS}, got {odds!r}")
    return model_prob * odds - 1.0


def edge_from_percent_proba(proba_pct: float, odds: float) -> float:
    """Drop-in replacement for the legacy ``_compute_edge`` in ticket_generator.

    Accepts ``proba_pct`` in 0..100 form. Returns ``0.0`` (not raises) for
    invalid inputs so the legacy filter loops can keep silently skipping
    bad rows during migration.
    """
    if odds <= 1.0 or proba_pct <= 0.0:
        return 0.0
    try:
        return edge(model_prob=proba_pct / 100.0, odds=odds)
    except ValueError:
        return 0.0
