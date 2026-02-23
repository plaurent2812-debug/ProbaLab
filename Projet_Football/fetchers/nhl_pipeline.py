"""
nhl_pipeline.py — Pipeline NHL complet (équivalent du Google Apps Script)

Fetches data from NHL public API (api-web.nhle.com/v1):
- Schedule du jour
- Standings (classements)
- Club-stats (rosters de joueurs + stats saison)
- Goalie form (5 derniers matchs)

Calcule les scores de probabilité pour chaque joueur (but, passe, point, tir)
et push dans nhl_data_lake + nhl_fixtures dans Supabase.
"""

import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import supabase, logger

NHL_API = "https://api-web.nhle.com/v1"

TEAM_NAMES = {
    "ANA": "Anaheim Ducks", "BOS": "Boston Bruins", "BUF": "Buffalo Sabres",
    "CGY": "Calgary Flames", "CAR": "Carolina Hurricanes", "CHI": "Chicago Blackhawks",
    "COL": "Colorado Avalanche", "CBJ": "Columbus Blue Jackets", "DAL": "Dallas Stars",
    "DET": "Detroit Red Wings", "EDM": "Edmonton Oilers", "FLA": "Florida Panthers",
    "LAK": "Los Angeles Kings", "MIN": "Minnesota Wild", "MTL": "Montréal Canadiens",
    "NSH": "Nashville Predators", "NJD": "New Jersey Devils", "NYI": "New York Islanders",
    "NYR": "New York Rangers", "OTT": "Ottawa Senators", "PHI": "Philadelphia Flyers",
    "PIT": "Pittsburgh Penguins", "SJS": "San Jose Sharks", "SEA": "Seattle Kraken",
    "STL": "St. Louis Blues", "TBL": "Tampa Bay Lightning", "TOR": "Toronto Maple Leafs",
    "UTA": "Utah Hockey Club", "VAN": "Vancouver Canucks", "VGK": "Vegas Golden Knights",
    "WSH": "Washington Capitals", "WPG": "Winnipeg Jets",
}


# ─── HTTP helpers ────────────────────────────────────────────────

def _fetch_json(endpoint: str) -> Optional[dict]:
    """Fetch JSON from NHL API with retries."""
    url = f"{NHL_API}{endpoint}"
    for attempt in range(3):
        try:
            resp = httpx.get(url, timeout=15.0)
            if resp.status_code == 200:
                return resp.json()
            elif resp.status_code in (429, 500, 502, 503):
                import time
                time.sleep(1.5 * (attempt + 1))
            else:
                logger.error(f"[NHL] HTTP {resp.status_code} on {endpoint}")
                return None
        except Exception as e:
            logger.error(f"[NHL] Error fetching {endpoint}: {e}")
            import time
            time.sleep(1.0 * (attempt + 1))
    return None


# ─── Data fetchers ───────────────────────────────────────────────

def fetch_schedule() -> list[dict]:
    """Fetch today's NHL games."""
    data = _fetch_json("/schedule/now")
    if not data or "gameWeek" not in data:
        return []

    today = datetime.utcnow().strftime("%Y-%m-%d")
    for day in data["gameWeek"]:
        if day["date"] == today:
            return day.get("games", [])
    # If today not found, return first day with games
    for day in data["gameWeek"]:
        if day.get("games"):
            return day["games"]
    return []


def fetch_standings() -> dict:
    """Fetch current standings and return team stats dict."""
    data = _fetch_json("/standings/now")
    if not data or "standings" not in data:
        return {}

    team_stats = {}
    for t in data["standings"]:
        abbrev = t.get("teamAbbrev", {}).get("default", "")
        gp = max(1, t.get("gamesPlayed", 1))
        ga = t.get("goalAgainst", 0)
        team_stats[abbrev] = {
            "gaa": round(ga / gp, 2),
            "pp_pct": t.get("powerPlayPctg", 0.20),
            "pk_pct": t.get("penaltyKillPctg", 0.80),
            "l10_pts_pct": t.get("l10PtsPctg", 0.5),
            "wins": t.get("wins", 0),
            "losses": t.get("losses", 0),
            "points": t.get("points", 0),
        }
    return team_stats


