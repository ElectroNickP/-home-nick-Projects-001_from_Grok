#!/bin/bash
# Telegram Bot Manager Service Manager
# Convenient service management commands

SERVICE_NAME="telegram-bot-manager"

case "$1" in
    start)
        echo "🚀 Starting Telegram Bot Manager service..."
        sudo systemctl start $SERVICE_NAME
        sudo systemctl status $SERVICE_NAME --no-pager -l
        ;;
    stop)
        echo "⏹️ Stopping Telegram Bot Manager service..."
        sudo systemctl stop $SERVICE_NAME
        echo "✅ Service stopped"
        ;;
    restart)
        echo "🔄 Restarting Telegram Bot Manager service..."
        sudo systemctl restart $SERVICE_NAME
        sudo systemctl status $SERVICE_NAME --no-pager -l
        ;;
    status)
        echo "📊 Telegram Bot Manager service status:"
        sudo systemctl status $SERVICE_NAME --no-pager -l
        ;;
    logs)
        echo "📋 Live logs (Ctrl+C to exit):"
        sudo journalctl -u $SERVICE_NAME -f
        ;;
    enable)
        echo "✅ Enabling auto-start on boot..."
        sudo systemctl enable $SERVICE_NAME
        echo "Service will start automatically on system boot"
        ;;
    disable)
        echo "❌ Disabling auto-start on boot..."
        sudo systemctl disable $SERVICE_NAME
        echo "Service will not start automatically on system boot"
        ;;
    install)
        echo "🔧 Installing service..."
        ./service-install.sh
        ;;
    uninstall)
        echo "🗑️ Uninstalling service..."
        sudo systemctl stop $SERVICE_NAME 2>/dev/null || true
        sudo systemctl disable $SERVICE_NAME 2>/dev/null || true
        sudo rm -f /etc/systemd/system/$SERVICE_NAME.service
        sudo systemctl daemon-reload
        echo "✅ Service uninstalled"
        ;;
    *)
        echo "🤖 Telegram Bot Manager Service Manager"
        echo ""
        echo "Usage: $0 {command}"
        echo ""
        echo "Commands:"
        echo "  start      - Start the service"
        echo "  stop       - Stop the service"
        echo "  restart    - Restart the service"
        echo "  status     - Show service status"
        echo "  logs       - Show live logs"
        echo "  enable     - Enable auto-start on boot"
        echo "  disable    - Disable auto-start on boot"
        echo "  install    - Install service"
        echo "  uninstall  - Remove service"
        echo ""
        echo "Examples:"
        echo "  $0 start     # Start service in background"
        echo "  $0 logs      # Monitor logs in real-time"
        echo "  $0 status    # Check if service is running"
        exit 1
esac
