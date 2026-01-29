"""
VYAAS AI - Local Commands (Cloud-Side)
These tools send commands to the Desktop Bridge running on user's PC via HTTP.

The Desktop Bridge must be running for these commands to work.
"""

import os
import logging
import httpx
from typing import Optional

logger = logging.getLogger("vyaas_local_commands")

# Configuration
BRIDGE_URL = os.getenv("BRIDGE_URL", "http://localhost:18790")
BRIDGE_SECRET = os.getenv("BRIDGE_SECRET", "vyaas_local_bridge_2025")

# HTTP client for async requests
_http_client: Optional[httpx.AsyncClient] = None


def get_client() -> httpx.AsyncClient:
    """Get or create HTTP client"""
    global _http_client
    if _http_client is None:
        _http_client = httpx.AsyncClient(timeout=30.0)
    return _http_client


async def _send_command(command: str, params: dict) -> str:
    """Send command to Desktop Bridge"""
    try:
        client = get_client()
        response = await client.post(
            f"{BRIDGE_URL}/command",
            json={
                "secret": BRIDGE_SECRET,
                "command": command,
                "params": params
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f"✅ Command {command} executed: {data.get('result', 'ok')}")
            return data.get("result", "Command executed")
        elif response.status_code == 401:
            return "❌ Bridge authorization failed. Check BRIDGE_SECRET."
        else:
            return f"❌ Bridge error: {response.status_code}"
            
    except httpx.ConnectError:
        return "❌ Desktop Bridge nahi chal raha. Please run start_bridge.bat on your PC."
    except Exception as e:
        logger.error(f"Error sending command: {e}")
        return f"❌ Error: {str(e)}"


# ============== LOCAL COMMAND TOOLS ==============

async def open_whatsapp_local() -> str:
    """
    Open WhatsApp Desktop on user's PC.
    Use this when user asks to open WhatsApp.
    """
    return await _send_command("open_app", {"app": "whatsapp"})


async def open_maps_local(query: str = "") -> str:
    """
    Open Google Maps on user's PC.
    
    Args:
        query: Optional location to search (e.g., "Delhi", "restaurants near me")
    """
    return await _send_command("open_maps", {"query": query})


async def open_notes_local(content: str = "") -> str:
    """
    Open Notepad on user's PC.
    
    Args:
        content: Optional text to paste into Notepad
    """
    return await _send_command("open_notes", {"content": content})


async def open_app_local(app_name: str) -> str:
    """
    Open any application on user's PC.
    
    Args:
        app_name: Name of the app (e.g., "spotify", "chrome", "calculator", "vscode")
    """
    return await _send_command("open_app", {"app": app_name})


async def send_whatsapp_local(phone: str, message: str) -> str:
    """
    Send WhatsApp message using phone number.
    
    Args:
        phone: Phone number with country code (e.g., "919876543210")
        message: Message to send
    """
    return await _send_command("send_whatsapp", {"phone": phone, "message": message})


async def send_whatsapp_contact_local(contact_name: str, message: str) -> str:
    """
    Send WhatsApp message by searching contact name.
    
    Args:
        contact_name: Name of the contact (e.g., "Mitul", "Papa")
        message: Message to send
    """
    return await _send_command("send_whatsapp_contact", {"contact": contact_name, "message": message})


async def type_text_local(text: str) -> str:
    """
    Type text using keyboard automation on user's PC.
    The text will be typed wherever the cursor is focused.
    
    Args:
        text: Text to type
    """
    return await _send_command("type_text", {"text": text})


async def press_key_local(key: str) -> str:
    """
    Press keyboard key or combination on user's PC.
    
    Args:
        key: Key to press (e.g., "enter", "ctrl+s", "alt+f4")
    """
    return await _send_command("press_key", {"key": key})


async def open_url_local(url: str) -> str:
    """
    Open URL in browser on user's PC.
    
    Args:
        url: URL to open (e.g., "https://google.com")
    """
    return await _send_command("open_url", {"url": url})


async def play_youtube_local(query: str) -> str:
    """
    Search and play YouTube video on user's PC.
    
    Args:
        query: Search query (e.g., "Arijit Singh songs", "coding tutorial")
    """
    return await _send_command("play_youtube", {"query": query})


async def take_screenshot_local() -> str:
    """Take a screenshot on user's PC and save to Pictures folder."""
    return await _send_command("screenshot", {})


async def set_volume_local(level: int) -> str:
    """
    Set system volume on user's PC.
    
    Args:
        level: Volume level 0-100
    """
    return await _send_command("set_volume", {"level": level})


async def lock_pc_local() -> str:
    """Lock user's PC immediately."""
    return await _send_command("lock_pc", {})


async def shutdown_pc_local(delay: int = 60) -> str:
    """
    Schedule PC shutdown.
    
    Args:
        delay: Seconds before shutdown (default 60)
    """
    return await _send_command("shutdown", {"delay": delay})


async def cancel_shutdown_local() -> str:
    """Cancel any scheduled shutdown."""
    return await _send_command("cancel_shutdown", {})