def fetch_roster(team: str) -> list[dict]:
    """Fetch skater stats for a team."""
    data = _fetch_json(f"/club-stats/{team}/now")
    if not data:
        return []
    return data.get("skaters", [])


def fetch_goalie_form(teams: list[str]) -> dict:
    """Fetch goalie form (last 5 games GA) for each team."""
    goalie_stats = {}
    for team in set(teams):
        data = _fetch_json(f"/club-schedule-season/{team}/now")
        if not data or "games" not in data:
            goalie_stats[team] = {"form": 0, "reason": "Neutre"}
            continue

        finished = [
            g for g in data["games"]
            if g.get("gameState") in ("FINAL", "OFF")
            and datetime.fromisoformat(g["startTimeUTC"].replace("Z", "+00:00")) < datetime.now().astimezone()
        ]
        finished.sort(key=lambda g: g["startTimeUTC"], reverse=True)
        last5 = finished[:5]

        if not last5:
            goalie_stats[team] = {"form": 0, "reason": "Neutre"}
            continue

        total_ga = 0
        for g in last5:
            is_home = g.get("homeTeam", {}).get("abbrev") == team
            total_ga += g.get("awayTeam" if is_home else "homeTeam", {}).get("score", 0)

        avg_ga = total_ga / len(last5)
        form = 0
        if avg_ga < 2.0:
            form = 0.15
        elif avg_ga < 2.7:
            form = 0.08
        elif avg_ga > 4.2:
            form = -0.15
        elif avg_ga > 3.4:
            form = -0.08

        reason = "Neutre"
        if form > 0.1:
            reason = f"🧱 Mur ({avg_ga:.1f} GA/m L5)"
        elif form > 0:
            reason = f"🛡️ Solide ({avg_ga:.1f} GA/m)"
        elif form < -0.1:
            reason = f"🚨 Passoire ({avg_ga:.1f} GA/m L5)"
        elif form < 0:
            reason = f"⚠️ Friable ({avg_ga:.1f} GA/m)"

        goalie_stats[team] = {"form": form, "reason": reason}

    return goalie_stats


# ─── Player scoring ─────────────────────────────────────────────

def _score_player(skater: dict, team: str, opp: str, my_stats: dict, opp_stats: dict,
                  is_home: bool, goalie_form: dict) -> dict:
    """Score a single player for goal, assist, point, shot probabilities."""
    name = skater.get("firstName", {}).get("default", "") + " " + skater.get("lastName", {}).get("default", "")
    player_id = str(skater.get("playerId", ""))

    gp = max(1, skater.get("gamesPlayed", 1))
    goals = skater.get("goals", 0)
    assists = skater.get("assists", 0)
    points = skater.get("points", 0)
    shots = skater.get("shootingPctg", 0)
    toi_per_game = skater.get("avgToi", "00:00")

    # Parse TOI
    try:
        parts = str(toi_per_game).split(":")
        toi_minutes = int(parts[0]) + int(parts[1]) / 60 if len(parts) == 2 else 0
    except (ValueError, IndexError):
        toi_minutes = 0

    # Per-game rates
    gpg = goals / gp  # Goals per game
    apg = assists / gp  # Assists per game
    ppg = points / gp  # Points per game
    spg = skater.get("shootingPctg", 0)  # We'll use shots per game instead

    # Calculate shots per game from goals and shooting percentage
    shooting_pct = skater.get("shootingPctg", 0)
    shots_per_game = (goals / max(0.01, shooting_pct)) / gp if shooting_pct > 0 else 2.0

    # --- Goal probability ---
    base_goal_prob = min(gpg * 100, 60)
    # Adjust for opponent defense
    opp_gaa = opp_stats.get("gaa", 3.0) if opp_stats else 3.0
    defense_factor = opp_gaa / 3.0  # >1 = weak defense, <1 = strong
    # Adjust for goalie form
    goalie_adj = goalie_form.get(opp, {}).get("form", 0)
    base_goal_prob *= defense_factor * (1 + goalie_adj)
    # Home ice advantage
    if is_home:
        base_goal_prob *= 1.05
    # TOI bonus
    if toi_minutes > 20:
        base_goal_prob *= 1.1
    elif toi_minutes > 18:
        base_goal_prob *= 1.05

    # --- Assist probability ---
    base_assist_prob = min(apg * 100, 60)
    base_assist_prob *= defense_factor
    if is_home:
        base_assist_prob *= 1.03

    # --- Point probability ---
    base_point_prob = min(ppg * 100, 80)
    base_point_prob *= defense_factor * (1 + goalie_adj * 0.5)
    if is_home:
        base_point_prob *= 1.05

    # --- Shot probability (2.5+ shots on goal) ---
    base_shot_prob = min(shots_per_game / 2.5 * 50, 90)  # Normalize around 2.5 SOG
    if toi_minutes > 19:
        base_shot_prob *= 1.15
    if is_home:
        base_shot_prob *= 1.03

    return {
        "player_id": player_id,
        "player_name": name.strip(),
        "team": team,
        "opp": opp,
        "is_home": 1 if is_home else 0,
        "prob_goal": round(min(base_goal_prob, 65), 1),
        "prob_assist": round(min(base_assist_prob, 65), 1),
        "prob_point": round(min(base_point_prob, 80), 1),
        "prob_shot": round(min(base_shot_prob, 95), 1),
        "algo_score_goal": int(min(base_goal_prob, 100)),
        "algo_score_shot": int(min(base_shot_prob, 100)),
        "goals_per_game": round(gpg, 3),
        "assists_per_game": round(apg, 3),
        "shots_per_game": round(shots_per_game, 1),
        "toi_minutes": round(toi_minutes, 1),
        "games_played": gp,
    }


