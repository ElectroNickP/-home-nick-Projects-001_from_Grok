#!/bin/bash
echo "🔄 Test restart script starting..."
cd /home/nick/Projects/Phuket/-home-nick-Projects-001_from_Grok/src
echo "📍 Working directory: $(pwd)"
echo "🛑 Stopping processes..."
pkill -9 -f "python.*app.py" 2>/dev/null || true
sleep 2
echo "🐍 Activating venv..."
source ../venv/bin/activate || echo "Venv activation failed"
echo "🚀 Starting app..."
nohup python app.py > test_restart.log 2>&1 &
echo "📋 Started with PID: $!"
sleep 3
echo "✅ Test restart completed"
