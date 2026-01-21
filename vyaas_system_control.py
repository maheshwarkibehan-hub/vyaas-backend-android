"""
VYAAS AI - System Control Module
System operations like shutdown, restart, open apps, open files, etc.
Supports Windows and Android (Termux).
"""

import subprocess
import os
import logging
from livekit.agents import function_tool
import termux_compatibility as termux

# Configure logging
logger = logging.getLogger("vyaas_system_control")
logger.setLevel(logging.INFO)

@function_tool()
async def system_shutdown(delay_seconds: int = 60) -> str:
    """
    Shutdown the computer after a delay.
    Args:
        delay_seconds: Seconds to wait before shutdown (default 60 seconds for safety)
    Returns:
        Status message confirming shutdown scheduled
    """
    if termux.is_android():
        return "⚠️ Shutdown is not supported on Android without root."

    logger.info(f"System shutdown scheduled in {delay_seconds} seconds")
    try:
        # Windows shutdown command
        subprocess.run(["shutdown", "/s", "/t", str(delay_seconds)], check=True)
        return f"✅ System shutdown scheduled in {delay_seconds} seconds. Say 'cancel shutdown' to stop it."
    except Exception as e:
        logger.error(f"Shutdown failed: {e}")
        return f"❌ Shutdown failed: {str(e)}"

@function_tool()
async def system_restart(delay_seconds: int = 60) -> str:
    """
    Restart the computer after a delay.
    Args:
        delay_seconds: Seconds to wait before restart (default 60 seconds for safety)
    Returns:
        Status message confirming restart scheduled
    """
    if termux.is_android():
        return "⚠️ Restart is not supported on Android without root."

    logger.info(f"System restart scheduled in {delay_seconds} seconds")
    try:
        # Windows restart command
        subprocess.run(["shutdown", "/r", "/t", str(delay_seconds)], check=True)
        return f"✅ System restart scheduled in {delay_seconds} seconds. Say 'cancel restart' to stop it."
    except Exception as e:
        logger.error(f"Restart failed: {e}")
        return f"❌ Restart failed: {str(e)}"

@function_tool()
async def cancel_shutdown() -> str:
    """
    Cancel any scheduled shutdown or restart.
    Returns:
        Status message confirming cancellation
    """
    if termux.is_android():
        return "⚠️ No shutdown to cancel on Android."

    logger.info("Cancelling scheduled shutdown/restart")
    try:
        subprocess.run(["shutdown", "/a"], check=True)
        return "✅ Shutdown/restart cancelled successfully!"
    except Exception as e:
        logger.error(f"Cancel failed: {e}")
        return f"❌ No shutdown/restart was scheduled or cancel failed: {str(e)}"

@function_tool()
async def open_chrome(url: str = "") -> str:
    """
    Open Google Chrome browser, optionally with a specific URL.
    Args:
        url: Optional URL to open (leave empty to just open Chrome)
    Returns:
        Status message
    """
    logger.info(f"Opening Chrome with URL: {url if url else 'homepage'}")
    
    if termux.is_android():
        target = url if url else "https://google.com"
        termux.termux_open_url(target)
        return f"✅ Opened {target} on Android."

    try:
        import webbrowser
        
        if url:
            # Use webbrowser module for reliable URL opening
            webbrowser.open(url)
            return f"Done! Chrome opened with {url}"
        else:
            # Try to open Chrome directly
            chrome_paths = [
                r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
                os.path.expanduser(r"~\AppData\Local\Google\Chrome\Application\chrome.exe")
            ]
            
            for path in chrome_paths:
                if os.path.exists(path):
                    subprocess.Popen([path])
                    return "Done! Chrome browser opened!"
            
            # Fallback - use start command
            subprocess.Popen("start chrome", shell=True)
            return "Done! Chrome opened!"
    except Exception as e:
        logger.error(f"Failed to open Chrome: {e}")
        return f"Chrome open karne mein error: {str(e)}"

