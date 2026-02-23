from __future__ import annotations
import os
from datetime import datetime
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from config import supabase, api_get, logger
from brain import ask_claude, extract_json

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False

# ─── Telegram Config ────────────────────────────────────────────
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8313502721:AAFOlAmD3zyiz8P143Kc16XcArBg-4g3AzY")
TELEGRAM_CHAT_IDS = os.getenv("TELEGRAM_CHAT_IDS", "5721158019,7003371099").split(",")


def _send_telegram_alert(home: str, away: str, analysis: str, bet: str, confidence: int) -> bool:
    """Send a Telegram message to all registered chat IDs."""
    if not HTTPX_AVAILABLE or not TELEGRAM_BOT_TOKEN:
        logger.warning("[Telegram] httpx not available or no token")
        return False

    message = (
        f"🔥 *ALERTE LIVE — ProbaLab*\n\n"
        f"⚽ *{home} vs {away}*\n\n"
        f"{analysis}\n\n"
        f"💰 *Pari suggéré :* {bet}\n"
        f"📊 *Confiance :* {confidence}/10"
    )

    sent = False
    for chat_id in TELEGRAM_CHAT_IDS:
        chat_id = chat_id.strip()
        if not chat_id:
            continue
        try:
            resp = httpx.post(
                f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                json={
                    "chat_id": chat_id,
                    "text": message,
                    "parse_mode": "Markdown",
                },
                timeout=10.0,
            )
            if resp.status_code == 200:
                logger.info(f"[Telegram] ✅ Message envoyé à {chat_id}")
                sent = True
            else:
                logger.error(f"[Telegram] Erreur {resp.status_code}: {resp.text}")
        except Exception as e:
            logger.error(f"[Telegram] Erreur envoi à {chat_id}: {e}")
    return sent

router = APIRouter(prefix="/api/trigger", tags=["Trigger"])

class AnalyzeRequest(BaseModel):
    fixture_id: str

SYSTEM_PROMPT = """Tu es un expert en paris sportifs spécialisé dans le Live Betting.
On te fournit les statistiques à la mi-temps d'un match (tirs, possession, xG, corners, score).
Ton but est de proposer une analyse courte et percutante (3 phrases max) si tu détectes
une anomalie statistique exploitable, et de suggérer le meilleur pari Live.

IMPORTANT : Réponds UNIQUEMENT avec un JSON valide.
{
  "analysis_text": "L'équipe à domicile a 1.8 xG mais 0 but, 8 tirs cadrés et 70% de possession. Le match devrait tourner en seconde période.",
  "recommended_bet": "Victoire Equipe Domicile ou Prochain But Domicile",
  "confidence_score": 8
}
"""

# ─── Helper ─────────────────────────────────────────────────────
def _get_stat(team_stats: dict, stat_type: str) -> float:
    """Extract a stat value from API-Football statistics response."""
    for s in team_stats.get("statistics", []):
        if s["type"] == stat_type:
            val = s["value"]
            if val is None:
                return 0.0
            if isinstance(val, str) and "%" in val:
                return float(val.replace("%", ""))
            try:
                return float(val)
            except (ValueError, TypeError):
                return 0.0
    return 0.0


