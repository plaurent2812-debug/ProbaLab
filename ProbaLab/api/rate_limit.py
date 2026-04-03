"""
api/rate_limit.py — Shared rate-limiting decorator.

Wraps slowapi's limiter with a graceful fallback when slowapi is not installed.
Import `_rate_limit` from here in any router that needs rate limiting.
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

try:
    from slowapi import Limiter, _rate_limit_exceeded_handler  # noqa: F401
    from slowapi.errors import RateLimitExceeded  # noqa: F401
    from slowapi.util import get_remote_address

    limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])
    RATE_LIMITING = True
except ImportError:
    logging.critical(
        "SECURITY: slowapi is NOT installed — rate limiting is DISABLED. "
        "Install slowapi to enforce rate limits in production."
    )
    RATE_LIMITING = False
    limiter = None  # type: ignore[assignment]

_rate_limit_warned = False


def _rate_limit(limit_string: str):
    """Apply rate limiting if slowapi is available, otherwise log a warning."""
    if RATE_LIMITING and limiter:
        return limiter.limit(limit_string)

    def _noop_decorator(f):
        global _rate_limit_warned
        if not _rate_limit_warned:
            logger.warning(
                "SECURITY: rate limit '%s' not enforced — slowapi not installed",
                limit_string,
            )
            _rate_limit_warned = True
        return f

    return _noop_decorator
