import os

import pytest
import requests

from src.config import API_FOOTBALL_KEY

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        os.getenv("RUN_LIVE_API_TESTS") != "1",
        reason="Live API-Football probe; set RUN_LIVE_API_TESTS=1 to run.",
    ),
]

API_FOOTBALL_URL = "https://v3.football.api-sports.io"
API_FOOTBALL_HEADERS = {
    "x-rapidapi-host": "v3.football.api-sports.io",
    "x-rapidapi-key": API_FOOTBALL_KEY,
}


def test_team_squad_probe():
    resp = requests.get(
        f"{API_FOOTBALL_URL}/players/squads",
        headers=API_FOOTBALL_HEADERS,
        params={"team": 85},
        timeout=20,
    ).json()

    assert resp.get("response"), resp
    assert resp["response"][0].get("players")
