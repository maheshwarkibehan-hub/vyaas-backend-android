"""
VYAAS AI - Desktop Bridge (HTTP Version)
Run this script on your PC to receive and execute commands from the cloud AI agent.

This version uses HTTP polling instead of LiveKit, which is simpler and more reliable.

Usage:
    python vyaas_desktop_bridge.py

Requirements:
    pip install pyautogui pyperclip requests python-dotenv
"""

import asyncio
import json
import logging
import subprocess
import os
import sys
import time
import urllib.parse
import requests
from datetime import datetime
from threading import Thread
from http.server import HTTPServer, BaseHTTPRequestHandler
from dotenv import load_dotenv

# Optional imports (graceful fallback)
try:
    import pyautogui
    pyautogui.FAILSAFE = True  # Move mouse to corner to abort
except ImportError:
    pyautogui = None
    print("⚠️ pyautogui not installed. Some features won't work. Run: pip install pyautogui")

try:
    import pyperclip
except ImportError:
    pyperclip = None
    print("⚠️ pyperclip not installed. Clipboard features limited. Run: pip install pyperclip")

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - VYAAS Bridge - %(levelname)s - %(message)s'
)
logger = logging.getLogger("vyaas_bridge")

# Configuration
BRIDGE_PORT = 18790
BRIDGE_SECRET = os.getenv("BRIDGE_SECRET", "vyaas_local_bridge_2025")

# Command queue
command_queue = []
command_results = {}


class BridgeHandler(BaseHTTPRequestHandler):
    """HTTP handler for receiving commands"""
    
    def log_message(self, format, *args):
        pass  # Suppress HTTP logs
    
    def do_GET(self):
        """Health check"""
        if self.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok", "bridge": "vyaas_desktop"}).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_POST(self):
        """Receive command"""
        if self.path == "/command":
            try:
                content_length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(content_length).decode("utf-8")
                data = json.loads(body)
                
                # Verify secret
                if data.get("secret") != BRIDGE_SECRET:
                    self.send_response(401)
                    self.end_headers()
                    self.wfile.write(b'{"error": "unauthorized"}')
                    return
                
                command = data.get("command")
                params = data.get("params", {})
                
                logger.info(f"📥 Received command: {command}")
                
                # Execute command synchronously
                result = execute_command(command, params)
                
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps({"status": "ok", "result": result}).encode())
                
            except Exception as e:
                logger.error(f"Error processing command: {e}")
                self.send_response(500)
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_OPTIONS(self):
        """CORS preflight"""
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()


# App mappings for Windows
APP_MAPPINGS = {
    "notepad": "notepad",
    "notes": "notepad",
    "calculator": "calc",
    "paint": "mspaint",
    "word": "winword",
    "excel": "excel",
    "powerpoint": "powerpnt",
    "outlook": "outlook",
    "file explorer": "explorer",
    "explorer": "explorer",
    "cmd": "cmd",
    "command prompt": "cmd",
    "terminal": "wt",
    "powershell": "powershell",
    "task manager": "taskmgr",
    "settings": "ms-settings:",
    "control panel": "control",
    "spotify": "spotify",
    "discord": "discord",
    "slack": "slack",
    "teams": "msteams",
    "zoom": "zoom",
    "vscode": "code",
    "visual studio code": "code",
    "vs code": "code",
    "chrome": "chrome",
    "firefox": "firefox",
    "edge": "msedge",
    "brave": "brave",
    "whatsapp": "whatsapp:",
    "telegram": "telegram",
    "camera": "microsoft.windows.camera:",
    "photos": "ms-photos:",
    "calendar": "outlookcal:",
    "mail": "outlookmail:",
    "maps": "bingmaps:",
    "store": "ms-windows-store:",
    "clock": "ms-clock:",
    "weather": "bingweather:",
}


def execute_command(command: str, params: dict) -> str:
    """Execute a local command"""
    try:
        if command == "open_app":
            return open_app(params.get("app", ""))
        
        elif command == "open_maps":
            return open_maps(params.get("query", ""))
        
        elif command == "open_notes":
            return open_notes(params.get("content", ""))
        
        elif command == "send_whatsapp":
            return send_whatsapp(params.get("phone", ""), params.get("message", ""))
        
        elif command == "send_whatsapp_contact":
            return send_whatsapp_contact(params.get("contact", ""), params.get("message", ""))
        
        elif command == "type_text":
            return type_text(params.get("text", ""))
        
        elif command == "press_key":
            return press_key(params.get("key", ""))
        
        elif command == "open_url":
            return open_url(params.get("url", ""))
        
        elif command == "play_youtube":
            return play_youtube(params.get("query", ""))
        
        elif command == "screenshot":
            return take_screenshot()
        
        elif command == "set_volume":
            return set_volume(params.get("level", 50))
        
        elif command == "lock_pc":
            return lock_pc()
        
        elif command == "shutdown":
            return shutdown(params.get("delay", 60))
        
        elif command == "cancel_shutdown":
            return cancel_shutdown()
        
        else:
            return f"Unknown command: {command}"
            
    except Exception as e:
        logger.error(f"Error executing {command}: {e}")
        return f"Error: {str(e)}"


