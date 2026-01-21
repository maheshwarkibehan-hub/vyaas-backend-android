
"""
VYAAS AI - Android Automation Module
Controls a connected Android device via ADB (Android Debug Bridge).
Requires 'USB Debugging' to be enabled on the phone.
"""

import subprocess
import logging
import time
from livekit.agents import function_tool

logger = logging.getLogger("vyaas_android")
logger.setLevel(logging.INFO)

# Hardcoded ADB Path found on user system
ADB_PATH = r"C:\Users\mahes\AppData\Local\Android\Sdk\platform-tools\adb.exe"

def run_adb_command(command_list):
    """Run an ADB command and return output."""
    try:
        full_command = [ADB_PATH] + command_list
        # Increased timeout for connection attempts
        result = subprocess.run(full_command, capture_output=True, text=True, timeout=15)
        return result.stdout.strip()
    except Exception as e:
        logger.error(f"ADB Error: {e}")
        return f"Error: {str(e)}"

@function_tool()
async def pair_android_device(ip_address: str, pairing_port: str, pairing_code: str) -> str:
    """
    Pair Android device using Wireless Debugging (Step 1).
    Use this if device is NOT yet paired.
    Args:
        ip_address: IP Address of phone
        pairing_port: Port from 'Pair device with pairing code' dialog
        pairing_code: 6-digit Wi-Fi pairing code
    Returns:
        Status message
    """
    logger.info(f"Pairing with {ip_address}:{pairing_port} using code {pairing_code}")
    
    # Run: adb pair ip:port code
    pair_out = run_adb_command(["pair", f"{ip_address}:{pairing_port}", pairing_code])
    
    if "successfully paired" in (pair_out or "").lower() or "already" in (pair_out or "").lower():
        return f"Done! Successfully paired. Now you MUST Connect using the main IP and Port."
    else:
        return f"Pairing Failed: {pair_out}. Check IP, Port, and Code carefully."

@function_tool()
async def connect_android_device(ip_address: str, port: str) -> str:
    """
    Connect to Android device via ADB Wireless (Step 2).
    Args:
        ip_address: IP Address (from 'Wireless Debugging' main screen)
        port: Port (from 'Wireless Debugging' main screen - DIFFERENT from pairing port)
    Returns:
        Status message
    """
    logger.info(f"Connecting to {ip_address}:{port}")
    
    # 0. Clear stale connections first (Fixes 'offline' status)
    run_adb_command(["disconnect"])
    time.sleep(1)
    
    # 1. Connect
    connect_out = run_adb_command(["connect", f"{ip_address}:{port}"])
    time.sleep(1)
    
    if "connected to" in (connect_out or "").lower() or "already connected" in (connect_out or "").lower():
        # Verify device listing
        devices = run_adb_command(["devices"])
        if f"{ip_address}:{port}" in devices and "offline" not in devices:
             return f"Done! Connected to {ip_address}:{port} via Wi-Fi."
        elif "offline" in devices:
             # Try one kill-server reset if still offline
             run_adb_command(["kill-server"])
             run_adb_command(["connect", f"{ip_address}:{port}"])
             return f"Device connected but showed 'offline'. I restarted ADB. Please check if it works now."
        return f"Command said connected, but device not in list. Try again."
    else:
        return f"Connection Failed: {connect_out}. Ensure 'Wireless Debugging' is ON and using the MAIN port (not pairing port)."

@function_tool()
async def open_android_app(app_name: str) -> str:
    """
    Open an app on the connected Android phone.
    Args:
        app_name: Name of the app (e.g., 'whatsapp', 'youtube', 'chrome', 'spotify', 'instagram')
    Returns:
        Status message
    """
    app_map = {
        "whatsapp": "com.whatsapp",
        "youtube": "com.google.android.youtube",
        "chrome": "com.android.chrome",
        "spotify": "com.spotify.music",
        "instagram": "com.instagram.android",
        "maps": "com.google.android.apps.maps",
        "gmail": "com.google.android.gm",
        "phone": "com.google.android.dialer",
        "camera": "com.android.camera2" # Varies by device
    }
    
    package = app_map.get(app_name.lower())
    
    if not package:
        # Try generic launch logic for unknown apps?
        return f"Error: I don't know the package name for '{app_name}'. Supported: {', '.join(app_map.keys())}"
    
    logger.info(f"Opening Android App: {app_name} ({package})")
    
    # Check device
    devices = run_adb_command(["devices"])
    if "device" not in devices.replace("List of devices attached", "").strip():
        return "Error: No Android phone connected via USB/ADB. Please connect phone and enable USB Debugging."

    # Launch App
    # monkey -p <package> 1 is a robust way to launch main activity without knowing activity name
    run_adb_command(["shell", "monkey", "-p", package, "-c", "android.intent.category.LAUNCHER", "1"])
    
    return f"Done! Opened {app_name} on your phone."

