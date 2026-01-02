import requests
import json
import os
import time
import threading
import shutil
from datetime import datetime, timezone

# Configuration
API_KEY = os.environ.get('RIOT_API_KEY')

# Optimally distributed routing configuration for parallel processing
ROUTING_DISTRIBUTION = {
    'americas': [
        ('na1', 'North America', 300),
        ('br1', 'Brazil', 200),
        ('tw2', 'Taiwan', 200),
        ('eun1', 'Europe Nordic & East', 200),
        ('jp1', 'Japan', 50),
        ('ru', 'Russia', 50),
    ],
    'europe': [
        ('euw1', 'Europe West', 300),
        ('tr1', 'Turkey', 200),
        ('vn2', 'Vietnam', 300),
        ('oc1', 'Oceania', 50),
        ('me1', 'Middle East', 50),
    ],
    'asia': [
        ('kr', 'Korea', 300),
        ('sg2', 'Southeast Asia', 300),
        ('la1', 'Latin America North', 200),
        ('la2', 'Latin America South', 200),
    ]
}

def get_challenger_league(platform_region):
    """Fetch current Challenger league data from platform-specific endpoint"""
    url = f'https://{platform_region}.api.riotgames.com/lol/league/v4/challengerleagues/by-queue/RANKED_SOLO_5x5'
    headers = {'X-Riot-Token': API_KEY}
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json(), response.status_code
    except Exception as e:
        print(f"Error fetching Challenger league for {platform_region}: {e}")
        return None, None

def detect_season_reset():
    """
    Detect season reset by checking if Challenger leagues are empty after having data.
    Returns True if reset detected, False otherwise.
    """
    print(f"\n{'='*60}")
    print("CHECKING FOR SEASON RESET")
    print(f"{'='*60}")
    
    # Check a sample of regions to detect reset
    sample_regions = [('euw1', 'Europe West'), ('na1', 'North America'), ('kr', 'Korea')]
    
    empty_count = 0
    had_data_count = 0
    total_checked = 0
    
    for platform_region, region_name in sample_regions:
        # Check if region had data yesterday
        data_file = f'data/{platform_region}_players.json'
        had_data = False
        
        if os.path.exists(data_file):
            try:
                with open(data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Consider it had data if there were active players
                    active_players = [p for p in data.get('players', []) if p.get('isActive', False)]
                    if len(active_players) > 0:
                        had_data = True
                        had_data_count += 1
            except:
                pass
        
        # Check current league status
        league_data, status_code = get_challenger_league(platform_region)
        
        if status_code == 200 and league_data:
            entries = league_data.get('entries', [])
            is_empty = len(entries) == 0
            
            print(f"  {region_name}: {len(entries)} players (Had data: {had_data})")
            
            if is_empty and had_data:
                empty_count += 1
            
            total_checked += 1
            time.sleep(1.2)  # Rate limiting
    
    # Season reset detected if at least 2 regions are empty that had data
    reset_detected = empty_count >= 2 and had_data_count >= 2
    
    if reset_detected:
        print(f"\n🔄 SEASON RESET DETECTED!")
        print(f"  {empty_count}/{total_checked} sample regions are now empty")
    else:
        print(f"\n✓ No season reset detected")
        print(f"  {empty_count}/{total_checked} empty regions")
    
    return reset_detected

def get_next_archive_name():
    """Generate the next archive folder name in format YYYY_N"""
    current_year = datetime.now(timezone.utc).year
    archives_dir = 'data/archives'
    
    if not os.path.exists(archives_dir):
        return f"{current_year}_1"
    
    # Find existing archives for current year
    existing = [d for d in os.listdir(archives_dir) 
                if d.startswith(f"{current_year}_") and os.path.isdir(os.path.join(archives_dir, d))]
    
    if not existing:
        return f"{current_year}_1"
    
    # Extract numbers and find max
    numbers = []
    for archive in existing:
        try:
            num = int(archive.split('_')[1])
            numbers.append(num)
        except:
            pass
    
    next_num = max(numbers) + 1 if numbers else 1
    return f"{current_year}_{next_num}"

def archive_current_data(archive_name):
    """Archive all current data files into a folder"""
    archive_dir = f'data/archives/{archive_name}'
    os.makedirs(archive_dir, exist_ok=True)
    
    print(f"\n{'='*60}")
    print(f"ARCHIVING TO: {archive_name}")
    print(f"{'='*60}")
    
    archived_count = 0
    all_regions = [region[0] for regions in ROUTING_DISTRIBUTION.values() for region in regions]
    
    for region_code in all_regions:
        source_file = f'data/{region_code}_players.json'
        if os.path.exists(source_file):
            dest_file = f'{archive_dir}/{region_code}_players.json'
            shutil.copy2(source_file, dest_file)
            archived_count += 1
            print(f"  ✓ Archived {region_code}_players.json")
    
    # Create archive metadata
    metadata = {
        'archive_name': archive_name,
        'archived_date': datetime.now(timezone.utc).isoformat(),
        'regions_archived': archived_count,
    }
    
    with open(f'{archive_dir}/metadata.json', 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"\n✓ Archived {archived_count} files to {archive_name}")
    
    # Clear current data files
    print(f"\nClearing current data files...")
    for region_code in all_regions:
        data_file = f'data/{region_code}_players.json'
        if os.path.exists(data_file):
            os.remove(data_file)
    print(f"✓ Data cleared for fresh season start")
    generate_seasons_list()

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

def update_region(platform_region, region_name, routing_region, max_slots):
    """Update player data for a single region"""
    print(f"\n{'='*60}")
    print(f"Processing {region_name} ({platform_region})")
    print(f"Using routing: {routing_region} | Max Slots: {max_slots}")
    print(f"{'='*60}")
    
    # Fetch Challenger league
    league_data, status_code = get_challenger_league(platform_region)
    if not league_data or status_code != 200:
        print(f"Failed to fetch data for {region_name}")
        return
    
    # Load existing data
    existing_data = load_existing_data(platform_region)
    player_map = {p['puuid']: p for p in existing_data['players']}
    
    current_date = datetime.now(timezone.utc).isoformat()
    current_puuids = set()
    
    # Calculate threshold based on the dynamic max_slots
    min_players_threshold = int(max_slots * 0.15)
    total_league_entries = len(league_data['entries'])
    
    print(f"Found {total_league_entries} Challenger players (Threshold: {min_players_threshold})")
    
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
                
                if 'rankHistory' in player:
                    player['rankHistory'].append(idx + 1)
                else:
                    player['rankHistory'] = [idx + 1]
                
                player['avgRankAll'] = sum(player['rankHistory']) / len(player['rankHistory'])
                
                # Dynamic threshold check
                if total_league_entries >= min_players_threshold:
                    player['avgRank'] = player['avgRankAll']
                else:
                    player['avgRank'] = None
            else:
                # Add new player
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
                    'avgRank': idx + 1 if total_league_entries >= min_players_threshold else None,
                    'avgRankAll': idx + 1,
                    'rankHistory': [idx + 1],
                    'isActive': True
                }
            
            if (idx + 1) % 50 == 0:
                print(f"  Progress: {idx + 1}/{total_league_entries} players processed...")
                
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

