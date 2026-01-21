"""
VYAAS AI - Advanced Automation Module
Keyboard/mouse automation for typing, clicking, and complete task execution
"""

import subprocess
import os
import time
import logging
from livekit.agents import function_tool

logger = logging.getLogger("vyaas_automation")
logger.setLevel(logging.INFO)

# Global variable to store last known mouse position for fail-safe
_last_mouse_pos = None
_automation_active = False

def check_user_interrupt():
    """
    Check if user has moved the mouse during automation.
    If mouse moved more than 50 pixels, user probably wants to take over.
    Returns True if user interrupted, False otherwise.
    """
    global _last_mouse_pos
    try:
        import pyautogui
        current_pos = pyautogui.position()
        
        if _last_mouse_pos is not None:
            dx = abs(current_pos[0] - _last_mouse_pos[0])
            dy = abs(current_pos[1] - _last_mouse_pos[1])
            
            # If mouse moved more than 50 pixels, user is interfering
            if dx > 50 or dy > 50:
                logger.warning("User interrupt detected - mouse moved!")
                return True
        
        _last_mouse_pos = current_pos
        return False
    except:
        return False

def safe_sleep(seconds: float) -> bool:
    """
    Sleep for specified seconds but check for user interrupt.
    Returns True if interrupted, False if completed normally.
    """
    global _last_mouse_pos
    try:
        import pyautogui
        _last_mouse_pos = pyautogui.position()
    except:
        pass
    
    time.sleep(seconds)
    return check_user_interrupt()


@function_tool()
async def type_text(text: str, delay: float = 0.05) -> str:
    """
    Type text using keyboard automation. Use this after opening an app to type content.
    Args:
        text: The text to type
        delay: Delay between keystrokes (default 0.05 seconds)
    Returns:
        Status message
    """
    logger.info(f"Typing text: {text[:50]}...")
    try:
        import pyautogui
        # Small delay to ensure app is focused
        time.sleep(0.5)
        pyautogui.typewrite(text, interval=delay) if text.isascii() else pyautogui.write(text)
        return f"Done! Text typed successfully"
    except ImportError:
        return "pyautogui not installed"
    except Exception as e:
        logger.error(f"Typing error: {e}")
        return f"Typing error: {str(e)}"

@function_tool()
async def type_text_unicode(text: str) -> str:
    """
    Type text including Hindi/Unicode characters using clipboard method.
    Args:
        text: The text to type (supports Hindi and special characters)
    Returns:
        Status message
    """
    logger.info(f"Typing unicode text: {text[:50]}...")
    try:
        import pyperclip
        import pyautogui
        
        # Save current clipboard
        old_clipboard = ""
        try:
            old_clipboard = pyperclip.paste()
        except:
            pass
        
        # Copy text to clipboard and paste
        pyperclip.copy(text)
        time.sleep(0.3)
        pyautogui.hotkey('ctrl', 'v')
        time.sleep(0.2)
        
        # Restore old clipboard
        try:
            pyperclip.copy(old_clipboard)
        except:
            pass
        
        return f"Done! Text typed successfully"
    except ImportError:
        return "pyautogui or pyperclip not installed"
    except Exception as e:
        logger.error(f"Typing error: {e}")
        return f"Typing error: {str(e)}"

@function_tool()
async def press_key(key: str) -> str:
    """
    Press a keyboard key or combination.
    Args:
        key: Key to press (e.g., 'enter', 'tab', 'escape', 'ctrl+s', 'alt+f4')
    Returns:
        Status message
    """
    logger.info(f"Pressing key: {key}")
    try:
        import pyautogui
        
        if '+' in key:
            # Key combination
            keys = key.lower().split('+')
            pyautogui.hotkey(*keys)
        else:
            pyautogui.press(key.lower())
        
        return f"Done! Pressed {key}"
    except ImportError:
        return "pyautogui not installed"
    except Exception as e:
        logger.error(f"Key press error: {e}")
        return f"Key press error: {str(e)}"

@function_tool()
async def open_notepad_and_write(content: str) -> str:
    """
    Open Notepad and write content to it.
    Args:
        content: The text content to write in Notepad
    Returns:
        Status message
    """
    logger.info(f"Opening Notepad and writing content")
    try:
        import pyautogui
        import pyperclip
        
        # Open Notepad
        subprocess.Popen("notepad", shell=True)
        time.sleep(1.5)  # Wait for Notepad to open
        
        # Type/Paste content
        pyperclip.copy(content)
        pyautogui.hotkey('ctrl', 'v')
        
        return f"Done! Notepad opened and content written"
    except Exception as e:
        logger.error(f"Notepad write error: {e}")
        return f"Error: {str(e)}"

