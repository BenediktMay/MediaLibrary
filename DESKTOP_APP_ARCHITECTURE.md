# 🎬 Desktop Application Architecture

## Overview

The Media Library Desktop Application combines the Flask backend with a PyQt6 desktop frontend featuring an embedded VLC player. This creates a seamless, professional application experience without requiring a browser.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                     Desktop Application                         │
│                                                                 │
│  ┌────────────────────────┐      ┌────────────────────────┐   │
│  │   QMainWindow          │      │     Flask Backend      │   │
│  │  (Main Container)      │      │                        │   │
│  │                        │      │  - Media Scanning      │   │
│  │  ┌──────────────────┐ │      │  - Progress Tracking   │   │
│  │  │ Stacked Widget   │ │      │  - Cover Fetching      │   │
│  │  │                  │ │      │  - File Management     │   │
│  │  │ ┌──────────────┐ │ │      │                        │   │
│  │  │ │Library View   │ │ │      │  (Running as     │   │
│  │  │ │(WebEngineView)│ │ │      │   subprocess on   │   │
│  │  │ └──────────────┘ │ │      │   port 5000)          │   │
│  │  │        ↕          │ │      │                        │   │
│  │  │ ┌──────────────┐ │ │      └────────────────────────┘   │
│  │  │ │ VLC Player   │ │ │                ↑                  │
│  │  │ │  - Play/Pause│ │ │                │ HTTP APIs        │
│  │  │ │  - Controls  │ │ │                │                  │
│  │  │ │  - Volume    │ │ │                ↓                  │
│  │  │ │  - Progress  │ │ │      ┌────────────────────────┐   │
│  │  │ └──────────────┘ │ │      │  DesktopBridge        │   │
│  │  └──────────────────┘ │      │  (PyQt Signal/Slot)    │   │
│  │                        │      │                        │   │
│  │  ┌──────────────────┐ │      │  - playMedia()        │   │
│  │  │ DesktopBridge    │──────→ │  - goBack()           │   │
│  │  │(QObject)         │ │      │                        │   │
│  │  │                  │ │      └────────────────────────┘   │
│  │  │ QWebChannel      │ │            ↑                      │
│  │  │ (JS Bridge)      │ │            │ JavaScript calls    │
│  │  └──────────────────┘ │            │                     │
│  └────────────────────────┘      ┌─────────────────────┐     │
│                                  │   JavaScript        │     │
│                                  │   (frontend/app.js) │     │
│                                  │                     │     │
│                                  │ window.desktopBridge│     │
│                                  │ .playMedia()        │     │
│                                  └─────────────────────┘     │
└─────────────────────────────────────────────────────────────────┘
```

## Key Components

### 1. PyQt6 Main Application (`desktop_app.py`)

**Class: MediaLibraryApp (QMainWindow)**
- Main application window
- Creates stacked widget for view switching
- Manages Flask server subprocess
- Handles window lifecycle

**Key Features:**
- Starts Flask backend automatically
- Manages Python-JavaScript communication via `DesktopBridge`
- Communicates with user (back button, play requests)
- Stops Flask server on close

### 2. Library View (QWebEngineView)

- Embeds the Flask web interface (HTML/CSS/JS)
- Loads from `http://localhost:5000`
- Communicates with Python via `QWebChannel`
- Allows user to browse and select media

**JavaScript Bridge Integration:**
```javascript
// Automatically initialized when page loads
window.desktopBridge.playMedia(filePath, startTime)
window.desktopBridge.goBack()
```

### 3. VLC Player Widget

**Class: VLCPlayer (QWidget)**
- Embeds LibVLC (python-vlc library)
- Provides playback controls
- Shows time/duration
- Volume control
- Back to library button

**Controls:**
- ▶/⏸ Play/Pause toggle
- ⏹ Stop playback
- ← Back to Library (returns to browse view)
- Volume slider
- Time display (current / total)

### 4. Desktop Bridge (DesktopBridge - QObject)

**Purpose:** Two-way communication between JavaScript and Python

**Methods Called from JavaScript:**
```python
playMedia(file_path: str, start_position: float)
    # Called when user clicks play in the library view
    # Emits play_requested signal with file path and start time
    
goBack()
    # Called when user clicks back button in player
    # Emits back_requested signal
```

**Signals Connected to UI:**
```python
play_requested → show_player(file_path, start_position)
back_requested → show_library()
```

## Communication Flow

### Playing a Media File

```
User clicks "Play" on episode/movie
        ↓
JavaScript playMedia() is called
        ↓
Check if isDesktopApp && desktopBridge available
        ↓
Call: desktopBridge.playMedia(path, startTime)
        ↓
PyQt6 receives via QWebChannel
        ↓
DesktopBridge.playMedia() emits play_requested signal
        ↓
MediaLibraryApp.show_player(file_path, start_position)
        ↓
Switch stacked widget to player view
        ↓
VLCPlayer.play_file() starts playback
```

