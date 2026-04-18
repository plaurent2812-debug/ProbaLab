"""Registre stable des bookmakers FR ciblés par SS1.

Source The Odds API v4 : https://the-odds-api.com/sports-odds-data/betting-markets.html
Les clés bookmaker sont celles exposées par l'endpoint /v4/sports/{sport}/odds.
"""
from __future__ import annotations

BOOKMAKERS_FR: list[str] = [
    "pinnacle",  # benchmark CLV interne (sharp book)
    "betclic",
    "winamax",
    "unibet",
    "zebet",
]

# Nos noms internes → clés The Odds API
# (valeurs à valider en live avec /v4/sports/{sport}/odds?bookmakers=...)
ODDS_API_KEY_BY_BOOKMAKER: dict[str, str] = {
    "pinnacle": "pinnacle",
    "betclic": "betclic",
    "winamax": "winamax_fr",
    "unibet": "unibet_fr",
    "zebet": "zebet",
}

# Sport keys The Odds API (v4)
SPORT_KEYS: dict[str, list[str]] = {
    "football": [
        "soccer_france_ligue_one",     # Ligue 1
        "soccer_france_ligue_two",     # Ligue 2
        "soccer_epl",                  # Premier League
        "soccer_spain_la_liga",        # La Liga
        "soccer_italy_serie_a",        # Serie A
        "soccer_germany_bundesliga",   # Bundesliga
        "soccer_uefa_champs_league",   # UCL
        "soccer_uefa_europa_league",   # UEL
    ],
    "nhl": ["icehockey_nhl"],
}


def get_bookmaker_from_api_key(api_key: str) -> str | None:
    """Inverse lookup : The Odds API key → nom interne."""
    for internal, api in ODDS_API_KEY_BY_BOOKMAKER.items():
        if api == api_key:
            return internal
    return None


def normalize_bookmaker(name: str) -> str:
    """Normalise un nom arbitraire → nom interne canonique.

    Accepte les aliases (casse, espaces). Lève ValueError si inconnu.
    """
    candidate = name.strip().lower()
    if candidate in BOOKMAKERS_FR:
        return candidate
    raise ValueError(f"Unknown bookmaker: {name!r} — expected one of {BOOKMAKERS_FR}")
