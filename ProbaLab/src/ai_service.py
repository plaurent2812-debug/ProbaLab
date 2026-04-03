from __future__ import annotations

"""
ai_service.py — Gemini client, JSON extraction, and raw API call.

Responsibilities:
  - Lazy singleton Gemini client initialisation
  - ``extract_json`` : 4-fallback JSON parser
  - ``ask_gemini``   : send a (system, user) prompt pair to Gemini and
                       return the raw response text
"""

import json
import os
import re
import time

from google import genai
from google.genai import types

from src.config import GEMINI_API_KEY, logger

# ── Model constants ───────────────────────────────────────────────
MODEL_NAME: str = "gemini-2.5-flash"
TEMPERATURE: float = 0.2
MAX_OUTPUT_TOKENS: int = 4000

# ── Lazy singleton ────────────────────────────────────────────────
_gemini_client: genai.Client | None = None


def get_gemini_client() -> genai.Client | None:
    """Return the shared Gemini client, creating it on first call.

    Returns:
        A configured :class:`genai.Client` instance, or ``None`` when the
        ``GEMINI_API_KEY`` environment variable is absent.
    """
    global _gemini_client
    if _gemini_client is None:
        api_key = GEMINI_API_KEY or os.getenv("GEMINI_API_KEY")
        if not api_key:
            logger.critical("ERREUR: GEMINI_API_KEY manquante.")
            return None
        _gemini_client = genai.Client(api_key=api_key)
    return _gemini_client


# ═══════════════════════════════════════════════════════════════════
#  EXTRACTION JSON
# ═══════════════════════════════════════════════════════════════════


def extract_json(text: str) -> dict | None:
    """Extract a JSON object from a Gemini response string.

    Attempts four strategies in order:
      1. Direct ``json.loads`` on the whole text.
      2. Regex extraction of a fenced ``json`` code-block.
      3. Regex extraction of each ``{…}`` block (non-greedy, first valid).
      4. Ultra-fallback greedy ``{…}`` span.

    Args:
        text: Raw text returned by the Gemini API.

    Returns:
        Parsed JSON as a dict, or ``None`` if no valid JSON is found.
    """
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    m = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(1).strip())
        except (json.JSONDecodeError, ValueError):
            pass

    # Last resort: find all {…} blocks and try parsing each
    for m in re.finditer(r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}", text, re.DOTALL):
        try:
            return json.loads(m.group(0))
        except (json.JSONDecodeError, ValueError):
            continue

    # Ultra-fallback: greedy match (may grab too much but catches nested JSON)
    m = re.search(r"\{[\s\S]*\}", text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(0))
        except (json.JSONDecodeError, ValueError):
            pass

    return None


# ═══════════════════════════════════════════════════════════════════
#  APPEL GEMINI
# ═══════════════════════════════════════════════════════════════════


def ask_gemini(system_prompt: str, user_prompt: str) -> str | None:
    """Send an enriched prompt to the Gemini API and return the raw response.

    Retries once on failure with a 2-second backoff.

    Args:
        system_prompt: System-level instruction defining Gemini's role.
        user_prompt: User-level message containing the statistical data
            and analysis request.

    Returns:
        The text content of Gemini's reply, or ``None`` on API error.
    """
    gclient = get_gemini_client()
    if not gclient:
        return None

    for _attempt in range(2):
        try:
            response = gclient.models.generate_content(
                model=MODEL_NAME,
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=TEMPERATURE,
                    max_output_tokens=MAX_OUTPUT_TOKENS,
                    response_mime_type="application/json",
                ),
            )
            if response and response.text:
                return response.text
            logger.warning("Gemini attempt %d: response has no text", _attempt + 1)
        except Exception as e:
            logger.warning("Gemini attempt %d failed: %s", _attempt + 1, e)
        if _attempt == 0:
            time.sleep(2)

    return None
