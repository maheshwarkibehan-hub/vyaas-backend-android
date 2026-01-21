"""
VYAAS AI - Music Control Module
Control music playback - Spotify, YouTube Music, and media keys
Supports Windows and Android (Termux).
"""

import subprocess
import os
import logging
from livekit.agents import function_tool
import termux_compatibility as termux

logger = logging.getLogger("vyaas_music")
logger.setLevel(logging.INFO)

@function_tool()
async def play_spotify(query: str = "") -> str:
    """
    Open Spotify and optionally search/play something.
    Args:
        query: Song, artist, or playlist to search for (optional)
    Returns:
        Status message
    """
    logger.info(f"Opening Spotify with query: {query}")
    
    if termux.is_android():
        # Android Intent for Spotify Search
        # am start -a android.media.action.MEDIA_PLAY_FROM_SEARCH -e query "query"
        # Or specifically for spotify:
        # am start -n com.spotify.music/.MainActivity -a android.intent.action.VIEW -d "spotify:search:query"
        try:
             import urllib.parse
             if query:
                 uri = f"spotify:search:{urllib.parse.quote(query)}"
                 subprocess.run(["am", "start", "-a", "android.intent.action.VIEW", "-d", uri])
             else:
                 subprocess.run(["monkey", "-p", "com.spotify.music", "-c", "android.intent.category.LAUNCHER", "1"])
             return f"✅ Spotify opened on Android for: {query}"
        except Exception as e:
             return f"❌ Spotify launch failed: {e}"

    try:
        import urllib.parse
        
        if query:
            # Open Spotify with search
            spotify_uri = f"spotify:search:{urllib.parse.quote(query)}"
            os.system(f'start "" "{spotify_uri}"')
            return f"Done! Spotify opened with search: {query}"
        else:
            # Just open Spotify
            subprocess.Popen("spotify", shell=True)
            return "Done! Spotify opened"
    except Exception as e:
        logger.error(f"Spotify error: {e}")
        return f"Error: {str(e)}"

@function_tool()
async def play_youtube_music(query: str) -> str:
    """
    Open YouTube Music with a search query.
    Args:
        query: Song or artist to search for
    Returns:
        Status message
    """
    logger.info(f"Opening YouTube Music: {query}")
    
    if termux.is_android():
        try:
             import urllib.parse
             # Use YouTube Music App Intent if possible, or browser
             # Package: com.google.android.apps.youtube.music
             target_url = f"https://music.youtube.com/search?q={urllib.parse.quote(query)}"
             termux.termux_open_url(target_url)
             return f"✅ YouTube Music opened for: {query}"
        except Exception as e:
             return f"❌ YT Music launch failed: {e}"

    try:
        import urllib.parse
        import webbrowser
        
        url = f"https://music.youtube.com/search?q={urllib.parse.quote(query)}"
        webbrowser.open(url)
        return f"Done! YouTube Music opened with search: {query}"
    except Exception as e:
        logger.error(f"YouTube Music error: {e}")
        return f"Error: {str(e)}"

@function_tool()
async def play_pause_media() -> str:
    """
    Press play/pause media key to control current media.
    Returns:
        Status message
    """
    if termux.is_android():
        # Input keyevent 85 is PLAY/PAUSE
        try:
            subprocess.run(["input", "keyevent", "85"])
            return "✅ Play/Pause toggled on Android"
        except Exception as e:
            return f"❌ Failed: {e}"

    try:
        # Using PowerShell to send media key
        ps_command = '''
        $obj = New-Object -ComObject WScript.Shell
        $obj.SendKeys([char]0xB3)
        '''
        subprocess.run(["powershell", "-Command", ps_command], check=True, capture_output=True)
        return "Done! Play/Pause toggled"
    except Exception as e:
        logger.error(f"Media control error: {e}")
        return f"Error: {str(e)}"

@function_tool()
async def next_track() -> str:
    """
    Skip to next track in current media player.
    Returns:
        Status message
    """
    if termux.is_android():
        # Input keyevent 87 is NEXT
        try:
            subprocess.run(["input", "keyevent", "87"])
            return "✅ Skipped to next track on Android"
        except Exception as e:
            return f"❌ Failed: {e}"

    try:
        ps_command = '''
        $obj = New-Object -ComObject WScript.Shell
        $obj.SendKeys([char]0xB0)
        '''
        subprocess.run(["powershell", "-Command", ps_command], check=True, capture_output=True)
        return "Done! Skipped to next track"
    except Exception as e:
        logger.error(f"Next track error: {e}")
        return f"Error: {str(e)}"