# ============== COMMAND IMPLEMENTATIONS ==============

def open_app(app_name: str) -> str:
    """Open an application by name"""
    app_lower = app_name.lower().strip()
    command = APP_MAPPINGS.get(app_lower, app_name)
    
    logger.info(f"🚀 Opening: {app_name}")
    
    try:
        # Handle URI schemes (whatsapp:, ms-settings:, etc.)
        if command.endswith(":") or "://" in command:
            os.startfile(command)
        else:
            subprocess.Popen(command, shell=True)
        logger.info(f"✅ Opened {app_name}")
        return f"Opened {app_name}"
    except Exception as e:
        logger.error(f"Failed to open {app_name}: {e}")
        return f"Failed: {e}"


def open_maps(query: str = "") -> str:
    """Open Google Maps with optional search"""
    import webbrowser
    
    if query:
        url = f"https://www.google.com/maps/search/{urllib.parse.quote(query)}"
    else:
        url = "https://www.google.com/maps"
    
    logger.info(f"🗺️ Opening Maps: {query if query else 'home'}")
    webbrowser.open(url)
    return f"Opened Maps: {query if query else 'home'}"


def open_notes(content: str = "") -> str:
    """Open Notepad and optionally write content"""
    subprocess.Popen("notepad", shell=True)
    
    if content and pyautogui and pyperclip:
        time.sleep(1.5)  # Wait for Notepad
        pyperclip.copy(content)
        pyautogui.hotkey('ctrl', 'v')
        logger.info(f"📝 Opened Notepad with content")
        return "Opened Notepad with content"
    else:
        logger.info("📝 Opened Notepad")
        return "Opened Notepad"


def send_whatsapp(phone: str, message: str) -> str:
    """Send WhatsApp message via Desktop app"""
    logger.info(f"📱 Sending WhatsApp to {phone}")
    
    if not pyautogui:
        return "Error: pyautogui required"
    
    # Use WhatsApp Desktop URI scheme
    encoded_message = urllib.parse.quote(message)
    whatsapp_uri = f"whatsapp://send?phone={phone}&text={encoded_message}"
    
    # Open WhatsApp with message
    subprocess.Popen(f'start "" "{whatsapp_uri}"', shell=True)
    time.sleep(4)  # Wait for WhatsApp to open
    
    # Focus and send
    screen_width, screen_height = pyautogui.size()
    pyautogui.click(int(screen_width * 0.5), int(screen_height * 0.5))
    time.sleep(0.3)
    pyautogui.press('enter')
    
    logger.info(f"✅ WhatsApp message sent to {phone}")
    return f"Sent to {phone}"


def send_whatsapp_contact(contact: str, message: str) -> str:
    """Send WhatsApp message by searching contact name"""
    logger.info(f"📱 Sending WhatsApp to contact: {contact}")
    
    if not pyautogui or not pyperclip:
        return "Error: pyautogui and pyperclip required"
    
    # Open WhatsApp
    subprocess.Popen('start whatsapp:', shell=True)
    time.sleep(5)
    
    # Search for contact
    screen_width, screen_height = pyautogui.size()
    pyautogui.click(int(screen_width * 0.5), int(screen_height * 0.5))
    time.sleep(0.3)
    pyautogui.press('escape')
    time.sleep(0.1)
    pyautogui.hotkey('ctrl', 'f')
    time.sleep(0.5)
    
    # Type contact name
    pyautogui.hotkey('ctrl', 'a')
    pyperclip.copy(contact)
    time.sleep(0.1)
    pyautogui.hotkey('ctrl', 'v')
    time.sleep(1)
    
    # Select first result
    pyautogui.press('down')
    time.sleep(0.1)
    pyautogui.press('enter')
    time.sleep(1)
    
    # Type and send message
    pyperclip.copy(message)
    time.sleep(0.1)
    pyautogui.hotkey('ctrl', 'v')
    time.sleep(0.2)
    pyautogui.press('enter')
    
    logger.info(f"✅ WhatsApp sent to {contact}")
    return f"Sent to {contact}"


