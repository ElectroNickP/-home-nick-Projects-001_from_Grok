@echo off
REM Telegram Bot Manager - Windows Quick Start Script

echo 🚀 Starting Telegram Bot Manager...
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed. Please install Python 3.8+ first.
    echo Download from: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Run the application
python start.py

pause

