import os
from datetime import datetime
from config import supabase, logger

def calculate_implied_odds(probability: int) -> float:
    """Calculates the implied odds for a given probability with an assumed bookmaker margin.
    
    Returns:
        float: Estimated odds (e.g., 2.10). Returns 1.01 if calculation fails.
    """
    if not probability or probability <= 0:
        return 0.0
    
    # Typical bookmaker margin is roughly 5% to 8%, so we take 0.95 
    real_prob = probability / 100.0
    # Avoid extremely high odds or division by zero
    if real_prob < 0.05:
        real_prob = 0.05
        
    estimated_odds = (1 / real_prob) * 0.95
    return round(estimated_odds, 2)

def generate_daily_tickets():
    """Fetches today's fixtures and generates Safe and Fun tickets."""
    today = datetime.now().strftime("%Y-%m-%d")
    
    # 1. Fetch today's fixtures
    fixtures_resp = (
        supabase.table("fixtures")
        .select("id, api_fixture_id, home_team, away_team, date, league_id")
        .like("date", f"{today}%")
        .neq("status", "PST")
        .neq("status", "CANC")
        .execute()
    )
    
    if not fixtures_resp or not fixtures_resp.data:
        logger.info("Aucun match trouvé pour aujourd'hui.")
        return None, None
        
    todays_fixture_ids = [f["id"] for f in fixtures_resp.data]
    
    # 2. Fetch predictions
    preds_resp = (
        supabase.table("predictions")
        .select("*")
        .in_("fixture_id", todays_fixture_ids)
        .order("confidence_score", desc=True)
        .execute()
    )
    
    if not preds_resp or not preds_resp.data:
        logger.info("Aucune prédiction générée pour aujourd'hui.")
        return None, None
        
    predictions = preds_resp.data
    fixture_map = {f["id"]: f for f in fixtures_resp.data}
    
    return build_safe_ticket(predictions, fixture_map), build_fun_ticket(predictions, fixture_map)
    

def get_best_market(pred: dict) -> dict:
    """Picks the safest market for a given prediction based on probas."""
    markets = []
    
    # 1X2 Probabilities
    if pred.get("proba_home", 0) > 0: markets.append({"name": "Victoire Domicile", "proba": pred["proba_home"]})
    if pred.get("proba_draw", 0) > 0: markets.append({"name": "Match Nul", "proba": pred["proba_draw"]})
    if pred.get("proba_away", 0) > 0: markets.append({"name": "Victoire Extérieur", "proba": pred["proba_away"]})
    
    # Recommended Bet Override (If it's explicitly recommended and highly rated)
    rec = pred.get("recommended_bet")
    if rec and "Victoire" in rec:
         return {"name": rec, "proba": max([pred.get("proba_home", 0), pred.get("proba_away", 0)])}
    elif rec and "Over" in rec:
         pass # Let the next block handle goals
         
    # Goals Probabilities
    if pred.get("proba_btts", 0) > 0: markets.append({"name": "Les deux marquent (Oui)", "proba": pred["proba_btts"]})
    if pred.get("proba_over_15", 0) > 0: markets.append({"name": "Plus de 1.5 buts", "proba": pred["proba_over_15"]})
    if pred.get("proba_over_25", 0) > 0: markets.append({"name": "Plus de 2.5 buts", "proba": pred["proba_over_25"]})
    
    # Sort and pick the absolute highest probability event
    best = sorted(markets, key=lambda x: x["proba"], reverse=True)
    if not best:
        return {"name": "Inconnu", "proba": 0}
        
    return best[0]


def build_safe_ticket(predictions: list, fixture_map: dict) -> dict:
    """Builds a ticket targeting cumulative odds of ~2.0 to 3.0"""
    # Filter highly confident predictions only
    confident_preds = [p for p in predictions if (p.get("confidence_score") or 0) >= 5]
    
    ticket_matches = []
    total_odds = 1.0
    
    for pred in confident_preds:
        fix = fixture_map.get(pred["fixture_id"])
        if not fix: continue
        
        market = get_best_market(pred)
        if market["proba"] < 60: 
            # Too risky for a SAFE ticket (implies odds > 1.6)
            continue
            
        odds = calculate_implied_odds(market["proba"])
        if odds == 0.0: continue
        
        ticket_matches.append({
            "match": f"{fix['home_team']} - {fix['away_team']}",
            "time": fix['date'][11:16],
            "pick": market["name"],
            "proba": market["proba"],
            "odds": odds
        })
        
        total_odds *= odds
        if total_odds >= 2.0:
            break
            
    if len(ticket_matches) == 0:
        return None
        
    return {
        "type": "SAFE",
        "matches": ticket_matches,
        "total_odds": round(total_odds, 2)
    }


