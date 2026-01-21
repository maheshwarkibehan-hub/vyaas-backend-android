"""
VYAAS AI - Clipboard Control Module
Copy, paste, and manage clipboard content
"""

import logging
from livekit.agents import function_tool

logger = logging.getLogger("vyaas_clipboard")
logger.setLevel(logging.INFO)

@function_tool()
async def copy_to_clipboard(text: str) -> str:
    """
    Copy text to clipboard.
    Args:
        text: Text to copy to clipboard
    Returns:
        Confirmation message
    """
    try:
        import pyperclip
        pyperclip.copy(text)
        preview = text[:50] + "..." if len(text) > 50 else text
        return f"Done! Copied to clipboard: '{preview}'"
    except ImportError:
        # Fallback using PowerShell
        try:
            import subprocess
            subprocess.run(
                ["powershell", "-Command", f"Set-Clipboard -Value '{text}'"],
                check=True,
                capture_output=True
            )
            return f"Done! Text copied to clipboard"
        except Exception as e:
            return f"Error: {str(e)}"
    except Exception as e:
        logger.error(f"Clipboard copy error: {e}")
        return f"Error copying to clipboard: {str(e)}"

@function_tool()
async def get_clipboard_content() -> str:
    """
    Read current clipboard content.
    Returns:
        Content currently in clipboard
    """
    try:
        import pyperclip
        content = pyperclip.paste()
        if not content:
            return "Clipboard is empty"
        preview = content[:200] + "..." if len(content) > 200 else content
        return f"Clipboard content: {preview}"
    except ImportError:
        # Fallback using PowerShell
        try:
            import subprocess
            result = subprocess.run(
                ["powershell", "-Command", "Get-Clipboard"],
                capture_output=True,
                text=True
            )
            content = result.stdout.strip()
            if not content:
                return "Clipboard is empty"
            preview = content[:200] + "..." if len(content) > 200 else content
            return f"Clipboard content: {preview}"
        except Exception as e:
            return f"Error: {str(e)}"
    except Exception as e:
        logger.error(f"Clipboard read error: {e}")
        return f"Error reading clipboard: {str(e)}"

@function_tool()
async def clear_clipboard() -> str:
    """
    Clear the clipboard contents.
    Returns:
        Confirmation message
    """
    try:
        import pyperclip
        pyperclip.copy('')
        return "Done! Clipboard cleared"
    except ImportError:
        try:
            import subprocess
            subprocess.run(
                ["powershell", "-Command", "Set-Clipboard -Value $null"],
                check=True,
                capture_output=True
            )
            return "Done! Clipboard cleared"
        except Exception as e:
            return f"Error: {str(e)}"
    except Exception as e:
        logger.error(f"Clipboard clear error: {e}")
        return f"Error clearing clipboard: {str(e)}"

@function_tool()
async def clipboard_word_count() -> str:
    """
    Count words in clipboard content.
    Returns:
        Word count of clipboard content
    """
    try:
        import pyperclip
        content = pyperclip.paste()
        if not content:
            return "Clipboard is empty"
        words = len(content.split())
        chars = len(content)
        lines = content.count('\n') + 1
        return f"Clipboard stats: {words} words, {chars} characters, {lines} lines"
    except ImportError:
        try:
            import subprocess
            result = subprocess.run(
                ["powershell", "-Command", "Get-Clipboard"],
                capture_output=True,
                text=True
            )
            content = result.stdout.strip()
            if not content:
                return "Clipboard is empty"
            words = len(content.split())
            chars = len(content)
            lines = content.count('\n') + 1
            return f"Clipboard stats: {words} words, {chars} characters, {lines} lines"
        except Exception as e:
            return f"Error: {str(e)}"
    except Exception as e:
        return f"Error: {str(e)}"
