let players = [];
let currentSort = { column: 'rank', direction: 'asc' };

// Load player data
async function loadData() {
    try {
        console.log('Starting to load data...');
        const response = await fetch('data/players.json');
        console.log('Response status:', response.status);
        const data = await response.json();
        console.log('Data loaded:', data);
        console.log('Number of players:', data.players.length);
        
        players = data.players;
        
        if (players.length === 0) {
            console.warn('No players in data!');
            document.getElementById('playerTableBody').innerHTML = 
                '<tr><td colspan="7" class="loading">No player data available yet. Run the update workflow.</td></tr>';
            return;
        }
        
        updateStats(data);
        renderTable();
        
        document.getElementById('lastUpdate').textContent = 
            new Date(data.lastUpdate).toLocaleString();
    } catch (error) {
        console.error('Error loading data:', error);
        document.getElementById('playerTableBody').innerHTML = 
            '<tr><td colspan="7" class="loading">Error loading data. Please try again later.</td></tr>';
    }
}

// Update statistics
function updateStats(data) {
    const totalPlayers = players.length;
    const currentPlayers = players.filter(p => p.isActive).length;
    const avgDays = (players.reduce((sum, p) => sum + p.daysInChallenger, 0) / totalPlayers).toFixed(1);
    
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
    
    tbody.innerHTML = filteredPlayers.map((player, index) => `
        <tr>
            <td>${index + 1}</td>
            <td><strong>${player.summonerName}</strong>#${player.tagLine}</td>
            <td>${player.daysInChallenger}</td>
            <td>${player.avgRank ? player.avgRank.toFixed(1) : 'N/A'}</td>
            <td>${player.currentRank || 'N/A'}</td>
            <td>${player.leaguePoints !== null ? player.leaguePoints : 'N/A'}</td>
            <td>
                <span class="status-badge ${player.isActive ? 'status-active' : 'status-inactive'}">
                    ${player.isActive ? 'Active' : 'Inactive'}
                </span>
            </td>
        </tr>
    `).join('');
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
loadData();