@function_tool()
async def open_application(app_name: str) -> str:
    """
    Open any application by name.
    Args:
        app_name: Name of the application to open
    Returns:
        Status message
    """
    logger.info(f"Opening application: {app_name}")
    
    if termux.is_android():
        # Map common names to Android packages or use simple launch attempt
        # Ideally, we should use 'monkey' via ADB if permissions allow, 
        # but termux-open works for files/urls. Launching apps directly from Termux 
        # without ADB usually requires 'am start' which might work.
        
        app_map = {
            "whatsapp": "com.whatsapp",
            "youtube": "com.google.android.youtube",
            "chrome": "com.android.chrome",
            "spotify": "com.spotify.music",
            "instagram": "com.instagram.android",
            "settings": "com.android.settings",
            "camera": "com.android.camera2",
            "maps": "com.google.android.apps.maps"
        }
        
        pkg = app_map.get(app_name.lower())
        if pkg:
            # Try launching with monkey tool (requires ADB usually, but let's try direct am start)
            # 'am start' works in Termux!
            try:
                 subprocess.run(["am", "start", "--user", "0", "-n", f"{pkg}/.MainActivity"], stderr=subprocess.DEVNULL)
                 # If MainActivity fails, try monkey
                 subprocess.run(["monkey", "-p", pkg, "-c", "android.intent.category.LAUNCHER", "1"], stderr=subprocess.DEVNULL)
                 return f"✅ Attempted to open {app_name} on Android."
            except Exception as e:
                 return f"❌ Failed to launch {app_name}: {e}"
        return f"⚠️ App '{app_name}' not mapped for Android launch. Try 'open whatsapp' etc."

    # Windows Logic
    app_mappings = {
        "notepad": "notepad",
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
        "terminal": "wt",  # Windows Terminal
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
        "sublime": "subl",
        "chrome": "chrome",
        "firefox": "firefox",
        "edge": "msedge",
        "brave": "brave",
        "whatsapp": "WhatsApp",
        "telegram": "Telegram",
    }
    
    app_lower = app_name.lower().strip()
    command = app_mappings.get(app_lower, app_name)
    
    try:
        # Try to run directly first
        subprocess.Popen(command, shell=True)
        return f"✅ {app_name} opened successfully!"
    except Exception as e:
        try:
            # Try using 'start' command
            os.system(f'start "" "{command}"')
            return f"✅ {app_name} opened!"
        except Exception as e2:
            logger.error(f"Failed to open {app_name}: {e2}")
            return f"❌ Failed to open {app_name}: {str(e2)}"

@function_tool()  
async def open_file(file_path: str) -> str:
    """
    Open any file with its default application.
    Args:
        file_path: Full path to the file to open
    Returns:
        Status message
    """
    logger.info(f"Opening file: {file_path}")
    
    if termux.is_android():
        try:
            subprocess.run(["termux-open", file_path])
            return f"✅ File opened on Android: {file_path}"
        except Exception as e:
            return f"❌ Failed to open file: {e}"

    try:
        # Normalize path
        file_path = os.path.normpath(file_path)
        
        if not os.path.exists(file_path):
            return f"❌ File not found: {file_path}"
        
        # Use os.startfile on Windows to open with default app
        os.startfile(file_path)
        return f"✅ File opened: {file_path}"
    except Exception as e:
        logger.error(f"Failed to open file: {e}")
        return f"❌ Failed to open file: {str(e)}"

@function_tool()
async def open_folder(folder_path: str) -> str:
    """
    Open a folder in File Explorer.
    Args:
        folder_path: Full path to the folder
    Returns:
        Status message
    """
    logger.info(f"Opening folder: {folder_path}")
    
    if termux.is_android():
        try:
             subprocess.run(["termux-open", folder_path])
             return f"✅ Folder opened: {folder_path}"
        except Exception as e:
             return f"❌ Failed: {e}"

    try:
        folder_path = os.path.normpath(folder_path)
        
        if not os.path.exists(folder_path):
            return f"❌ Folder not found: {folder_path}"
        
        subprocess.Popen(['explorer', folder_path])
        return f"✅ Folder opened: {folder_path}"
    except Exception as e:
        logger.error(f"Failed to open folder: {e}")
        return f"❌ Failed to open folder: {str(e)}"

@function_tool()
async def lock_computer() -> str:
    """
    Lock the computer screen.
    Returns:
        Status message
    """
    if termux.is_android():
        # Try to lock using keyevent if possible, or just fail
        return "⚠️ Locking phone screen requires admin/root. Not supported."

    logger.info("Locking computer")
    try:
        subprocess.run(["rundll32.exe", "user32.dll,LockWorkStation"], check=True)
        return "✅ Computer locked!"
    except Exception as e:
        logger.error(f"Failed to lock: {e}")
        return f"❌ Failed to lock computer: {str(e)}"