### Returning to Library

```
User clicks "← Back to Library"
        ↓
VLCPlayer.back_button.clicked signal
        ↓
MediaLibraryApp.show_library()
        ↓
VLCPlayer.stop() called
        ↓
Switch stacked widget to library view
```

## Key Differences from Web Version

### Web Version (Flask Only)
- Uses external VLC application
- Communicates via HTTP polling (every 30 seconds)
- Progress tracked by monitoring VLC HTTP interface
- Browser window + separate VLC window

### Desktop Version (PyQt6 + Flask)
- Embedded LibVLC (python-vlc)
- Direct VLC control (no HTTP polling needed)
- Direct memory communication
- Single integrated window
- Seamless navigation

## File Structure

```
MediaLibrary/
├── desktop_app.py          # Main PyQt6 application
├── app.py                  # Flask backend (unchanged)
├── static/
│   ├── index.html         # Web interface
│   ├── app.js             # Enhanced with desktop bridge detection
│   ├── style.css          # Styling
│   └── favicon.svg        # Icon
├── requirements.txt        # Dependencies (updated with PyQt6)
├── run_desktop.py         # Easy launcher script
├── run_desktop.bat        # Windows batch launcher
├── verify_setup.py        # Setup verification script
├── build_executable.py    # Executable builder (optional)
└── README.md             # Updated with desktop app instructions
```

## Dependencies

**New Dependencies (for desktop app):**
- `PyQt6==6.6.1` - GUI framework
- `PyQt6-WebEngine==6.6.1` - Web embedding
- `python-vlc==3.0.20123` - Direct VLC control

**Existing Dependencies (still used):**
- `Flask==3.0.0` - Backend server
- `requests==2.31.0` - API calls
- `flask-cors==4.0.0` - CORS support

## Runtime Behavior

1. **Startup:**
   - PyQt6 creates main window
   - Flask subprocess started in background (port 5000)
   - QWebEngineView loads `http://localhost:5000`
   - JavaScript detects desktop bridge and emits `desktopBridgeReady`
   - Library automatically loads and displays

2. **During Use:**
   - User browses library (HTML/CSS/JS)
   - Clicking play triggers JavaScript → Python communication
   - Desktop app switches to player view
   - VLC media plays with controls available
   - Clicking back stops playback and returns to library
   - Progress automatically saved to Flask backend

3. **Shutdown:**
   - User closes application window
   - Flask subprocess terminated
   - VLC playback stopped
   - Application exits cleanly

## Performance Considerations

1. **Memory Usage:**
   - Python interpreter: ~50-100 MB
   - Flask backend: ~20-30 MB
   - LibVLC: ~30-50 MB
   - PyQt6/WebEngine: ~100-150 MB
   - Total: ~200-300 MB typical usage

2. **Startup Time:**
   - PyQt6 loading: ~1-2 seconds
   - Flask startup: ~1-2 seconds
   - WebEngineView page load: ~1-2 seconds
   - Total: ~3-5 seconds (system dependent)

3. **Playback:**
   - Direct VLC control (no HTTP polling overhead)
   - Minimal network traffic
   - Smooth playback and responsiveness

## Future Enhancements

1. **Playlist Support:**
   - Add queue management
   - Multi-episode selection

2. **Subtitle Handling:**
   - Subtitle track selection
   - Display settings UI

3. **Advanced Search:**
   - Full-text search
   - Genre/category filtering

4. **Keyboard Shortcuts:**
   - Space for play/pause
   - Arrow keys for prev/next
   - Escape to return to library

5. **Customization:**
   - User preferences window
   - Theme selection

6. **Performance Optimization:**
   - Lazy-load thumbnails
   - Cache improvements
   - Faster startup

## Troubleshooting

**Desktop bridge not connecting:**
- Check browser console for errors
- Verify QWebChannel script loaded correctly
- Check Flask server is running

**VLC playback issues:**
- Verify VLC is installed
- Check file paths are accessible
- Ensure sufficient disk space

**Slow performance:**
- Check system resources
- Verify Flask backend is responsive
- Monitor network if using network storage

## Running the Application

### Simple Start (Recommended)
```powershell
# Windows
run_desktop.bat

# Or Python
python run_desktop.py
```

### Verify Setup
```powershell
python verify_setup.py
```

### Build Executable (Windows)
```powershell
python build_executable.py
# Creates: dist/MediaLibrary.exe
```

---

**Version:** 2.0 (Desktop)
**Created:** February 2026
**Technology Stack:** Python 3.11, PyQt6 6.6, Flask 3.0, LibVLC 3.0
