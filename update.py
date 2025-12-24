import requests
import json
import os
import time
from datetime import datetime, timezone

# Configuration
API_KEY = os.environ.get('RIOT_API_KEY')
REGION = 'euw1'  # Change to your region: na1, euw1, kr, etc.
ROUTING = 'europe'  # Change based on region: americas, europe, asia
DATA_FILE = 'data/players.json'

def get_challenger_league():
    """Fetch current Challenger league data"""
    url = f'https://{REGION}.api.riotgames.com/lol/league/v4/challengerleagues/by-queue/RANKED_SOLO_5x5'
    headers = {'X-Riot-Token': API_KEY}
    
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()

def get_account_info(puuid):
    """Get account info (riot ID) from PUUID"""
    url = f'https://{ROUTING}.api.riotgames.com/riot/account/v1/accounts/by-puuid/{puuid}'
    headers = {'X-Riot-Token': API_KEY}
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        return data['gameName'], data['tagLine']
    except Exception as e:
        print(f"Error fetching account info for PUUID {puuid}: {e}")
        return "Unknown", "0000"

def load_existing_data():
    """Load existing player data"""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {'players': [], 'lastUpdate': None}

def update_player_data():
    """Main function to update player data"""
    print("Fetching Challenger league data...")
    league_data = get_challenger_league()
    
    print("Loading existing player data...")
    existing_data = load_existing_data()
    
    # Create a map of existing players by PUUID
    player_map = {p['puuid']: p for p in existing_data['players']}
    
    # Get current date
    current_date = datetime.now(timezone.utc).isoformat()
    
    # Track current challenger PUUIDs
    current_puuids = set()
    
    print(f"Processing {len(league_data['entries'])} Challenger players...")
    
    for idx, entry in enumerate(league_data['entries']):
        try:
            # PUUID is directly in the entry now!
            puuid = entry['puuid']
            current_puuids.add(puuid)
            
            # Get Riot ID (gameName#tagLine)
            game_name, tag_line = get_account_info(puuid)
            
            # Rate limiting: 100 requests per 2 minutes
            # 301 total requests needs ~6 minutes to stay under limit
            # 1.2 seconds per request = safe rate
            time.sleep(1.2)
            
            if puuid in player_map:
                # Update existing player
                player = player_map[puuid]
                player['summonerName'] = game_name
                player['tagLine'] = tag_line
                player['leaguePoints'] = entry['leaguePoints']
                player['wins'] = entry['wins']
                player['losses'] = entry['losses']
                player['isActive'] = True
                player['currentRank'] = idx + 1
                
                # Add 1 day every time we see them in Challenger (they've been here for at least 24h)
                player['daysInChallenger'] = player.get('daysInChallenger', 0) + 1
                
                # Update average rank
                if 'rankHistory' in player:
                    player['rankHistory'].append(idx + 1)
                    player['avgRank'] = sum(player['rankHistory']) / len(player['rankHistory'])
                else:
                    player['rankHistory'] = [idx + 1]
                    player['avgRank'] = idx + 1
            else:
                # Add new player (first time seeing them = 1 day in Challenger)
                player_map[puuid] = {
                    'puuid': puuid,
                    'summonerName': game_name,
                    'tagLine': tag_line,
                    'leaguePoints': entry['leaguePoints'],
                    'wins': entry['wins'],
                    'losses': entry['losses'],
                    'firstSeenDate': current_date,
                    'daysInChallenger': 1,
                    'currentRank': idx + 1,
                    'avgRank': idx + 1,
                    'rankHistory': [idx + 1],
                    'isActive': True
                }
            
            # Progress update
            if (idx + 1) % 50 == 0:
                print(f"Processed {idx + 1}/{len(league_data['entries'])} players...")
                
        except Exception as e:
            print(f"Error processing player at index {idx}: {e}")
            continue
    
    # Mark players who are no longer in Challenger as inactive
    for puuid, player in player_map.items():
        if puuid not in current_puuids:
            player['isActive'] = False
            player['currentRank'] = None
            player['leaguePoints'] = None
    
    # Sort players by days in challenger (descending)
    sorted_players = sorted(player_map.values(), key=lambda x: x['daysInChallenger'], reverse=True)
    
    # Assign overall rank
    for idx, player in enumerate(sorted_players):
        player['rank'] = idx + 1
    
    # Save updated data
    updated_data = {
        'players': sorted_players,
        'lastUpdate': current_date
    }
    
    os.makedirs('data', exist_ok=True)
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(updated_data, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Data updated successfully!")
    print(f"  Total players tracked: {len(sorted_players)}")
    print(f"  Currently in Challenger: {len(current_puuids)}")
    print(f"  Last update: {current_date}")

if __name__ == '__main__':
    if not API_KEY:
        print("Error: RIOT_API_KEY environment variable not set!")
        exit(1)
    
    try:
        update_player_data()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
