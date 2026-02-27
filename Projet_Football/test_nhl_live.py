import requests
import json

def test_nhl_live():
    # Attempt to get today's scores
    url = "https://api-web.nhle.com/v1/score/now"
    print(f"Fetching: {url}")
    resp = requests.get(url)
    if resp.status_code != 200:
        print(f"Error: {resp.status_code}")
        return
    
    data = resp.json()
    games = data.get("games", [])
    print(f"Found {len(games)} games in scores API.")
    
    if games:
        g = games[0]
        print(f"Game ID: {g.get('id')}")
        print(f"Status: {g.get('gameState')}")
        print(f"Teams: {g.get('homeTeam', {}).get('abbrev')} vs {g.get('awayTeam', {}).get('abbrev')}")
        print(f"Score: {g.get('homeTeam', {}).get('score')} - {g.get('awayTeam', {}).get('score')}")
        
        # Test Landing for events
        game_id = g.get('id')
        landing_url = f"https://api-web.nhle.com/v1/gamecenter/{game_id}/landing"
        print(f"\nFetching Landing: {landing_url}")
        l_resp = requests.get(landing_url)
        if l_resp.status_code == 200:
            l_data = l_resp.json()
            summary = l_data.get("summary", {})
            scoring = summary.get("scoring", [])
            print(f"Scoring events: {len(scoring)}")
            if scoring:
                print("First score:", scoring[0].get("goals", [{}])[0].get("name", {}).get("default"))

if __name__ == "__main__":
    test_nhl_live()