@function_tool()
async def play_youtube_video(query: str) -> str:
    """
    Search YouTube and play the first video result.
    Args:
        query: What to search and play on YouTube
    Returns:
        Status message
    """
    logger.info(f"Playing YouTube video: {query}")
    try:
        import webbrowser
        import urllib.parse
        import pyautogui
        
        # Open YouTube search
        youtube_url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}"
        webbrowser.open(youtube_url)
        
        # Wait for page to load fully
        time.sleep(5)
        
        # Method 1: Click on first video thumbnail area
        # YouTube search results usually have first video around x=400, y=400
        screen_width, screen_height = pyautogui.size()
        # Click roughly where first video thumbnail would be
        click_x = int(screen_width * 0.25)  # Left-center area
        click_y = int(screen_height * 0.45)  # Middle-upper area
        
        pyautogui.click(click_x, click_y)
        time.sleep(0.5)
        pyautogui.click(click_x, click_y)  # Double click to be sure
        
        return f"Done! Playing: {query}"
    except Exception as e:
        logger.error(f"YouTube play error: {e}")
        return f"Error: {str(e)}"

@function_tool()
async def send_email_gmail(to_email: str, subject: str, body: str) -> str:
    """
    Open Gmail compose, fill details, AND automatically send the email.
    Args:
        to_email: Recipient email address
        subject: Email subject
        body: Email body content
    Returns:
        Status message
    """
    logger.info(f"Composing and sending email to: {to_email}")
    try:
        import webbrowser
        import urllib.parse
        import pyautogui
        import pyperclip
        
        # Open Gmail compose with prefilled data
        gmail_url = f"https://mail.google.com/mail/?view=cm&fs=1&to={urllib.parse.quote(to_email)}&su={urllib.parse.quote(subject)}&body={urllib.parse.quote(body)}"
        webbrowser.open(gmail_url)
        
        # Wait for Gmail to load fully (7 seconds)
        time.sleep(7)
        
        # Press Ctrl+Enter to send
        pyautogui.hotkey('ctrl', 'enter')
        
        return f"Done! Email opened and sent to {to_email}"
    except Exception as e:
        logger.error(f"Email error: {e}")
        return f"Error: {str(e)}"

@function_tool()
async def click_screen(x: int, y: int) -> str:
    """
    Click at specific screen coordinates.
    Args:
        x: X coordinate on screen
        y: Y coordinate on screen
    Returns:
        Status message
    """
    logger.info(f"Clicking at ({x}, {y})")
    try:
        import pyautogui
        pyautogui.click(x, y)
        return f"Done! Clicked at ({x}, {y})"
    except Exception as e:
        logger.error(f"Click error: {e}")
        return f"Error: {str(e)}"

@function_tool()
async def scroll(direction: str = "down", amount: int = 3) -> str:
    """
    Scroll the screen up or down.
    Args:
        direction: 'up' or 'down'
        amount: Number of scroll units (default 3)
    Returns:
        Status message
    """
    logger.info(f"Scrolling {direction} by {amount}")
    try:
        import pyautogui
        scroll_amount = amount if direction.lower() == "up" else -amount
        pyautogui.scroll(scroll_amount)
        return f"Done! Scrolled {direction}"
    except Exception as e:
        logger.error(f"Scroll error: {e}")
        return f"Error: {str(e)}"

@function_tool()
async def wait_seconds(seconds: float) -> str:
    """
    Wait for specified seconds before next action.
    Args:
        seconds: Number of seconds to wait
    Returns:
        Status message
    """
    time.sleep(seconds)
    return f"Done! Waited {seconds} seconds"

@function_tool()
async def get_screen_size() -> str:
    """
    Get the screen resolution.
    Returns:
        Screen dimensions
    """
    try:
        import pyautogui
        width, height = pyautogui.size()
        return f"Screen size: {width}x{height} pixels"
    except Exception as e:
        return f"Error: {str(e)}"

@function_tool()
async def focus_window(window_title: str) -> str:
    """
    Bring a window to focus by its title.
    Args:
        window_title: Part of the window title to search for
    Returns:
        Status message
    """
    logger.info(f"Focusing window: {window_title}")
    try:
        import pyautogui
        
        # Use PowerShell to focus window
        ps_command = f'''
        Add-Type @"
            using System;
            using System.Runtime.InteropServices;
            public class Win32 {{
                [DllImport("user32.dll")]
                public static extern bool SetForegroundWindow(IntPtr hWnd);
            }}
"@
        $process = Get-Process | Where-Object {{ $_.MainWindowTitle -like "*{window_title}*" }} | Select-Object -First 1
        if ($process) {{
            [Win32]::SetForegroundWindow($process.MainWindowHandle)
        }}
        '''
        subprocess.run(["powershell", "-Command", ps_command], capture_output=True)
        time.sleep(0.5)
        return f"Done! Focused window: {window_title}"
    except Exception as e:
        logger.error(f"Focus error: {e}")
        return f"Error: {str(e)}"