@function_tool()
async def previous_track() -> str:
    """
    Go to previous track in current media player.
    Returns:
        Status message
    """
    if termux.is_android():
        # Input keyevent 88 is PREVIOUS
        try:
            subprocess.run(["input", "keyevent", "88"])
            return "✅ Previous track on Android"
        except Exception as e:
            return f"❌ Failed: {e}"

    try:
        ps_command = '''
        $obj = New-Object -ComObject WScript.Shell
        $obj.SendKeys([char]0xB1)
        '''
        subprocess.run(["powershell", "-Command", ps_command], check=True, capture_output=True)
        return "Done! Went to previous track"
    except Exception as e:
        logger.error(f"Previous track error: {e}")
        return f"Error: {str(e)}"

@function_tool()
async def stop_media() -> str:
    """
    Stop current media playback.
    Returns:
        Status message
    """
    if termux.is_android():
        # Input keyevent 86 is STOP
        try:
            subprocess.run(["input", "keyevent", "86"])
            return "✅ Media stopped on Android"
        except Exception as e:
            return f"❌ Failed: {e}"

    try:
        ps_command = '''
        $obj = New-Object -ComObject WScript.Shell
        $obj.SendKeys([char]0xB2)
        '''
        subprocess.run(["powershell", "-Command", ps_command], check=True, capture_output=True)
        return "Done! Media stopped"
    except Exception as e:
        logger.error(f"Stop media error: {e}")
        return f"Error: {str(e)}"

@function_tool()
async def open_music_app(app_name: str = "spotify") -> str:
    """
    Open a specific music application.
    Args:
        app_name: Name of music app (spotify, youtube_music, apple_music, vlc)
    Returns:
        Status message
    """
    app_lower = app_name.lower().strip()
    
    if termux.is_android():
         # Simple intent mapping
         pkg_map = {
             "spotify": "com.spotify.music",
             "vlc": "org.videolan.vlc",
             "youtube music": "com.google.android.apps.youtube.music",
             "ytmusic": "com.google.android.apps.youtube.music"
         }
         pkg = pkg_map.get(app_lower)
         if not pkg:
             if "youtube" in app_lower: pkg = "com.google.android.apps.youtube.music"
             else: pkg = "com.spotify.music" # Default fallback
             
         try:
             subprocess.run(["monkey", "-p", pkg, "-c", "android.intent.category.LAUNCHER", "1"])
             return f"✅ Opened {app_name} on Android."
         except Exception as e:
             return f"❌ Failed to open app: {e}"

    app_commands = {
        "spotify": "spotify",
        "vlc": "vlc",
        "itunes": "iTunes",
        "windows media player": "wmplayer",
        "groove": "mswindowsmusic:",
    }
    
    try:
        if app_lower in ["youtube music", "youtube_music", "ytmusic"]:
            import webbrowser
            webbrowser.open("https://music.youtube.com")
            return "Done! YouTube Music opened"
        elif app_lower in ["apple music", "apple_music"]:
            import webbrowser
            webbrowser.open("https://music.apple.com")
            return "Done! Apple Music opened"
        else:
            command = app_commands.get(app_lower, app_lower)
            subprocess.Popen(command, shell=True)
            return f"Done! {app_name} opened"
    except Exception as e:
        logger.error(f"Music app error: {e}")
        return f"Error: {str(e)}"

@function_tool()
async def search_song(query: str, platform: str = "youtube") -> str:
    """
    Search for a song on specified platform.
    Args:
        query: Song name or artist to search
        platform: Platform to search on (youtube, spotify, google)
    Returns:
        Status message
    """
    try:
        import urllib.parse
        
        platform = platform.lower()
        if termux.is_android():
             # Basic URL/Intent routing
             if platform == "spotify":
                 return await play_spotify(query)
             else:
                 return await play_youtube_music(query)

        import webbrowser
        if platform == "spotify":
            url = f"spotify:search:{urllib.parse.quote(query)}"
            os.system(f'start "" "{url}"')
        elif platform == "youtube":
            url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(query + ' song')}"
            webbrowser.open(url)
        elif platform == "google":
            url = f"https://www.google.com/search?q={urllib.parse.quote(query + ' song')}"
            webbrowser.open(url)
        else:
            url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}"
            webbrowser.open(url)
        
        return f"Done! Searching for '{query}' on {platform}"
    except Exception as e:
        logger.error(f"Search error: {e}")
        return f"Error: {str(e)}"
