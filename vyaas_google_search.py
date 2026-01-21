import os
import requests
import logging
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone
from livekit.agents import function_tool
from livekit import agents

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@function_tool()
async def google_search(query: str) -> str:
    """
    Searches Google and returns the top 3 results with heading and summary only.
    """

    logger.info(f"Query प्राप्त हुई: {query}")

    api_key = os.getenv("GOOGLE_SEARCH_API_KEY")
    search_engine_id = os.getenv("SEARCH_ENGINE_ID")

    if not api_key or not search_engine_id:
        missing = []
        if not api_key:
            missing.append("GOOGLE_SEARCH_API_KEY")
        if not search_engine_id:
            missing.append("SEARCH_ENGINE_ID")
        return f"Missing environment variables: {', '.join(missing)}"

    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": api_key,
        "cx": search_engine_id,
        "q": query,
        "num": 3
    }

    try:
        logger.info("Google Custom Search API को request भेजी जा रही है...")
        response = requests.get(url, params=params, timeout=10)
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed: {e}")
        return f"Google Search API request failed: {e}"

    if response.status_code != 200:
        logger.error(f"Google API error: {response.status_code} - {response.text}")
        return f"Google Search API में error आया: {response.status_code} - {response.text}"

    data = response.json()
    results = data.get("items", [])

    if not results:
        logger.info("कोई results नहीं मिले।")
        return "कोई results नहीं मिले।"

    formatted = "Here are the top results:\n"
    for i, item in enumerate(results, start=1):
        title = item.get("title", "No title")
        snippet = item.get("snippet", "").strip()
        formatted += f"{i}. {title}. {snippet}\n\n"

    return formatted.strip()


# ✅ IST timezone (GMT+5:30)
IST = timezone(timedelta(hours=5, minutes=30))

@function_tool()
async def get_current_datetime() -> str:
    """
    Returns the current date and time in Indian Standard Time (GMT+5:30)
    """
    now = datetime.now(IST)
    formatted = now.strftime("%d %B %Y, %I:%M %p (IST)")
    return formatted