def type_text(text: str) -> str:
    """Type text using keyboard automation"""
    if not pyautogui:
        return "Error: pyautogui required"
    
    logger.info(f"⌨️ Typing text...")
    
    if pyperclip and not text.isascii():
        # Use clipboard for Unicode text
        pyperclip.copy(text)
        time.sleep(0.1)
        pyautogui.hotkey('ctrl', 'v')
    else:
        pyautogui.typewrite(text, interval=0.05)
    
    logger.info("✅ Text typed")
    return "Text typed"


def press_key(key: str) -> str:
    """Press a keyboard key or combination"""
    if not pyautogui:
        return "Error: pyautogui required"
    
    logger.info(f"⌨️ Pressing: {key}")
    
    if '+' in key:
        keys = key.lower().split('+')
        pyautogui.hotkey(*keys)
    else:
        pyautogui.press(key.lower())
    
    logger.info(f"✅ Pressed {key}")
    return f"Pressed {key}"


def open_url(url: str) -> str:
    """Open URL in default browser"""
    import webbrowser
    logger.info(f"🌐 Opening URL: {url}")
    webbrowser.open(url)
    return f"Opened {url}"


def play_youtube(query: str) -> str:
    """Search and play YouTube video"""
    import webbrowser
    
    url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}"
    logger.info(f"▶️ Playing YouTube: {query}")
    webbrowser.open(url)
    
    # Click on first video after page loads
    if pyautogui:
        time.sleep(5)
        screen_width, screen_height = pyautogui.size()
        click_x = int(screen_width * 0.25)
        click_y = int(screen_height * 0.45)
        pyautogui.click(click_x, click_y)
    
    return f"Playing {query}"


def take_screenshot() -> str:
    """Take a screenshot"""
    pictures = os.path.expanduser("~/Pictures")
    filename = f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    filepath = os.path.join(pictures, filename)
    
    logger.info(f"📸 Taking screenshot...")
    
    # Use PowerShell screenshot
    ps_command = f'''
    Add-Type -AssemblyName System.Windows.Forms
    $screen = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
    $bitmap = New-Object System.Drawing.Bitmap($screen.Width, $screen.Height)
    $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
    $graphics.CopyFromScreen($screen.Location, [System.Drawing.Point]::Empty, $screen.Size)
    $bitmap.Save("{filepath}")
    '''
    subprocess.run(["powershell", "-Command", ps_command], capture_output=True)
    
    logger.info(f"✅ Screenshot saved: {filepath}")
    return f"Screenshot saved: {filepath}"


def set_volume(level: int) -> str:
    """Set system volume"""
    level = max(0, min(100, level))
    logger.info(f"🔊 Setting volume to {level}%")
    
    ps_command = f'''
    $obj = New-Object -ComObject WScript.Shell
    1..50 | ForEach-Object {{ $obj.SendKeys([char]174) }}
    1..{level // 2} | ForEach-Object {{ $obj.SendKeys([char]175) }}
    '''
    subprocess.run(["powershell", "-Command", ps_command], capture_output=True)
    
    logger.info(f"✅ Volume set to ~{level}%")
    return f"Volume set to {level}%"


def lock_pc() -> str:
    """Lock the computer"""
    logger.info("🔒 Locking PC...")
    subprocess.run(["rundll32.exe", "user32.dll,LockWorkStation"])
    logger.info("✅ PC locked")
    return "PC locked"


def shutdown(delay: int) -> str:
    """Schedule PC shutdown"""
    logger.info(f"⏻ Scheduling shutdown in {delay}s...")
    subprocess.run(["shutdown", "/s", "/t", str(delay)])
    logger.info(f"✅ Shutdown scheduled")
    return f"Shutdown in {delay}s"


def cancel_shutdown() -> str:
    """Cancel scheduled shutdown"""
    logger.info("❌ Cancelling shutdown...")
    subprocess.run(["shutdown", "/a"])
    logger.info("✅ Shutdown cancelled")
    return "Shutdown cancelled"


def main():
    """Entry point"""
    print("\n" + "="*50)
    print("  VYAAS AI Desktop Bridge (HTTP)")
    print(f"  Listening on http://localhost:{BRIDGE_PORT}")
    print("  Press Ctrl+C to stop")
    print("="*50 + "\n")
    
    try:
        server = HTTPServer(("0.0.0.0", BRIDGE_PORT), BridgeHandler)
        logger.info(f"✅ Bridge running on port {BRIDGE_PORT}")
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 Bridge stopped by user")
    except Exception as e:
        logger.error(f"Failed to start server: {e}")


if __name__ == "__main__":
    main()
