let players = [];
let currentSort = { column: 'rank', direction: 'asc' };
let currentRegion = 'euw1';
let currentSeason = 'current';
let availableSeasons = ['current'];

// Region configuration

const REGIONS = {
    'euw1': { name: 'Europe West', profileUrl: 'https://xdx.gg', maxSlots: 300 },
    'na1': { name: 'North America', profileUrl: 'https://xdx.gg', maxSlots: 300 },
    'kr': { name: 'Korea', profileUrl: 'https://xdx.gg', maxSlots: 300 },
    'eun1': { name: 'Europe Nordic & East', profileUrl: 'https://xdx.gg', maxSlots: 200 },
    'br1': { name: 'Brazil', profileUrl: 'https://xdx.gg', maxSlots: 200 },
    'la1': { name: 'Latin America North', profileUrl: 'https://xdx.gg', maxSlots: 200 },
    'la2': { name: 'Latin America South', profileUrl: 'https://xdx.gg', maxSlots: 200 },
    'vn2': { name: 'Vietnam', profileUrl: 'https://xdx.gg', maxSlots: 300 },
    'sg2': { name: 'Southeast Asia', profileUrl: 'https://xdx.gg', maxSlots: 300 },
    'tw2': { name: 'Taiwan', profileUrl: 'https://xdx.gg', maxSlots: 200 },
    'tr1': { name: 'Turkey', profileUrl: 'https://xdx.gg', maxSlots: 200 },
    'oc1': { name: 'Oceania', profileUrl: 'https://xdx.gg', maxSlots: 50 },
    'jp1': { name: 'Japan', profileUrl: 'https://xdx.gg', maxSlots: 50 },
    'ru': { name: 'Russia', profileUrl: 'https://xdx.gg', maxSlots: 50 },
    'me1': { name: 'Middle East', profileUrl: 'https://xdx.gg', maxSlots: 50 }
};

// Region short codes mapping
const REGION_SHORT_CODES = {
    'br1': 'BR',
    'eun1': 'EUNE',
    'euw1': 'EUW',
    'jp1': 'JP',
    'kr': 'KR',
    'la1': 'LAN',
    'la2': 'LAS',
    'me1': 'ME',
    'na1': 'NA',
    'oc1': 'OC',
    'sg2': 'SEA',
    'ru': 'RU',
    'tr1': 'TR',
    'tw2': 'TW',
    'vn2': 'VN'
};

// Load available seasons from archives
async function loadAvailableSeasons() {
    try {
        // Try to fetch the archives directory listing
        // This requires a seasons.json file that lists all available seasons
        const response = await fetch('data/archives/seasons.json');
        if (response.ok) {
            const data = await response.json();
            availableSeasons = ['current', ...data.seasons];
        }
    } catch (error) {
        console.log('No archived seasons found or seasons.json missing');
    }
    
    updateSeasonSelector();
}

// Update season selector buttons
function updateSeasonSelector() {
    const seasonButtons = document.getElementById('seasonButtons');
    seasonButtons.innerHTML = availableSeasons.map(season => {
        const label = season === 'current' ? 'Current Season' : `Season ${season.replace('_', ' - Split ')}`;
        const activeClass = season === currentSeason ? 'active' : '';
        return `<button class="selector-button ${activeClass}" data-season="${season}">${label}</button>`;
    }).join('');
    
    // Add click listeners
    seasonButtons.querySelectorAll('.selector-button').forEach(button => {
        button.addEventListener('click', () => {
            currentSeason = button.dataset.season;
            updateSeasonSelector();
            document.getElementById('searchInput').value = '';
            currentSort = { column: 'rank', direction: 'asc' };
            updateSortIndicators();
            loadData(currentRegion, currentSeason);
        });
    });
}

// Create region selector buttons
function createRegionSelector() {
    const regionButtons = document.getElementById('regionButtons');
    regionButtons.innerHTML = Object.keys(REGIONS).map(code => {
        const shortCode = REGION_SHORT_CODES[code];
        const activeClass = code === currentRegion ? 'active' : '';
        return `<button class="selector-button ${activeClass}" data-region="${code}">${shortCode}</button>`;
    }).join('');
    
    // Add click listeners
    regionButtons.querySelectorAll('.selector-button').forEach(button => {
        button.addEventListener('click', () => {
            currentRegion = button.dataset.region;
            createRegionSelector();
            updateTooltip(); // Add this line
            document.getElementById('searchInput').value = '';
            currentSort = { column: 'rank', direction: 'asc' };
            updateSortIndicators();
            loadData(currentRegion, currentSeason);
        });
    });
}