def _detect_anomalies(t1: dict, t2: dict, score_home: int, score_away: int) -> list[str]:
    """Multi-criteria anomaly detection. Returns a list of triggered anomaly labels.
    An alert is fired if >= 2 anomalies are detected.
    """
    anomalies = []

    t1_shots = _get_stat(t1, "Shots on Goal")
    t2_shots = _get_stat(t2, "Shots on Goal")
    t1_xg = _get_stat(t1, "expected_goals")
    t2_xg = _get_stat(t2, "expected_goals")
    t1_poss = _get_stat(t1, "Ball Possession")
    t2_poss = _get_stat(t2, "Ball Possession")
    t1_corners = _get_stat(t1, "Corner Kicks")
    t2_corners = _get_stat(t2, "Corner Kicks")
    t1_total_shots = _get_stat(t1, "Total Shots")
    t2_total_shots = _get_stat(t2, "Total Shots")

    t1_name = t1.get("team", {}).get("name", "Team1")
    t2_name = t2.get("team", {}).get("name", "Team2")

    # ── Critère 1 : xG élevé mais aucun but ──────────────────────
    if t1_xg >= 1.2 and score_home == 0:
        anomalies.append(f"{t1_name} a {t1_xg} xG mais 0 but")
    if t2_xg >= 1.2 and score_away == 0:
        anomalies.append(f"{t2_name} a {t2_xg} xG mais 0 but")

    # ── Critère 2 : Domination aux tirs cadrés ───────────────────
    if t1_shots >= t2_shots + 4:
        anomalies.append(f"{t1_name} domine aux tirs cadrés ({int(t1_shots)} vs {int(t2_shots)})")
    elif t2_shots >= t1_shots + 4:
        anomalies.append(f"{t2_name} domine aux tirs cadrés ({int(t2_shots)} vs {int(t1_shots)})")

    # ── Critère 3 : Score inversé (équipe dominante perd ou fait nul) ──
    t1_dominance = (t1_shots > t2_shots + 2) and (t1_poss >= 55)
    t2_dominance = (t2_shots > t1_shots + 2) and (t2_poss >= 55)
    if t1_dominance and score_home <= score_away:
        anomalies.append(f"{t1_name} domine mais ne mène pas ({score_home}-{score_away})")
    if t2_dominance and score_away <= score_home:
        anomalies.append(f"{t2_name} domine mais ne mène pas ({score_home}-{score_away})")

    # ── Critère 4 : Écart de corners flagrant (pression constante) ──
    if t1_corners >= t2_corners + 5:
        anomalies.append(f"{t1_name} a {int(t1_corners)} corners vs {int(t2_corners)}")
    elif t2_corners >= t1_corners + 5:
        anomalies.append(f"{t2_name} a {int(t2_corners)} corners vs {int(t1_corners)}")

    # ── Critère 5 : Volume de tirs total écrasant ────────────────
    if t1_total_shots >= t2_total_shots + 8:
        anomalies.append(f"{t1_name} a tiré {int(t1_total_shots)} fois vs {int(t2_total_shots)}")
    elif t2_total_shots >= t1_total_shots + 8:
        anomalies.append(f"{t2_name} a tiré {int(t2_total_shots)} fois vs {int(t1_total_shots)}")

    return anomalies


# ─── Routes ─────────────────────────────────────────────────────

@router.get("/daily-matches")
def get_daily_matches():
    """Returns all matches planned for today that haven't started yet."""
    today = datetime.now().strftime("%Y-%m-%d")
    fixtures = (
        supabase.table("fixtures")
        .select("id, api_fixture_id, date, home_team, away_team")
        .gte("date", f"{today}T00:00:00Z")
        .lt("date", f"{today}T23:59:59Z")
        .in_("status", ["NS", "TBD"])
        .execute()
        .data or []
    )
    return {"date": today, "matches": fixtures}


