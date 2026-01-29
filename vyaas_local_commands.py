"""
VYAAS AI - Local Commands (Cloud-Side)
Sends commands via LiveKit data channel to the frontend,
which then forwards them to the Desktop Bridge running on user's PC.

Flow: Cloud AI -> LiveKit Data Channel -> Frontend -> HTTP -> Desktop Bridge
"""

import json
import logging
from typing import Optional

logger = logging.getLogger("vyaas_local_commands")

# Global room reference
_current_room = None


def set_room(room):
    """Set the LiveKit room for data channel communication"""
    global _current_room
    _current_room = room
    logger.info("Room set for local commands")


async def _send_local_command(command: str, params: dict) -> str:
    """Send command to frontend via LiveKit data channel"""
    global _current_room
    
    if not _current_room:
        logger.error("No room available for sending local commands")
        return "❌ LiveKit room not connected"
    
    try:
        payload = {
            "type": "local_command",
            "command": command,
            "params": params
        }
        
        # Send via data channel - frontend will receive and forward to bridge
        await _current_room.local_participant.publish_data(
            json.dumps(payload).encode('utf-8'),
            topic="local_commands"
        )
        logger.info(f"✅ Sent local command via data channel: {command}")
        return f"Command sent to your PC: {command}"
    except Exception as e:
        logger.error(f"Failed to send local command: {e}")
        return f"❌ Error: {str(e)}"


# ============== LOCAL COMMAND TOOLS ==============

async def open_whatsapp_local() -> str:
    """
    Open WhatsApp Desktop on user's PC.
    Use this when user asks to open WhatsApp.
    """
    return await _send_local_command("open_app", {"app": "whatsapp"})


async def open_maps_local(query: str = "") -> str:
    """
    Open Google Maps on user's PC.
    
    Args:
        query: Optional location to search (e.g., "Delhi", "restaurants near me")
    """
    return await _send_local_command("open_maps", {"query": query})


async def open_notes_local(content: str = "") -> str:
    """
    Open Notepad on user's PC.
    
    Args:
        content: Optional text to paste into Notepad
    """
    return await _send_local_command("open_notes", {"content": content})


async def open_app_local(app_name: str) -> str:
    """
    Open any application on user's PC.
    
    Args:
        app_name: Name of the app (e.g., "spotify", "chrome", "calculator", "vscode")
    """
    return await _send_local_command("open_app", {"app": app_name})


async def send_whatsapp_local(phone: str, message: str) -> str:
    """
    Send WhatsApp message using phone number.
    
    Args:
        phone: Phone number with country code (e.g., "919876543210")
        message: Message to send
    """
    return await _send_local_command("send_whatsapp", {"phone": phone, "message": message})


async def send_whatsapp_contact_local(contact_name: str, message: str) -> str:
    """
    Send WhatsApp message by searching contact name.
    
    Args:
        contact_name: Name of the contact (e.g., "Mitul", "Papa")
        message: Message to send
    """
    return await _send_local_command("send_whatsapp_contact", {"contact": contact_name, "message": message})


async def type_text_local(text: str) -> str:
    """
    Type text using keyboard automation on user's PC.
    The text will be typed wherever the cursor is focused.
    
    Args:
        text: Text to type
    """
    return await _send_local_command("type_text", {"text": text})


async def press_key_local(key: str) -> str:
    """
    Press keyboard key or combination on user's PC.
    
    Args:
        key: Key to press (e.g., "enter", "ctrl+s", "alt+f4")
    """
    return await _send_local_command("press_key", {"key": key})


async def open_url_local(url: str) -> str:
    """
    Open URL in browser on user's PC.
    
    Args:
        url: URL to open (e.g., "https://google.com")
    """
    return await _send_local_command("open_url", {"url": url})


async def play_youtube_local(query: str) -> str:
    """
    Search and play YouTube video on user's PC.
    
    Args:
        query: Search query (e.g., "Arijit Singh songs", "coding tutorial")
    """
    return await _send_local_command("play_youtube", {"query": query})


async def take_screenshot_local() -> str:
    """Take a screenshot on user's PC and save to Pictures folder."""
    return await _send_local_command("screenshot", {})


async def set_volume_local(level: int) -> str:
    """
    Set system volume on user's PC.
    
    Args:
        level: Volume level 0-100
    """
    return await _send_local_command("set_volume", {"level": level})


async def lock_pc_local() -> str:
    """Lock user's PC immediately."""
    return await _send_local_command("lock_pc", {})


async def shutdown_pc_local(delay: int = 60) -> str:
    """
    Schedule PC shutdown.
    
    Args:
        delay: Seconds before shutdown (default 60)
    """
    return await _send_local_command("shutdown", {"delay": delay})


async def cancel_shutdown_local() -> str:
    """Cancel any scheduled shutdown."""
    return await _send_local_command("cancel_shutdown", {})
