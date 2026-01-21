
import asyncio
import logging
import warnings
# Suppress kasa deprecation warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

from typing import Dict, List, Optional
from kasa import Discover, SmartDevice, SmartBulb, SmartPlug, SmartStrip
from livekit.agents.llm import function_tool

logger = logging.getLogger("vyaas_iot")

# Cache discovered devices to avoid re-scanning every time
# Map: alias -> SmartDevice
CACHED_DEVICES: Dict[str, SmartDevice] = {}

# Mock devices for demonstration if no real devices found
MOCK_DEVICES = {
    "bedroom light": {"state": "off", "brightness": 100, "type": "bulb"},
    "kitchen plug": {"state": "on", "type": "plug"},
    "fan": {"state": "off", "type": "plug"}
}
USE_MOCK = False

async def _get_device(alias: str) -> Optional[SmartDevice]:
    """Helper to find a device by alias (case-insensitive)"""
    global CACHED_DEVICES
    
    # Refresh if empty
    if not CACHED_DEVICES and not USE_MOCK:
        await scan_iot_devices()
        
    target = alias.lower()
    for name, dev in CACHED_DEVICES.items():
        if name.lower() == target or target in name.lower():
            return dev
    return None

@function_tool()
async def scan_iot_devices() -> str:
    """
    Scan local network for Smart Home devices (Kasa/TP-Link).
    Returns a list of found devices and their status.
    """
    global CACHED_DEVICES, USE_MOCK
    
    logger.info("Scanning for Kasa devices...")
    try:
        found = await Discover.discover(timeout=3)
        
        if not found:
            logger.warning("No Kasa devices found. Enabled MOCK mode.")
            USE_MOCK = True
            return f"No physical devices found. Switched to MOCK mode.\nMock Devices:\n" + \
                   "\n".join([f"- {k} ({v['type']}): {v['state']}" for k, v in MOCK_DEVICES.items()])
        
        CACHED_DEVICES = {}
        output = []
        
        for dev in found.values():
            await dev.update()
            alias = dev.alias
            CACHED_DEVICES[alias] = dev
            state = "ON" if dev.is_on else "OFF"
            info = f"- {alias} ({dev.model}): {state}"
            output.append(info)
            
        USE_MOCK = False
        return "Found devices:\n" + "\n".join(output)
        
    except Exception as e:
        logger.error(f"Error scanning devices: {e}")
        # Fallback to mock
        USE_MOCK = True
        return f"Error scanning network ({e}). Using MOCK mode.\nMock Devices available."

@function_tool()
async def control_iot_device(device_name: str, action: str) -> str:
    """
    Turn a smart home device on or off.
    Args:
        device_name: Name/Alias of the device (e.g., "Bedroom Light")
        action: "on" or "off"
    """
    cleaned_action = action.lower().strip()
    if cleaned_action not in ["on", "off"]:
        return "Please specify 'on' or 'off'."
        
    logger.info(f"Controlling {device_name} -> {cleaned_action}")
    
    if USE_MOCK:
        # Mock Logic
        target = device_name.lower()
        matched = None
        for k in MOCK_DEVICES:
            if target in k:
                matched = k
                break
        
        if matched:
            MOCK_DEVICES[matched]["state"] = cleaned_action
            return f"MOCK: Turned {cleaned_action.upper()} {matched}."
        return f"MOCK: Device '{device_name}' not found. Available: {', '.join(MOCK_DEVICES.keys())}"

    # Real Logic
    device = await _get_device(device_name)
    if not device:
        # Try rescan once
        await scan_iot_devices()
        device = await _get_device(device_name)
        
    if not device:
        return f"Device '{device_name}' not found on network."
        
    try:
        if cleaned_action == "on":
            await device.turn_on()
        else:
            await device.turn_off()
        return f"Turned {cleaned_action.upper()} {device.alias}."
    except Exception as e:
        return f"Failed to control {device_name}: {e}"

@function_tool()
async def set_iot_brightness(device_name: str, brightness: int) -> str:
    """
    Set brightness of a smart bulb.
    Args:
        device_name: Name of the bulb
        brightness: Level from 0 to 100
    """
    if not (0 <= brightness <= 100):
        return "Brightness must be between 0 and 100."
        
    if USE_MOCK:
        target = device_name.lower()
        matched = None
        for k, v in MOCK_DEVICES.items():
            if target in k and v['type'] == 'bulb':
                matched = k
                break
        
        if matched:
            MOCK_DEVICES[matched]["brightness"] = brightness
            return f"MOCK: Set {matched} brightness to {brightness}%."
        return f"MOCK: Bulb '{device_name}' not found."

    device = await _get_device(device_name)
    if not device:
        return f"Device '{device_name}' not found."
        
    if not device.is_dimmable:
        return f"{device.alias} does not support brightness control."
        
    try:
        # Ensure it's on first? usually yes
        if not device.is_on:
            await device.turn_on()
            
        await device.set_brightness(brightness)
        return f"Set {device.alias} brightness to {brightness}%."
    except Exception as e:
        return f"Failed to set brightness: {e}"
