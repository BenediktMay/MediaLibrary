# 🚀 Desktop Application Quick Start Guide

## What You're Getting

A **professional desktop application** with:
- ✅ Embedded VLC player (no external windows)
- ✅ Beautiful dark interface with orange accents
- ✅ Automatic episode progression
- ✅ Watch progress tracking
- ✅ Seamless library ↔ player navigation
- ✅ Single integrated window

## Why Desktop App?

| Feature | Web App | Desktop App |
|---------|---------|------------|
| Player Type | External VLC | Embedded |
| Windows | Browser + VLC | Single App |
| Performance | HTTP polling | Direct control |
| User Experience | Multiple windows | Seamless |
| Navigation | Switch windows | One click |
| Startup | Browser needed | Standalone |

## Installation (First Time Only)

### Option 1: Windows Batch File (Easiest) ⭐
```powershell
# Just double-click this in File Explorer:
run_desktop.bat

# Or from PowerShell:
powershell -ExecutionPolicy Bypass -File run_desktop.bat
```

### Option 2: Command Line
```powershell
python run_desktop.py
```

### Option 3: Python Direct
```powershell
pip install -r requirements.txt
python desktop_app.py
```

## First Run

1. **Install dependencies:**
   ```
   run_desktop.bat     # This handles everything
   ```

2. **The app will:**
   - Install PyQt6, Flask, and other dependencies (if missing)
   - Start Flask backend automatically
   - Open desktop application window
   - Load your media library

3. **Wait for:**
   - Flask server to start (~1-2 seconds)
   - Library to load (~2-3 seconds)
   - Total startup: 3-5 seconds

## Using the Application

### Browse Your Library
- See all movies and TV series
- Shows cover images (fetched from TVMaze/OpenLibrary)
- Series organized by season
- "Continue Watching" section at top
- Last watched date for each series

### Play a Video
1. Click on any movie or episode thumbnail
2. Interface switches to player view
3. Video starts from where you left off
4. Progress bar filled shows your position

### Player Controls

```
┌──────────────────────────────────┐
│   Your Video Playing Here        │
│   (Black background)             │
├──────────────────────────────────┤
│ ▶ Play  ⏹ Stop  ← Back           │
│ 🔊 ███████░░ 75%                 │
│ 12:34 / 45:00                    │
└──────────────────────────────────┘
```

- **▶ Play / ⏸ Pause**: Toggle playback
- **⏹ Stop**: Stop watching
- **← Back to Library**: Return to browsing
- **🔊 Volume**: Adjust (0-100%)
- **Time Display**: Current position / Duration

### Return to Library
- Click **← Back to Library** button
- Video stops and returns to library
- Progress automatically saved

### Auto-Play Next Episode
- When episode finishes playing
- Next episode **automatically starts**
- No action needed, just keep watching!
- Works with series only (not movies)

## Keyboard Navigation

While in library:
- Click on any item to play
- Right-click for menu (Reset, Mark Watched, Delete)

While playing:
- Click back button to return to library

## Configuration

### Change Media Folder
Edit `app.py`, line ~15:
```python
MEDIA_FOLDER = Path(__file__).parent.parent  # c:\Torrent\
```

### Change VLC Path (if installed elsewhere)
Edit `app.py`, line ~17:
```python
VLC_PATH = r"C:\Path\To\VLC\vlc.exe"
```

### Change Accent Color
Edit `static/style.css`, line ~1:
```css
:root {
    --primary-orange: #ff8c42;  /* Change to your color */
}
```

## Troubleshooting

### "QWebChannel not available"
- Flask might not have started
- Wait 2-3 seconds for Flask
- Check console for errors

### No videos showing
- Verify media folder (parent of MediaLibrary)
- Check file extensions (.mp4, .mkv, .avi, etc.)
- Click Refresh button in library

### VLC won't play
- Check VLC is installed: `C:\Program Files\VideoLAN\VLC\vlc.exe`
- Verify media files are readable
- Try another file

### App crashes
- Run `verify_setup.py` to check installation
- Reinstall dependencies: `pip install -r requirements.txt --upgrade`
- Check Windows Event Viewer for errors

### Performance issues
- Close other applications
- Check available RAM (need ~300-400 MB)
- Ensure media folder is local (not network)

## Advanced: Create Windows Shortcut

1. **Create shortcut:**
   - Right-click desktop → New → Shortcut
   - Target: `python run_desktop.py`
   - Start in: `c:\Torrent\MediaLibrary`
   - Icon: `c:\Torrent\MediaLibrary\static\favicon.svg`

2. **Or run batch file:**
   - Right-click `run_desktop.bat`
   - Create shortcut
   - Add to desktop

## Advanced: Build Executable

To create a standalone `.exe` file (no Python required):

```powershell
python build_executable.py
# Creates: dist/MediaLibrary.exe
```

Then distribute and run `.exe` directly - no dependencies!

## File Locations

- **Settings**: `progress.json` - watch progress
- **Cache**: `covers_cache.json` - image URLs
- **Logs**: Console output while running
- **Exe**: `dist/MediaLibrary.exe` - if built

## Features

### Watch Progress
- Automatically saves to `progress.json`
- Next time you play, starts from last position
- Tracks duration and completion status

### Cover Images
- Auto-fetches from:
  - **TV Shows**: TVMaze API
  - **Movies**: Open Library API
- Cached to avoid repeated lookups
- Cache: `covers_cache.json`

### Smart Organization
- Automatically detects:
  - TV series (folders with seasons)
  - Movies (standalone files)
- Recognizes episode patterns:
  - `S01E01`, `1x01`, `Episode 1`, etc.
  - Various folder structures

### Series Sorting
- "Continue Watching": Sorted by last watched
- Movies: All movies in grid view
- Series: Sorted by most recently watched episode

## Getting Help

1. **Check console:**
   - Look for error messages
   - Red text indicates problems

2. **Run verification:**
   ```powershell
   python verify_setup.py
   ```

3. **Check documentation:**
   - `README.md` - General features
   - `DESKTOP_APP_ARCHITECTURE.md` - Technical details

## Version Info

- **App Type**: PyQt6 Desktop Application
- **Backend**: Flask REST API
- **Player**: Embedded LibVLC
- **UI**: Web-based HTML/CSS/JS
- **Platform**: Windows (Mac/Linux also supported)

## Next Steps

1. Run the app: `run_desktop.bat`
2. Enjoy your media library!
3. Customize colors/folder paths as needed
4. Create a shortcut for easy access

---

**Happy Watching! 🍿**

Questions? Check the README.md or DESKTOP_APP_ARCHITECTURE.md
