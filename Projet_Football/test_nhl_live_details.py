import requests
import json

def test_nhl_live_details():
    url = "https://api-web.nhle.com/v1/score/now"
    resp = requests.get(url)
    if resp.status_code != 200: return
    
    games = resp.json().get("games", [])
    if not games: return
    
    # Find a game that likely has score
    g = next((game for game in games if game.get("gameState") in ("LIVE", "FINAL", "OFF")), games[0])
    game_id = g.get('id')
    landing_url = f"https://api-web.nhle.com/v1/gamecenter/{game_id}/landing"
    print(f"Fetching Landing: {landing_url}")
    l_resp = requests.get(landing_url)
    if l_resp.status_code == 200:
        l_data = l_resp.json()
        summary = l_data.get("summary", {})
        scoring = summary.get("scoring", [])
        if scoring:
            # Print the first scoring period
            period_data = scoring[0]
            print(f"Period: {period_data.get('period')}")
            goals = period_data.get("goals", [])
            if goals:
                print("Goal structure:")
                print(json.dumps(goals[0], indent=2))

if __name__ == "__main__":
    test_nhl_live_details()
