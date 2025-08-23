#!/bin/bash
# Telegram Bot Manager - Linux/macOS Quick Start Script

echo "🚀 Starting Telegram Bot Manager..."
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 is not installed. Please install Python 3.8+ first."
    exit 1
fi

# Make start.py executable
chmod +x start.py

# Run the application
python3 start.py