// Load player data for a specific region and season
async function loadData(regionCode, season = 'current') {
    try {
        console.log(`Loading data for region: ${regionCode}, season: ${season}`);
        
        let dataPath;
        if (season === 'current') {
            dataPath = `data/${regionCode}_players.json`;
        } else {
            dataPath = `data/archives/${season}/${regionCode}_players.json`;
        }
        
        const response = await fetch(dataPath);
        console.log('Response status:', response.status);
        
        if (!response.ok) {
            throw new Error(`Failed to fetch data for ${regionCode}`);
        }
        
        const data = await response.json();
        console.log('Data loaded:', data);
        console.log('Number of players:', data.players.length);
        
        players = data.players;
        
        if (players.length === 0) {
            console.warn('No players in data!');
            const seasonText = season === 'current' ? '' : ` for season ${season}`;
            document.getElementById('playerTableBody').innerHTML = 
                `<tr><td colspan="8" class="loading">No player data available${seasonText}.</td></tr>`;
            return;
        }
        
        updateStats(data);
        renderTable();
        
        document.getElementById('lastUpdate').textContent = 
            new Date(data.lastUpdate).toLocaleString();
    } catch (error) {
        console.error('Error loading data:', error);
        const seasonText = season === 'current' ? '' : ` for season ${season}`;
        document.getElementById('playerTableBody').innerHTML = 
            `<tr><td colspan="8" class="loading">Error loading data for ${REGIONS[regionCode].name}${seasonText}.</td></tr>`;
    }
}

// Update statistics
function updateStats(data) {
    const totalPlayers = players.length;
    const currentPlayers = players.filter(p => p.isActive).length;
    const avgDays = totalPlayers > 0 
        ? (players.reduce((sum, p) => sum + p.daysInChallenger, 0) / totalPlayers).toFixed(1)
        : '0';
    
    document.getElementById('totalPlayers').textContent = totalPlayers;
    document.getElementById('currentPlayers').textContent = currentPlayers;
    document.getElementById('avgDays').textContent = avgDays;
}

// Render table
function renderTable(filteredPlayers = players) {
    const tbody = document.getElementById('playerTableBody');
    
    if (filteredPlayers.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" class="loading">No players found</td></tr>';
        return;
    }
    
    const regionConfig = REGIONS[currentRegion];
    
    tbody.innerHTML = filteredPlayers.map((player, index) => {
        const profileUrl = `${regionConfig.profileUrl}/${player.summonerName}-${player.tagLine}`;
        const avgRank = player.avgRank ? player.avgRank.toFixed(1) : '-';
        const avgRankAll = player.avgRankAll ? player.avgRankAll.toFixed(1) : '-';
        const currentRank = player.currentRank ? player.currentRank : '-';
        const lp = player.leaguePoints !== null && player.leaguePoints !== undefined ? player.leaguePoints : '-';
        
        return `
            <tr>
                <td>${player.rank}</td>
                <td><a href="${profileUrl}" target="_blank" rel="noopener noreferrer"><strong>${player.summonerName}#${player.tagLine}</strong></a></td>
                <td>${player.daysInChallenger}</td>
                <td>${avgRank}</td>
                <td>${avgRankAll}</td>
                <td>${currentRank}</td>
                <td>${lp}</td>
                <td>
                    <span class="status-badge ${player.isActive ? 'status-active' : 'status-inactive'}">
                        ${player.isActive ? 'Active' : 'Inactive'}
                    </span>
                </td>
            </tr>
        `;
    }).join('');
}

// Sort table
function sortTable(column) {
    if (currentSort.column === column) {
        currentSort.direction = currentSort.direction === 'asc' ? 'desc' : 'asc';
    } else {
        currentSort.column = column;
        currentSort.direction = 'asc';
    }
    
    players.sort((a, b) => {
        let aVal = a[column];
        let bVal = b[column];
        
        // Handle null/undefined values
        if (aVal === null || aVal === undefined) aVal = -Infinity;
        if (bVal === null || bVal === undefined) bVal = -Infinity;
        
        // String comparison
        if (typeof aVal === 'string') {
            aVal = aVal.toLowerCase();
            bVal = bVal.toLowerCase();
        }
        
        if (aVal < bVal) return currentSort.direction === 'asc' ? -1 : 1;
        if (aVal > bVal) return currentSort.direction === 'asc' ? 1 : -1;
        return 0;
    });
    
    updateSortIndicators();
    renderTable();
}

// Update sort indicators
function updateSortIndicators() {
    document.querySelectorAll('th.sortable').forEach(th => {
        th.classList.remove('asc', 'desc');
        if (th.dataset.sort === currentSort.column) {
            th.classList.add(currentSort.direction);
        }
    });
}

function updateTooltip() {
    const maxSlots = REGIONS[currentRegion].maxSlots;
    const threshold = Math.floor(maxSlots * 0.15);
    const tooltipText = document.querySelector('.tooltip .tooltiptext');
    
    if (tooltipText) {
        tooltipText.textContent = `Average rank calculated only when ladder has 15%+ of max slots (${threshold}+ players) to avoid a permanent rank 1 by excluding early season data.`;
    }
}

// Search functionality
document.getElementById('searchInput').addEventListener('input', (e) => {
    const searchTerm = e.target.value.toLowerCase();
    const filtered = players.filter(player => 
        player.summonerName.toLowerCase().includes(searchTerm) ||
        player.tagLine.toLowerCase().includes(searchTerm)
    );
    renderTable(filtered);
});

// Add sort event listeners
document.querySelectorAll('th.sortable').forEach(th => {
    th.addEventListener('click', () => {
        sortTable(th.dataset.sort);
    });
});

// Initialize
createRegionSelector();
updateTooltip(); // Add this line
loadAvailableSeasons().then(() => {
    loadData(currentRegion, currentSeason);
});
