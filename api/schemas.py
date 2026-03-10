"""
api/schemas.py — Pydantic models for API request validation.

Replaces raw `dict` parameters with typed, validated models.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


# ─── Email Endpoints ─────────────────────────────────────────────

class EmailPayload(BaseModel):
    email: str = Field(..., description="Recipient email address")
    name: str | None = Field(None, description="Recipient name (optional)")


# ─── Best Bets ───────────────────────────────────────────────────

class SaveBetRequest(BaseModel):
    date: str = Field(..., description="ISO date YYYY-MM-DD")
    sport: str = Field(..., description="'football' or 'nhl'")
    label: str = Field(..., description="Bet description label")
    market: str = Field(..., description="Bet market type")
    odds: float = Field(..., ge=1.0, description="Decimal odds")
    confidence: int = Field(..., ge=1, le=10, description="Confidence score 1-10")
    proba_model: float = Field(..., ge=0, le=100, description="Model probability %")
    fixture_id: int | str | None = Field(None, description="Fixture ID (optional)")
    player_name: str | None = Field(None, description="Player name for props")


class UpdateBetResultRequest(BaseModel):
    result: str = Field(..., description="WIN, LOSS, VOID, or PENDING")
    notes: str = Field("", description="Optional notes")


# ─── CRON / Pipeline ─────────────────────────────────────────────

class DateRequest(BaseModel):
    date: str | None = Field(None, description="ISO date YYYY-MM-DD (defaults to today)")


class ResolveBetsRequest(BaseModel):
    date: str = Field(..., description="ISO date YYYY-MM-DD")
    sport: str = Field(..., description="'football' or 'nhl'")


class ResolveExpertPicksRequest(BaseModel):
    date: str = Field(..., description="ISO date YYYY-MM-DD")
    sport: str | None = Field(None, description="'football' or 'nhl' (optional)")


class RunPipelineRequest(BaseModel):
    mode: str = Field("full", description="Pipeline mode: full, data, analyze, results, nhl")