@function_tool()
async def send_whatsapp_to_phone(phone_number: str, message: str) -> str:
    """
    Send a WhatsApp message to a phone number using WhatsApp Desktop App.
    This is the MOST RELIABLE method - works without saving contacts!
    Args:
        phone_number: Phone number with country code (e.g., '919876543210' for India +91)
                     Do NOT include + sign, brackets, dashes or spaces
        message: Content of the message
    Returns:
        Status message
    """
    logger.info(f"Sending WhatsApp to phone: {phone_number}")
    try:
        import urllib.parse
        import pyautogui
        import pyperclip
        
        # Clean phone number - remove any non-digit characters
        clean_phone = ''.join(filter(str.isdigit, phone_number))
        
        # URL encode the message
        encoded_message = urllib.parse.quote(message)
        
        # Use WhatsApp Desktop URI scheme - opens directly in the app!
        whatsapp_uri = f"whatsapp://send?phone={clean_phone}&text={encoded_message}"
        
        # Open WhatsApp Desktop with the message
        subprocess.Popen(f'start "" "{whatsapp_uri}"', shell=True)
        
        # Wait for WhatsApp Desktop to open and load chat (reduced from 8s to 4s)
        time.sleep(4)
        
        # Get screen dimensions
        screen_width, screen_height = pyautogui.size()
        
        # Click center to ensure app is focused
        pyautogui.click(int(screen_width * 0.5), int(screen_height * 0.5))
        time.sleep(0.3)
        
        # The message is pre-filled, just press Enter to send!
        pyautogui.press('enter')
        
        return f"Done! Message sent to {phone_number}"
    except Exception as e:
        logger.error(f"WhatsApp phone error: {e}")
        return f"Error: {str(e)}"


@function_tool()
async def send_whatsapp_message(contact_name: str, message: str) -> str:
    """
    Send a WhatsApp message by searching contact name via WhatsApp Desktop App.
    IMPORTANT: Use send_whatsapp_to_phone if you have a phone number - it's more reliable!
    If you move your mouse during automation, it will stop.
    Args:
        contact_name: Precise contact name to search (supports Hindi/Unicode names)
        message: Content of the message (supports Hindi/Unicode)
    Returns:
        Status message
    """
    logger.info(f"Sending WhatsApp to contact: {contact_name}")
    try:
        import pyautogui
        import pyperclip
        global _last_mouse_pos
        
        # 1. Open WhatsApp Desktop App
        subprocess.Popen('start whatsapp:', shell=True)
        
        # Wait for WhatsApp Desktop to open
        if safe_sleep(5): return "Cancelled - user took over mouse"
        
        # 2. Get screen dimensions
        screen_width, screen_height = pyautogui.size()
        
        # 3. Click on WhatsApp window to ensure focus
        pyautogui.click(int(screen_width * 0.5), int(screen_height * 0.5))
        if safe_sleep(0.3): return "Cancelled - user took over mouse"
        
        # 4. Press Escape to clear any open dialogs
        pyautogui.press('escape')
        if safe_sleep(0.1): return "Cancelled - user took over mouse"
        
        # 5. Use Ctrl+F to open search in WhatsApp Desktop
        pyautogui.hotkey('ctrl', 'f')
        if safe_sleep(0.5): return "Cancelled - user took over mouse"
        
        # 6. Save clipboard
        old_clipboard = ""
        try:
            old_clipboard = pyperclip.paste()
        except:
            pass
        
        # 7. Clear search box and type contact name
        pyautogui.hotkey('ctrl', 'a')
        if safe_sleep(0.1): return "Cancelled - user took over mouse"
        
        # Type contact name using clipboard (supports Hindi/Unicode)
        pyperclip.copy(contact_name)
        time.sleep(0.1)
        pyautogui.hotkey('ctrl', 'v')
        
        # Wait for search results
        if safe_sleep(1): return "Cancelled - user took over mouse"
        
        # 8. Select first result
        pyautogui.press('down')
        if safe_sleep(0.1): return "Cancelled - user took over mouse"
        pyautogui.press('enter')
        
        # Wait for chat to load
        if safe_sleep(1): return "Cancelled - user took over mouse"
        
        # 9. Type message and send
        pyperclip.copy(message)
        time.sleep(0.1)
        pyautogui.hotkey('ctrl', 'v')
        if safe_sleep(0.2): return "Cancelled - user took over mouse"
        
        # 10. Send the message
        pyautogui.press('enter')
        
        # Restore original clipboard
        try:
            if old_clipboard:
                pyperclip.copy(old_clipboard)
        except:
            pass
        
        return f"Done! Message sent to {contact_name}"
    except Exception as e:
        logger.error(f"WhatsApp error: {e}")
        return f"Error: {str(e)}"