# ─── Win probability ────────────────────────────────────────────

def calculate_win_prob(home: str, away: str, standings: dict) -> dict:
    """Calculate win probability based on standings."""
    h = standings.get(home, {})
    a = standings.get(away, {})

    h_pts = h.get("l10_pts_pct", 0.5)
    a_pts = a.get("l10_pts_pct", 0.5)

    # Simple Elo-ish calculation
    h_power = h_pts * 1.05  # Home ice advantage
    a_power = a_pts

    total = h_power + a_power
    if total == 0:
        return {"home": 50, "away": 50}

    home_pct = round(h_power / total * 100)
    away_pct = 100 - home_pct

    return {"home": home_pct, "away": away_pct}


# ─── Main Pipeline ──────────────────────────────────────────────

def run_nhl_pipeline() -> dict:
    """Run the full NHL pipeline: fetch data, score players, save to Supabase."""
    logger.info("=" * 60)
    logger.info("🏒 NHL PIPELINE — Collecte + Analyse")
    logger.info("=" * 60)

    # 1. Fetch schedule
    games = fetch_schedule()
    if not games:
        logger.info("[NHL] Aucun match aujourd'hui.")
        return {"status": "no_games", "matches": 0}

    future_games = [g for g in games if datetime.fromisoformat(
        g["startTimeUTC"].replace("Z", "+00:00")) > datetime.now().astimezone()]

    logger.info(f"[NHL] {len(games)} matchs trouvés ({len(future_games)} à venir)")

    # 2. Fetch standings
    standings = fetch_standings()
    logger.info(f"[NHL] Standings chargés pour {len(standings)} équipes")

    # 3. Fetch goalie form
    all_teams = []
    for g in future_games:
        all_teams.append(g.get("homeTeam", {}).get("abbrev", ""))
        all_teams.append(g.get("awayTeam", {}).get("abbrev", ""))
    goalie_form = fetch_goalie_form(all_teams)

    # 4. Analyze each game
    today = datetime.utcnow().strftime("%Y-%m-%d")
    all_players = []
    fixtures_data = []

    for game in future_games:
        home_abbrev = game.get("homeTeam", {}).get("abbrev", "")
        away_abbrev = game.get("awayTeam", {}).get("abbrev", "")
        game_id = game.get("id", 0)
        start_time = game.get("startTimeUTC", "")

        home_name = TEAM_NAMES.get(home_abbrev, home_abbrev)
        away_name = TEAM_NAMES.get(away_abbrev, away_abbrev)

        logger.info(f"[NHL] Analyse: {home_name} vs {away_name}")

        # Fetch rosters
        home_roster = fetch_roster(home_abbrev)
        away_roster = fetch_roster(away_abbrev)

        h_stats = standings.get(home_abbrev, {})
        a_stats = standings.get(away_abbrev, {})

        # Score players
        for skater in home_roster:
            player = _score_player(skater, home_abbrev, away_abbrev, h_stats, a_stats, True, goalie_form)
            if player["prob_goal"] > 5 or player["prob_shot"] > 15:
                all_players.append(player)

        for skater in away_roster:
            player = _score_player(skater, away_abbrev, home_abbrev, a_stats, h_stats, False, goalie_form)
            if player["prob_goal"] > 5 or player["prob_shot"] > 15:
                all_players.append(player)

        # Win probabilities
        win_prob = calculate_win_prob(home_abbrev, away_abbrev, standings)

        fixtures_data.append({
            "api_fixture_id": game_id,
            "date": start_time,
            "status": "NS",
            "home_team": home_name,
            "away_team": away_name,
            "proba_home": win_prob["home"],
            "proba_away": win_prob["away"],
        })

    # 5. Save to Supabase — nhl_data_lake
    if all_players:
        rows = [
            {
                "date": today,
                "player_id": p["player_id"],
                "player_name": p["player_name"],
                "team": p["team"],
                "opp": p["opp"],
                "algo_score_goal": p["algo_score_goal"],
                "algo_score_shot": p["algo_score_shot"],
                "is_home": p["is_home"],
                "python_prob": round(p["prob_goal"] / 100, 4),
                "python_vol": round(p["shots_per_game"], 2),
            }
            for p in all_players
        ]
        # Delete today's existing data first
        try:
            supabase.table("nhl_data_lake").delete().eq("date", today).execute()
        except Exception:
            pass

        # Insert in batches of 500
        for i in range(0, len(rows), 500):
            try:
                supabase.table("nhl_data_lake").insert(rows[i:i + 500]).execute()
            except Exception as e:
                logger.error(f"[NHL] Error inserting data_lake batch: {e}")

        logger.info(f"[NHL] ✅ {len(rows)} joueurs insérés dans nhl_data_lake")

    # 6. Save to Supabase — nhl_fixtures (upsert)
    for f in fixtures_data:
        try:
            existing = (
                supabase.table("nhl_fixtures")
                .select("id")
                .eq("api_fixture_id", f["api_fixture_id"])
                .execute()
                .data
            )
            if existing:
                supabase.table("nhl_fixtures").update({
                    "date": f["date"],
                    "status": f["status"],
                    "home_team": f["home_team"],
                    "away_team": f["away_team"],
                    "predictions_json": {"proba_home": f["proba_home"], "proba_away": f["proba_away"]},
                }).eq("api_fixture_id", f["api_fixture_id"]).execute()
            else:
                supabase.table("nhl_fixtures").insert({
                    "api_fixture_id": f["api_fixture_id"],
                    "date": f["date"],
                    "status": f["status"],
                    "home_team": f["home_team"],
                    "away_team": f["away_team"],
                    "predictions_json": {"proba_home": f["proba_home"], "proba_away": f["proba_away"]},
                }).execute()
        except Exception as e:
            logger.error(f"[NHL] Error upserting fixture {f['home_team']} vs {f['away_team']}: {e}")

    logger.info(f"[NHL] ✅ {len(fixtures_data)} matchs insérés dans nhl_fixtures")

    return {
        "status": "ok",
        "matches": len(fixtures_data),
        "players_analyzed": len(all_players),
        "fixtures": [
            {"match": f"{f['home_team']} vs {f['away_team']}", "home_pct": f["proba_home"], "away_pct": f["proba_away"]}
            for f in fixtures_data
        ],
    }
