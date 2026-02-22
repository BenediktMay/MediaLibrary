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
VLC_PATH = r"C:\Program Files\VideoLAN\VLC\vlc.exe"
VLC_HTTP_PORT = 8080
VLC_HTTP_PASSWORD = "medialibrary"

# Supported video formats
VIDEO_EXTENSIONS = {'.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm', 
                   '.m4v', '.mpg', '.mpeg', '.3gp', '.m2ts', '.ts', '.vob'}

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
    
    for root, dirs, files in os.walk(MEDIA_FOLDER):
        root_path = Path(root)
        
        # Skip the repo folder
        if root_path == repo_folder or repo_folder in root_path.parents:
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
                # Try to determine series name from folder structure
                series_name = None
                for parent in rel_path.parents:
                    parent_str = str(parent)
                    # Skip season folders
                    if not re.search(r'season[\s_-]*\d+', parent_str.lower()) and parent_str != '.':
                        series_name = parent_str
                        break
                
                if not series_name:
                    series_name = root_path.name
                
                if series_name not in series:
                    series[series_name] = {}
                
                if season not in series[series_name]:
                    series[series_name][season] = []
                
                file_info['season'] = season
                file_info['episode'] = episode
                series[series_name][season].append(file_info)
            else:
                # This is a standalone movie
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
    """Get the complete media library"""
    library = scan_media_library()
    return jsonify(library)

@app.route('/api/play', methods=['POST'])
def play_video():
    """Play a video in VLC"""
    data = request.json
    video_path = data.get('path')
    start_time = data.get('start_time', 0)
    
    if not video_path or not Path(video_path).exists():
        return jsonify({'error': 'Video not found'}), 404
    
    # Build VLC command with HTTP interface
    cmd = [
        VLC_PATH,
        video_path,
        f'--start-time={int(start_time)}',
        '--extraintf=http',
        f'--http-port={VLC_HTTP_PORT}',
        f'--http-password={VLC_HTTP_PASSWORD}',
        '--no-video-title-show'  # Don't show filename on video
    ]
    
    try:
        subprocess.Popen(cmd)
        return jsonify({'success': True, 'message': 'VLC launched'})
    except Exception as e:
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

if __name__ == '__main__':
    print(f"Media Library Server Starting...")
    print(f"Scanning folder: {MEDIA_FOLDER}")
    print(f"VLC Path: {VLC_PATH}")
    print(f"Open http://localhost:5000 in your browser")
    app.run(debug=True, host='0.0.0.0', port=5000)
