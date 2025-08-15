#!/usr/bin/env python3
"""
Version management module - automatically determines version from git
"""
import subprocess
import os
import datetime
from typing import Dict, Optional

# Fallback version if git is not available
FALLBACK_VERSION = "2.3.0"

def run_git_command(command: str) -> Optional[str]:
    """Execute git command and return output"""
    try:
        result = subprocess.run(
            ["git"] + command.split(),
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.dirname(__file__)),
            timeout=5
        )
        if result.returncode == 0:
            return result.stdout.strip()
        return None
    except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError):
        return None

def get_git_version() -> Optional[str]:
    """Get version from git describe"""
    # Try to get version from git tag
    version = run_git_command("describe --tags --always --dirty")
    if version:
        return version
    
    # Fallback: get short commit hash
    commit = run_git_command("rev-parse --short HEAD")
    if commit:
        return f"dev-{commit}"
    
    return None

def get_git_commit_info() -> Dict[str, str]:
    """Get detailed git commit information"""
    info = {}
    
    # Get full commit hash
    commit_hash = run_git_command("rev-parse HEAD")
    info["commit_hash"] = commit_hash[:12] if commit_hash else "unknown"
    
    # Get commit date
    commit_date = run_git_command("log -1 --format=%ci")
    if commit_date:
        try:
            # Parse git date format and convert to readable format
            dt = datetime.datetime.strptime(commit_date[:19], "%Y-%m-%d %H:%M:%S")
            info["commit_date"] = dt.strftime("%Y-%m-%d %H:%M")
        except ValueError:
            info["commit_date"] = commit_date
    else:
        info["commit_date"] = "unknown"
    
    # Get branch name
    branch = run_git_command("rev-parse --abbrev-ref HEAD")
    info["branch"] = branch if branch else "unknown"
    
    # Get commit message
    commit_msg = run_git_command("log -1 --format=%s")
    info["commit_message"] = commit_msg if commit_msg else "unknown"
    
    return info

def get_build_info() -> Dict[str, str]:
    """Get build and runtime information"""
    info = {}
    
    # Build timestamp (when this is called)
    info["build_time"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Python version
    import sys
    info["python_version"] = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    
    return info

class VersionInfo:
    """Version information container"""
    
    def __init__(self):
        self.version = get_git_version() or FALLBACK_VERSION
        self.git_info = get_git_commit_info()
        self.build_info = get_build_info()
        
        # Determine if this is a development version
        self.is_dev = (
            "dirty" in self.version or
            "dev-" in self.version or
            self.git_info.get("branch") not in ["main", "master"]
        )
    
    @property
    def version_string(self) -> str:
        """Get clean version string"""
        return self.version
    
    @property
    def full_version_string(self) -> str:
        """Get full version with commit info"""
        base = self.version
        commit = self.git_info.get("commit_hash", "")
        
        if commit and commit != "unknown":
            if commit not in base:
                base += f" ({commit})"
        
        if self.is_dev:
            base += " [DEV]"
            
        return base
    
    @property
    def version_details(self) -> Dict[str, str]:
        """Get detailed version information"""
        return {
            "version": self.version,
            "commit_hash": self.git_info.get("commit_hash", "unknown"),
            "commit_date": self.git_info.get("commit_date", "unknown"),
            "branch": self.git_info.get("branch", "unknown"),
            "commit_message": self.git_info.get("commit_message", "unknown"),
            "build_time": self.build_info.get("build_time", "unknown"),
            "python_version": self.build_info.get("python_version", "unknown"),
            "is_dev": self.is_dev
        }
    
    def __str__(self) -> str:
        return self.full_version_string

# Global version instance
__version_info = None

def get_version_info() -> VersionInfo:
    """Get cached version info instance"""
    global __version_info
    if __version_info is None:
        __version_info = VersionInfo()
    return __version_info

def get_version() -> str:
    """Get version string"""
    return get_version_info().version_string

def get_full_version() -> str:
    """Get full version string with details"""
    return get_version_info().full_version_string

# For backward compatibility
__version__ = get_version()

if __name__ == "__main__":
    # Test version detection
    info = get_version_info()
    print(f"Version: {info.version_string}")
    print(f"Full Version: {info.full_version_string}")
    print("\nDetails:")
    for key, value in info.version_details.items():
        print(f"  {key}: {value}")