@function_tool()
async def send_instagram_message(username: str, message: str) -> str:
    """
    Send an Instagram DM via Web (requires Login).
    Args:
        username: Instagram username target
        message: Content of the message
    Returns:
        Status message
    """
    logger.info(f"Sending Insta DM to {username}")
    try:
        import webbrowser
        import pyautogui
        import pyperclip
        
        # 1. Open New Direct Message Page
        webbrowser.open("https://www.instagram.com/direct/new/")
        time.sleep(8)
        
        # 2. Type Username (Focus is usually on input)
        pyautogui.write(username, interval=0.05)
        time.sleep(3)
        
        # 3. Select First User (Tab + Tab + Enter usually works)
        pyautogui.press('tab') 
        time.sleep(0.2)
        pyautogui.press('tab') 
        time.sleep(0.2)
        pyautogui.press('enter') # Toggle selection
        time.sleep(1)
        
        # 4. Move to Chat (Next button)
        pyautogui.press('tab')
        pyautogui.press('enter') 
        time.sleep(5) # Wait for chat to load
        
        # 5. Send Message
        pyautogui.write(message, interval=0.01)
        time.sleep(0.5)
        pyautogui.press('enter')
        
        return f"Done! Attempted to send Insta DM to {username}"
    except Exception as e:
        logger.error(f"Instagram error: {e}")
        return f"Error: {str(e)}"


@function_tool()
async def send_whatsapp_file(phone_number: str, file_path: str, caption: str = "") -> str:
    """
    Send a file via WhatsApp Desktop App.
    Use this to share documents, images, PDFs, Excel files, etc.
    
    Args:
        phone_number: Phone number with country code (e.g., '919876543210' for India +91)
                     Do NOT include + sign, brackets, dashes or spaces
        file_path: Full path to the file to send (e.g., the file you just created on Desktop)
                  For Desktop files, use the exact filename returned by create_* functions
        caption: Optional caption/message to send with the file
    
    Returns:
        Status message
    """
    logger.info(f"Sending file via WhatsApp to: {phone_number}")
    try:
        import pyautogui
        import pyperclip
        
        # Clean phone number
        clean_phone = ''.join(filter(str.isdigit, phone_number))
        
        # Verify file exists
        if not os.path.exists(file_path):
            # Try looking on Desktop
            desktop = os.path.join(os.path.expanduser("~"), "Desktop")
            desktop_path = os.path.join(desktop, os.path.basename(file_path))
            if os.path.exists(desktop_path):
                file_path = desktop_path
            else:
                return f"Error: File not found at {file_path}"
        
        # Step 1: Open WhatsApp Desktop with the contact
        whatsapp_uri = f"whatsapp://send?phone={clean_phone}"
        subprocess.Popen(f'start "" "{whatsapp_uri}"', shell=True)
        time.sleep(5)  # Wait for WhatsApp to open
        
        # Step 2: Get screen dimensions and click to focus
        screen_width, screen_height = pyautogui.size()
        pyautogui.click(int(screen_width * 0.5), int(screen_height * 0.5))
        time.sleep(0.5)
        
        # Step 3: Use attachment button (Ctrl+Shift+A in some versions) or click attachment icon
        # First try keyboard shortcut
        pyautogui.hotkey('ctrl', 'o')  # Some versions use this
        time.sleep(1)
        
        # If that didn't work, try clicking the attachment icon (usually near bottom left of chat)
        # Typically around 15% from left, 85% from top
        attach_x = int(screen_width * 0.25)
        attach_y = int(screen_height * 0.92)
        pyautogui.click(attach_x, attach_y)
        time.sleep(1)
        
        # Click on "Document" option (usually appears as a menu)
        pyautogui.click(attach_x, attach_y - 100)  # Document is usually above
        time.sleep(2)
        
        # Step 4: File dialog should be open - type the file path
        pyperclip.copy(file_path)
        pyautogui.hotkey('ctrl', 'v')
        time.sleep(0.5)
        pyautogui.press('enter')
        time.sleep(2)
        
        # Step 5: Add caption if provided
        if caption:
            pyperclip.copy(caption)
            pyautogui.hotkey('ctrl', 'v')
            time.sleep(0.3)
        
        # Step 6: Send the file
        pyautogui.press('enter')
        
        return f"Done! File sent to {phone_number}"
    except Exception as e:
        logger.error(f"WhatsApp file send error: {e}")
        return f"Error: {str(e)}"
