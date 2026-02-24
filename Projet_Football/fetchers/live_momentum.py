"""
Live Momentum Tracker pour le Football.
Analyse les matchs en cours (en temps réel) pour repérer les "Tempêtes" (domination soudaine).
1. Récupère les matchs 'Live' pour NOS ligues.
2. Pour chaque match, récupère les statistiques détaillées (tirs, corners).
3. Compare avec T-5 et T-10 minutes (stockés via Supabase).
4. Envoie une alerte Telegram si un momentum important est détecté.
"""

import os
import sys
import json
import time
from datetime import datetime, timezone
from pathlib import Path

# Ajouter la racine au path pour les imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import supabase, logger, api_get, LEAGUES

# On restreint la surveillance aux ligues majeures pour économiser les quotas API
LEAGUE_IDS = "-".join([str(l["id"]) for l in LEAGUES])

# Seuils pour déclencher une alerte Momentum (sur une fenêtre de 10 min par exemple)
MOMENTUM_THRESHOLD_SHOTS_ON_TARGET = 3
MOMENTUM_THRESHOLD_CORNERS = 2

def get_live_fixtures():
    """Récupère les IDs des matchs actuellement en live dans nos ligues."""
    # On précise nos ligues pour ne pas récupérer les 3e divisions ouziébeks
    data = api_get("fixtures", {"live": LEAGUE_IDS})
    if not data or not data.get("response"):
        return []
    
    fixtures = []
    # Filtrer ceux qui sont vraiment en train de jouer (1H, 2H, ET...)
    for item in data["response"]:
        status = item.get("fixture", {}).get("status", {}).get("short", "")
        if status in ["1H", "2H", "HT", "ET", "P", "LIVE"]:
            fixtures.append({
                "fixture_id": item["fixture"]["id"],
                "home_team": item["teams"]["home"]["name"],
                "away_team": item["teams"]["away"]["name"],
                "elapsed": item["fixture"]["status"]["elapsed"],
                "goals_home": item["goals"]["home"],
                "goals_away": item["goals"]["away"]
            })
    return fixtures

def get_live_statistics(fixture_id):
    """Récupère les statistiques détaillées d'un match."""
    data = api_get("fixtures/statistics", {"fixture": fixture_id})
    if not data or not data.get("response"):
        return None
    
    # Transformer la réponse en un dictionnaire facile à lire
    stats_dict = {"home": {}, "away": {}}
    try:
        home_data = data["response"][0]
        away_data = data["response"][1]
        
        for item in home_data["statistics"]:
            stats_dict["home"][item["type"]] = item["value"] if item["value"] is not None else 0
        for item in away_data["statistics"]:
            stats_dict["away"][item["type"]] = item["value"] if item["value"] is not None else 0
            
    except (IndexError, KeyError) as e:
        logger.warning(f"Impossible de parser les statistiques de {fixture_id}: {e}")
        return None
        
    return stats_dict

def extract_key_stats(stats_dict):
    """Extrait les stats clés qui composent le Momentum : Tirs Cadrés, Corners, Attaques Dangereuses."""
    if not stats_dict:
        return {"home": {}, "away": {}}
        
    def _get(team_stats):
        return {
            "shots_on_target": int(team_stats.get("Shots on Goal", 0)),
            "corners": int(team_stats.get("Corner Kicks", 0)),
            "dangerous_attacks": int(team_stats.get("Dangerous Attacks", 0))
        }
        
    return {
        "home": _get(stats_dict["home"]),
        "away": _get(stats_dict["away"])
    }

def update_momentum_cache(fixture_id, current_elapsed, current_stats):
    """Maintenir l'historique des stats dans une table séparée pour calculer le Delta."""
    now = datetime.now(timezone.utc).isoformat()
    
    # 1. On cherche s'il existe déjà un record pour ce match
    result = supabase.table("football_momentum_cache").select("*").eq("api_fixture_id", fixture_id).execute()
    data = result.data
    
    if not data:
        # Créer le premier record
        history = [{"elapsed": current_elapsed, "stats": current_stats, "timestamp": now}]
        supabase.table("football_momentum_cache").insert({
            "api_fixture_id": fixture_id,
            "stats_history": history,
            "last_updated": now
        }).execute()
        return None, history # Pas de momentum mesurable tout de suite
        
    # 2. Le record existe, on le met à jour
    record = data[0]
    history = record.get("stats_history", [])
    
    # On ajoute la stat actuelle
    history.append({"elapsed": current_elapsed, "stats": current_stats, "timestamp": now})
    
    # On garde seulement les 3 ou 4 dernières mesures (ex: T-0, T-5, T-10, T-15) pour pas saturer la BDD
    if len(history) > 4:
        history.pop(0)
        
    supabase.table("football_momentum_cache").update({
        "stats_history": history,
        "last_updated": now
    }).eq("api_fixture_id", fixture_id).execute()
    
    # 3. Calcul du Momentum
    # On compare la situation actuelle (index -1) avec la situation il y a 2 itérations (index -3 ou -2, environ T-10 mins)
    
    if len(history) < 2:
        return None, history
        
    past_state = history[0] # Le plus vieux qu'on a gardé
    
    delta_home = {
        "shots_on_target": current_stats["home"]["shots_on_target"] - past_state["stats"]["home"]["shots_on_target"],
        "corners": current_stats["home"]["corners"] - past_state["stats"]["home"]["corners"],
        "dangerous_attacks": current_stats["home"]["dangerous_attacks"] - past_state["stats"]["home"]["dangerous_attacks"]
    }
    
    delta_away = {
        "shots_on_target": current_stats["away"]["shots_on_target"] - past_state["stats"]["away"]["shots_on_target"],
        "corners": current_stats["away"]["corners"] - past_state["stats"]["away"]["corners"],
        "dangerous_attacks": current_stats["away"]["dangerous_attacks"] - past_state["stats"]["away"]["dangerous_attacks"]
    }
    
    time_diff = current_elapsed - past_state["elapsed"]
    
    return {
        "time_window": time_diff,
        "delta_home": delta_home,
        "delta_away": delta_away
    }, history

