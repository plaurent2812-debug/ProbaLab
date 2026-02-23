from __future__ import annotations
from datetime import datetime
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from config import supabase, api_get, logger
from brain import ask_claude

router = APIRouter(prefix="/api/trigger", tags=["Trigger"])

class AnalyzeRequest(BaseModel):
    fixture_id: str

SYSTEM_PROMPT = """Tu es un expert en paris sportifs spécialisé dans le Live Betting.
On te fournit les statistiques à la mi-temps d'un match (tirs, possession, etc.).
Ton but est de proposer une analyse courte et percutante (3 phrases max) si l'une des deux équipes est scandaleusement malchanceuse ou dominatrice, et de suggérer le meilleur pari Live.

IMPORTANT : Réponds UNIQUEMENT avec un JSON valide.
{
  "analysis_text": "L'équipe à domicile a eu 70% de possession et 8 tirs cadrés mais perd 0-1. Le match devrait tourner.",
  "recommended_bet": "Victoire Equipe Domicile ou Prochain But Domicile",
  "confidence_score": 8
}
"""

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
    """Fetches half-time stats, looks for anomalies, and triggers an AI analysis if needed."""
    logger.info(f"[Live] Analyze halftime triggered for fixture {req.fixture_id}")
    
    # 1. Get fixture from DB
    fixture_data = supabase.table("fixtures").select("*").eq("id", req.fixture_id).execute().data
    if not fixture_data:
        raise HTTPException(status_code=404, detail="Fixture not found")
        
    fixture = fixture_data[0]
    api_id = fixture["api_fixture_id"]
    
    # 2. Get live stats from API-Football
    # endpoint is fixtures/statistics
    stats_resp = api_get("fixtures/statistics", {"fixture": api_id})
    if not stats_resp or not stats_resp.get("response"):
        return {"status": "skipped", "message": "No live stats available"}
        
    stats_list = stats_resp["response"]
    if len(stats_list) < 2:
        return {"status": "skipped", "message": "Incomplete live stats"}

    # 3. Simple Anomaly Filter
    # Let's see if one team dominates shots on target but doesn't lead
    
    def get_stat(team_stats, stat_type):
        for s in team_stats["statistics"]:
            if s["type"] == stat_type:
                val = s["value"]
                if val is None: return 0
                if isinstance(val, str) and "%" in val:
                    return int(val.replace("%", ""))
                return int(val)
        return 0

    team1 = stats_list[0]
    team2 = stats_list[1]
    
    t1_shots = get_stat(team1, "Shots on Goal")
    t2_shots = get_stat(team2, "Shots on Goal")
    t1_xg = get_stat(team1, "expected_goals") # NOTE: API-Football doesn't always provide xG live
    t2_xg = get_stat(team2, "expected_goals")
    t1_poss = get_stat(team1, "Ball Possession")
    t2_poss = get_stat(team2, "Ball Possession")
    
    # Just an arbitrary rule for the anomaly filter: 
    # If a team has >= 4 more shots on goal than the other AND >= 60% possession
    # (Since we don't have live score in stats payload easily without another call, we'll assume it's interesting)
    
    anomaly = False
    if (t1_shots >= t2_shots + 4 and t1_poss >= 60) or (t2_shots >= t1_shots + 4 and t2_poss >= 60):
        anomaly = True
        
    if not anomaly:
        return {"status": "no_anomaly", "message": "Match looks balanced or not crazy enough."}
        
    # 4. Prompt AI
    user_prompt = f"""
MATCH: {fixture['home_team']} vs {fixture['away_team']}

STATISTIQUES MI-TEMPS:
[{team1['team']['name']}]
- Possession: {t1_poss}%
- Tirs Cadrés: {t1_shots}

[{team2['team']['name']}]
- Possession: {t2_poss}%
- Tirs Cadrés: {t2_shots}

Il y a eu une nette domination d'une équipe. 
Quel pari en direct recommandes-tu ? Retourne le JSON.
    """
    
    from brain import extract_json
    ai_text = ask_claude(SYSTEM_PROMPT, user_prompt)
    ai_result = extract_json(ai_text) if ai_text else None
    
    if not ai_result:
        return {"status": "error", "message": "AI failed to return valid JSON"}
        
    # 5. Save to live_alerts
    supabase.table("live_alerts").insert({
        "fixture_id": req.fixture_id,
        "analysis_text": ai_result.get("analysis_text", ""),
        "recommended_bet": ai_result.get("recommended_bet", ""),
        "confidence_score": ai_result.get("confidence_score", 5)
    }).execute()
    
    return {"status": "alert_created", "alert": ai_result}

