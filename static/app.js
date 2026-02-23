// API Base URL
const API_BASE = 'http://localhost:5000/api';

// Global state
let library = { series: {}, movies: [] };
let currentlyPlaying = null;
let vlcMonitorInterval = null;
let contextMenuTarget = null;
let isDesktopApp = false;
let desktopBridge = null;

// Initialize the app
document.addEventListener('DOMContentLoaded', () => {
    // Check if running as desktop app
    document.addEventListener('desktopBridgeReady', () => {
        isDesktopApp = true;
        desktopBridge = window.desktopBridge;
        console.log('Desktop bridge connected!');
    });
    
    // Give the bridge a moment to initialize
    setTimeout(() => {
        loadLibrary();
        setupEventListeners();
        startVLCMonitor();
    }, 100);
});

// Setup event listeners
function setupEventListeners() {
    document.getElementById('refreshBtn').addEventListener('click', loadLibrary);
    
    // Close modal when clicking outside
    document.getElementById('episodeModal').addEventListener('click', (e) => {
        if (e.target.id === 'episodeModal') {
            closeModal();
        }
    });
    
    // Close context menu when clicking anywhere
    document.addEventListener('click', () => {
        document.getElementById('contextMenu').style.display = 'none';
    });
    
    // Prevent context menu from closing when clicking inside it
    document.getElementById('contextMenu').addEventListener('click', (e) => {
        e.stopPropagation();
    });
}

// Setup watch button listeners using event delegation
function setupWatchButtonListeners() {
    document.addEventListener('click', (event) => {
        // Check if clicked element is a watch button
        const watchButton = event.target.closest('[data-path][class*="watch-"]');
        if (watchButton) {
            const path = watchButton.getAttribute('data-path');
            if (path) {
                event.preventDefault();
                event.stopPropagation();
                toggleWatched(path);
            }
        }
    }, true); // Use capture phase to intercept clicks
}

// Load the media library
async function loadLibrary() {
    try {
        const response = await fetch(`${API_BASE}/library`);
        library = await response.json();
        
        renderLibrary();
        updateStats();
        
        // Setup watch button listeners after rendering
        setupWatchButtonListeners();
    } catch (error) {
        console.error('Error loading library:', error);
        showError('Failed to load media library');
    }
}

// Render the entire library
function renderLibrary() {
    renderContinueWatching();
    renderMovies();
    renderSeries();
}

// Render continue watching section
function renderContinueWatching() {
    const section = document.getElementById('continueWatchingSection');
    const grid = document.getElementById('continueWatchingGrid');
    
    // Collect all items with progress
    const inProgress = [];
    
    // Add series episodes
    for (const [seriesName, seasons] of Object.entries(library.series)) {
        for (const [seasonNum, episodes] of Object.entries(seasons)) {
            for (const episode of episodes) {
                if (episode.current_time > 0 && !episode.completed) {
                    inProgress.push({
                        ...episode,
                        type: 'episode',
                        seriesName,
                        displayName: `${seriesName} - S${episode.season}E${episode.episode}`
                    });
                }
            }
        }
    }
    
    // Add movies
    for (const movie of library.movies) {
        if (movie.current_time > 0 && !movie.completed) {
            inProgress.push({
                ...movie,
                type: 'movie',
                displayName: movie.name
            });
        }
    }
    
    // Sort by last played
    inProgress.sort((a, b) => {
        if (!a.last_played) return 1;
        if (!b.last_played) return -1;
        return new Date(b.last_played) - new Date(a.last_played);
    });
    
    if (inProgress.length === 0) {
        section.style.display = 'none';
        return;
    }
    
    section.style.display = 'block';
    grid.innerHTML = inProgress.slice(0, 6).map(item => createMediaCard(item)).join('');
}

// Render series
function renderSeries() {
    const container = document.getElementById('seriesContainer');
    
    if (Object.keys(library.series).length === 0) {
        container.innerHTML = '<div class="empty-state"><div class="empty-state-icon">📺</div><div class="empty-state-text">No TV series found</div></div>';
        return;
    }
    
    // Get entries and sort by last watched date (most recent first)
    const seriesEntries = Object.entries(library.series);
    seriesEntries.sort(([nameA, seasonsA], [nameB, seasonsB]) => {
        // Find the latest last_played date in each series
        const getLatestDate = (seasons) => {
            let latestDate = null;
            for (const episodes of Object.values(seasons)) {
                for (const episode of episodes) {
                    if (episode.last_played) {
                        const episodeDate = new Date(episode.last_played);
                        if (!latestDate || episodeDate > latestDate) {
                            latestDate = episodeDate;
                        }
                    }
                }
            }
            return latestDate;
        };
        
        const dateA = getLatestDate(seasonsA);
        const dateB = getLatestDate(seasonsB);
        
        // Most recent first (null dates go to bottom)
        if (!dateA && !dateB) return nameA.localeCompare(nameB); // Alphabetical if both unwatched
        if (!dateA) return 1; // Unwatched goes down
        if (!dateB) return -1; // Unwatched goes down
        return dateB - dateA; // Most recent first
    });
    
    container.innerHTML = seriesEntries
        .map(([seriesName, seasons]) => createSeriesCard(seriesName, seasons))
        .join('');
}

