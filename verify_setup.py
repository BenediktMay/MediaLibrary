#!/usr/bin/env python3
"""
Test script to verify desktop app setup
"""

import sys
import subprocess
from pathlib import Path

def check_python_version():
    """Check Python version"""
    print("✓ Checking Python version...", end=" ")
    if sys.version_info >= (3, 8):
        print(f"✅ {sys.version.split()[0]}")
        return True
    else:
        print(f"❌ Found {sys.version.split()[0]}, need 3.8+")
        return False

def check_dependencies():
    """Check if required packages are installed"""
    print("✓ Checking dependencies...")
    required = ['flask', 'flask_cors', 'requests', 'PyQt6', 'PyQt6.QtWebEngineWidgets', 'vlc']
    all_installed = True
    
    for package in required:
        try:
            if '.' in package:
                __import__('.'.join(package.split('.')[:-1]))
            else:
                __import__(package)
            print(f"  ✅ {package}")
        except ImportError:
            print(f"  ❌ {package} - NOT INSTALLED")
            all_installed = False
    
    return all_installed

def check_vlc_installed():
    """Check if VLC is installed"""
    print("✓ Checking VLC...", end=" ")
    vlc_path = Path(r"C:\Program Files\VideoLAN\VLC\vlc.exe")
    if vlc_path.exists():
        print(f"✅ Found at {vlc_path}")
        return True
    else:
        print(f"❌ Not found at {vlc_path}")
        print("  Please install VLC from: https://www.videolan.org/vlc/")
        return False

def check_flask_backend():
    """Check if Flask app.py exists"""
    print("✓ Checking Flask backend...", end=" ")
    app_path = Path(__file__).parent / "app.py"
    if app_path.exists():
        print(f"✅ Found {app_path}")
        return True
    else:
        print(f"❌ Not found")
        return False

def check_desktop_app():
    """Check if desktop_app.py exists"""
    print("✓ Checking desktop app...", end=" ")
    app_path = Path(__file__).parent / "desktop_app.py"
    if app_path.exists():
        print(f"✅ Found {app_path}")
        return True
    else:
        print(f"❌ Not found")
        return False

def main():
    """Run all checks"""
    print("🧪 Media Library Desktop App - Setup Verification")
    print("=" * 50)
    print()
    
    checks = [
        check_python_version,
        check_dependencies,
        check_vlc_installed,
        check_flask_backend,
        check_desktop_app,
    ]
    
    results = []
    for check in checks:
        try:
            results.append(check())
        except Exception as e:
            print(f"❌ Error: {e}")
            results.append(False)
        print()
    
    print("=" * 50)
    if all(results):
        print("✅ All checks passed! Ready to run.")
        print()
        print("📱 To start the desktop app:")
        print("   Windows: run_desktop.bat")
        print("   Or:      python run_desktop.py")
        return 0
    else:
        print("❌ Some checks failed. Please fix the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
