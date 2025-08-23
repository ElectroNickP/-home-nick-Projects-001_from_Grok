#!/usr/bin/env python3
"""
Production Deployment Test Script
Tests if the project is ready for production deployment
"""

import os
import sys
import subprocess
import json
from pathlib import Path

def run_command(cmd, check=True):
    """Run shell command and return result"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=check)
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.CalledProcessError as e:
        return False, e.stdout, e.stderr

def check_python_version():
    """Check Python version compatibility"""
    print("🐍 Checking Python version...")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro} - OK")
        return True
    else:
        print(f"❌ Python {version.major}.{version.minor}.{version.micro} - Need Python 3.8+")
        return False

def check_required_files():
    """Check if all required files exist"""
    print("\n📁 Checking required files...")
    required_files = [
        'start.py',
        'requirements-prod.txt', 
        'requirements.txt',
        'src/app.py',
        'src/config_manager.py',
        'src/bot_manager.py',
        'QUICK_START.md'
    ]
    
    all_exist = True
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} - Missing!")
            all_exist = False
    
    return all_exist

def check_directory_structure():
    """Check if directory structure is correct"""  
    print("\n🏗️ Checking directory structure...")
    required_dirs = [
        'src',
        'src/api',
        'src/templates', 
        'src/static',
        'src/static/uploads',
        'tests'
    ]
    
    all_exist = True
    for dir_path in required_dirs:
        if Path(dir_path).exists():
            print(f"✅ {dir_path}/")
        else:
            print(f"❌ {dir_path}/ - Missing!")
            all_exist = False
    
    return all_exist

def check_imports():
    """Check if critical imports work"""
    print("\n📦 Checking critical imports...")
    imports = [
        ('flask', 'Flask'),
        ('aiogram', 'Bot'),
        ('openai', 'OpenAI'),
        ('PIL', 'Image'),
        ('psutil', None),
        ('yaml', None)
    ]
    
    all_imports_ok = True
    for module, attr in imports:
        try:
            if attr:
                exec(f"from {module} import {attr}")
            else:
                exec(f"import {module}")
            print(f"✅ {module}")
        except ImportError as e:
            print(f"❌ {module} - {e}")
            all_imports_ok = False
    
    return all_imports_ok

def check_config_template():
    """Check if bot_configs.json template exists or can be created"""
    print("\n⚙️ Checking configuration...")
    
    config_file = Path("src/bot_configs.json")
    if config_file.exists():
        print("⚠️ bot_configs.json exists (should be gitignored)")
        try:
            with open(config_file) as f:
                config = json.load(f)
                if "bots" in config:
                    print("✅ Valid config structure")
                    return True
        except json.JSONDecodeError:
            print("❌ Invalid JSON in bot_configs.json")
            return False
    
    # Create template config
    template_config = {"bots": {}}
    try:
        with open(config_file, 'w') as f:
            json.dump(template_config, f, indent=2)
        print("✅ Created template bot_configs.json")
        return True
    except Exception as e:
        print(f"❌ Could not create config template: {e}")
        return False

def check_start_script():
    """Test if start.py works"""
    print("\n🚀 Testing start script...")
    
    if not Path("start.py").exists():
        print("❌ start.py not found")
        return False
    
    # Test start.py --help
    success, stdout, stderr = run_command("python start.py --help", check=False)
    if success and "Telegram Bot Manager" in stdout:
        print("✅ start.py executable and responsive")
        return True
    else:
        print(f"❌ start.py test failed: {stderr}")
        return False

def check_git_status():
    """Check git repository status"""
    print("\n🔄 Checking git status...")
    
    success, stdout, stderr = run_command("git status --porcelain", check=False)
    if not success:
        print("❌ Not a git repository")
        return False
        
    if stdout.strip():
        print("⚠️ Uncommitted changes found:")
        print(stdout)
        return False
    else:
        print("✅ Working directory clean") 
        return True

def main():
    """Main test function"""
    print("🔍 PRODUCTION DEPLOYMENT READINESS CHECK")
    print("=" * 50)
    
    tests = [
        ("Python Version", check_python_version),
        ("Required Files", check_required_files), 
        ("Directory Structure", check_directory_structure),
        ("Critical Imports", check_imports),
        ("Configuration", check_config_template),
        ("Start Script", check_start_script),
        ("Git Status", check_git_status)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test failed with exception: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS:")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status:<10} {test_name}")
        if result:
            passed += 1
    
    print(f"\n📈 Score: {passed}/{total} ({(passed/total*100):.1f}%)")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! Ready for production deployment.")
        return True
    else:
        print(f"⚠️ {total-passed} tests failed. Fix issues before deployment.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