// Render movies
function renderMovies() {
    const grid = document.getElementById('moviesGrid');
    
    if (library.movies.length === 0) {
        grid.innerHTML = '<div class="empty-state"><div class="empty-state-icon">🎬</div><div class="empty-state-text">No movies found</div></div>';
        return;
    }
    
    grid.innerHTML = library.movies.map(movie => createMediaCard(movie)).join('');
}

// Create a media card
function createMediaCard(item) {
    const progressPercent = item.progress_percent || 0;
    const hasProgress = progressPercent > 0;
    const completed = item.completed ? ' completed' : '';
    
    return `
        <div class="media-card ${completed}" data-path="${escapeHtml(item.path)}" onclick="playMediaFromCard(this)" oncontextmenu="showContextMenuFromCard(event, this)">
            <div class="media-card-thumbnail" style="background-image: url('${item.cover_url || ''}'); background-size: cover; background-position: center;">
                ${item.cover_url ? '' : (item.type === 'episode' ? '📺' : '🎬')}
                <div class="media-card-overlay">
                    <button class="watch-button" type="button" data-path="${escapeHtml(item.path)}">
                        ${completed ? '✓ Watched' : 'Mark Watched'}
                    </button>
                </div>
            </div>
            <div class="media-card-content">
                <div class="media-card-title">${escapeHtml(item.displayName || item.name)}</div>
                <div class="media-card-info">${formatFileSize(item.size)}</div>
                ${hasProgress ? `
                    <div class="progress-bar-container">
                        <div class="progress-bar" style="width: ${progressPercent}%"></div>
                    </div>
                    <div class="progress-text">${Math.round(progressPercent)}% watched</div>
                ` : ''}
            </div>
        </div>
    `;
}

// Create a series card
function createSeriesCard(seriesName, seasons) {
    const totalEpisodes = Object.values(seasons).reduce((sum, eps) => sum + eps.length, 0);
    const watchedEpisodes = Object.values(seasons).reduce((sum, eps) => 
        sum + eps.filter(ep => ep.completed).length, 0);
    
    return `
        <div class="series-item">
            <div class="series-header">
                <div class="series-title">📺 ${escapeHtml(seriesName)}</div>
                <div class="series-stats">${Object.keys(seasons).length} Season${Object.keys(seasons).length !== 1 ? 's' : ''} • ${totalEpisodes} Episodes • ${watchedEpisodes} Watched</div>
            </div>
            <div class="seasons-container">
                ${Object.entries(seasons)
                    .sort(([a], [b]) => parseInt(a) - parseInt(b))
                    .map(([seasonNum, episodes]) => createSeasonCard(seriesName, seasonNum, episodes))
                    .join('')}
            </div>
        </div>
    `;
}

// Create a season card
function createSeasonCard(seriesName, seasonNum, episodes) {
    const seasonId = `season-${seriesName.replace(/\s/g, '-')}-${seasonNum}`;
    const watchedCount = episodes.filter(ep => ep.completed).length;
    
    return `
        <div class="season-item">
            <div class="season-header" onclick="toggleSeason('${seasonId}')">
                <div>
                    <div class="season-title">Season ${seasonNum}</div>
                    <div class="season-episodes">${watchedCount}/${episodes.length} Episodes Watched</div>
                </div>
                <div class="season-toggle" id="${seasonId}-toggle">▼</div>
            </div>
            <div class="episodes-grid" id="${seasonId}" style="display: grid;">
                ${episodes.map(episode => createEpisodeCard(episode)).join('')}
            </div>
        </div>
    `;
}

