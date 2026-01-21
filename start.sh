#!/bin/bash

# Start the API server (FastAPI)
# Render provides the PORT environment variable
uvicorn server:app --host 0.0.0.0 --port $PORT
