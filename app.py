from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import os
import json
import subprocess
import re
from pathlib import Path
from datetime import datetime
import requests
from urllib.parse import quote

app = Flask(__name__, static_folder='static', static_url_path='')
CORS(app)

# Configuration
MEDIA_FOLDER = Path(__file__).parent.parent  # Parent folder of this repo
PROGRESS_FILE = Path(__file__).parent / 'progress.json'
COVERS_CACHE_FILE = Path(__file__).parent / 'covers_cache.json'
VLC_PATH = r"C:\Program Files\VideoLAN\VLC\vlc.exe"
VLC_HTTP_PORT = 8080
VLC_HTTP_PASSWORD = "medialibrary"

# Cover image API (optional - only uses if available)
TMDB_API_KEY = None  # Set your TMDB API key here if you want to auto-fetch covers
IMDB_API_URL = "https://www.imdb.com"

# Supported video formats
VIDEO_EXTENSIONS = {'.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm', 
                   '.m4v', '.mpg', '.mpeg', '.3gp', '.m2ts', '.ts', '.vob'}

def load_covers_cache():
    """Load cover URLs cache"""
    if COVERS_CACHE_FILE.exists():
        try:
            with open(COVERS_CACHE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_covers_cache(cache):
    """Save cover URLs cache"""
    with open(COVERS_CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(cache, f, indent=2)

def load_progress():
    """Load watch progress from JSON file"""
    if PROGRESS_FILE.exists():
        try:
            with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_progress(progress_data):
    """Save watch progress to JSON file"""
    with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
        json.dump(progress_data, f, indent=2)

def get_video_duration_vlc(video_path):
    """Get video duration using VLC (approximate)"""
    # For now, return None. We'll track duration when playing
    return None

def clean_series_name(series_name):
    """Clean up series name by removing download quality info"""
    # First, remove tracker tags and specific markers
    series_name = re.sub(r'\[eztv\.re\]|\[TGx\]|\[Silence\]|\[Ghost\]|\[EZTVx\.to\]|\[MeGusta\]', '', series_name, flags=re.IGNORECASE)
    series_name = re.sub(r'\(eztv\.re\)|\(TGx\)|\(Silence\)|\(Ghost\)|\(EZTVx\.to\)|\(MeGusta\)', '', series_name, flags=re.IGNORECASE)
    
    # Remove season references like S01, S01-S06, COMPLETE
    series_name = re.sub(r'S0?\d+(?:-S0?\d+)?', '', series_name, flags=re.IGNORECASE)
    series_name = re.sub(r'Season\s+[0-9\-]+', '', series_name, flags=re.IGNORECASE)
    series_name = re.sub(r'\bCOMPLETE\b', '', series_name, flags=re.IGNORECASE)
    
    # Remove quality/format info (720p, 1080p, x264, x265, etc)
    series_name = re.sub(r'\d+p\b', '', series_name)
    series_name = re.sub(r'\b(?:WEBRip|BluRay|HDTV|DVDRip|BRRip|WEB-DL)\b', '', series_name, flags=re.IGNORECASE)
    series_name = re.sub(r'\bx26[45]\b', '', series_name)
    series_name = re.sub(r'\b(?:HEVC|H\.264|MPEG2|H 264)\b', '', series_name)
    series_name = re.sub(r'\b(?:AAC|EAC3|DTS|FLAC|MP3|DDP5)\b', '', series_name)
    series_name = re.sub(r'\b\d+bit\b', '', series_name)
    
    # Remove provider names
    series_name = re.sub(r'\b(?:NF|Netflix|AMZN|Amazon|Mixed)\b', '', series_name, flags=re.IGNORECASE)
    
    # Remove parenthetical content except for years like (2020)
    # Keep parentheses with 4-digit years, remove others
    series_name = re.sub(r'\([^)]*[a-zA-Z][^)]*\)', '', series_name)
    
    # Clean up dots, dashes, and extra spaces
    series_name = series_name.replace('.', ' ')
    series_name = re.sub(r'\s+', ' ', series_name)
    series_name = series_name.strip()
    series_name = re.sub(r'^[-\s]+|[-\s]+$', '', series_name)
    
    # Remove trailing "-AGLET" and similar tracker suffixes  
    series_name = re.sub(r'\s*-\s*(?:[A-Z]+|[a-z]+)$', '', series_name)
    
    # Remove trailing standalone numbers (leftover from format strings like "DDP5.1")
    series_name = re.sub(r'\s+\d+$', '', series_name)
    
    # Final cleanup
    series_name = re.sub(r'\s+', ' ', series_name).strip()
    
    return series_name

def parse_episode_info(filename, parent_folder):
    """Extract episode and season info from filename or folder structure"""
    filename_lower = filename.lower()
    parent_lower = parent_folder.lower()
    
    # Try various patterns
    patterns = [
        r's(\d+)e(\d+)',  # S01E01
        r'season\s*(\d+).*episode\s*(\d+)',  # Season 1 Episode 1
        r'(\d+)x(\d+)',  # 1x01
        r'episode[\s_-]*(\d+)',  # Episode 01 (look for season in folder)
        r'ep[\s_-]*(\d+)',  # Ep 01
        r'e(\d+)',  # E01
        r'\[(\d+)\]',  # [01]
    ]
    
    season = None
    episode = None
    
    # Check filename first
    for pattern in patterns:
        match = re.search(pattern, filename_lower)
        if match:
            groups = match.groups()
            if len(groups) == 2:
                season = int(groups[0])
                episode = int(groups[1])
                break
            elif len(groups) == 1:
                episode = int(groups[0])
    
    # Check parent folder for season info
    season_match = re.search(r'season[\s_-]*(\d+)', parent_lower)
    if season_match and not season:
        season = int(season_match.group(1))
    
    # Alternative season pattern in folder
    if not season:
        season_match = re.search(r's(\d+)', parent_lower)
        if season_match:
            season = int(season_match.group(1))
    
    # If we found episode but no season, default to season 1
    if episode and not season:
        season = 1
    
    return season, episode

def scan_media_library():
    """Scan the media folder and organize files into series and movies"""
    series = {}
    movies = []
    progress_data = load_progress()
    
    # Skip the MediaLibrary folder itself
    repo_folder = Path(__file__).parent
    
    # Folders to completely skip
    skip_folders = {'BOOKS', 'WATCHED', 'Featurettes', 'EXTRAS', 'Documentaries', 'Specials'}
    
    for root, dirs, files in os.walk(MEDIA_FOLDER):
        root_path = Path(root)
        
        # Skip the repo folder
        if root_path == repo_folder or repo_folder in root_path.parents:
            continue
        
        # Skip specific folders
        if any(skip in root_path.name for skip in skip_folders):
            continue
        
        for file in files:
            file_path = root_path / file
            ext = file_path.suffix.lower()
            
            if ext not in VIDEO_EXTENSIONS:
                continue
            
            file_path_str = str(file_path)
            rel_path = file_path.relative_to(MEDIA_FOLDER)
            
            # Get file info
            file_size = file_path.stat().st_size
            file_modified = datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
            
            # Get progress info
            progress_info = progress_data.get(file_path_str, {})
            current_time = progress_info.get('position', 0)
            duration = progress_info.get('duration', 0)
            last_played = progress_info.get('last_played', None)
            completed = progress_info.get('completed', False)
            
            # Try to parse episode info
            season, episode = parse_episode_info(file, root_path.name)
            
            file_info = {
                'path': file_path_str,
                'name': file_path.stem,
                'size': file_size,
                'modified': file_modified,
                'current_time': current_time,
                'duration': duration,
                'last_played': last_played,
                'completed': completed,
                'progress_percent': (current_time / duration * 100) if duration else 0
            }
            
            # Determine if this is part of a series or a standalone movie
            if season is not None and episode is not None:
                # This is a series episode
                # Find the top-level series folder
                series_name = None
                rel_parts = rel_path.parts[:-1]  # Exclude the filename
                
                # If file is in a Season subfolder, use the parent folder as series name
                if rel_parts:
                    # Check if the immediate parent is a season folder
                    if rel_parts[-1] and re.search(r'season[\s_-]*\d+', rel_parts[-1].lower()):
                        # Go up two levels for the series name
                        if len(rel_parts) >= 2:
                            series_name = rel_parts[-2]
                        else:
                            series_name = rel_parts[-1]
                    else:
                        # Use the first (top-level) folder as series name
                        series_name = rel_parts[0] if rel_parts else root_path.name
                else:
                    # File is directly in parent folder - extract series name from filename
                    # Remove "WATCHED" prefix and extract series name before season info
                    filename_clean = file_path.stem
                    filename_clean = re.sub(r'^WATCHED\s+', '', filename_clean, flags=re.IGNORECASE)
                    # Extract everything before the season/episode info
                    series_name = re.sub(r'\s*[Ss]0?\d+[Ee]0?\d+.*$', '', filename_clean).strip()
                
                if not series_name:
                    series_name = root_path.name
                
                # Clean up series name
                series_name = clean_series_name(series_name)
                
                if not series_name or series_name.lower() in ('torrent', 'medialibrary'):
                    continue
                
                if series_name not in series:
                    series[series_name] = {}
                
                if season not in series[series_name]:
                    series[series_name][season] = []
                
                file_info['season'] = season
                file_info['episode'] = episode
                series[series_name][season].append(file_info)
            else:
                # This is a standalone movie - skip featurettes/extras
                if any(skip.lower() in file_path_str.lower() for skip in skip_folders):
                    continue
                
                movies.append(file_info)
    
    # Sort episodes within each season
    for series_name in series:
        for season in series[series_name]:
            series[series_name][season].sort(key=lambda x: x['episode'])
    
    # Sort movies by name
    movies.sort(key=lambda x: x['name'])
    
    return {'series': series, 'movies': movies}

@app.route('/')
def index():
    """Serve the main HTML page"""
    return send_from_directory('static', 'index.html')

@app.route('/api/library')
def get_library():
    """Get the complete media library with cover URLs"""
    library = scan_media_library()
    covers_cache = load_covers_cache()
    
    # Add cover URLs to series
    for series_name in library['series']:
        cache_key = f"series:{series_name}"
        if cache_key not in covers_cache:
            # Try to fetch cover image
            cover_url = search_cover_image(series_name, 'series')
            if cover_url:
                covers_cache[cache_key] = cover_url
        
        cover_url = covers_cache.get(cache_key)
        
        # Add cover URL to all episodes in this series
        for season_episodes in library['series'][series_name].values():
            for episode in season_episodes:
                episode['cover_url'] = cover_url
    
    # Add cover URLs to movies
    for movie in library['movies']:
        cache_key = f"movie:{movie['name']}"
        if cache_key not in covers_cache:
            # Try to fetch cover image
            cover_url = search_cover_image(movie['name'], 'movie')
            if cover_url:
                covers_cache[cache_key] = cover_url
        
        movie['cover_url'] = covers_cache.get(cache_key)
    
    # Save updated cache
    save_covers_cache(covers_cache)
    
    return jsonify(library)

@app.route('/api/play', methods=['POST'])
def play_video():
    """Play a video in VLC"""
    data = request.json
    video_path = data.get('path')
    start_time = data.get('start_time', 0)
    
    print(f"[PLAY] Received request to play: {video_path}")
    print(f"[PLAY] Start time: {start_time}")
    
    if not video_path:
        return jsonify({'error': 'No video path provided'}), 400
    
    video_file = Path(video_path)
    if not video_file.exists():
        print(f"[ERROR] Video not found at: {video_path}")
        return jsonify({'error': f'Video not found: {video_path}'}), 404
    
    # Check VLC exists
    if not Path(VLC_PATH).exists():
        print(f"[ERROR] VLC not found at: {VLC_PATH}")
        return jsonify({'error': f'VLC not found at {VLC_PATH}'}), 500
    
    # Build VLC command with HTTP interface
    cmd = [
        VLC_PATH,
        str(video_file),  # Ensure path is string
        f'--start-time={int(start_time)}',
        '--extraintf=http',
        f'--http-port={VLC_HTTP_PORT}',
        f'--http-password={VLC_HTTP_PASSWORD}',
        '--no-video-title-show'  # Don't show filename on video
    ]
    
    print(f"[PLAY] Launching VLC with command: {' '.join(cmd)}")
    
    try:
        subprocess.Popen(cmd)
        print(f"[PLAY] VLC launched successfully")
        return jsonify({'success': True, 'message': 'VLC launched'})
    except Exception as e:
        print(f"[ERROR] Failed to launch VLC: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/progress', methods=['POST'])
def update_progress():
    """Update watch progress for a video"""
    data = request.json
    video_path = data.get('path')
    position = data.get('position', 0)
    duration = data.get('duration', 0)
    completed = data.get('completed', False)
    
    if not video_path:
        return jsonify({'error': 'Video path required'}), 400
    
    progress_data = load_progress()
    progress_data[video_path] = {
        'position': position,
        'duration': duration,
        'last_played': datetime.now().isoformat(),
        'completed': completed
    }
    save_progress(progress_data)
    
    return jsonify({'success': True})

@app.route('/api/vlc/status')
def vlc_status():
    """Get VLC playback status"""
    try:
        response = requests.get(
            f'http://localhost:{VLC_HTTP_PORT}/requests/status.json',
            auth=('', VLC_HTTP_PASSWORD),
            timeout=1
        )
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            return jsonify({'error': 'VLC not responding'}), 503
    except:
        return jsonify({'error': 'VLC not running'}), 503

@app.route('/api/next-episode', methods=['POST'])
def get_next_episode():
    """Get the next episode in a series"""
    data = request.json
    current_path = data.get('path')
    
    library = scan_media_library()
    
    # Find current episode in series
    for series_name, seasons in library['series'].items():
        for season_num, episodes in seasons.items():
            for idx, episode in enumerate(episodes):
                if episode['path'] == current_path:
                    # Found current episode, return next one
                    if idx + 1 < len(episodes):
                        # Next episode in same season
                        return jsonify(episodes[idx + 1])
                    else:
                        # Check next season
                        next_season = season_num + 1
                        if next_season in seasons and seasons[next_season]:
                            return jsonify(seasons[next_season][0])
    
    return jsonify({'error': 'No next episode found'}), 404

@app.route('/api/reset-progress', methods=['POST'])
def reset_progress():
    """Reset progress for a specific video"""
    data = request.json
    video_path = data.get('path')
    
    if not video_path:
        return jsonify({'error': 'Video path required'}), 400
    
    progress_data = load_progress()
    if video_path in progress_data:
        del progress_data[video_path]
        save_progress(progress_data)
    
    return jsonify({'success': True})

@app.route('/api/cover', methods=['GET', 'POST'])
def handle_cover():
    """Get or set cover image for a title"""
    if request.method == 'GET':
        title = request.args.get('title')
        media_type = request.args.get('type', 'movie')  # 'movie' or 'series'
        
        if not title:
            return jsonify({'error': 'Title required'}), 400
        
        covers_cache = load_covers_cache()
        cache_key = f"{media_type}:{title}"
        
        if cache_key in covers_cache:
            return jsonify({'cover_url': covers_cache[cache_key]})
        
        # Try to find cover from TMDB or other sources
        cover_url = search_cover_image(title, media_type)
        
        if cover_url:
            covers_cache[cache_key] = cover_url
            save_covers_cache(covers_cache)
            return jsonify({'cover_url': cover_url})
        
        return jsonify({'cover_url': None})
    
    elif request.method == 'POST':
        data = request.json
        title = data.get('title')
        media_type = data.get('type', 'movie')
        cover_url = data.get('cover_url')
        
        if not title or not cover_url:
            return jsonify({'error': 'Title and cover_url required'}), 400
        
        covers_cache = load_covers_cache()
        cache_key = f"{media_type}:{title}"
        covers_cache[cache_key] = cover_url
        save_covers_cache(covers_cache)
        
        return jsonify({'success': True})

def search_cover_image(title, media_type='movie'):
    """Search for cover image from online sources"""
    try:
        # Clean up title for searching
        search_title = re.sub(r'\s*\(.*?\)$', '', title).strip()
        
        if media_type == 'series':
            # Try TVMaze API for TV series (no key required)
            try:
                url = "https://api.tvmaze.com/singlesearch/shows"
                params = {'q': search_title}
                response = requests.get(url, params=params, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    if data.get('image') and data['image'].get('medium'):
                        # Return the larger image size
                        return data['image']['medium'].replace('http://', 'https://')
            except Exception as e:
                print(f"[COVER] TVMaze error: {e}")
        else:
            # Try OpenLibrary/Google Books for better coverage
            try:
                # Use a simple approach with DuckDuckGo zero-click info
                # Or use Open Library API
                url = "https://openlibrary.org/search.json"
                params = {
                    'title': search_title,
                    'limit': 1
                }
                response = requests.get(url, params=params, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    if data.get('docs') and data['docs'][0].get('cover_i'):
                        cover_id = data['docs'][0]['cover_i']
                        return f"https://covers.openlibrary.org/b/id/{cover_id}-M.jpg"
            except Exception as e:
                print(f"[COVER] Open Library error: {e}")
        
        # Try TMDB API if key is available
        if TMDB_API_KEY:
            try:
                endpoint = f"https://api.themoviedb.org/3/search/{media_type}"
                params = {
                    'api_key': TMDB_API_KEY,
                    'query': search_title
                }
                response = requests.get(endpoint, params=params, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    if data.get('results'):
                        poster_path = data['results'][0].get('poster_path')
                        if poster_path:
                            return f"https://image.tmdb.org/t/p/w342{poster_path}"
            except Exception as e:
                print(f"[COVER] TMDB error: {e}")
        
        # No cover found
        return None
    except Exception as e:
        print(f"[COVER] Error searching for cover: {e}")
        return None

if __name__ == '__main__':
    print(f"Media Library Server Starting...")
    print(f"Scanning folder: {MEDIA_FOLDER}")
    print(f"VLC Path: {VLC_PATH}")
    print(f"Open http://localhost:5000 in your browser")
    app.run(debug=True, host='0.0.0.0', port=5000)
