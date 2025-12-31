import requests
import json
import os
import time
import threading
from datetime import datetime, timezone

# Configuration
API_KEY = os.environ.get('RIOT_API_KEY')

# Optimally distributed routing configuration for parallel processing
ROUTING_DISTRIBUTION = {
    'americas': [
        ('na1', 'North America', 300),
        ('br1', 'Brazil', 200),
        ('kr', 'Korea', 300),
        ('eun1', 'Europe Nordic & East', 200),
        ('jp1', 'Japan', 50),
        ('ru', 'Russia', 50),
    ],
    'europe': [
        ('euw1', 'Europe West', 300),
        ('la1', 'Latin America North', 200),
        ('la2', 'Latin America South', 200),
        ('vn2', 'Vietnam', 300),
        ('oc1', 'Oceania', 50),
        ('me1', 'Middle East', 50),
    ],
    'asia': [
        ('tw2', 'Taiwan', 200),
        ('sg2', 'Southeast Asia', 200),
        ('tr1', 'Turkey', 200),
    ]
}

def get_challenger_league(platform_region):
    """Fetch current Challenger league data from platform-specific endpoint"""
    url = f'https://{platform_region}.api.riotgames.com/lol/league/v4/challengerleagues/by-queue/RANKED_SOLO_5x5'
    headers = {'X-Riot-Token': API_KEY}
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching Challenger league for {platform_region}: {e}")
        return None

def get_account_info(puuid, routing_region):
    """Get account info (riot ID) from PUUID using routing region"""
    url = f'https://{routing_region}.api.riotgames.com/riot/account/v1/accounts/by-puuid/{puuid}'
    headers = {'X-Riot-Token': API_KEY}
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        return data['gameName'], data['tagLine']
    except Exception as e:
        print(f"Error fetching account info for PUUID {puuid} via {routing_region}: {e}")
        return "Unknown", "0000"

def load_existing_data(region_code):
    """Load existing player data for a specific region"""
    data_file = f'data/{region_code}_players.json'
    if os.path.exists(data_file):
        with open(data_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {'players': [], 'lastUpdate': None}

def save_region_data(region_code, data):
    """Save player data for a specific region"""
    os.makedirs('data', exist_ok=True)
    data_file = f'data/{region_code}_players.json'
    with open(data_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def update_region(platform_region, region_name, routing_region):
    """Update player data for a single region"""
    print(f"\n{'='*60}")
    print(f"Processing {region_name} ({platform_region})")
    print(f"Using routing: {routing_region}")
    print(f"{'='*60}")
    
    # Fetch Challenger league
    league_data = get_challenger_league(platform_region)
    if not league_data:
        print(f"Failed to fetch data for {region_name}")
        return
    
    # Load existing data
    existing_data = load_existing_data(platform_region)
    player_map = {p['puuid']: p for p in existing_data['players']}
    
    current_date = datetime.now(timezone.utc).isoformat()
    current_puuids = set()
    
    total_players = len(league_data['entries'])
    print(f"Found {total_players} Challenger players")
    
    for idx, entry in enumerate(league_data['entries']):
        try:
            puuid = entry['puuid']
            current_puuids.add(puuid)
            
            # Get Riot ID using the specified routing region
            game_name, tag_line = get_account_info(puuid, routing_region)
            
            # Rate limiting: 1.2 seconds per request (safe rate for 100 req/2min)
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
                player['daysInChallenger'] = player.get('daysInChallenger', 0) + 1
                
               # Update rank history and calculate both average ranks
                if 'rankHistory' in player:
                    player['rankHistory'].append(idx + 1)
                else:
                    player['rankHistory'] = [idx + 1]
                
                # Calculate average rank (all data)
                player['avgRankAll'] = sum(player['rankHistory']) / len(player['rankHistory'])
                
                # Calculate average rank (only when ladder is 15%+ filled, assumes 300 max slots)
                max_challenger_slots = 300
                min_players_threshold = int(max_challenger_slots * 0.15)  # 15% of 300 = 45 players
                
                if len(league_data['entries']) >= min_players_threshold:
                    player['avgRank'] = sum(player['rankHistory']) / len(player['rankHistory'])
                else:
                    player['avgRank'] = None
            else:
                # Add new player (first time seeing them = 1 day in Challenger)
                max_challenger_slots = 300
                min_players_threshold = int(max_challenger_slots * 0.15)
                
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
                    'avgRank': idx + 1 if len(league_data['entries']) >= min_players_threshold else None,
                    'avgRankAll': idx + 1,
                    'rankHistory': [idx + 1],
                    'isActive': True
                }
            
            # Progress update
            if (idx + 1) % 50 == 0:
                print(f"  Progress: {idx + 1}/{total_players} players processed...")
                
        except Exception as e:
            print(f"  Error processing player at index {idx}: {e}")
            continue
    
    # Mark inactive players
    for puuid, player in player_map.items():
        if puuid not in current_puuids:
            player['isActive'] = False
            player['currentRank'] = None
            player['leaguePoints'] = None
    
    # Sort and rank
    sorted_players = sorted(player_map.values(), key=lambda x: x['daysInChallenger'], reverse=True)
    for idx, player in enumerate(sorted_players):
        player['rank'] = idx + 1
    
    # Save data
    updated_data = {
        'region': region_name,
        'regionCode': platform_region,
        'players': sorted_players,
        'lastUpdate': current_date
    }
    
    save_region_data(platform_region, updated_data)
    
    print(f"✓ {region_name} completed!")
    print(f"  Total tracked: {len(sorted_players)}")
    print(f"  Currently active: {len(current_puuids)}")

def process_routing_group(routing_region, regions):
    """Process all regions assigned to a routing region"""
    print(f"\n🌍 Starting {routing_region.upper()} routing group")
    start_time = time.time()
    
    for platform_region, region_name, expected_count in regions:
        update_region(platform_region, region_name, routing_region)
    
    elapsed = time.time() - start_time
    print(f"\n✓ {routing_region.upper()} group completed in {elapsed/60:.1f} minutes")

def update_all_regions():
    """Update all regions using parallel routing groups"""
    print("="*60)
    print("STARTING MULTI-REGION CHALLENGER TRACKER UPDATE")
    print("="*60)
    
    if not API_KEY:
        print("Error: RIOT_API_KEY environment variable not set!")
        return False
    
    start_time = time.time()
    
    # Create threads for each routing region
    threads = []
    for routing_region, regions in ROUTING_DISTRIBUTION.items():
        thread = threading.Thread(
            target=process_routing_group,
            args=(routing_region, regions)
        )
        threads.append(thread)
        thread.start()
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()
    
    elapsed = time.time() - start_time
    
    print("\n" + "="*60)
    print(f"✓ ALL REGIONS COMPLETED!")
    print(f"  Total time: {elapsed/60:.1f} minutes")
    print(f"  Timestamp: {datetime.now(timezone.utc).isoformat()}")
    print("="*60)
    
    return True

if __name__ == '__main__':
    try:
        success = update_all_regions()
        exit(0 if success else 1)
    except Exception as e:
        print(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
