# Vyaas AI Backend Documentation

This document explains the architecture and features of the **Vyaas AI Backend** (`Jarvis_code`).

## 📂 Project Structure

- **`agent.py`**: The main entry point. It initializes the LiveKit Agent, connects to the room, and manages the session.
- **`vyaas_prompts.py`**: Contains the logic for generating the AI's persona and instructions. It dynamically fetches time and weather to keep the context fresh.
- **`vyaas_google_search.py`**: A tool that allows Vyaas to search Google for real-time information.
- **`vyaas_get_weather.py`**: A tool that fetches current weather data for any city (defaults to Kaushambi/User location).
- **`vyaas_image_gen.py`**: A tool that generates images using the Hugging Face Flux model and uploads them to ImgBB for display.
- **`memory_loop.py`** & **`memory_store.py`**: Handles long-term memory by saving conversation history to a JSON file.

---

## 🚀 Features Explained

### 1. 🗣️ Advanced Voice Interaction
- **Engine**: Google Realtime API (Gemini).
- **Voice**: "Charon" (Deep, calm voice).
- **Language**: **Hinglish** (Hindi + English). The system instructions are tuned to make Vyaas speak naturally like an Indian user.

### 2. 🔍 Google Search
- **Function**: `google_search(query)`
- **How it works**: When you ask a question that requires current knowledge (e.g., "Who won the match yesterday?"), Vyaas uses the Google Custom Search API to find the answer.
- **Output**: Summarizes the top 3 results.

### 3. 🌦️ Weather Updates
- **Function**: `get_weather(city)`
- **How it works**: Fetches real-time weather (Temperature, Humidity, Wind) from OpenWeatherMap.
- **Smart Default**: If you don't specify a city, it defaults to **Kaushambi** (or tries to detect via IP).

### 4. 🎨 Image Generation
- **Function**: `generate_image_tool(prompt)`
- **How it works**:
    1.  Sends your prompt to **Hugging Face (Flux.1-dev model)**.
    2.  Receives the generated image.
    3.  Uploads it to **ImgBB** to get a public URL.
    4.  Returns the URL to the chat.
- **Usage**: "Show me a picture of a futuristic city."

### 5. 🧠 Long-Term Memory
- **System**: `MemoryExtractor`
- **How it works**: A background loop watches the conversation. When new messages appear, it saves them to a local JSON file (`conversations/Maheshwar_22.json`).
- **Future Potential**: This data can be used to "remember" past conversations (requires implementing a retrieval mechanism).

---

## 🛠️ How to Add New Features

To add a new tool (e.g., News, Stocks):

1.  **Create a new file** (e.g., `vyaas_news.py`).
2.  **Write a function** decorated with `@function_tool()`.
3.  **Import it in `agent.py`**.
4.  **Add it to the `tools` list** in the `Assistant` class.

```python
# Example: vyaas_news.py
from livekit.agents import function_tool

@function_tool()
async def get_news(topic: str) -> str:
    # Logic to fetch news
    return "Here is the news..."
```

## ⚠️ Important Notes
- **Environment Variables**: Ensure `.env` has all keys (`LIVEKIT_*`, `GOOGLE_API_KEY`, `OPENWEATHER_API_KEY`, `HF_TOKEN`, `IMGBB_KEY`).
- **Free Tier Deployment**: The `agent.py` includes a "dummy server" to allow deployment on Render's Free Tier.
