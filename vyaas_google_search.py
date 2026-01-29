
import logging
from datetime import datetime
try:
    from googlesearch import search
except ImportError:
    search = None
    print("Warning: googlesearch-python not installed. Web search will fail.")

logger = logging.getLogger("vyaas_google_search")

def get_current_datetime():
    """Returns the current date and time string."""
    now = datetime.now()
    return now.strftime("%A, %B %d, %Y %I:%M %p")

async def google_search(query: str):
    """
    Performs a Google search for the given query.
    Returns:
        str: A summary of the search results or an error message.
    """
    if not query:
        return "Please provide a search query."

    logger.info(f"Searching Google for: {query}")
    
    if not search:
        return "Error: Search functionality unavailable (googlesearch-python missing)."

    try:
        # Perform the search
        results = []
        for j in search(query, num_results=5, advanced=True):
            results.append(f"Title: {j.title}\nDescription: {j.description}\nURL: {j.url}")
        
        if not results:
            return f"No results found for '{query}'."
            
        return "\n\n".join(results)

    except Exception as e:
        logger.error(f"Search failed: {e}")
        return f"Failed to perform search: {str(e)}"
