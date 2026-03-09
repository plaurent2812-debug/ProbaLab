"""
telegram_parser.py — Analyse un screenshot Winamax avec Gemini Vision.

Extrait:
  - player_name   : Nom du joueur (si paris joueur)
  - market        : Type de pari (ex: "Over 0.5 Points")
  - odds          : Cote décimale (ex: 2.45)
  - match_label   : "Équipe A vs Équipe B"
  - sport         : "nhl" | "football"
  - date          : YYYY-MM-DD (date du match détectée ou aujourd'hui)
  - expert_note   : Texte libre capturé (ex: caption envoyé avec l'image)
"""
from __future__ import annotations

import base64
import json
import logging
import os
import re
from datetime import datetime

logger = logging.getLogger("telegram_parser")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

SYSTEM_PROMPT = """Tu es un assistant expert en paris sportifs.
On te donne une capture d'écran de l'application Winamax (ou un bookmaker similaire).
Tu dois extraire les informations du pari visible et répondre UNIQUEMENT en JSON valide.

Champs à extraire :
- player_name (string | null) : nom complet du joueur si c'est un pari joueur
- market (string) : type de pari. Exemples: "Over 0.5 Points", "Buteur", "Victoire domicile", "Over 2.5 buts"
- odds (number | null) : cote décimale (ex: 2.45). null si non visible.
- match_label (string | null) : "Équipe A vs Équipe B" si visible
- sport (string) : "nhl" ou "football" selon le sport détecté
- date (string | null) : date du match au format YYYY-MM-DD si visible, sinon null

Réponds UNIQUEMENT avec le JSON, sans markdown, sans explication.
Exemple:
{"player_name":"Mikael Backlund","market":"Over 0.5 Points","odds":2.45,"match_label":"Washington Capitals vs Calgary Flames","sport":"nhl","date":null}
"""


def parse_winamax_screenshot(image_bytes: bytes, caption: str = "") -> dict:
    """
    Analyse une image de pari Winamax et retourne les champs extraits.

    Args:
        image_bytes: Image en bytes (JPEG/PNG)
        caption: Texte optionnel envoyé avec l'image par l'utilisateur

    Returns:
        dict avec les clés: player_name, market, odds, match_label, sport, date, expert_note
        ou {"error": "..."} en cas d'échec
    """
    if not GEMINI_API_KEY:
        logger.error("GEMINI_API_KEY non définie")
        return {"error": "GEMINI_API_KEY manquante"}

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=GEMINI_API_KEY)

        # Encode image en base64 pour Gemini
        image_b64 = base64.b64encode(image_bytes).decode("utf-8")

        user_text = "Analyse ce screenshot de pari Winamax."
        if caption:
            user_text += f"\n\nNote de l'expert : {caption}"

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_bytes(
                            data=image_bytes,
                            mime_type="image/jpeg",
                        ),
                        types.Part.from_text(text=user_text),
                    ],
                )
            ],
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=0.1,
                max_output_tokens=512,
            ),
        )

        raw_text = ""
        if response and response.candidates:
            for part in response.candidates[0].content.parts:
                if hasattr(part, "text") and part.text:
                    raw_text += part.text
        if not raw_text:
            raw_text = getattr(response, "text", "") or ""

        # Clean JSON (remove markdown fences if any)
        raw_text = raw_text.strip()
        if raw_text.startswith("```"):
            raw_text = re.sub(r"```[a-z]*\n?", "", raw_text).strip()
        if raw_text.endswith("```"):
            raw_text = raw_text[:-3].strip()

        parsed = json.loads(raw_text)

        # Ensure date fallback to today
        if not parsed.get("date"):
            parsed["date"] = datetime.utcnow().strftime("%Y-%m-%d")

        # Add expert note from caption
        parsed["expert_note"] = caption or ""

        logger.info(
            "Screenshot parsed: %s %s @%s",
            parsed.get("player_name") or parsed.get("market"),
            parsed.get("match_label", ""),
            parsed.get("odds"),
        )
        return parsed

    except json.JSONDecodeError as e:
        logger.error("JSON parse error: %s | raw: %s", e, raw_text[:200])
        return {"error": f"Impossible de parser la réponse Gemini: {e}"}
    except Exception as e:
        logger.error("Gemini Vision error: %s", e)
        return {"error": str(e)}


def format_confirmation_message(pick: dict) -> str:
    """Formatte le message de confirmation Telegram."""
    sport_emoji = "🏒" if pick.get("sport") == "nhl" else "⚽"
    lines = ["🎯 *Pick détecté :*", ""]

    if pick.get("player_name"):
        lines.append(f"👤 {pick['player_name']}")
    if pick.get("market"):
        lines.append(f"{sport_emoji} {pick['market']}")
    if pick.get("match_label"):
        lines.append(f"🏟 {pick['match_label']}")
    if pick.get("odds"):
        lines.append(f"💰 @{pick['odds']}")
    if pick.get("date"):
        lines.append(f"📅 {pick['date']}")
    if pick.get("expert_note"):
        lines.append(f"💬 _{pick['expert_note']}_")

    lines.extend(["", "Confirmer ? 👍 ou ❌"])
    return "\n".join(lines)