def build_fun_ticket(predictions: list, fixture_map: dict) -> dict:
    """Builds a ticket targeting cumulative odds of ~20.0"""
    # Sort essentially randomly, or pick somewhat confident ones
    fun_preds = [p for p in predictions if 4 <= (p.get("confidence_score") or 0) <= 8]
    if not fun_preds:
        fun_preds = predictions # Fallback
        
    ticket_matches = []
    total_odds = 1.0
    
    # To hit 20 odds, we might need 4-6 matches
    for pred in fun_preds:
        fix = fixture_map.get(pred["fixture_id"])
        if not fix: continue
        
        market = get_best_market(pred)
        # Avoid extremely obvious bets so we actually build odds
        # Keep probs between 45% and 75%
        if not (45 <= market["proba"] <= 75):
            continue
            
        odds = calculate_implied_odds(market["proba"])
        if odds == 0.0: continue
        
        # Don't add duplicate matches (in case it was in safe)
        if any(m["match"] == f"{fix['home_team']} - {fix['away_team']}" for m in ticket_matches):
            continue
            
        ticket_matches.append({
            "match": f"{fix['home_team']} - {fix['away_team']}",
            "time": fix['date'][11:16],
            "pick": market["name"],
            "proba": market["proba"],
            "odds": odds
        })
        
        total_odds *= odds
        if total_odds >= 18.0:
            break
            
    if len(ticket_matches) < 3: # Not fun enough
        return None
        
    return {
        "type": "FUN",
        "matches": ticket_matches,
        "total_odds": round(total_odds, 2)
    }

def format_telegram_message(safe_ticket: dict, fun_ticket: dict) -> str:
    """Formats the tickets into HTML for Telegram"""
    
    msg = "🏆 <b>LES PRONOS VIP DU JOUR</b> 🏆\n"
    msg += f"<i>Généré par l'IA ProbaLab - {datetime.now().strftime('%d/%m/%Y')}</i>\n\n"
    
    if safe_ticket:
        msg += "🛡 <b>TICKET SAFE (Objectif Doubler)</b>\n"
        for m in safe_ticket["matches"]:
            msg += f"• <code>{m['time']}</code> | {m['match']}\n"
            msg += f"  👉 <b>{m['pick']}</b> <i>(Cote estimée: {m['odds']})</i>\n"
        msg += f"\n📊 <b>Cote Totale ~ {safe_ticket['total_odds']}</b>\n\n"
    else:
        msg += "🛡 <i>Pas de Ticket Safe au programme aujourd'hui. L'IA juge les matchs trop risqués.</i>\n\n"
        
    if fun_ticket:
        msg += "🔥 <b>TICKET FUN (Grosse Cote)</b>\n"
        for m in fun_ticket["matches"]:
            msg += f"• <code>{m['time']}</code> | {m['match']}\n"
            msg += f"  👉 <b>{m['pick']}</b> <i>(Cote estimée: {m['odds']})</i>\n"
        msg += f"\n🚀 <b>Cote Totale ~ {fun_ticket['total_odds']}</b>\n\n"
        
    msg += "<i>⚠️ Jouez uniquement ce que vous pouvez vous permettre de perdre. Les cotes sont des estimations mathématiques.</i>"
    return msg

if __name__ == "__main__":
    from telegram_bot import send_telegram_message
    
    safe, fun = generate_daily_tickets()
    if not safe and not fun:
        print("Aucun ticket généré.")
    else:
        message = format_telegram_message(safe, fun)
        print(message)
        
        # Test the send module
        if os.getenv("TELEGRAM_BOT_TOKEN") and os.getenv("TELEGRAM_CHANNEL_ID"):
            send_telegram_message(message)