// Create an episode card
function createEpisodeCard(episode) {
    const progressPercent = episode.progress_percent || 0;
    const hasProgress = progressPercent > 0;
    
    return `
        <div class="episode-card ${episode.completed ? 'completed' : ''}" data-path="${escapeHtml(episode.path)}" onclick="playMediaFromCard(this)" oncontextmenu="showContextMenuFromCard(event, this)">
            <div class="episode-header">
                <div class="episode-number">Episode ${episode.episode}</div>
                <button class="watch-toggle" type="button" data-path="${escapeHtml(episode.path)}">
                    ${episode.completed ? '✓' : '○'}
                </button>
            </div>
            <div class="episode-name">${escapeHtml(episode.name)}</div>
            <div class="episode-size">${formatFileSize(episode.size)}</div>
            ${hasProgress ? `
                <div class="progress-bar-container" style="margin-top: 8px;">
                    <div class="progress-bar" style="width: ${progressPercent}%"></div>
                </div>
            ` : ''}
        </div>
    `;
}

// Toggle season visibility
function toggleSeason(seasonId) {
    const seasonEl = document.getElementById(seasonId);
    const toggleEl = document.getElementById(`${seasonId}-toggle`);
    
    if (seasonEl.style.display === 'none') {
        seasonEl.style.display = 'grid';
        toggleEl.textContent = '▼';
    } else {
        seasonEl.style.display = 'none';
        toggleEl.textContent = '▶';
    }
}

// Play media from card element
function playMediaFromCard(element) {
    const path = element.getAttribute('data-path');
    if (path) {
        playMedia(path);
    }
}

// Show context menu from card element
function showContextMenuFromCard(event, element) {
    event.preventDefault();
    event.stopPropagation();
    const path = element.getAttribute('data-path');
    if (path) {
        showContextMenu(event, path);
    }
}

// Play media
async function playMedia(path) {
    console.log('[PLAY] Attempting to play:', path);
    
    try {
        // Get current progress
        const item = findItemByPath(path);
        const startTime = item ? item.current_time : 0;
        
        console.log('[PLAY] Found item:', item ? item.name : 'Not found');
        console.log('[PLAY] Start time:', startTime);
        
        // If running as desktop app, use embedded player
        if (isDesktopApp && desktopBridge) {
            console.log('[PLAY] Using desktop player');
            currentlyPlaying = path;
            showNotification(`Playing: ${getItemName(path)}`);
            // Call Python function to show player
            desktopBridge.playMedia(path, startTime);
            return;
        }
        
        // Otherwise, launch external VLC
        const requestBody = { path, start_time: startTime };
        console.log('[PLAY] Sending request to Flask:', requestBody);
        
        const response = await fetch(`${API_BASE}/play`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestBody)
        });
        
        console.log('[PLAY] Response status:', response.status);
        
        if (response.ok) {
            currentlyPlaying = path;
            showNotification(`Playing: ${getItemName(path)}`);
        } else {
            const errorData = await response.json().catch(() => ({}));
            const errorMsg = errorData.error || `HTTP ${response.status}`;
            console.error('[PLAY] Error response:', errorData);
            throw new Error(errorMsg);
        }
    } catch (error) {
        console.error('Error playing media:', error);
        showError(`Failed to play media: ${error.message}`);
    }
}

// Monitor VLC playback
async function startVLCMonitor() {
    // Only monitor external VLC if not in desktop app mode
    if (isDesktopApp) {
        console.log('Desktop app mode: VLC monitoring disabled (handled by desktop player)');
        return;
    }
    
    vlcMonitorInterval = setInterval(async () => {
        if (!currentlyPlaying) return;
        
        try {
            const response = await fetch(`${API_BASE}/vlc/status`);
            if (!response.ok) {
                // VLC not running
                return;
            }
            
            const status = await response.json();
            
            if (status.state === 'playing' || status.state === 'paused') {
                const position = status.time || 0;
                const duration = status.length || 0;
                
                // Update progress silently (don't reload library)
                if (position > 0 && duration > 0) {
                    await updateProgress(currentlyPlaying, position, duration, false);
                }
            } else if (status.state === 'stopped') {
                // Video ended - only then reload library
                const item = findItemByPath(currentlyPlaying);
                if (item) {
                    // Mark as completed
                    await updateProgress(currentlyPlaying, 0, item.duration || 0, true);
                    
                    // Check if this was an episode and play next
                    if (item.season && item.episode) {
                        await playNextEpisode(currentlyPlaying);
                    }
                }
                
                currentlyPlaying = null;
            }
        } catch (error) {
            // VLC not responding, ignore
        }
    }, 30000); // Check every 30 seconds to reduce flashing
}

// Update progress
async function updateProgress(path, position, duration, completed) {
    try {
        await fetch(`${API_BASE}/progress`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ path, position, duration, completed })
        });
        
        // Refresh library to show updated progress
        if (completed) {
            await loadLibrary();
        }
    } catch (error) {
        console.error('Error updating progress:', error);
    }
}

