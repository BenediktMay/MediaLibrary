#!/usr/bin/env python3
"""
Media Library Desktop Application
Combines Flask backend with PyQt6 frontend and embedded VLC player
"""

import sys
import os
import json
import subprocess
import time
import threading
import vlc
from pathlib import Path

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QLabel, QStackedWidget, QFrame, QSlider
)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import Qt, QTimer, QUrl, pyqtSignal, QObject, QSize
from PyQt6.QtGui import QIcon, QFont, QColor
from PyQt6.QtWidgets import QDialog, QMessageBox
from PyQt6.QtWebChannel import QWebChannel

# Configuration
FLASK_PORT = 5000
FLASK_HOST = "127.0.0.1"
WINDOW_WIDTH = 1400
WINDOW_HEIGHT = 900

# Paths
APP_DIR = Path(__file__).parent
MEDIA_DIR = APP_DIR.parent


class DesktopBridge(QObject):
    """Bridge between JavaScript and Python"""
    
    # Signal emitted when JavaScript calls play
    play_requested = pyqtSignal(str, float)  # file_path, start_position
    back_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
    
    def playMedia(self, file_path, start_position=0):
        """Called from JavaScript to play a media file in the desktop player"""
        print(f"Play requested: {file_path} at {start_position}")
        self.play_requested.emit(file_path, float(start_position))
    
    def goBack(self):
        """Called from JavaScript to go back to library"""
        print("Back requested")
        self.back_requested.emit()