@router.post("/analyze-halftime")
def analyze_halftime(req: AnalyzeRequest):
    """Fetches half-time stats, detects anomalies with multi-criteria, and triggers AI if needed."""
    logger.info(f"[Live] Analyze halftime triggered for fixture {req.fixture_id}")

    # 1. Get fixture from DB
    fixture_data = supabase.table("fixtures").select("*").eq("id", req.fixture_id).execute().data
    if not fixture_data:
        raise HTTPException(status_code=404, detail="Fixture not found")

    fixture = fixture_data[0]
    api_id = fixture["api_fixture_id"]

    # 2. Get live stats from API-Football
    stats_resp = api_get("fixtures/statistics", {"fixture": api_id})
    if not stats_resp or not stats_resp.get("response"):
        return {"status": "skipped", "message": "No live stats available"}

    stats_list = stats_resp["response"]
    if len(stats_list) < 2:
        return {"status": "skipped", "message": "Incomplete live stats"}

    team1 = stats_list[0]
    team2 = stats_list[1]

    # 3. Get current score from API-Football
    score_resp = api_get("fixtures", {"id": api_id})
    score_home, score_away = 0, 0
    if score_resp and score_resp.get("response"):
        goals = score_resp["response"][0].get("goals", {})
        score_home = goals.get("home", 0) or 0
        score_away = goals.get("away", 0) or 0

    # 4. Multi-criteria anomaly detection (need >= 2 triggers)
    anomalies = _detect_anomalies(team1, team2, score_home, score_away)
    logger.info(f"[Live] {fixture['home_team']} vs {fixture['away_team']}: {len(anomalies)} anomalies détectées")

    if len(anomalies) < 2:
        return {
            "status": "no_anomaly",
            "anomalies_found": len(anomalies),
            "details": anomalies,
            "message": "Pas assez d'anomalies détectées (minimum 2 requises).",
        }

    # 5. Build rich prompt for Claude
    t1_name = team1.get("team", {}).get("name", fixture["home_team"])
    t2_name = team2.get("team", {}).get("name", fixture["away_team"])

    user_prompt = f"""
MATCH: {fixture['home_team']} vs {fixture['away_team']}
SCORE MI-TEMPS: {score_home} - {score_away}

STATISTIQUES MI-TEMPS:
[{t1_name}]
- Possession: {_get_stat(team1, 'Ball Possession')}%
- Tirs Cadrés: {int(_get_stat(team1, 'Shots on Goal'))}
- Tirs Totaux: {int(_get_stat(team1, 'Total Shots'))}
- xG: {_get_stat(team1, 'expected_goals')}
- Corners: {int(_get_stat(team1, 'Corner Kicks'))}

[{t2_name}]
- Possession: {_get_stat(team2, 'Ball Possession')}%
- Tirs Cadrés: {int(_get_stat(team2, 'Shots on Goal'))}
- Tirs Totaux: {int(_get_stat(team2, 'Total Shots'))}
- xG: {_get_stat(team2, 'expected_goals')}
- Corners: {int(_get_stat(team2, 'Corner Kicks'))}

ANOMALIES DÉTECTÉES:
{chr(10).join(f'⚠️ {a}' for a in anomalies)}

Analyse ces anomalies et recommande le meilleur pari en direct. Retourne le JSON.
    """

    ai_text = ask_claude(SYSTEM_PROMPT, user_prompt)
    ai_result = extract_json(ai_text) if ai_text else None

    if not ai_result:
        return {"status": "error", "message": "AI failed to return valid JSON"}

    # 6. Save to live_alerts
    alert_text = ai_result.get("analysis_text", "")
    alert_bet = ai_result.get("recommended_bet", "")
    alert_confidence = ai_result.get("confidence_score", 5)

    supabase.table("live_alerts").insert({
        "fixture_id": req.fixture_id,
        "analysis_text": alert_text,
        "recommended_bet": alert_bet,
        "confidence_score": alert_confidence
    }).execute()

    # 7. Send Telegram notification
    _send_telegram_alert(
        home=fixture["home_team"],
        away=fixture["away_team"],
        analysis=alert_text,
        bet=alert_bet,
        confidence=alert_confidence,
    )

    logger.info(f"[Live] 🔥 ALERTE CRÉÉE pour {fixture['home_team']} vs {fixture['away_team']}")
    return {"status": "alert_created", "anomalies": anomalies, "alert": ai_result}


# ─── Live Scores Update ─────────────────────────────────────────

@router.post("/update-live-scores")
def update_live_scores():
    """Fetch all live scores from API-Football and update Supabase fixtures table."""
    logger.info("[Live Scores] Fetching live fixtures...")

    resp = api_get("fixtures", {"live": "all"})
    if not resp or not resp.get("response"):
        return {"status": "no_live_matches", "updated": 0}

    live_fixtures = resp["response"]
    updated = 0
    errors = 0

    for lf in live_fixtures:
        api_fixture_id = lf.get("fixture", {}).get("id")
        goals = lf.get("goals", {})
        home_goals = goals.get("home")
        away_goals = goals.get("away")
        status_short = lf.get("fixture", {}).get("status", {}).get("short", "")

        if not api_fixture_id:
            continue

        try:
            # Map API status to our status codes
            status_map = {
                "1H": "1H", "HT": "HT", "2H": "2H",
                "ET": "ET", "P": "PEN", "FT": "FT",
                "AET": "FT", "PEN": "FT",
                "BT": "BT", "SUSP": "SUSP", "INT": "INT",
                "LIVE": "LIVE",
            }
            our_status = status_map.get(status_short, status_short)

            result = (
                supabase.table("fixtures")
                .update({
                    "home_goals": home_goals,
                    "away_goals": away_goals,
                    "status": our_status,
                })
                .eq("api_fixture_id", api_fixture_id)
                .execute()
            )
            if result.data:
                updated += 1
        except Exception as e:
            logger.error(f"[Live Scores] Error updating fixture {api_fixture_id}: {e}")
            errors += 1

    logger.info(f"[Live Scores] ✅ {updated} scores mis à jour, {errors} erreurs")
    return {"status": "ok", "updated": updated, "errors": errors, "total_live": len(live_fixtures)}
