"""
VYAAS AI - Desktop Bridge
Run this script on your PC to receive and execute commands from the cloud AI agent.

This lightweight bridge:
1. Connects to LiveKit as a hidden participant
2. Listens for 'local_command' data messages from the AI agent
3. Executes commands locally using subprocess, pyautogui, etc.

Usage:
    python vyaas_desktop_bridge.py

Requirements:
    pip install livekit pyautogui pyperclip python-dotenv
"""

import asyncio
import json
import logging
import subprocess
import os
import sys
import time
import urllib.parse
from datetime import datetime
from dotenv import load_dotenv

# Optional imports (graceful fallback)
try:
    import pyautogui
    pyautogui.FAILSAFE = True  # Move mouse to corner to abort
except ImportError:
    pyautogui = None
    print("[WARN] pyautogui not installed. Some features won't work. Run: pip install pyautogui")

try:
    import pyperclip
except ImportError:
    pyperclip = None
    print("[WARN] pyperclip not installed. Clipboard features limited. Run: pip install pyperclip")

try:
    from livekit import rtc
except ImportError:
    print("[ERR] livekit SDK not installed. Run: pip install livekit")
    sys.exit(1)

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - VYAAS Bridge - %(levelname)s - %(message)s'
)
logger = logging.getLogger("vyaas_bridge")

# Configuration
LIVEKIT_URL = os.getenv("LIVEKIT_URL", "wss://vyass-sxwzn7ti.livekit.cloud")
BRIDGE_IDENTITY = "vyaas_desktop_bridge"


