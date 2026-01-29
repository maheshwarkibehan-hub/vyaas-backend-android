"""
VYAAS AI - Local Commands Module (Cloud-Side)
Sends commands to Local Desktop Bridge via LiveKit Data Channel

These tools run on the cloud server and send commands to the user's PC
via LiveKit's data channel. The Desktop Bridge running locally receives
and executes these commands.
"""

import json
import logging
from typing import Optional

logger = logging.getLogger("vyaas_local_commands")
logger.setLevel(logging.INFO)

# Global reference to the room for sending data
_current_room = None

def set_room(room):
    """Set the LiveKit room reference for data channel communication"""
    global _current_room
    _current_room = room
    logger.info("Room set for local commands")

async def _send_local_command(command_type: str, params: dict) -> bool:
    """
    Send a command to the local desktop bridge via data channel.
    Returns True if command was sent successfully.
    """
    global _current_room
    
    if not _current_room:
        logger.error("No room available for sending local commands")
        return False
    
    try:
        payload = {
            "type": "local_command",
            "command": command_type,
            "params": params
        }
        
        await _current_room.local_participant.publish_data(
            json.dumps(payload),
            topic="local_commands"
        )
        logger.info(f"Sent local command: {command_type}")
        return True
    except Exception as e:
        logger.error(f"Failed to send local command: {e}")
        return False


# ============== LOCAL APP OPENING TOOLS ==============

async def open_whatsapp_local() -> str:
    """
    Open WhatsApp Desktop app on the user's PC.
    This command is sent to the local desktop bridge for execution.
    Returns:
        Status message
    """
    success = await _send_local_command("open_app", {"app": "whatsapp"})
    if success:
        return "Done! WhatsApp open karne ka command bhej diya hai Bhaiya!"
    return "Error: Desktop bridge se connection nahi hai. Please check if bridge is running."


async def open_maps_local(query: str = "") -> str:
    """
    Open Google Maps on the user's PC, optionally with a search query.
    Args:
        query: Optional location or place to search (e.g., "Taj Mahal", "restaurants near me")
    Returns:
        Status message
    """
    success = await _send_local_command("open_maps", {"query": query})
    if success:
        return f"Done! Google Maps {'with ' + query if query else ''} open kar diya!"
    return "Error: Desktop bridge se connection nahi hai."


async def open_notes_local(content: str = "") -> str:
    """
    Open Notepad/Notes app on user's PC, optionally with content to write.
    Args:
        content: Optional text content to write in the notes
    Returns:
        Status message
    """
    success = await _send_local_command("open_notes", {"content": content})
    if success:
        return "Done! Notes app open kar diya Bhaiya!"
    return "Error: Desktop bridge se connection nahi hai."


async def open_app_local(app_name: str) -> str:
    """
    Open any application on the user's PC by name.
    Common apps: whatsapp, chrome, spotify, discord, telegram, calculator, notepad,
                 excel, word, powerpoint, vs code, file explorer, settings, camera
    Args:
        app_name: Name of the application to open
    Returns:
        Status message
    """
    success = await _send_local_command("open_app", {"app": app_name})
    if success:
        return f"Done! {app_name} open karne ka command bhej diya!"
    return "Error: Desktop bridge se connection nahi hai."


async def send_whatsapp_local(phone_number: str, message: str) -> str:
    """
    Send a WhatsApp message to a phone number via local desktop automation.
    This uses the WhatsApp Desktop app on user's PC for reliable messaging.
    Args:
        phone_number: Phone number with country code (e.g., '919876543210' for India +91)
                     Do NOT include + sign, brackets, dashes or spaces
        message: Content of the message to send
    Returns:
        Status message
    """
    # Clean phone number
    clean_phone = ''.join(filter(str.isdigit, phone_number))
    
    success = await _send_local_command("send_whatsapp", {
        "phone": clean_phone,
        "message": message
    })
    if success:
        return f"Done! WhatsApp message {phone_number} ko bhejne ka command diya Bhaiya!"
    return "Error: Desktop bridge se connection nahi hai."


