
"""
VYAAS AI - Termux Compatibility Layer
Handles Android-specific operations when running in Termux.
"""

import os
import sys
import subprocess
import shutil
import logging

# Configure logging
logger = logging.getLogger("termux_compat")

# Detect if running in Termux
IS_ANDROID = "ANDROID_ROOT" in os.environ or "TERMUX_VERSION" in os.environ

def is_android():
    return IS_ANDROID

def get_adb_path():
    """
    Get the path to ADB executable.
    On Windows: Uses hardcoded path or searches.
    On Android (Termux): checks for 'adb' in path.
    """
    if IS_ANDROID:
        # Check if android-tools is installed
        adb_path = shutil.which("adb")
        if adb_path:
            return adb_path
        else:
            logger.warning("ADB not found in Termux. Please run: pkg install android-tools")
            return None
    else:
        # Windows/Desktop paths
        paths = [
            r"C:\Users\mahes\AppData\Local\Android\Sdk\platform-tools\adb.exe",
            "adb"
        ]
        for path in paths:
            if shutil.which(path) or os.path.exists(path):
                return path
        return "adb"

def run_termux_command(command_list):
    """
    Run a command using termux-api or standard shell tools.
    """
    if not IS_ANDROID:
        return "Not running on Android"
    
    try:
        result = subprocess.run(command_list, capture_output=True, text=True, timeout=10)
        return result.stdout.strip()
    except Exception as e:
        return f"Error: {e}"

def termux_vibrate(duration_ms=500):
    """Vibrate the phone."""
    if IS_ANDROID:
        subprocess.run(["termux-vibrate", "-d", str(duration_ms)])

def termux_toast(message):
    """Show a toast message."""
    if IS_ANDROID:
        subprocess.run(["termux-toast", message])

def termux_speak(text):
    """Speak text using Termux TTS."""
    if IS_ANDROID:
        subprocess.run(["termux-tts-speak", text])

def termux_volume(stream, volume):
    """Set volume using termux-volume. Stream: music, call, system, ring, alarm, notification."""
    if IS_ANDROID:
        subprocess.run(["termux-volume", stream, str(volume)])

def termux_open_url(url):
    """Open a URL in the default Android browser using termux-open-url."""
    if IS_ANDROID:
        subprocess.run(["termux-open-url", url])

def termux_get_battery():
    """Get battery status using termux-battery-status."""
    if IS_ANDROID:
        try:
            res = subprocess.run(["termux-battery-status"], capture_output=True, text=True)
            import json
            return json.loads(res.stdout)
        except:
            return None
    return None
