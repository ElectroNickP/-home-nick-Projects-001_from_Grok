#!/usr/bin/env python3
"""
Quick start script to launch app and test auto-update
Avoids hanging terminal commands
"""
import subprocess
import time
import os
import signal
import sys

def kill_existing():
    """Kill existing python app.py processes"""
    try:
        subprocess.run(["pkill", "-f", "python.*app.py"], timeout=5)
        time.sleep(2)
        print("✅ Killed existing processes")
    except:
        print("⚠️ No existing processes to kill")

def start_app():
    """Start the application"""
    try:
        # Start app in background
        process = subprocess.Popen([
            sys.executable, "app.py"
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        print(f"🚀 Started app with PID: {process.pid}")
        
        # Wait a moment for startup
        time.sleep(5)
        
        # Test if it's responding
        try:
            import requests
            response = requests.get("http://localhost:60183/", timeout=3)
            print(f"📊 HTTP Status: {response.status_code}")
            return True
        except:
            print("❌ App not responding")
            return False
            
    except Exception as e:
        print(f"❌ Failed to start app: {e}")
        return False

def create_test_commit():
    """Create a test commit for auto-update"""
    try:
        with open("README.md", "a") as f:
            f.write(f"\n# Auto-update test at {time.strftime('%H:%M:%S')}\n")
        
        subprocess.run(["git", "add", "README.md"], timeout=10, cwd="..")
        subprocess.run(["git", "commit", "-m", "test: auto-update trigger"], timeout=10, cwd="..")
        print("✅ Test commit created")
        return True
    except Exception as e:
        print(f"❌ Failed to create test commit: {e}")
        return False

def test_auto_update():
    """Test auto-update via API"""
    try:
        import requests
        from requests.auth import HTTPBasicAuth
        
        # Trigger auto-update
        response = requests.post(
            "http://localhost:60183/api/update",
            auth=HTTPBasicAuth('admin', 'securepassword123'),
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ Auto-update triggered successfully")
            return True
        else:
            print(f"❌ Auto-update failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Auto-update test failed: {e}")
        return False

if __name__ == "__main__":
    print("🔧 QUICK TEST OF FIXED AUTO-UPDATE")
    print("=" * 50)
    
    # Step 1: Clean start
    kill_existing()
    
    # Step 2: Start app
    if not start_app():
        print("❌ App failed to start")
        sys.exit(1)
    
    # Step 3: Create test commit
    if not create_test_commit():
        print("❌ Failed to create test commit")
        sys.exit(1)
    
    # Step 4: Test auto-update
    if test_auto_update():
        print("🎉 AUTO-UPDATE TEST SUCCESSFUL!")
    else:
        print("❌ AUTO-UPDATE TEST FAILED!")

