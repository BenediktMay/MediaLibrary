# 🎬 Media Library

A beautiful, dark-themed media library manager that automatically organizes and tracks your TV series and movies. Built with Python Flask backend and a modern HTML/CSS/JS frontend with orange accents.

## ✨ Features

- **Automatic Media Detection**: Scans parent folder for video files (MP4, MKV, AVI, MOV, WMV, FLV, WEBM, etc.)
- **Smart Organization**: Automatically detects TV series with seasons/episodes and standalone movies
- **Watch Progress Tracking**: Remembers where you left off in each video
- **VLC Integration**: Launches VLC player at the exact position you stopped
- **Auto-Play Next Episode**: Automatically plays the next episode when one finishes
- **Beautiful Dark Theme**: Modern UI with orange accents and smooth animations
- **Continue Watching**: Quick access to videos you're currently watching
- **Flexible Episode Detection**: Works with various naming conventions (S01E01, 1x01, Episode 1, etc.)

## 📋 Requirements

- Python 3.8 or higher
- VLC Media Player installed at: `C:\Program Files\VideoLAN\VLC\vlc.exe`
- Modern web browser (Chrome, Firefox, Edge)

## 🚀 Installation

1. **Install Python dependencies:**
   ```powershell
   pip install -r requirements.txt
   ```

2. **Verify VLC is installed:**
   Make sure VLC is installed at `C:\Program Files\VideoLAN\VLC\vlc.exe`

## 📁 Folder Structure

The tool scans the parent folder (`c:\Torrent\`) for media files. Organize your media like this:

```
c:\Torrent\
├── MediaLibrary\          (this repo)
│   ├── app.py
│   ├── static\
│   └── progress.json      (created automatically)
│
├── BreakingBad\           (TV Series)
│   ├── Season 1\
│   │   ├── S01E01.mkv
│   │   └── S01E02.mkv
│   └── Season 2\
│       └── S02E01.mkv
│
├── TheOffice\             (TV Series - flexible naming)
│   ├── Season1\
│   │   ├── Episode 1.mp4
│   │   └── Episode 2.mp4
│   └── Season2\
│       └── 2x01.mp4
│
├── Inception.mp4          (Standalone Movie)
└── Interstellar.mkv       (Standalone Movie)
```

## 🎯 Usage

1. **Start the server:**
   ```powershell
   python app.py
   ```

2. **Open your browser:**
   Navigate to `http://localhost:5000`

3. **Browse and play:**
   - Click on any movie or episode to play it in VLC
   - VLC will start at your last watched position
   - Progress is automatically saved
   - When an episode ends, the next one plays automatically

## 🎮 Features Guide

### Continue Watching
Shows videos you've started but haven't finished, sorted by most recently played.

### TV Series
- Organized by show name and season
- Click episode numbers to play
- Visual progress bars show watch status
- Auto-advance to next episode when one finishes

### Movies
- Grid view of all standalone movie files
- Shows watch progress if you've started watching

### Context Menu
Right-click on any video to:
- **Reset Progress**: Clear watch history for that video
- **Mark as Watched**: Mark a video as completed

### Keyboard Shortcuts
- Click **Refresh** button to rescan the media library

## ⚙️ Configuration

Edit `app.py` to customize:

```python
# Media folder location
MEDIA_FOLDER = Path(__file__).parent.parent

# VLC installation path
VLC_PATH = r"C:\Program Files\VideoLAN\VLC\vlc.exe"

# VLC HTTP interface settings
VLC_HTTP_PORT = 8080
VLC_HTTP_PASSWORD = "medialibrary"
```

## 🎨 Customization

### Change Accent Color
Edit `static/style.css`:
```css
:root {
    --primary-orange: #ff8c42;  /* Change this color */
}
```

### Supported Video Formats
Currently supports: .mp4, .mkv, .avi, .mov, .wmv, .flv, .webm, .m4v, .mpg, .mpeg, .3gp, .m2ts, .ts, .vob

Add more in `app.py`:
```python
VIDEO_EXTENSIONS = {'.mp4', '.mkv', '.your_format'}
```

## 🔧 Troubleshooting

### VLC doesn't launch
- Verify VLC is installed at the correct path
- Check that VLC is not already running with HTTP interface on port 8080

### Videos not detected
- Make sure video files are in the parent folder (`c:\Torrent\`)
- Check that files have supported extensions
- Click the Refresh button to rescan

### Progress not saving
- Check that `progress.json` can be created in the MediaLibrary folder
- Verify VLC HTTP interface is accessible

### Auto-play next episode not working
- Ensure VLC is launched with HTTP interface (the app does this automatically)
- Check that VLC HTTP port (8080) is not blocked by firewall

## 📊 Progress Storage

Watch progress is stored in `progress.json` in the repo folder:
```json
{
  "C:\\Torrent\\Show\\S01E01.mkv": {
    "position": 1234,
    "duration": 2400,
    "last_played": "2026-02-22T10:30:00",
    "completed": false
  }
}
```

## 🤝 Contributing

Feel free to customize this tool for your needs!

## 📝 License

MIT License - Feel free to use and modify as needed.