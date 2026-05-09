"""Provider health logging.

Master plan Phase 2.1. Every fetch to API-Football, The Odds API, NHL API,
etc. should log one row in `provider_health_log` so the admin endpoint
`/api/admin/data-health` can surface failures BEFORE the UI is empty.

Design:

- ``build_row``: pure, deterministic, redacts query-string secrets, decides
  whether the call counts as a success. HTTP 200 with ``row_count == 0`` is
  treated as a FAILURE by default — the only legit reason to flip that is
  ``empty_is_ok=True`` (e.g. NHL on a non-game day).
- ``log_call``: thin wrapper around the Supabase client that swallows any
  exception. A monitoring write must never break the pipeline.
- ``recent_failures``: read helper used by the admin endpoint.

The Supabase client is injected so callers can pass a mock. Production code
defaults to ``src.config.supabase``.
"""

from __future__ import annotations

import logging
import re
from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.parse import urlsplit, urlunsplit

logger = logging.getLogger(__name__)

_TABLE = "provider_health_log"
_VALID_SPORTS: frozenset[str] = frozenset({"football", "nhl"})
_SECRET_QUERY_KEYS = (
    "api_key",
    "apikey",
    "key",
    "token",
    "access_token",
    "secret",
)


def _redact_endpoint(endpoint: str) -> str:
    """Strip query-string secrets from an endpoint string before persisting it.

    Drops the entire query string when any sensitive key is present. We could
    keep the non-sensitive params, but stripping is safer and the endpoint
    column is meant for log triage, not exact replay.
    """
    parts = urlsplit(endpoint)
    if not parts.query:
        return endpoint
    lowered = parts.query.lower()
    if any(k in lowered for k in _SECRET_QUERY_KEYS):
        return urlunsplit((parts.scheme, parts.netloc, parts.path, "", parts.fragment))
    # Defensive sanity: the keys above can also appear inside path-style tokens.
    return re.sub(r"(api[_-]?key|token|secret)=[^&]+", r"\1=REDACTED", endpoint)


def build_row(
    *,
    provider: str,
    sport: str | None,
    endpoint: str,
    status_code: int | None,
    row_count: int | None,
    latency_ms: int | None,
    quota_remaining: int | None = None,
    plan_label: str | None = None,
    error: str | None = None,
    empty_is_ok: bool = False,
) -> dict[str, Any]:
    """Return the dict to insert into ``provider_health_log``.

    Raises ``ValueError`` if ``sport`` is provided but not one of the
    accepted values. ``None`` is accepted for non-sport meta calls.
    """
    if sport is not None and sport not in _VALID_SPORTS:
        raise ValueError(f"sport must be one of {sorted(_VALID_SPORTS)} or None, got {sport!r}")

    is_success = (
        status_code is not None
        and 200 <= status_code < 300
        and (empty_is_ok or (isinstance(row_count, int) and row_count > 0))
    )

    return {
        "provider": provider,
        "sport": sport,
        "endpoint": _redact_endpoint(endpoint),
        "status_code": status_code,
        "row_count": row_count,
        "latency_ms": latency_ms,
        "quota_remaining": quota_remaining,
        "plan_label": plan_label,
        "error": error,
        "is_success": is_success,
    }


def _resolve_client(client: Any) -> Any:
    if client is not None:
        return client
    # Lazy import to avoid pulling Supabase at module import time.
    from src.config import supabase  # noqa: PLC0415

    return supabase


def log_call(
    *,
    provider: str,
    sport: str | None,
    endpoint: str,
    status_code: int | None,
    row_count: int | None,
    latency_ms: int | None,
    quota_remaining: int | None = None,
    plan_label: str | None = None,
    error: str | None = None,
    empty_is_ok: bool = False,
    client: Any = None,
) -> None:
    """Persist one provider call to ``provider_health_log``.

    Never raises. Failure to persist is logged at WARNING level so a broken
    Supabase connection does not break the data pipeline.
    """
    try:
        row = build_row(
            provider=provider,
            sport=sport,
            endpoint=endpoint,
            status_code=status_code,
            row_count=row_count,
            latency_ms=latency_ms,
            quota_remaining=quota_remaining,
            plan_label=plan_label,
            error=error,
            empty_is_ok=empty_is_ok,
        )
    except Exception:
        logger.warning("provider_health: build_row failed", exc_info=True)
        return None

    try:
        target = _resolve_client(client)
        target.table(_TABLE).insert(row).execute()
    except Exception:
        logger.warning("provider_health: insert failed", exc_info=True)
    return None


def recent_failures(
    *,
    hours: int = 24,
    limit: int = 200,
    client: Any = None,
) -> list[dict[str, Any]]:
    """Return rows where ``is_success = false`` within the last ``hours``.

    Used by the admin endpoint. Read failures degrade gracefully to an empty
    list — the admin UI must not crash if the log table is unreachable.
    """
    try:
        target = _resolve_client(client)
        cutoff = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()
        result = (
            target.table(_TABLE)
            .select("*")
            .eq("is_success", False)
            .gte("recorded_at", cutoff)
            .order("recorded_at", desc=True)
            .limit(limit)
            .execute()
        )
        return list(result.data or [])
    except Exception:
        logger.warning("provider_health: recent_failures read failed", exc_info=True)
        return []
