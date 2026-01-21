#!/bin/bash

# VYAAS AI - Termux Setup Script
# Run this on your Android phone using Termux app.

echo "🚀 VYAAS AI Termux Setup"
echo "========================"
echo "Updating packages..."

# Update package lists
pkg update -y && pkg upgrade -y

# Install essential dependencies
echo "📦 Installing system dependencies..."
pkg install -y python git clang make rust termux-api android-tools tur-repo

# Install some python build dependencies
pkg install -y libjpeg-turbo libpng freetype openjpeg

# Setup virtual environment
echo "🐍 Setting up Python environment..."
python3 -m venv venv
source venv/bin/activate

# Install Python requirements
echo "📥 Installing Python libraries..."
pip install --upgrade pip
pip install setuptools wheel

# Install dependencies one by one to handle build issues
pip install python-dotenv requests
pip install "livekit-agents>=0.8.0"
pip install "livekit-plugins-google>=0.4.0"
pip install psutil
pip install Pillow
pip install screeninfo

# Note: pyautogui and pyperclip might fail or need X11 on Termux. 
# We'll try to install them, but our code handles if they are missing.
pip install pyautogui pyperclip || echo "⚠️ PyAutoGUI/Pyperclip install failed (expected on headless Termux), continuing..."

echo "✅ Setup Complete!"
echo "-------------------"
echo "To start VYAAS AI:"
echo "1. Activate venv: source venv/bin/activate"
echo "2. Run agent: python agent.py"
echo "-------------------"
echo "If you want to control THIS phone, ensure:"
echo "1. You have Termux:API app installed from Play Store/F-Droid"
echo "2. You have enabled 'ADB Wireless' locally if you want advanced control:"
echo "   - Enable Developer Options > Wireless Debugging"
echo "   - Run: adb connect localhost:5555 (after pairing if needed)"
