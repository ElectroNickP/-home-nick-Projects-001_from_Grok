#!/bin/bash
# Telegram Bot Manager Service Installation Script
# This script installs the systemd service for background operation

set -e

echo "🔧 Installing Telegram Bot Manager as systemd service..."

# Get current directory
CURRENT_DIR="$(pwd)"
SERVICE_FILE="telegram-bot-manager.service"

# Check if service file exists
if [[ ! -f "$SERVICE_FILE" ]]; then
    echo "❌ Error: $SERVICE_FILE not found in current directory"
    echo "Please run this script from the project root directory"
    exit 1
fi

# Update service file with current directory path
echo "📝 Updating service paths..."
sed -i "s|/root/Telegram-Bot-Manager|$CURRENT_DIR|g" "$SERVICE_FILE"

# Update user in service file (use current user instead of root)
CURRENT_USER=$(whoami)
sed -i "s|User=root|User=$CURRENT_USER|g" "$SERVICE_FILE"
sed -i "s|Group=root|Group=$CURRENT_USER|g" "$SERVICE_FILE"

# Copy service file to systemd directory
echo "📋 Installing service file..."
sudo cp "$SERVICE_FILE" /etc/systemd/system/

# Reload systemd daemon
echo "🔄 Reloading systemd daemon..."
sudo systemctl daemon-reload

# Enable service (auto-start on boot)
echo "✅ Enabling auto-start on boot..."
sudo systemctl enable telegram-bot-manager.service

echo ""
echo "✅ Service installed successfully!"
echo ""
echo "📋 Available commands:"
echo "  sudo systemctl start telegram-bot-manager    - Start service"
echo "  sudo systemctl stop telegram-bot-manager     - Stop service" 
echo "  sudo systemctl restart telegram-bot-manager  - Restart service"
echo "  sudo systemctl status telegram-bot-manager   - Check status"
echo "  sudo systemctl disable telegram-bot-manager  - Disable auto-start"
echo "  sudo journalctl -u telegram-bot-manager -f   - View live logs"
echo ""
echo "🚀 To start the service now, run:"
echo "  sudo systemctl start telegram-bot-manager"