// Play next episode
async function playNextEpisode(currentPath) {
    try {
        const response = await fetch(`${API_BASE}/next-episode`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ path: currentPath })
        });
        
        if (response.ok) {
            const nextEpisode = await response.json();
            showNotification(`Auto-playing next episode: ${nextEpisode.name}`);
            
            // Wait a moment before playing
            setTimeout(() => {
                playMedia(nextEpisode.path);
            }, 2000);
        }
    } catch (error) {
        console.error('Error playing next episode:', error);
    }
}

// Show context menu
function showContextMenu(event, path) {
    event.preventDefault();
    event.stopPropagation();
    
    const menu = document.getElementById('contextMenu');
    contextMenuTarget = path;
    
    menu.style.display = 'block';
    menu.style.left = `${event.pageX}px`;
    menu.style.top = `${event.pageY}px`;
}

// Reset progress
async function resetProgress() {
    if (!contextMenuTarget) return;
    
    try {
        await fetch(`${API_BASE}/reset-progress`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ path: contextMenuTarget })
        });
        
        showNotification('Progress reset');
        await loadLibrary();
    } catch (error) {
        console.error('Error resetting progress:', error);
        showError('Failed to reset progress');
    }
    
    document.getElementById('contextMenu').style.display = 'none';
}

// Mark as watched
async function markAsWatched() {
    if (!contextMenuTarget) return;
    
    const item = findItemByPath(contextMenuTarget);
    const duration = item ? item.duration : 3600; // Default 1 hour
    
    try {
        await fetch(`${API_BASE}/progress`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                path: contextMenuTarget, 
                position: duration, 
                duration: duration, 
                completed: true 
            })
        });
        
        showNotification('Marked as watched');
        await loadLibrary();
    } catch (error) {
        console.error('Error marking as watched:', error);
        showError('Failed to mark as watched');
    }
    
    document.getElementById('contextMenu').style.display = 'none';
}

// Toggle watched status
async function toggleWatched(path) {
    console.log('toggleWatched called with path:', path);
    
    const item = findItemByPath(path);
    console.log('Found item:', item);
    if (!item) {
        console.log('Item not found!');
        return;
    }
    
    try {
        const newCompleted = !item.completed;
        const position = newCompleted ? (item.duration || 3600) : 0;
        const duration = item.duration || 3600;
        
        console.log('Sending update:', { path, position, duration, completed: newCompleted });
        
        const response = await fetch(`${API_BASE}/progress`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                path: path, 
                position: position, 
                duration: duration, 
                completed: newCompleted 
            })
        });
        
        console.log('Response status:', response.status);
        
        showNotification(newCompleted ? 'Marked as watched' : 'Marked as unwatched');
        await loadLibrary();
    } catch (error) {
        console.error('Error toggling watched status:', error);
        showError('Failed to update watch status');
    }
}

// Close modal
function closeModal() {
    document.getElementById('episodeModal').classList.remove('active');
}

// Update stats
function updateStats() {
    const seriesCount = Object.keys(library.series).length;
    const movieCount = library.movies.length;
    const totalEpisodes = Object.values(library.series).reduce((sum, seasons) => 
        sum + Object.values(seasons).reduce((s, eps) => s + eps.length, 0), 0);
    
    document.getElementById('statsText').textContent = 
        `${seriesCount} Series • ${totalEpisodes} Episodes • ${movieCount} Movies`;
}

// Helper functions
function findItemByPath(path) {
    // Search in series
    for (const seasons of Object.values(library.series)) {
        for (const episodes of Object.values(seasons)) {
            const episode = episodes.find(ep => ep.path === path);
            if (episode) return episode;
        }
    }
    
    // Search in movies
    return library.movies.find(movie => movie.path === path);
}

function getItemName(path) {
    const item = findItemByPath(path);
    return item ? (item.displayName || item.name) : 'Unknown';
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function showNotification(message) {
    console.log('Notification:', message);
    // Create a simple toast notification
    const toast = document.createElement('div');
    toast.style.cssText = 'position: fixed; top: 20px; right: 20px; background: var(--primary-orange); color: white; padding: 15px 20px; border-radius: 8px; z-index: 10000; box-shadow: 0 5px 20px rgba(0,0,0,0.5); animation: slideIn 0.3s ease;';
    toast.textContent = message;
    document.body.appendChild(toast);
    setTimeout(() => {
        toast.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

function showError(message) {
    console.error('Error:', message);
    alert(message);
}
