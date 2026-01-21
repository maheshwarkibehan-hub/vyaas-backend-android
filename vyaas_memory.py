"""
VYAAS AI - Long Term Memory Module (Mem0 Integration)
Stores and retrieves user facts using Mem0 Cloud for semantic memory.
Functions: remember_fact, get_fact, search_memory, delete_fact
"""

import os
import logging
import asyncio
from typing import Dict, List, Optional
from livekit.agents import function_tool
from mem0 import AsyncMemoryClient

# Configure logging
logger = logging.getLogger("vyaas_memory")
logger.setLevel(logging.INFO)

# User ID for memory segmentation
USER_ID = "vyaas_user_main"

def get_mem0_client():
    """Initialize Mem0 Client"""
    api_key = os.getenv("MEM0_API_KEY")
    if not api_key:
        logger.error("MEM0_API_KEY not found in environment variables")
        return None
    return AsyncMemoryClient(api_key=api_key)

@function_tool()
async def remember_fact(text: str) -> str:
    """
    Store a specific fact about the user or preference using Mem0.
    Args:
        text: The information to remember (e.g., "My wifi password is admin123", "I like paneer")
    Returns:
        Status message
    """
    logger.info(f"Remembering via Mem0: {text}")
    try:
        client = get_mem0_client()
        if not client:
            return "Error: Mem0 API Key missing"
            
        # Add to memory
        result = await client.add(messages=[{"role": "user", "content": text}], user_id=USER_ID)
        logger.info(f"Mem0 add result: {result}")
        
        return f"Done! Remembered: {text}"
    except Exception as e:
        logger.error(f"Mem0 save error: {e}")
        return f"Error saving to Mem0: {str(e)}"

@function_tool()
async def get_fact(query: str) -> str:
    """
    Retrieve specific info using semantic search.
    Args:
        query: What to look for (e.g., "what is my wifi password?", "what do I like to eat?")
    Returns:
        The requested information found in memory
    """
    return await search_memory(query)

@function_tool()
async def search_memory(query: str) -> str:
    """
    Search through memory semantically using Mem0.
    Args:
        query: What to search for
    Returns:
        All matching facts
    """
    logger.info(f"Searching Mem0 for: {query}")
    try:
        client = get_mem0_client()
        if not client:
            return "Error: Mem0 API Key missing"
            
        # FIX 1: Use filters={"user_id": ...} as identified by test script to avoid 400 Bad Request
        # FIX 2: Handle dict response format {'results': [...]}
        logger.info(f"DEBUG: Calling client.search('{query}', filters={{'user_id': '{USER_ID}'}})")
        response = await client.search(query, filters={"user_id": USER_ID})
        logger.info(f"DEBUG: Mem0 search raw response: {response}")
        
        # Extract list from dict if needed
        results = response.get("results", []) if isinstance(response, dict) else response

        if not results:
            return f"I don't recall anything about '{query}'"
            
        # Format results
        memory_texts = []
        for res in results:
            if 'memory' in res:
                memory_texts.append(f"- {res['memory']}")
        
        if memory_texts:
            return "Found in memory:\n" + "\n".join(memory_texts)
        else:
            return "No relevant memory found."
            
    except Exception as e:
        logger.error(f"Mem0 search error: {e}")
        return f"Error searching Mem0: {str(e)}"

@function_tool()
async def list_all_memories() -> str:
    """
    List recent memories.
    Returns:
        List of memories
    """
    try:
        client = get_mem0_client()
        if not client:
            return "Error: Mem0 API Key missing"
            
        response = await client.get_all(user_id=USER_ID, limit=10)
        all_memories = response.get("results", []) if isinstance(response, dict) else response
        
        formatted = []
        for mem in all_memories:
            if 'memory' in mem:
                formatted.append(f"- {mem['memory']}")
                
        if formatted:
            return "Recent memories:\n" + "\n".join(formatted)
        return "Memory is empty."
    except Exception as e:
        return f"Error listing memories: {str(e)}"

@function_tool()
async def delete_fact(memory_id: str) -> str:
    """
    Delete a specific memory by ID (Advanced use only).
    For now, simply clears all memory if 'all' is passed.
    """
    # Mem0 deletion usually requires memory_id. 
    # Providing a simple clear_all for now if helpful, or we can implement search-then-delete logic later.
    if memory_id.lower() == "all":
        try:
            client = get_mem0_client()
            if client:
                await client.delete_all(user_id=USER_ID)
                return "All memories cleared."
        except Exception as e:
            return f"Error clearing: {e}"
            
    return "To delete, please ask me to 'forget everything' (clears all) as deleting specific ID is complex via voice."
