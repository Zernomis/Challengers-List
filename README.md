# Challenger Tracker - All Regions
## https://zernomis.github.io/Challengers-List/

A comprehensive website that tracks all League of Legends players who have reached Challenger rank during the current season across **15 regions** with availability from Riot's API.

## Supported Regions

- **Europe West** (EUW)
- **North America** (NA)
- **Korea** (KR)
- **Europe Nordic & East** (EUNE)
- **Brazil** (BR)
- **Latin America North** (LAN)
- **Latin America South** (LAS)
- **Vietnam** (VN)
- **Sougheast Asia** (SEA)
- **Taiwan** (TW)
- **Middle East** (ME)
- **Turkey** (TR)
- **Oceania** (OCE)
- **Japan** (JP)
- **Russia** (RU)

## Features

- **Historical Tracking**: Records all players who reach Challenger (not just current)
- **Smart Region Selector**: Easy dropdown to switch between regions
- **Automatic Daily Updates**: Updates every region daily at 00:00 UTC
- **Sortable Columns**: Sort by Days in Challenger, Average Rank, Current Rank, LP
- **Player Search**: Search for specific summoners by name or tag
- **PUUID-Based Tracking**: Handles name changes
- **Active/Inactive Status**: See who's currently in Challenger vs. who fell out

## Technical Highlights

### Optimized Multi-Region Updates
The tracker uses an intelligent routing distribution strategy:

- **Parallel Processing**: All 3 routing regions (Americas, Europe, Asia) run simultaneously
- **Cross-Routing Optimization**: Balances API load across routing regions for maximum speed
- **Smart Rate Limiting**: Respects Riot's 100 requests/2 minutes per routing region
- **Total Update Time**: ~22 minutes for all 15 regions (first run), ~7 minutes after caching

### Routing Distribution
```
AMERICAS (22 min):  NA, BR, KR, EUNE, JP, RU
EUROPE (21 min):    EUW, LAN, LAS, VN, OCE, ME
ASIA (18 min):      SEA, TW, TR
```

### Data Structure
Each region maintains its own JSON file:
- `euw1_players.json`
- `na1_players.json`
- `kr_players.json`
- etc.

## Statistics Tracked

For each player:
- **Days in Challenger**: Total days spent in Challenger
- **Average Rank**: Mean rank position while in Challenger
- **Current Rank**: Current ladder position (if active)
- **League Points**: Current LP (if active)
- **Win/Loss Record**: Total wins and losses
- **Rank History**: Complete history of rank positions
- **Active Status**: Whether currently in Challenger

## Future Enhancements

- [ ] Per-season archival (automatic season detection)
- [ ] Historical season viewer

## License

This project is for educational purposes. Riot Games API data usage complies with their Terms of Service.

- [Riot Games Developer Portal](https://developer.riotgames.com/)
- XDX.gg for profile links
---

**Note**: This tracker respects Riot's API rate limits and updates responsibly. Data is refreshed once daily to minimize API usage while keeping information current.