async def send_whatsapp_contact_local(contact_name: str, message: str) -> str:
    """
    Send a WhatsApp message to a contact by searching their name.
    Uses local WhatsApp Desktop app with search functionality.
    Args:
        contact_name: Name of the contact to search and message
        message: Content of the message to send
    Returns:
        Status message
    """
    success = await _send_local_command("send_whatsapp_contact", {
        "contact": contact_name,
        "message": message
    })
    if success:
        return f"Done! {contact_name} ko WhatsApp message bhej diya!"
    return "Error: Desktop bridge se connection nahi hai."


async def type_text_local(text: str) -> str:
    """
    Type text on the user's PC using keyboard automation.
    Useful for typing in any currently focused application.
    Args:
        text: The text to type
    Returns:
        Status message
    """
    success = await _send_local_command("type_text", {"text": text})
    if success:
        return "Done! Text type kar diya!"
    return "Error: Desktop bridge se connection nahi hai."


async def press_key_local(key: str) -> str:
    """
    Press a keyboard key or combination on user's PC.
    Args:
        key: Key to press (e.g., 'enter', 'tab', 'escape', 'ctrl+s', 'alt+f4')
    Returns:
        Status message
    """
    success = await _send_local_command("press_key", {"key": key})
    if success:
        return f"Done! {key} press kar diya!"
    return "Error: Desktop bridge se connection nahi hai."


async def open_url_local(url: str) -> str:
    """
    Open a URL in the default browser on user's PC.
    Args:
        url: The URL to open
    Returns:
        Status message
    """
    success = await _send_local_command("open_url", {"url": url})
    if success:
        return f"Done! Browser mein {url} open kar diya!"
    return "Error: Desktop bridge se connection nahi hai."


async def play_youtube_local(query: str) -> str:
    """
    Search and play a YouTube video on user's PC.
    Args:
        query: What to search and play on YouTube
    Returns:
        Status message
    """
    success = await _send_local_command("play_youtube", {"query": query})
    if success:
        return f"Done! YouTube pe {query} search kar raha hoon!"
    return "Error: Desktop bridge se connection nahi hai."


async def take_screenshot_local() -> str:
    """
    Take a screenshot on the user's PC and save it to Pictures folder.
    Returns:
        Status message
    """
    success = await _send_local_command("screenshot", {})
    if success:
        return "Done! Screenshot le liya aur Pictures folder mein save kar diya!"
    return "Error: Desktop bridge se connection nahi hai."


async def set_volume_local(level: int) -> str:
    """
    Set system volume level on user's PC.
    Args:
        level: Volume level from 0 to 100
    Returns:
        Status message
    """
    success = await _send_local_command("set_volume", {"level": level})
    if success:
        return f"Done! Volume {level}% kar diya!"
    return "Error: Desktop bridge se connection nahi hai."


@function_tool()
async def lock_pc_local() -> str:
    """
    Lock the user's PC screen.
    Returns:
        Status message
    """
    success = await _send_local_command("lock_pc", {})
    if success:
        return "Done! PC lock kar diya Bhaiya!"
    return "Error: Desktop bridge se connection nahi hai."


@function_tool()
async def shutdown_pc_local(delay_seconds: int = 60) -> str:
    """
    Schedule PC shutdown after a delay.
    Args:
        delay_seconds: Seconds to wait before shutdown (default 60 for safety)
    Returns:
        Status message
    """
    success = await _send_local_command("shutdown", {"delay": delay_seconds})
    if success:
        return f"Done! PC {delay_seconds} seconds mein shutdown ho jayega. Cancel karne ke liye bolo."
    return "Error: Desktop bridge se connection nahi hai."


@function_tool()
async def cancel_shutdown_local() -> str:
    """
    Cancel any scheduled PC shutdown.
    Returns:
        Status message
    """
    success = await _send_local_command("cancel_shutdown", {})
    if success:
        return "Done! Shutdown cancel kar diya!"
    return "Error: Desktop bridge se connection nahi hai."
