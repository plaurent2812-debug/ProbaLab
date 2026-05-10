from __future__ import annotations

import os
import time

import requests
from dotenv import load_dotenv

from src.config import logger
from src.constants import LEAGUES_TO_FETCH
from src.monitoring.provider_health import log_call
from supabase import Client, create_client


def _safe_log_api_football(**kwargs) -> None:
    """Defensive wrapper around log_call. Monitoring must not break the fetcher."""
    try:
        log_call(**kwargs)
    except Exception:  # pragma: no cover - defensive
        logger.warning("matches: log_call failed", exc_info=True)


# 1. Chargement des secrets
load_dotenv()
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")
api_key = os.getenv("API_FOOTBALL_KEY")

if not api_key:
    logger.error("ERREUR: API_FOOTBALL_KEY manquante dans le fichier .env")
    exit()

supabase: Client = create_client(url, key)

# 2. Configuration API-Football
SEASON = 2025

headers = {"x-rapidapi-host": "v3.football.api-sports.io", "x-rapidapi-key": api_key}


def get_fixtures_by_date(league_id: int, date_from: str, date_to: str) -> list[dict]:
    """Fetch fixtures within a specific date range.

    Args:
        league_id: API league identifier.
        date_from: Start date (YYYY-MM-DD).
        date_to: End date (YYYY-MM-DD).

    Returns:
        List of raw fixture items.
    """
    url_api = "https://v3.football.api-sports.io/fixtures"
    querystring = {
        "league": str(league_id),
        "season": str(SEASON),
        "from": date_from,
        "to": date_to,
        "timezone": "Europe/Paris",  # Intentional: API returns dates in CET/CEST for display consistency
    }

    start = time.monotonic()
    try:
        response = requests.get(url_api, headers=headers, params=querystring)
        data = response.json()
        rows = data.get("response", [])
        _safe_log_api_football(
            provider="api_football",
            sport="football",
            endpoint=url_api,
            status_code=response.status_code,
            row_count=len(rows) if isinstance(rows, list) else 0,
            latency_ms=int((time.monotonic() - start) * 1000),
            plan_label="api_football_pro",
            empty_is_ok=True,
        )
        return rows
    except Exception as e:
        logger.error(f"Erreur API pour ligue {league_id}: {e}")
        _safe_log_api_football(
            provider="api_football",
            sport="football",
            endpoint=url_api,
            status_code=None,
            row_count=None,
            latency_ms=int((time.monotonic() - start) * 1000),
            plan_label="api_football_pro",
            error=f"{type(e).__name__}: {e}"[:200],
        )
        return []


def fetch_and_store(date_from: str = None, date_to: str = None) -> None:
    """Fetch fixtures for a specific range (defaults to next 7 days).

    Args:
        date_from: Start date (YYYY-MM-DD).
        date_to: End date (YYYY-MM-DD).
    """
    from datetime import datetime, timedelta, timezone

    if not date_from:
        date_from = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    if not date_to:
        date_to = (datetime.now(timezone.utc) + timedelta(days=7)).strftime("%Y-%m-%d")

    logger.info(f"--- Démarrage de l'importation par date : {date_from} -> {date_to} ---")
    total_imported = 0

    for league_id in LEAGUES_TO_FETCH:
        logger.info(f"Récupération ligue {league_id}...")
        fixtures_list = get_fixtures_by_date(league_id, date_from, date_to)

        if not fixtures_list:
            continue

        for item in fixtures_list:
            fixture = item.get("fixture")
            teams = item.get("teams")
            goals = item.get("goals") or {}
            league = item.get("league") or {}

            if not fixture or not teams:
                logger.warning(
                    "Malformed fixture item: %s", item.get("fixture", {}).get("id", "unknown")
                )
                continue

            # Upsert Ligue
            try:
                supabase.table("leagues").upsert(
                    {
                        "api_id": league["id"],
                        "name": league["name"],
                        "country": league["country"],
                        "season": league["season"],
                    },
                    on_conflict="api_id",
                ).execute()
            except Exception as e:
                logger.error("Failed to upsert league %s: %s", league.get("id", "unknown"), e)

            # Upsert Match
            try:
                stats_raw = {
                    "venue": fixture.get("venue"),
                    "status_short": fixture["status"]["short"],
                    "round": league.get("round"),
                }

                match_data = {
                    "api_fixture_id": fixture["id"],
                    "date": fixture["date"],
                    "league_id": league["id"],
                    "home_team": teams["home"]["name"],
                    "away_team": teams["away"]["name"],
                    "status": fixture["status"]["short"],
                    "home_goals": goals.get("home"),
                    "away_goals": goals.get("away"),
                    "model_version": "v1",
                    "stats_json": stats_raw,
                }

                supabase.table("fixtures").upsert(
                    match_data, on_conflict="api_fixture_id"
                ).execute()

                total_imported += 1

            except Exception as e:
                logger.error(f"   [ERREUR] Match {fixture['id']} : {e}")

    logger.info(f"--- Terminé : {total_imported} matchs importés ---")


if __name__ == "__main__":
    fetch_and_store()
