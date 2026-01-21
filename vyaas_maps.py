import json
from livekit.agents import function_tool
import logging

logger = logging.getLogger("vyaas-maps")

class MapManager:
    """
    Manages map-related interactions and state.
    """
    def __init__(self):
        self._current_room = None

    def set_room(self, room):
        self._current_room = room

    async def show_map_internal(self, location: str, query_type: str = "place"):
        """
        Internal method to trigger the map event.
        """
        logger.info(f"Executing show_google_map for: {location} ({query_type})")
        
        if self._current_room and self._current_room.local_participant:
            payload = {
                "type": "show_map",
                "location": location,
                "query_type": query_type
            }
            try:
                await self._current_room.local_participant.publish_data(
                    json.dumps(payload),
                    topic="map_events"
                )
                return f"Map of {location} is now being displayed on the screen."
            except Exception as e:
                logger.error(f"Failed to publish map event: {e}")
                return "I tried to show the map, but there was a connection error."
        
        return "Map system is not yet connected."

# Global instance
map_manager = MapManager()

# Top-level tool definition
@function_tool()
async def show_google_map(location: str, query_type: str = "place"):
    """
    Show a Google Map of a specific location to the user.
    
    Args:
        location: The location to show on the map (e.g., 'New York', 'Eiffel Tower', 'Mumbai').
        query_type: The type of map query. Options: 'place', 'view', 'directions'. Default is 'place'.
    """
    # Delegate to the global manager instance
    return await map_manager.show_map_internal(location, query_type)