@function_tool()
async def send_android_whatsapp(phone_number: str, message: str) -> str:
    """
    Send a WhatsApp message via Android Phone using phone number.
    Args:
        phone_number: Number with country code (e.g., '919876543210')
        message: Text message to send
    Returns:
        Status message
    """
    logger.info(f"Sending Android WhatsApp to {phone_number}")
    
    # Sanitize number
    phone_number = phone_number.replace("+", "").replace(" ", "")
    
    try:
        # Use Intent to open chat with prefilled text
        url = f"https://api.whatsapp.com/send?phone={phone_number}&text={message}"
        cmd = ["shell", "am", "start", "-a", "android.intent.action.VIEW", "-d", f"\"{url}\""]
        
        run_adb_command(cmd)
        
        # Wait for WhatsApp to open and load
        time.sleep(3)
        
        # Click "Send" button by pressing Enter
        run_adb_command(["shell", "input", "keyevent", "66"]) # KEYCODE_ENTER
        run_adb_command(["shell", "input", "keyevent", "66"]) # Twice to be sure
        
        return f"Done! WhatsApp opened on phone with message for {phone_number}. (Tap Send if it didn't go)"
    except Exception as e:
        return f"Error: {str(e)}"


@function_tool()
async def search_and_send_android_whatsapp(contact_name: str, message: str) -> str:
    """
    Search for a contact by name in WhatsApp and send message via Android Phone.
    This opens WhatsApp, searches for the contact, and sends the message.
    Args:
        contact_name: Name of the contact to search for (e.g., 'Mithul', 'Mom')
        message: Text message to send
    Returns:
        Status message
    """
    logger.info(f"Searching and sending Android WhatsApp to {contact_name}")
    
    try:
        # 1. Open WhatsApp
        run_adb_command(["shell", "monkey", "-p", "com.whatsapp", "-c", "android.intent.category.LAUNCHER", "1"])
        time.sleep(3)  # Wait for WhatsApp to open
        
        # 2. Tap on Search icon (usually top right)
        # Get screen size first
        screen_info = run_adb_command(["shell", "wm", "size"])
        # Default to common screen size if can't get
        width, height = 1080, 2400
        try:
            if "x" in screen_info:
                parts = screen_info.split(":")[-1].strip().split("x")
                width = int(parts[0])
                height = int(parts[1])
        except:
            pass
        
        # Search icon is usually at top right
        search_x = int(width * 0.85)  # 85% from left
        search_y = int(height * 0.06)  # 6% from top (in status bar area)
        
        run_adb_command(["shell", "input", "tap", str(search_x), str(search_y)])
        time.sleep(1)
        
        # 3. Type contact name
        # First clear any existing text
        run_adb_command(["shell", "input", "keyevent", "28"])  # KEYCODE_CLEAR
        time.sleep(0.3)
        
        # Type the contact name
        # ADB input text doesn't work well with spaces, so replace with %s
        safe_name = contact_name.replace(" ", "%s")
        run_adb_command(["shell", "input", "text", safe_name])
        time.sleep(2)  # Wait for search results
        
        # 4. Tap on first search result (usually below search bar)
        result_x = int(width * 0.5)  # Center horizontally
        result_y = int(height * 0.18)  # About 18% from top
        
        run_adb_command(["shell", "input", "tap", str(result_x), str(result_y)])
        time.sleep(2)  # Wait for chat to open
        
        # 5. Type message in the message input
        # The message input is at the bottom of the screen
        # But we need to tap it first to focus
        msg_input_x = int(width * 0.5)
        msg_input_y = int(height * 0.93)  # Bottom area
        
        run_adb_command(["shell", "input", "tap", str(msg_input_x), str(msg_input_y)])
        time.sleep(0.5)
        
        # Type the message
        safe_message = message.replace(" ", "%s")
        run_adb_command(["shell", "input", "text", safe_message])
        time.sleep(0.5)
        
        # 6. Send the message (tap send button or press enter)
        # Send button is at bottom right
        send_x = int(width * 0.95)
        send_y = int(height * 0.93)
        
        run_adb_command(["shell", "input", "tap", str(send_x), str(send_y)])
        
        return f"Done! Searched for {contact_name} and sent message on WhatsApp."
    except Exception as e:
        logger.error(f"Android WhatsApp search error: {e}")
        return f"Error: {str(e)}"


@function_tool()
async def make_android_call(phone_number: str) -> str:
    """
    Make a phone call via Android Phone.
    Args:
        phone_number: Number to call
    Returns:
        Status message
    """
    logger.info(f"Calling {phone_number} on Android")
    
    # ADB Command to dial
    # am start -a android.intent.action.CALL -d tel:123456789 (Direct Call, permissions needed)
    # am start -a android.intent.action.DIAL -d tel:123456789 (Opens Dialer, safer)
    
    cmd = ["shell", "am", "start", "-a", "android.intent.action.CALL", "-d", f"tel:{phone_number}"]
    output = run_adb_command(cmd)
    
    # If ACTION_CALL fails due to permissions, fallback to DIAL
    if "SecurityException" in (output or ""):
        run_adb_command(["shell", "am", "start", "-a", "android.intent.action.DIAL", "-d", f"tel:{phone_number}"])
        return f"Done! Opened dialer for {phone_number}. Please press Call."
        
    return f"Done! Calling {phone_number}..."

@function_tool()
async def search_android_youtube(query: str) -> str:
    """
    Search and play video on Android YouTube app.
    Args:
        query: Video to search
    Returns:
        Status
    """
    # Intent: https://www.youtube.com/results?search_query=...
    # Or strict intent
    query_url = query.replace(" ", "+")
    cmd = ["shell", "am", "start", "-a", "android.intent.action.VIEW", "-d", f"\"https://www.youtube.com/results?search_query={query_url}\""]
    run_adb_command(cmd)
    
    # Wait and tap first video?
    time.sleep(4)
    # Generic Center Tap?
    # run_adb_command(["shell", "input", "tap", "500", "500"]) 
    
    return f"Done! Opened YouTube search for '{query}'"
