#!/usr/bin/env python3
"""
Telegram Bot Manager - Professional Entry Point
Simple and reliable way to start the application
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

# Colors for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_header():
    """Print application header"""
    print(f"\n{Colors.PURPLE}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}🚀 Telegram Bot Manager v3.6.0 - Professional Entry Point{Colors.END}")
    print(f"{Colors.PURPLE}{'='*60}{Colors.END}\n")

def print_success(message):
    """Print success message"""
    print(f"{Colors.GREEN}✅ {message}{Colors.END}")

def print_error(message):
    """Print error message"""
    print(f"{Colors.RED}❌ {message}{Colors.END}")

def print_warning(message):
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠️ {message}{Colors.END}")

def print_info(message):
    """Print info message"""
    print(f"{Colors.BLUE}ℹ️ {message}{Colors.END}")

def check_python_version():
    """Check if Python version is compatible"""
    print_info("Checking Python version...")
    
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print_error(f"Python 3.8+ required. Current version: {version.major}.{version.minor}")
        return False
    
    print_success(f"Python {version.major}.{version.minor}.{version.micro} ✓")
    return True

def check_virtual_env():
    """Check and activate virtual environment"""
    venv_path = Path("venv")
    
    if not venv_path.exists():
        print_warning("Virtual environment not found. Creating...")
        try:
            subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)
            print_success("Virtual environment created")
        except subprocess.CalledProcessError:
            print_error("Failed to create virtual environment")
            return False
    
    # Check if we're in virtual environment
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print_success("Already in virtual environment")
        return sys.executable
    
    # Get activation script path
    if platform.system() == "Windows":
        activate_script = venv_path / "Scripts" / "activate"
        python_exe = venv_path / "Scripts" / "python.exe"
    else:
        activate_script = venv_path / "bin" / "activate"
        python_exe = venv_path / "bin" / "python"
    
    if not activate_script.exists():
        print_error("Virtual environment activation script not found")
        return False
    
    print_success("Virtual environment ready")
    return python_exe

def install_dependencies(python_exe):
    """Install required dependencies"""
    print_info("Checking dependencies...")
    
    try:
        # Check if requirements.txt exists
        if not Path("requirements.txt").exists():
            print_error("requirements.txt not found")
            return False
        
        # Install dependencies
        subprocess.run([
            str(python_exe), "-m", "pip", "install", "-r", "requirements.txt", "--quiet"
        ], check=True)
        
        # Install in editable mode
        subprocess.run([
            str(python_exe), "-m", "pip", "install", "-e", ".", "--quiet"
        ], check=True)
        
        print_success("Dependencies installed")
        return True
        
    except subprocess.CalledProcessError as e:
        print_error(f"Failed to install dependencies: {e}")
        return False

def find_free_port(start_port=5000):
    """Find a free port starting from start_port"""
    import socket
    
    for port in range(start_port, start_port + 100):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('localhost', port))
                return port
        except OSError:
            continue
    return start_port

def start_application(python_exe, port=5000, host='127.0.0.1'):
    """Start the Flask application"""
    print_info(f"Starting application on {host}:{port}...")
    
    # Set environment variables
    env = os.environ.copy()
    env['PYTHONPATH'] = str(Path.cwd())
    env['FLASK_APP'] = 'src.app'
    env['FLASK_ENV'] = 'development'
    
    try:
        # Change to src directory and run app
        os.chdir("src")
        
        print_success("🌟 Application starting...")
        print_info(f"🌐 Web Interface: http://{host}:{port}")
        print_info("🔐 Login credentials:")
        print(f"   📧 Username: {Colors.BOLD}admin{Colors.END}")
        print(f"   🔑 Password: {Colors.BOLD}securepassword123{Colors.END}")
        print_info(f"🏪 ElectroNick bot Market: http://{host}:{port}/marketplace")
        print_warning("Press Ctrl+C to stop the server\n")
        
        # Run the application
        subprocess.run([
            str(python_exe), "app.py"
        ], env=env, check=True)
        
    except KeyboardInterrupt:
        print_info("\n👋 Application stopped by user")
        return True
    except subprocess.CalledProcessError as e:
        print_error(f"Failed to start application: {e}")
        return False
    finally:
        # Return to original directory
        os.chdir("..")

def main():
    """Main entry point"""
    print_header()
    
    try:
        # Change to script directory
        script_dir = Path(__file__).parent
        os.chdir(script_dir)
        
        # Step 1: Check Python version
        if not check_python_version():
            sys.exit(1)
        
        # Step 2: Setup virtual environment
        python_exe = check_virtual_env()
        if not python_exe:
            sys.exit(1)
        
        # Step 3: Install dependencies
        if not install_dependencies(python_exe):
            sys.exit(1)
        
        # Step 4: Find free port
        port = find_free_port()
        if port != 5000:
            print_warning(f"Port 5000 is busy, using port {port}")
        
        # Step 5: Start application
        success = start_application(python_exe, port)
        
        if success:
            print_success("Application stopped successfully")
        else:
            print_error("Application encountered errors")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print_info("\n👋 Setup interrupted by user")
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        sys.exit(1)

def print_help():
    """Print help information"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}Telegram Bot Manager - Professional Entry Point{Colors.END}")
    print(f"{Colors.GREEN}Simple and reliable way to start the application{Colors.END}\n")
    print("Usage:")
    print("  python start.py          - Start the application")
    print("  python start.py --help   - Show this help message")
    print("  python start.py -h       - Show this help message")
    print("\nFeatures:")
    print("  • Automatic virtual environment setup")
    print("  • Dependency installation and verification")
    print("  • Port detection and conflict resolution")
    print("  • Professional error handling")
    print("  • Production-ready deployment")
    print(f"\nVersion: v3.6.0{Colors.END}\n")

if __name__ == "__main__":
    # Check for help flag
    if len(sys.argv) > 1 and sys.argv[1] in ['--help', '-h', 'help']:
        print_help()
        sys.exit(0)
    
    main()
