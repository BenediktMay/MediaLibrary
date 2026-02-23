#!/usr/bin/env python3
"""
Build executable for Windows using PyInstaller

Run: python build_executable.py
Requires: pyinstaller
"""

import subprocess
import sys
from pathlib import Path

def build_executable():
    """Build desktop app as Windows executable"""
    
    print("📦 Building Media Library Desktop Application...")
    print()
    
    # Check if PyInstaller is installed
    try:
        import PyInstaller
    except ImportError:
        print("Installing PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "pyinstaller"])
    
    # Build the executable
    print("Compiling application...")
    subprocess.check_call([
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--windowed",
        "--name=MediaLibrary",
        "--icon=static/favicon.svg",
        "--add-data=static:static",
        "--hidden-import=vlc",
        "--hidden-import=PyQt6.sip",
        "desktop_app.py"
    ])
    
    print()
    print("✅ Build complete!")
    print()
    print("📁 Executable location: dist/MediaLibrary.exe")
    print()
    print("📋 Next steps:")
    print("  1. Copy 'dist/MediaLibrary.exe' to desired location")
    print("  2. Create a shortcut on your desktop")
    print("  3. Run the executable")
    print()

if __name__ == "__main__":
    build_executable()
