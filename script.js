let players = [];
let currentSort = { column: 'rank', direction: 'asc' };
let currentRegion = 'euw1'; // Default region

// Region configuration
const REGIONS = {
    'euw1': { name: 'Europe West', profileUrl: 'https://xdx.gg' },
    'na1': { name: 'North America', profileUrl: 'https://xdx.gg' },
    'kr': { name: 'Korea', profileUrl: 'https://xdx.gg' },
    'eun1': { name: 'Europe Nordic & East', profileUrl: 'https://xdx.gg' },
    'br1': { name: 'Brazil', profileUrl: 'https://xdx.gg' },
    'la1': { name: 'Latin America North', profileUrl: 'https://xdx.gg' },
    'la2': { name: 'Latin America South', profileUrl: 'https://xdx.gg' },
    'vn2': { name: 'Vietnam', profileUrl: 'https://xdx.gg' },
    'sg2': { name: 'Southeast Asia', profileUrl: 'https://xdx.gg' },
    'tw2': { name: 'Taiwan', profileUrl: 'https://xdx.gg' },
    'tr1': { name: 'Turkey', profileUrl: 'https://xdx.gg' },
    'oc1': { name: 'Oceania', profileUrl: 'https://xdx.gg' },
    'jp1': { name: 'Japan', profileUrl: 'https://xdx.gg' },
    'ru': { name: 'Russia', profileUrl: 'https://xdx.gg' },
    'me1': { name: 'Middle East', profileUrl: 'https://xdx.gg' }
};

// Load player data for a specific region
async function loadData(regionCode) {
    try {
        console.log(`Loading data for region: ${regionCode}`);
        const response = await fetch(`data/${regionCode}_players.json`);
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
            document.getElementById('playerTableBody').innerHTML = 
                '<tr><td colspan="7" class="loading">No player data available yet. The tracker will update daily.</td></tr>';
            return;
        }
        
        updateStats(data);
        renderTable();
        
        document.getElementById('lastUpdate').textContent = 
            new Date(data.lastUpdate).toLocaleString();
    } catch (error) {
        console.error('Error loading data:', error);
        document.getElementById('playerTableBody').innerHTML = 
            `<tr><td colspan="7" class="loading">Error loading data for ${REGIONS[regionCode].name}. This region may not have data yet.</td></tr>`;
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
        tbody.innerHTML = '<tr><td colspan="7" class="loading">No players found</td></tr>';
        return;
    }
    
    const regionConfig = REGIONS[currentRegion];
    
    tbody.innerHTML = filteredPlayers.map((player, index) => {
        const profileUrl = `${regionConfig.profileUrl}/${player.summonerName}-${player.tagLine}`;
        const avgRank = player.avgRank ? player.avgRank.toFixed(1) : '-';
        const currentRank = player.currentRank ? player.currentRank : '-';
        const lp = player.leaguePoints !== null && player.leaguePoints !== undefined ? player.leaguePoints : '-';
        
        return `
            <tr>
                <td>${index + 1}</td>
                <td><strong><a href="${profileUrl}" target="_blank" rel="noopener noreferrer">${player.summonerName}</a></strong>#${player.tagLine}</td>
                <td>${player.daysInChallenger}</td>
                <td>${avgRank}</td>
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

// Region selector change
document.getElementById('regionSelect').addEventListener('change', (e) => {
    currentRegion = e.target.value;
    console.log(`Region changed to: ${currentRegion}`);
    
    // Reset search
    document.getElementById('searchInput').value = '';
    
    // Reset sort
    currentSort = { column: 'rank', direction: 'asc' };
    updateSortIndicators();
    
    // Load new region data
    loadData(currentRegion);
});

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

// Initialize with default region
loadData(currentRegion);
