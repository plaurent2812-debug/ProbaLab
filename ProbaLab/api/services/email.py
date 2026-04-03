"""
api/services/email.py — Resend email delivery utility.

Provides a low-level helper for sending transactional emails via the Resend API.
"""

from __future__ import annotations

import os

try:
    import httpx

    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False

RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")
RESEND_FROM = os.getenv("RESEND_FROM", "ProbaLab <noreply@probalab.fr>")


def _send_resend_email(to: str, subject: str, html: str) -> bool:
    """Send an email via Resend API. Returns True on success."""
    if not RESEND_API_KEY or not HTTPX_AVAILABLE:
        return False
    try:
        resp = httpx.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {RESEND_API_KEY}",
                "Content-Type": "application/json",
            },
            json={"from": RESEND_FROM, "to": [to], "subject": subject, "html": html},
            timeout=10.0,
        )
        return resp.status_code in (200, 201)
    except Exception:
        return False