@function_tool()
async def set_volume(level: int) -> str:
    """
    Set system volume level.
    Args:
        level: Volume level from 0 to 100
    Returns:
        Status message
    """
    logger.info(f"Setting volume to {level}%")
    
    if termux.is_android():
        # Scale 0-100 to typical Android max 15
        android_vol = int((level / 100) * 15)
        termux.termux_volume("music", android_vol)
        return f"✅ Android Volume set to {android_vol}/15"

    try:
        # Using nircmd for volume control (if installed) or PowerShell
        level = max(0, min(100, level))  # Clamp between 0-100
        
        # PowerShell approach
        ps_command = f'''
        $obj = New-Object -ComObject WScript.Shell
        1..50 | ForEach-Object {{ $obj.SendKeys([char]174) }}
        1..{level // 2} | ForEach-Object {{ $obj.SendKeys([char]175) }}
        '''
        subprocess.run(["powershell", "-Command", ps_command], check=True, capture_output=True)
        return f"✅ Volume set to approximately {level}%"
    except Exception as e:
        logger.error(f"Failed to set volume: {e}")
        return f"❌ Failed to set volume: {str(e)}"

@function_tool()
async def mute_unmute() -> str:
    """
    Toggle mute/unmute system audio.
    Returns:
        Status message
    """
    if termux.is_android():
        return "⚠️ Mute toggle not directly supported via Termux. Set volume to 0 manually."

    logger.info("Toggling mute")
    try:
        ps_command = '''
        $obj = New-Object -ComObject WScript.Shell
        $obj.SendKeys([char]173)
        '''
        subprocess.run(["powershell", "-Command", ps_command], check=True, capture_output=True)
        return "✅ Audio muted/unmuted!"
    except Exception as e:
        logger.error(f"Failed to toggle mute: {e}")
        return f"❌ Failed to toggle mute: {str(e)}"

@function_tool()
async def take_screenshot() -> str:
    """
    Take a screenshot and save it to Pictures folder.
    Returns:
        Status message with file path
    """
    logger.info("Taking screenshot")
    
    if termux.is_android():
        # Use screencap
        try:
            import datetime
            filename = f"screenshot_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            # Save to /sdcard/Pictures
            filepath = f"/sdcard/Pictures/{filename}"
            subprocess.run(["screencap", "-p", filepath])
            return f"✅ Screenshot saved to {filepath}"
        except Exception as e:
            return f"❌ Screenshot failed: {e}"

    try:
        import datetime
        pictures_folder = os.path.expanduser("~/Pictures")
        filename = f"screenshot_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        filepath = os.path.join(pictures_folder, filename)
        
        # Use PowerShell to take screenshot
        ps_command = f'''
        Add-Type -AssemblyName System.Windows.Forms
        $screen = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
        $bitmap = New-Object System.Drawing.Bitmap($screen.Width, $screen.Height)
        $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
        $graphics.CopyFromScreen($screen.Location, [System.Drawing.Point]::Empty, $screen.Size)
        $bitmap.Save("{filepath}")
        '''
        subprocess.run(["powershell", "-Command", ps_command], check=True, capture_output=True)
        return f"✅ Screenshot saved to: {filepath}"
    except Exception as e:
        logger.error(f"Failed to take screenshot: {e}")
        return f"❌ Failed to take screenshot: {str(e)}"

@function_tool()
async def search_web(query: str) -> str:
    """
    Search the web using default browser.
    Args:
        query: Search query
    Returns:
        Status message
    """
    logger.info(f"Searching web for: {query}")
    try:
        import urllib.parse
        target_url = f"https://www.google.com/search?q={urllib.parse.quote(query)}"
        
        if termux.is_android():
            termux.termux_open_url(target_url)
        else:
            import webbrowser
            webbrowser.open(target_url)
            
        return f"Done! Searching for: {query}"
    except Exception as e:
        logger.error(f"Failed to search: {e}")
        return f"Search error: {str(e)}"

@function_tool()
async def play_youtube(query: str) -> str:
    """
    Search and open YouTube with a search query.
    Args:
        query: What to search on YouTube
    Returns:
        Status message
    """
    logger.info(f"Opening YouTube with search: {query}")
    try:
        import urllib.parse
        youtube_url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}"
        
        if termux.is_android():
            termux.termux_open_url(youtube_url)
        else:
            import webbrowser
            webbrowser.open(youtube_url)
            
        return f"Done! YouTube search for: {query}"
    except Exception as e:
        logger.error(f"Failed to open YouTube: {e}")
        return f"YouTube error: {str(e)}"
