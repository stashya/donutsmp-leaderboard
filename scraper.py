import requests
import json
import time

API_KEY = "41c9e4c6c3b44e38a06ce3e72ba3f7a5"
BASE_URL = "https://api.donutsmp.net/v1/leaderboards/money"
PAGES = 22  # ~46 players per page, 22 pages ≈ 1000 players

def fetch_leaderboard():
    all_players = []
    
    for page in range(1, PAGES + 1):
        print(f"Fetching page {page}/{PAGES}...")
        
        response = requests.get(
            f"{BASE_URL}/{page}",
            headers={
                "accept": "application/json",
                "Authorization": API_KEY
            }
        )
        
        if response.status_code != 200:
            print(f"Error on page {page}: {response.status_code}")
            continue
        
        data = response.json()
        players = data.get("result", [])
        all_players.extend(players)
        
        # Be nice to the API
        time.sleep(0.5)
    
    print(f"Total players fetched: {len(all_players)}")
    return all_players

def main():
    players = fetch_leaderboard()
    
    # Create output with both a lookup set and full data
    output = {
        "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "count": len(players),
        "players": players
    }
    
    with open("top1000.json", "w") as f:
        json.dump(output, f, indent=2)
    
    # Also create a simple username list for quick lookups
    usernames = [p["username"] for p in players if p.get("username")]
    with open("usernames.json", "w") as f:
        json.dump(usernames, f)
    
    print("Done! Files written.")

if __name__ == "__main__":
    main()
