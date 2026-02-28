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
    start_of_day = f"{today}T00:00:00Z"
    end_of_day = f"{today}T23:59:59Z"
    
    fixtures_resp = (
        supabase.table("fixtures")
        .select("id, api_fixture_id, home_team, away_team, date, league_id")
        .gte("date", start_of_day)
        .lte("date", end_of_day)
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
    """Picks a safe and high-probability market, prioritizing Double Chance for safety."""
    markets = []
    
    ph = pred.get("proba_home") or 0
    pd = pred.get("proba_draw") or 0
    pa = pred.get("proba_away") or 0
    p15 = pred.get("proba_over_15") or 0

    # 1. Double Chance (Much safer than Win only)
    # 1X = Home or Draw
    p1x = ph + pd
    if p1x > 65:
        # Combined with Over 1.5 if both are strong
        if p15 > 70:
            # P(1X & +1.5) estimate
            p_comb = min(p1x, p15) * 0.90
            markets.append({"name": "Victoire ou Nul & +1.5 buts", "proba": p_comb, "priority": 2})
        markets.append({"name": "Victoire ou Nul", "proba": p1x, "priority": 1})

    # X2 = Away or Draw
    px2 = pa + pd
    if px2 > 65:
        if p15 > 70:
            p_comb = min(px2, p15) * 0.90
            markets.append({"name": "Nul ou Victoire Ext. & +1.5 buts", "proba": p_comb, "priority": 2})
        markets.append({"name": "Nul ou Victoire Ext.", "proba": px2, "priority": 1})

    # 2. Resultat Sec (Only if very high confidence, > 75%)
    if ph > 75: markets.append({"name": "Victoire Domicile", "proba": ph})
    if pa > 75: markets.append({"name": "Victoire Extérieur", "proba": pa})
    
    # 3. Recommended Bet Override (If it's explicitly recommended) - higher priority
    rec = pred.get("recommended_bet")
    if rec:
         # Try to map existing recommendations
         if "Victoire" in rec and (ph > 60 or pa > 60):
              markets.append({"name": rec, "proba": max(ph, pa), "priority": 1})
         
    # 4. Goals Probabilities
    if (pred.get("proba_btts") or 0) > 70: 
        markets.append({"name": "Les deux marquent", "proba": pred["proba_btts"]})
    if p15 > 80: 
        markets.append({"name": "Plus de 1.5 buts", "proba": p15})
    
    # Sort by probability, but prioritize items with "priority" field or combined markets
    # Note: We prioritize proba for safety in the "SAFE" ticket. 
    # But for the "FUN" ticket, we'll pick from the list differently.
    
    if not markets:
        # Fallback to the absolute safest
        return {"name": "Double Chance (1X)", "proba": p1x if p1x > px2 else px2}
        
    return sorted(markets, key=lambda x: (x.get("priority", 0), x["proba"]), reverse=True)[0]


def build_safe_ticket(predictions: list, fixture_map: dict) -> dict:
    """Builds a ticket targeting cumulative odds of ~2.0 by combining ~1.40 odds."""
    # Filter highly confident predictions
    confident_preds = [p for p in predictions if (p.get("confidence_score") or 0) >= 4]
    
    ticket_matches = []
    total_odds = 1.0
    
    for pred in confident_preds:
        fix = fixture_map.get(pred["fixture_id"])
        if not fix: continue
        
        market = get_best_market(pred)
        odds = calculate_implied_odds(market["proba"])
        
        # User Rule: No odds below 1.30
        if odds < 1.30:
            continue
            
        ticket_matches.append({
            "match": f"{fix['home_team']} - {fix['away_team']}",
            "time": fix['date'][11:16],
            "pick": market["name"],
            "proba": market["proba"],
            "odds": odds
        })
        
        total_odds *= odds
        # Aim for ~2.0 by combining usually 2 matches of ~1.40
        if total_odds >= 1.90:
            break
            
    if len(ticket_matches) < 2:
        return None
        
    return {
        "type": "SAFE",
        "matches": ticket_matches,
        "total_odds": round(total_odds, 2)
    }


def build_fun_ticket(predictions: list, fixture_map: dict) -> dict:
    """Builds a ticket targeting cumulative odds of ~20.0 with no odds below 1.30."""
    fun_preds = predictions 
        
    ticket_matches = []
    total_odds = 1.0
    
    for pred in fun_preds:
        fix = fixture_map.get(pred["fixture_id"])
        if not fix: continue
        
        market = get_best_market(pred)
        odds = calculate_implied_odds(market["proba"])
        
        # User Rule: No odds below 1.30
        if odds < 1.30:
            continue
            
        # Don't add duplicate matches
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
        if total_odds >= 20.0:
            break
            
    if len(ticket_matches) < 4:
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