def process_routing_group(routing_region, regions):
    """Process all regions assigned to a routing region"""
    print(f"\n🌍 Starting {routing_region.upper()} routing group")
    start_time = time.time()
    
    for platform_region, region_name, max_slots in regions:
        update_region(platform_region, region_name, routing_region, max_slots)
    
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
    
    # Check for season reset BEFORE updating
    if detect_season_reset():
        archive_name = get_next_archive_name()
        archive_current_data(archive_name)
    
    start_time = time.time()
    threads = []
    for routing_region, regions in ROUTING_DISTRIBUTION.items():
        thread = threading.Thread(
            target=process_routing_group,
            args=(routing_region, regions)
        )
        threads.append(thread)
        thread.start()
    
    for thread in threads:
        thread.join()
    
    elapsed = time.time() - start_time
    print(f"\n✓ ALL REGIONS COMPLETED in {elapsed/60:.1f} minutes")
    print(f"  Timestamp: {datetime.now(timezone.utc).isoformat()}")
    print("="*60)
    return True

def generate_seasons_list():
    """Generate a list of all available archived seasons"""
    archives_dir = 'data/archives'
    
    if not os.path.exists(archives_dir):
        seasons = []
    else:
        seasons = sorted([
            d for d in os.listdir(archives_dir) 
            if os.path.isdir(os.path.join(archives_dir, d)) and '_' in d
        ], reverse=True)  # Most recent first
    
    seasons_data = {
        'seasons': seasons,
        'last_updated': datetime.now(timezone.utc).isoformat()
    }
    
    with open(f'{archives_dir}/seasons.json', 'w') as f:
        json.dump(seasons_data, f, indent=2)
    
    print(f"✓ Generated seasons.json with {len(seasons)} archived seasons")

if __name__ == '__main__':
    try:
        success = update_all_regions()
        exit(0 if success else 1)
    except Exception as e:
        print(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
