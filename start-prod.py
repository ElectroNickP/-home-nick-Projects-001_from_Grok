#!/usr/bin/env python3
"""
Telegram Bot Manager - Production Entry Point
Optimized for fast deployment on Ubuntu servers
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

def check_python():
    """Check Python version"""
    version = sys.version_info
    if version.major != 3 or version.minor < 11:
        print("❌ Python 3.11+ required")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro}")
    return True

def setup_production():
    """Setup production environment"""
    print("🚀 Setting up production environment...")
    
    # Install system dependencies if needed
    try:
        # Install production requirements only
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements-prod.txt", "--user", "--quiet"], check=True)
        print("✅ Dependencies installed")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False
    
    return True

def start_server(port=5000):
    """Start the server"""
    print(f"🌟 Starting server on port {port}...")
    
    # Change to src directory
    src_path = Path("src")
    if not src_path.exists():
        print("❌ src directory not found")
        return False
    
    os.chdir(src_path)
    
    print(f"🌐 Web Interface: http://localhost:{port}")
    print("🔐 Login: admin / securepassword123")
    print(f"🏪 Marketplace: http://localhost:{port}/marketplace")
    
    # Start Flask application
    try:
        subprocess.run([sys.executable, "app.py"], 
                       env=dict(os.environ, FLASK_ENV="production"))
    except KeyboardInterrupt:
        print("\n👋 Server stopped")

def main():
    """Main entry point"""
    print("🚀 Telegram Bot Manager - Production Mode")
    
    if not check_python():
        sys.exit(1)
    
    if not setup_production():
        sys.exit(1)
    
    start_server()

if __name__ == "__main__":
    main()
