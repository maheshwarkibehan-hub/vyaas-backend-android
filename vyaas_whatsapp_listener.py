"""
VYAAS WhatsApp Listener Module
Integrates with Node.js WhatsApp service for message detection and replies
"""

import subprocess
import requests
import logging
import os
import time
import asyncio
from typing import Optional, List, Dict
from livekit.agents import function_tool

logger = logging.getLogger("vyaas_whatsapp")
logger.setLevel(logging.INFO)

# Configuration
WHATSAPP_SERVICE_URL = "http://127.0.0.1:3001"
WHATSAPP_SERVICE_PATH = os.path.join(os.path.dirname(__file__), "whatsapp-service")

# Global state
_whatsapp_process = None
_last_notified_messages = set()  # Track already notified message IDs


def is_whatsapp_service_running() -> bool:
    """Check if WhatsApp service is running and ready"""
    try:
        response = requests.get(f"{WHATSAPP_SERVICE_URL}/health", timeout=2)
        data = response.json()
        return data.get("ready", False)
    except:
        return False


def start_whatsapp_service() -> bool:
    """Start the WhatsApp Node.js service"""
    global _whatsapp_process
    
    if is_whatsapp_service_running():
        logger.info("WhatsApp service already running")
        return True
    
    try:
        # Check if node_modules exists, if not install
        node_modules = os.path.join(WHATSAPP_SERVICE_PATH, "node_modules")
        if not os.path.exists(node_modules):
            logger.info("Installing WhatsApp service dependencies...")
            subprocess.run(
                ["npm", "install"],
                cwd=WHATSAPP_SERVICE_PATH,
                shell=True,
                capture_output=True
            )
        
        # Start the service
        logger.info("Starting WhatsApp service...")
        _whatsapp_process = subprocess.Popen(
            ["node", "index.js"],
            cwd=WHATSAPP_SERVICE_PATH,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Wait for service to be ready
        for _ in range(30):  # Wait up to 30 seconds
            time.sleep(1)
            if is_whatsapp_service_running():
                logger.info("WhatsApp service started successfully")
                return True
        
        logger.warning("WhatsApp service started but not ready yet (may need QR scan)")
        return True
        
    except Exception as e:
        logger.error(f"Failed to start WhatsApp service: {e}")
        return False


def stop_whatsapp_service():
    """Stop the WhatsApp service"""
    global _whatsapp_process
    
    if _whatsapp_process:
        _whatsapp_process.terminate()
        _whatsapp_process = None
        logger.info("WhatsApp service stopped")


def get_pending_messages() -> List[Dict]:
    """Fetch pending messages from WhatsApp service"""
    try:
        response = requests.get(f"{WHATSAPP_SERVICE_URL}/messages", timeout=5)
        data = response.json()
        return data.get("messages", [])
    except Exception as e:
        logger.error(f"Error fetching messages: {e}")
        return []


def send_whatsapp_reply(to: str, message: str) -> bool:
    """Send a WhatsApp message via the service"""
    try:
        response = requests.post(
            f"{WHATSAPP_SERVICE_URL}/send",
            json={"to": to, "message": message},
            timeout=10
        )
        return response.status_code == 200
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        return False


# ============== Agent Tools ==============

@function_tool()
async def start_whatsapp_listener() -> str:
    """
    Start the WhatsApp message listener service.
    This will start monitoring for incoming WhatsApp messages.
    First time setup requires scanning QR code displayed in terminal.
    Returns:
        Status message
    """
    logger.info("Starting WhatsApp listener...")
    
    try:
        success = start_whatsapp_service()
        
        if success:
            # Check if needs QR scan
            try:
                response = requests.get(f"{WHATSAPP_SERVICE_URL}/health", timeout=2)
                data = response.json()
                
                if data.get("hasQR"):
                    return "WhatsApp service started! Please scan the QR code in the terminal window to connect WhatsApp."
                elif data.get("ready"):
                    return "WhatsApp listener is now active! I will notify you when new messages arrive."
                else:
                    return "WhatsApp service starting... Please check terminal for QR code."
            except:
                return "WhatsApp service started. Please check terminal for QR code to connect."
        else:
            return "Failed to start WhatsApp listener. Make sure Node.js is installed."
    except Exception as e:
        return f"Error starting WhatsApp listener: {str(e)}"


@function_tool()
async def check_whatsapp_messages() -> str:
    """
    Check for new WhatsApp messages.
    Returns list of unread messages with sender names and content.
    Returns:
        Description of new messages or 'No new messages'
    """
    global _last_notified_messages
    
    if not is_whatsapp_service_running():
        return "WhatsApp listener is not running. Say 'start WhatsApp listener' to begin."
    
    try:
        messages = get_pending_messages()
        
        if not messages:
            return "No new WhatsApp messages."
        
        # Filter out already notified messages
        new_messages = [m for m in messages if m.get("id") not in _last_notified_messages]
        
        if not new_messages:
            return "No new WhatsApp messages."
        
        # Mark as notified
        for msg in new_messages:
            _last_notified_messages.add(msg.get("id"))
        
        # Keep set size manageable
        if len(_last_notified_messages) > 100:
            _last_notified_messages = set(list(_last_notified_messages)[-50:])
        
        # Format response
        result = []
        for msg in new_messages:
            sender = msg.get("contactName", "Unknown")
            body = msg.get("body", "")[:100]  # Limit message length
            
            if msg.get("isGroup"):
                group = msg.get("groupName", "Group")
                result.append(f"{sender} in {group}: {body}")
            else:
                result.append(f"{sender}: {body}")
        
        return f"New messages - " + " | ".join(result)
        
    except Exception as e:
        logger.error(f"Error checking messages: {e}")
        return f"Error checking messages: {str(e)}"


@function_tool()
async def reply_to_whatsapp(contact_or_phone: str, message: str) -> str:
    """
    Send a WhatsApp reply to a contact or phone number.
    Args:
        contact_or_phone: Phone number with country code (e.g., 919876543210) or contact ID
        message: The reply message to send
    Returns:
        Status message
    """
    if not is_whatsapp_service_running():
        return "WhatsApp listener is not running. Say 'start WhatsApp listener' first."
    
    try:
        success = send_whatsapp_reply(contact_or_phone, message)
        
        if success:
            return f"Reply sent successfully!"
        else:
            return "Failed to send reply. Please check if WhatsApp is connected."
            
    except Exception as e:
        return f"Error sending reply: {str(e)}"


@function_tool()
async def get_whatsapp_status() -> str:
    """
    Check WhatsApp connection status.
    Returns:
        Current status of WhatsApp service
    """
    try:
        response = requests.get(f"{WHATSAPP_SERVICE_URL}/health", timeout=2)
        data = response.json()
        
        if data.get("ready"):
            return "WhatsApp is connected and listening for messages."
        elif data.get("hasQR"):
            return "WhatsApp needs QR code scan. Please check the terminal window."
        else:
            return "WhatsApp service is starting..."
            
    except requests.exceptions.ConnectionError:
        return "WhatsApp listener is not running."
    except Exception as e:
        return f"Error checking status: {str(e)}"


# Background message checker (to be used in agent loop)
async def poll_whatsapp_messages(callback):
    """
    Poll for new WhatsApp messages and call callback with each new message.
    This runs as a background task.
    """
    global _last_notified_messages
    
    while True:
        try:
            if is_whatsapp_service_running():
                messages = get_pending_messages()
                
                for msg in messages:
                    msg_id = msg.get("id")
                    if msg_id and msg_id not in _last_notified_messages:
                        _last_notified_messages.add(msg_id)
                        await callback(msg)
                        
        except Exception as e:
            logger.error(f"Polling error: {e}")
        
        await asyncio.sleep(2)  # Check every 2 seconds