def run_momentum_tracker():
    logger.info("🌪️ [Momentum Tracker] Scan des matchs live en cours...")
    
    live_fixtures = get_live_fixtures()
    if not live_fixtures:
        logger.info("[Momentum Tracker] Aucun match en cours dans nos ligues.")
        return {"status": "ok", "matches_analyzed": 0, "alerts_sent": 0}
        
    logger.info(f"[Momentum Tracker] {len(live_fixtures)} match(s) en cours de jeu.")
    alerts = []
    
    for fix in live_fixtures:
        fid = fix["fixture_id"]
        elapsed = fix["elapsed"]
        home = fix["home_team"]
        away = fix["away_team"]
        
        # 1. Choper les statistiques du match
        raw_stats = get_live_statistics(fid)
        if not raw_stats:
            continue
            
        current_stats = extract_key_stats(raw_stats)
        
        # 2. Mettre à jour le cache et évaluer le momentum
        momentum, history = update_momentum_cache(fid, elapsed, current_stats)
        
        if not momentum:
            continue
            
        # 3. Détecter l'Alerte Tempête
        d_home = momentum["delta_home"]
        d_away = momentum["delta_away"]
        time_win = momentum["time_window"]
        
        # S'il s'est passé moins de 3 minutes depuis la dernière stat, c'est trop court
        if time_win < 3:
            continue
            
        storm_home = (d_home["shots_on_target"] >= MOMENTUM_THRESHOLD_SHOTS_ON_TARGET and 
                     d_home["corners"] >= MOMENTUM_THRESHOLD_CORNERS)
                     
        storm_away = (d_away["shots_on_target"] >= MOMENTUM_THRESHOLD_SHOTS_ON_TARGET and 
                     d_away["corners"] >= MOMENTUM_THRESHOLD_CORNERS)
                     
        if storm_home:
            alerts.append({
                "match": f"{home} {fix['goals_home']}-{fix['goals_away']} {away}",
                "elapsed": elapsed,
                "team_on_fire": home,
                "time_window": time_win,
                "stats_added": f"+{d_home['shots_on_target']} tirs cadrés, +{d_home['corners']} corners"
            })
            
        elif storm_away:
             alerts.append({
                "match": f"{home} {fix['goals_home']}-{fix['goals_away']} {away}",
                "elapsed": elapsed,
                "team_on_fire": away,
                "time_window": time_win,
                "stats_added": f"+{d_away['shots_on_target']} tirs cadrés, +{d_away['corners']} corners"
            })
            
    # S'il y a des alertes, on envoie via Telegram
    if alerts:
        logger.info(f"🚨 {len(alerts)} ALERTE(S) TEMPETE DETECTEE(S) !")
        from api.routers.trigger import _send_telegram_message
        
        for a in alerts:
            msg = f"🌪️ *ALERTE TEMPÊTE LIVE !* 🌪️\n\n"
            msg += f"⚽ {a['match']} ({a['elapsed']}')\n"
            msg += f"🔥 *{a['team_on_fire']}* détruit tout sur son passage !\n\n"
            msg += f"📈 Sur les *{a['time_window']}* dernières minutes :\n"
            msg += f"└ {a['stats_added']}\n\n"
            msg += "⚠️ Un but est probablement imminent."
            
            logger.info(f"   -> {a['team_on_fire']} est on fire dans {a['match']} ({a['stats_added']} en {a['time_window']} mins)")
            _send_telegram_message(msg)

    return {"status": "ok", "matches_analyzed": len(live_fixtures), "alerts": alerts}

if __name__ == "__main__":
    run_momentum_tracker()