class DesktopBridge:
    """Local Desktop Bridge that executes commands from cloud AI agent"""
    
    def __init__(self):
        self.room = rtc.Room()
        self.running = False
        
        # App mappings for Windows
        self.app_mappings = {
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
    
    async def connect(self, token: str):
        """Connect to LiveKit room"""
        try:
            await self.room.connect(LIVEKIT_URL, token)
            logger.info(f"[OK] Connected to LiveKit as {BRIDGE_IDENTITY}")
            self.running = True
            
            # Register data handler
            @self.room.on("data_received")
            def on_data(data: rtc.DataPacket):
                asyncio.create_task(self.handle_data(data))
            
            return True
        except Exception as e:
            logger.error(f"[ERR] Failed to connect: {e}")
            return False
    
    async def handle_data(self, packet: rtc.DataPacket):
        """Handle incoming data messages"""
        try:
            payload = packet.data.decode('utf-8')
            data = json.loads(payload)
            
            if data.get("type") == "local_command":
                command = data.get("command")
                params = data.get("params", {})
                
                logger.info(f"[IN] Received command: {command}")
                await self.execute_command(command, params)
                
        except Exception as e:
            logger.error(f"Error handling data: {e}")
    
    async def execute_command(self, command: str, params: dict):
        """Execute a local command"""
        try:
            if command == "open_app":
                await self.open_app(params.get("app", ""))
            
            elif command == "open_maps":
                await self.open_maps(params.get("query", ""))
            
            elif command == "open_notes":
                await self.open_notes(params.get("content", ""))
            
            elif command == "send_whatsapp":
                await self.send_whatsapp(params.get("phone", ""), params.get("message", ""))
            
            elif command == "send_whatsapp_contact":
                await self.send_whatsapp_contact(params.get("contact", ""), params.get("message", ""))
            
            elif command == "type_text":
                await self.type_text(params.get("text", ""))
            
            elif command == "press_key":
                await self.press_key(params.get("key", ""))
            
            elif command == "open_url":
                await self.open_url(params.get("url", ""))
            
            elif command == "play_youtube":
                await self.play_youtube(params.get("query", ""))
            
            elif command == "screenshot":
                await self.take_screenshot()
            
            elif command == "set_volume":
                await self.set_volume(params.get("level", 50))
            
            elif command == "lock_pc":
                await self.lock_pc()
            
            elif command == "shutdown":
                await self.shutdown(params.get("delay", 60))
            
            elif command == "cancel_shutdown":
                await self.cancel_shutdown()
            
            else:
                logger.warning(f"Unknown command: {command}")
                
        except Exception as e:
            logger.error(f"Error executing {command}: {e}")
    
    # ============== COMMAND IMPLEMENTATIONS ==============
    
    async def open_app(self, app_name: str):
        """Open an application by name"""
        app_lower = app_name.lower().strip()
        command = self.app_mappings.get(app_lower, app_name)
        
        logger.info(f"[CMD] Opening: {app_name}")
        
        try:
            # Handle URI schemes (whatsapp:, ms-settings:, etc.)
            if command.endswith(":") or "://" in command:
                os.startfile(command)
            else:
                subprocess.Popen(command, shell=True)
            logger.info(f"[OK] Opened {app_name}")
        except Exception as e:
            logger.error(f"Failed to open {app_name}: {e}")
    
    async def open_maps(self, query: str = ""):
        """Open Google Maps with optional search"""
        import webbrowser
        
        if query:
            url = f"https://www.google.com/maps/search/{urllib.parse.quote(query)}"
        else:
            url = "https://www.google.com/maps"
        
        logger.info(f"[MAP] Opening Maps: {query if query else 'home'}")
        webbrowser.open(url)
    
    async def open_notes(self, content: str = ""):
        """Open Notepad and optionally write content"""
        subprocess.Popen("notepad", shell=True)
        
        if content and pyautogui and pyperclip:
            time.sleep(1.5)  # Wait for Notepad
            pyperclip.copy(content)
            pyautogui.hotkey('ctrl', 'v')
            logger.info(f"[NOTE] Opened Notepad with content")
        else:
            logger.info("[NOTE] Opened Notepad")
    
    async def send_whatsapp(self, phone: str, message: str):
        """Send WhatsApp message via Desktop app"""
        logger.info(f"[WA] Sending WhatsApp to {phone}")
        
        if not pyautogui:
            logger.error("pyautogui required for WhatsApp automation")
            return
        
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
        
        logger.info(f"[ok] WhatsApp message sent to {phone}")
    
    async def send_whatsapp_contact(self, contact: str, message: str):
        """Send WhatsApp message by searching contact name"""
        logger.info(f"[WA] Sending WhatsApp to contact: {contact}")
        
        if not pyautogui or not pyperclip:
            logger.error("pyautogui and pyperclip required")
            return
        
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
        
        logger.info(f"[OK] WhatsApp sent to {contact}")
    
    async def type_text(self, text: str):
        """Type text using keyboard automation"""
        if not pyautogui:
            logger.error("pyautogui required for typing")
            return
        
        logger.info(f"[KBD] Typing text...")
        
        if pyperclip and not text.isascii():
            # Use clipboard for Unicode text
            pyperclip.copy(text)
            time.sleep(0.1)
            pyautogui.hotkey('ctrl', 'v')
        else:
            pyautogui.typewrite(text, interval=0.05)
        
        logger.info("[OK] Text typed")
    
    async def press_key(self, key: str):
        """Press a keyboard key or combination"""
        if not pyautogui:
            logger.error("pyautogui required")
            return
        
        logger.info(f"[KBD] Pressing: {key}")
        
        if '+' in key:
            keys = key.lower().split('+')
            pyautogui.hotkey(*keys)
        else:
            pyautogui.press(key.lower())
        
        logger.info(f"[OK] Pressed {key}")
    
    async def open_url(self, url: str):
        """Open URL in default browser"""
        import webbrowser
        logger.info(f"[WEB] Opening URL: {url}")
        webbrowser.open(url)
    
    async def play_youtube(self, query: str):
        """Search and play YouTube video"""
        import webbrowser
        
        url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}"
        logger.info(f"[YT] Playing YouTube: {query}")
        webbrowser.open(url)
        
        # Click on first video after page loads
        if pyautogui:
            time.sleep(5)
            screen_width, screen_height = pyautogui.size()
            click_x = int(screen_width * 0.25)
            click_y = int(screen_height * 0.45)
            pyautogui.click(click_x, click_y)
    
    async def take_screenshot(self):
        """Take a screenshot"""
        pictures = os.path.expanduser("~/Pictures")
        filename = f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        filepath = os.path.join(pictures, filename)
        
        logger.info(f"[IMG] Taking screenshot...")
        
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
        
        logger.info(f"[OK] Screenshot saved: {filepath}")
    
    async def set_volume(self, level: int):
        """Set system volume"""
        level = max(0, min(100, level))
        logger.info(f"[VOL] Setting volume to {level}%")
        
        ps_command = f'''
        $obj = New-Object -ComObject WScript.Shell
        1..50 | ForEach-Object {{ $obj.SendKeys([char]174) }}
        1..{level // 2} | ForEach-Object {{ $obj.SendKeys([char]175) }}
        '''
        subprocess.run(["powershell", "-Command", ps_command], capture_output=True)
        
        logger.info(f"[OK] Volume set to ~{level}%")
    
    async def lock_pc(self):
        """Lock the computer"""
        logger.info("[LCK] Locking PC...")
        subprocess.run(["rundll32.exe", "user32.dll,LockWorkStation"])
        logger.info("[OK] PC locked")
    
    async def shutdown(self, delay: int):
        """Schedule PC shutdown"""
        logger.info(f"[PWR] Scheduling shutdown in {delay}s...")
        subprocess.run(["shutdown", "/s", "/t", str(delay)])
        logger.info(f"[OK] Shutdown scheduled")
    
    async def cancel_shutdown(self):
        """Cancel scheduled shutdown"""
        logger.info("[CAN] Cancelling shutdown...")
        subprocess.run(["shutdown", "/a"])
        logger.info("[OK] Shutdown cancelled")
    
    async def run(self, token: str):
        """Main run loop"""
        if not await self.connect(token):
            return
        
        print("\n" + "="*50)
        print("  VYAAS Desktop Bridge - Running")
        print("  Press Ctrl+C to stop")
        print("="*50 + "\n")
        
        try:
            while self.running:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            pass
        finally:
            await self.room.disconnect()
            logger.info("Bridge disconnected")


async def get_bridge_token():
    """Get a LiveKit token for the bridge"""
    from livekit import api as lk_api
    
    LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY")
    LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET")
    
    if not LIVEKIT_API_KEY or not LIVEKIT_API_SECRET:
        logger.error("Missing LIVEKIT_API_KEY or LIVEKIT_API_SECRET in .env")
        return None
    
    # Create token that can join any room
    room_name = os.getenv("VYAAS_ROOM_NAME", "vyaas_assist_room")
    
    token = lk_api.AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET) \
        .with_identity(BRIDGE_IDENTITY) \
        .with_name("Desktop Bridge") \
        .with_grants(lk_api.VideoGrants(
            room_join=True,
            room=room_name,
            can_subscribe=True,
            can_publish_data=True,
        ))
    
    return token.to_jwt()


async def main():
    """Entry point"""
    print("\n" + "="*50)
    print("  VYAAS AI Desktop Bridge")
    print("  Connecting to cloud AI agent...")
    print("="*50 + "\n")
    
    token = await get_bridge_token()
    if not token:
        print("[ERR] Failed to generate token. Check your .env file.")
        return
    
    bridge = DesktopBridge()
    await bridge.run(token)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[STOP] Bridge stopped by user")