class VLCPlayer(QWidget):
    """VLC Player widget with control buttons"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.vlc_instance = vlc.Instance()
        self.media_list_player = self.vlc_instance.media_list_player_new()
        self.media_list = self.vlc_instance.media_list_new()
        self.media_list_player.set_media_list(self.media_list)
        
        self.current_file = None
        self.is_playing = False
        
        self.init_ui()
        
    def init_ui(self):
        """Initialize VLC player UI"""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create VLC media object for display
        self.vlc_widget = QWidget()
        self.vlc_widget.setStyleSheet("background-color: #000000;")
        layout.addWidget(self.vlc_widget)
        
        # Controls
        controls_layout = QHBoxLayout()
        controls_layout.setContentsMargins(10, 10, 10, 10)
        
        # Play/Pause button
        self.play_button = QPushButton("▶ Play")
        self.play_button.setStyleSheet(self._button_style())
        self.play_button.clicked.connect(self.toggle_play)
        controls_layout.addWidget(self.play_button)
        
        # Stop button
        self.stop_button = QPushButton("⏹ Stop")
        self.stop_button.setStyleSheet(self._button_style())
        self.stop_button.clicked.connect(self.stop)
        controls_layout.addWidget(self.stop_button)
        
        # Back button
        self.back_button = QPushButton("← Back to Library")
        self.back_button.setStyleSheet(self._button_style("#ff8c42"))
        controls_layout.addWidget(self.back_button)
        
        # Time label
        self.time_label = QLabel("00:00 / 00:00")
        self.time_label.setStyleSheet("color: #ffffff; font-size: 12px;")
        controls_layout.addWidget(self.time_label)
        
        # Volume
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setMinimum(0)
        self.volume_slider.setMaximum(100)
        self.volume_slider.setValue(80)
        self.volume_slider.setMaximumWidth(100)
        self.volume_slider.setStyleSheet(self._slider_style())
        self.volume_slider.sliderMoved.connect(self.set_volume)
        controls_layout.addWidget(QLabel("🔊"))
        controls_layout.addWidget(self.volume_slider)
        
        layout.addLayout(controls_layout)
        
        self.setLayout(layout)
        self.setStyleSheet("background-color: #1a1a1a;")
        
        # Timer for position updates
        self.position_timer = QTimer()
        self.position_timer.timeout.connect(self.update_position)
        self.position_timer.start(500)
        
    def _button_style(self, color="#ff8c42"):
        """Generate button stylesheet"""
        return f"""
            QPushButton {{
                background-color: {color};
                color: #ffffff;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #b86a2f;
            }}
            QPushButton:pressed {{
                background-color: #8b4f22;
            }}
        """
    
    def _slider_style(self):
        """Generate slider stylesheet"""
        return """
            QSlider::groove:horizontal {
                background-color: #404040;
                height: 8px;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background-color: #ff8c42;
                width: 14px;
                margin: -3px 0;
                border-radius: 7px;
            }
            QSlider::handle:horizontal:hover {
                background-color: #ffaa6b;
            }
        """
    
    def play_file(self, file_path, start_position=0):
        """Play a media file"""
        try:
            media = self.vlc_instance.media_new(str(file_path))
            self.media_list.clear()
            self.media_list.add_media(media)
            self.media_list_player.play()
            
            # Set start position after brief delay to allow media to load
            time.sleep(0.5)
            if start_position > 0:
                self.media_list_player.get_media_player().set_time(int(start_position * 1000))
            
            self.current_file = file_path
            self.is_playing = True
            self.play_button.setText("⏸ Pause")
            
            return True
        except Exception as e:
            print(f"Error playing file: {e}")
            return False
    
    def toggle_play(self):
        """Toggle play/pause"""
        if not self.is_playing:
            self.media_list_player.play()
            self.is_playing = True
            self.play_button.setText("⏸ Pause")
        else:
            self.media_list_player.pause()
            self.is_playing = False
            self.play_button.setText("▶ Play")
    
    def stop(self):
        """Stop playback"""
        self.media_list_player.stop()
        self.is_playing = False
        self.play_button.setText("▶ Play")
        self.current_file = None
        self.time_label.setText("00:00 / 00:00")
    
    def set_volume(self, value):
        """Set volume level (0-100)"""
        if self.media_list_player.get_media_player():
            self.media_list_player.get_media_player().audio_set_volume(value)
    
    def update_position(self):
        """Update time display"""
        mp = self.media_list_player.get_media_player()
        if mp:
            try:
                current_time = mp.get_time() / 1000  # Convert to seconds
                duration = mp.get_length() / 1000
                
                if duration > 0:
                    current_str = self._format_time(current_time)
                    duration_str = self._format_time(duration)
                    self.time_label.setText(f"{current_str} / {duration_str}")
            except:
                pass
    
    @staticmethod
    def _format_time(seconds):
        """Format seconds to MM:SS"""
        if seconds < 0:
            return "00:00"
        minutes = int(seconds) // 60
        secs = int(seconds) % 60
        return f"{minutes:02d}:{secs:02d}"
    
    def get_current_position(self):
        """Get current playback position in seconds"""
        mp = self.media_list_player.get_media_player()
        if mp:
            return mp.get_time() / 1000
        return 0


class MediaLibraryApp(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        self.flask_process = None
        self.is_library_view = True
        
        # Create bridge for JS communication
        self.bridge = DesktopBridge()
        self.bridge.play_requested.connect(self.show_player)
        self.bridge.back_requested.connect(self.show_library)
        
        # Start Flask server
        self.start_flask_server()
        time.sleep(1)  # Give Flask time to start
        
        # Initialize UI
        self.init_ui()
        
        # Set window properties
        self.setWindowTitle("Media Library")
        self.setWindowIcon(self._create_icon())
        self.setGeometry(100, 100, WINDOW_WIDTH, WINDOW_HEIGHT)
        
    def init_ui(self):
        """Initialize main UI"""
        # Central widget with stacked layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        central_widget.setLayout(layout)
        
        # Stacked widget for switching between views
        self.stacked_widget = QStackedWidget()
        
        # Library view (web-based)
        self.library_view = self.create_library_view()
        self.stacked_widget.addWidget(self.library_view)
        
        # Player view
        self.player_view = VLCPlayer()
        self.player_view.back_button.clicked.connect(self.show_library)
        self.stacked_widget.addWidget(self.player_view)
        
        layout.addWidget(self.stacked_widget)
        
        # Apply dark theme
        self.setStyleSheet("""
            QMainWindow {
                background-color: #0f0f0f;
            }
            QLabel {
                color: #ffffff;
            }
        """)
    
    def create_library_view(self):
        """Create web view for library"""
        view = QWebEngineView()
        
        # Set up web channel for JS-Python communication
        channel = QWebChannel()
        channel.registerObject("desktopBridge", self.bridge)
        view.page().setWebChannel(channel)
        
        # Inject JavaScript to set up bridge after page load
        def on_load_finished(ok):
            if ok:
                # Inject the qwebchannel library and setup
                view.page().runJavaScript("""
                (function() {
                    console.log('Initializing desktop bridge...');
                    var scriptTag = document.createElement('script');
                    scriptTag.src = 'qrc:///qtwebchannel/qwebchannel.js';
                    scriptTag.onload = function() {
                        console.log('QWebChannel library loaded');
                        new QWebChannel(qt.webChannelTransport, function(channel) {
                            window.desktopBridge = channel.objects.desktopBridge;
                            console.log('Desktop bridge connected!');
                            // Notify app that bridge is ready
                            window.dispatchEvent(new CustomEvent('desktopBridgeReady'));
                        });
                    };
                    document.head.appendChild(scriptTag);
                })();
                """)
        
        view.page().loadFinished.connect(on_load_finished)
        
        url = QUrl(f"http://{FLASK_HOST}:{FLASK_PORT}")
        view.load(url)
        return view
    
    def show_library(self):
        """Switch to library view"""
        self.stacked_widget.setCurrentWidget(self.library_view)
        self.is_library_view = True
        self.player_view.stop()
    
    def show_player(self, file_path, start_position=0):
        """Switch to player view and play file"""
        self.stacked_widget.setCurrentWidget(self.player_view)
        self.is_library_view = False
        self.player_view.play_file(file_path, start_position)
    
    def _create_icon(self):
        """Create simple icon"""
        # Return empty icon - can be enhanced later
        return QIcon()
    
    def start_flask_server(self):
        """Start Flask backend server"""
        try:
            # Use pythonw.exe to run Flask without console window
            python_exe = sys.executable
            self.flask_process = subprocess.Popen(
                [python_exe, str(APP_DIR / "app.py")],
                cwd=str(APP_DIR),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            )
            print(f"Flask server started (PID: {self.flask_process.pid})")
        except Exception as e:
            print(f"Error starting Flask server: {e}")
    
    def closeEvent(self, event):
        """Clean up on application close"""
        # Stop Flask server
        if self.flask_process:
            try:
                self.flask_process.terminate()
                self.flask_process.wait(timeout=5)
                print("Flask server stopped")
            except Exception as e:
                print(f"Error stopping Flask server: {e}")
                self.flask_process.kill()
        
        event.accept()


def main():
    """Main entry point"""
    app = QApplication(sys.argv)
    
    window = MediaLibraryApp()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
