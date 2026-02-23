#!/usr/bin/env python3
"""
Run the Media Library Desktop Application
"""

import subprocess
import sys
import os

def main():
    """Install dependencies and run the desktop app"""
    
    # Install dependencies
    print("Installing dependencies...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt", "-q"])
    
    # Run the desktop app
    print("Starting Media Library Desktop Application...")
    subprocess.check_call([sys.executable, "desktop_app.py"])

if __name__ == "__main__":
    main()
