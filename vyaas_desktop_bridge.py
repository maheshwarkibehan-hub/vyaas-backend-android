"""
VYAAS AI - Desktop Bridge
Run this script on your PC to receive and execute commands from the cloud AI agent.

This lightweight bridge:
1. Connects to LiveKit as a hidden participant
2. Listens for 'local_command' data messages from the AI agent
3. Executes commands locally using subprocess, pyautogui, etc.
4. Integrates with WhatsApp Service for direct messaging (no UI automation!)

Usage:
    python vyaas_desktop_bridge.py

Requirements:
    pip install livekit pyautogui pyperclip python-dotenv requests
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
import requests

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

try:
    from livekit import rtc
except ImportError:
    print("❌ livekit SDK not installed. Run: pip install livekit")
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

# WhatsApp Service Configuration (runs locally via Node.js)
WHATSAPP_SERVICE_URL = "http://127.0.0.1:3001"
WHATSAPP_SERVICE_PATH = os.path.join(os.path.dirname(__file__), "whatsapp-service")


class DesktopBridge:
    """Local Desktop Bridge that executes commands from cloud AI agent"""
    
    def __init__(self):
        self.room = rtc.Room()
        self.running = False
        self.whatsapp_service_running = False
        self.whatsapp_contacts_cache = {}  # Cache contacts for name search
        
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
            logger.info(f"✅ Connected to LiveKit as {BRIDGE_IDENTITY}")
            self.running = True
            
            # Register data handler
            @self.room.on("data_received")
            def on_data(data: rtc.DataPacket):
                asyncio.create_task(self.handle_data(data))
            
            return True
        except Exception as e:
            logger.error(f"❌ Failed to connect: {e}")
            return False
    
    async def handle_data(self, packet: rtc.DataPacket):
        """Handle incoming data messages"""
        try:
            payload = packet.data.decode('utf-8')
            data = json.loads(payload)
            
            if data.get("type") == "local_command":
                command = data.get("command")
                params = data.get("params", {})
                
                logger.info(f"📥 Received command: {command}")
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
        
        logger.info(f"🚀 Opening: {app_name}")
        
        try:
            # Handle URI schemes (whatsapp:, ms-settings:, etc.)
            if command.endswith(":") or "://" in command:
                os.startfile(command)
            else:
                subprocess.Popen(command, shell=True)
            logger.info(f"✅ Opened {app_name}")
        except Exception as e:
            logger.error(f"Failed to open {app_name}: {e}")
    
    async def open_maps(self, query: str = ""):
        """Open Google Maps with optional search"""
        import webbrowser
        
        if query:
            url = f"https://www.google.com/maps/search/{urllib.parse.quote(query)}"
        else:
            url = "https://www.google.com/maps"
        
        logger.info(f"🗺️ Opening Maps: {query if query else 'home'}")
        webbrowser.open(url)
    
    async def open_notes(self, content: str = ""):
        """Open Notepad and optionally write content"""
        subprocess.Popen("notepad", shell=True)
        
        if content and pyautogui and pyperclip:
            time.sleep(1.5)  # Wait for Notepad
            pyperclip.copy(content)
            pyautogui.hotkey('ctrl', 'v')
            logger.info(f"📝 Opened Notepad with content")
        else:
            logger.info("📝 Opened Notepad")
    
    async def send_whatsapp(self, phone: str, message: str):
        """Send WhatsApp message via WhatsApp Service (Direct API - no UI automation!)"""
        logger.info(f"📱 Sending WhatsApp to {phone}")
        
        # Try WhatsApp Service first (fast, direct API)
        if await self.check_whatsapp_service():
            try:
                response = requests.post(
                    f"{WHATSAPP_SERVICE_URL}/send",
                    json={"to": phone, "message": message},
                    timeout=10
                )
                if response.status_code == 200:
                    logger.info(f"✅ WhatsApp message sent via Direct API to {phone}")
                    return
                else:
                    logger.warning(f"WhatsApp Service error: {response.json()}")
            except Exception as e:
                logger.warning(f"WhatsApp Service failed: {e}")
        
        # Fallback to UI automation if service not available
        logger.info("⚡ Falling back to UI automation...")
        await self._send_whatsapp_ui(phone, message)
    
    async def _send_whatsapp_ui(self, phone: str, message: str):
        """Fallback: Send WhatsApp using UI automation"""
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
        
        logger.info(f"✅ WhatsApp message sent to {phone}")
    
    async def send_whatsapp_contact(self, contact: str, message: str):
        """Send WhatsApp message by contact name using WhatsApp Service"""
        logger.info(f"📱 Sending WhatsApp to contact: {contact}")
        
        # Try WhatsApp Service first
        if await self.check_whatsapp_service():
            try:
                # Get chats and find the contact
                response = requests.get(f"{WHATSAPP_SERVICE_URL}/chats", timeout=10)
                if response.status_code == 200:
                    chats = response.json().get('chats', [])
                    
                    # Find matching contact (case-insensitive)
                    contact_lower = contact.lower()
                    matched_chat = None
                    
                    for chat in chats:
                        chat_name = chat.get('name', '').lower()
                        if contact_lower in chat_name or chat_name in contact_lower:
                            matched_chat = chat
                            break
                    
                    if matched_chat:
                        # Send to the matched contact
                        send_response = requests.post(
                            f"{WHATSAPP_SERVICE_URL}/send",
                            json={"to": matched_chat['id'], "message": message},
                            timeout=10
                        )
                        if send_response.status_code == 200:
                            logger.info(f"✅ WhatsApp sent to {matched_chat.get('name')} via Direct API")
                            return
                    else:
                        logger.warning(f"Contact '{contact}' not found in recent chats")
            except Exception as e:
                logger.warning(f"WhatsApp Service contact search failed: {e}")
        
        # Fallback to UI automation
        logger.info("⚡ Falling back to UI automation...")
        await self._send_whatsapp_contact_ui(contact, message)
    
    async def _send_whatsapp_contact_ui(self, contact: str, message: str):
        """Fallback: Send WhatsApp by contact name using UI automation"""
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
        
        logger.info(f"✅ WhatsApp sent to {contact}")
    
    async def check_whatsapp_service(self) -> bool:
        """Check if WhatsApp Service is running and connected"""
        try:
            response = requests.get(f"{WHATSAPP_SERVICE_URL}/health", timeout=2)
            if response.status_code == 200:
                data = response.json()
                if data.get('ready'):
                    self.whatsapp_service_running = True
                    return True
                elif data.get('hasQR'):
                    logger.warning("WhatsApp Service needs QR scan - check the terminal")
        except:
            pass
        
        self.whatsapp_service_running = False
        return False
    
    async def get_whatsapp_messages(self) -> list:
        """Get pending WhatsApp messages from the service"""
        try:
            response = requests.get(f"{WHATSAPP_SERVICE_URL}/messages", timeout=5)
            if response.status_code == 200:
                return response.json().get('messages', [])
        except:
            pass
        return []
    
    async def type_text(self, text: str):
        """Type text using keyboard automation"""
        if not pyautogui:
            logger.error("pyautogui required for typing")
            return
        
        logger.info(f"⌨️ Typing text...")
        
        if pyperclip and not text.isascii():
            # Use clipboard for Unicode text
            pyperclip.copy(text)
            time.sleep(0.1)
            pyautogui.hotkey('ctrl', 'v')
        else:
            pyautogui.typewrite(text, interval=0.05)
        
        logger.info("✅ Text typed")
    
    async def press_key(self, key: str):
        """Press a keyboard key or combination"""
        if not pyautogui:
            logger.error("pyautogui required")
            return
        
        logger.info(f"⌨️ Pressing: {key}")
        
        if '+' in key:
            keys = key.lower().split('+')
            pyautogui.hotkey(*keys)
        else:
            pyautogui.press(key.lower())
        
        logger.info(f"✅ Pressed {key}")
    
    async def open_url(self, url: str):
        """Open URL in default browser"""
        import webbrowser
        logger.info(f"🌐 Opening URL: {url}")
        webbrowser.open(url)
    
    async def play_youtube(self, query: str):
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
    
    async def take_screenshot(self):
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
    
    async def set_volume(self, level: int):
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
    
    async def lock_pc(self):
        """Lock the computer"""
        logger.info("🔒 Locking PC...")
        subprocess.run(["rundll32.exe", "user32.dll,LockWorkStation"])
        logger.info("✅ PC locked")
    
    async def shutdown(self, delay: int):
        """Schedule PC shutdown"""
        logger.info(f"⏻ Scheduling shutdown in {delay}s...")
        subprocess.run(["shutdown", "/s", "/t", str(delay)])
        logger.info(f"✅ Shutdown scheduled")
    
    async def cancel_shutdown(self):
        """Cancel scheduled shutdown"""
        logger.info("❌ Cancelling shutdown...")
        subprocess.run(["shutdown", "/a"])
        logger.info("✅ Shutdown cancelled")
    
    async def run(self, token: str):
        """Main run loop"""
        if not await self.connect(token):
            return
        
        print("\n" + "="*50)
        print("  VYAAS Desktop Bridge - Running")
        print("  Press Ctrl+C to stop")
        print("="*50 + "\n")
        
        # Check WhatsApp Service status
        if await self.check_whatsapp_service():
            print("✅ WhatsApp Service connected (Direct API mode)")
        else:
            print("⚠️ WhatsApp Service not running (Using UI automation fallback)")
            print("   To enable Direct API: cd whatsapp-service && npm start")
        print()
        
        # Start WhatsApp message polling
        asyncio.create_task(self.poll_whatsapp_messages())
        
        try:
            while self.running:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            pass
        finally:
            await self.room.disconnect()
            logger.info("Bridge disconnected")
    
    async def poll_whatsapp_messages(self):
        """Poll WhatsApp Service for incoming messages and forward to AI"""
        while self.running:
            try:
                if await self.check_whatsapp_service():
                    messages = await self.get_whatsapp_messages()
                    
                    for msg in messages:
                        # Log the message
                        sender = msg.get('contactName', msg.get('from', 'Unknown'))
                        body = msg.get('body', '')
                        is_group = msg.get('isGroup', False)
                        group_name = msg.get('groupName', '')
                        
                        if is_group:
                            logger.info(f"📩 WhatsApp [{group_name}] {sender}: {body[:50]}...")
                        else:
                            logger.info(f"📩 WhatsApp from {sender}: {body[:50]}...")
                        
                        # Forward to AI agent via LiveKit
                        await self.forward_whatsapp_to_ai(msg)
                
            except Exception as e:
                logger.debug(f"WhatsApp polling error: {e}")
            
            await asyncio.sleep(3)  # Poll every 3 seconds
    
    async def forward_whatsapp_to_ai(self, message: dict):
        """Forward WhatsApp message to AI agent via LiveKit data channel"""
        try:
            payload = {
                "type": "whatsapp_message",
                "data": message
            }
            
            # Send to AI agent via LiveKit
            await self.room.local_participant.publish_data(
                json.dumps(payload).encode('utf-8'),
                topic="whatsapp_notifications"
            )
            logger.info(f"📤 Forwarded WhatsApp message to AI agent")
        except Exception as e:
            logger.error(f"Failed to forward WhatsApp to AI: {e}")


async def get_bridge_token():
    """Get a LiveKit token for the bridge"""
    from livekit import api as lk_api
    
    LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY")
    LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET")
    
    if not LIVEKIT_API_KEY or not LIVEKIT_API_SECRET:
        logger.error("Missing LIVEKIT_API_KEY or LIVEKIT_API_SECRET in .env")
        return None
    
    # Create token that can join any room
    token = lk_api.AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET) \
        .with_identity(BRIDGE_IDENTITY) \
        .with_name("Desktop Bridge") \
        .with_grants(lk_api.VideoGrants(
            room_join=True,
            room="*",  # Can join any room
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
        print("❌ Failed to generate token. Check your .env file.")
        return
    
    bridge = DesktopBridge()
    await bridge.run(token)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Bridge stopped by user")
