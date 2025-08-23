"""
Version information for Telegram Bot Manager.

This module provides centralized version management by reading from pyproject.toml.
All components should import version from this module to ensure consistency.
"""

import sys
from pathlib import Path

def get_version():
    """
    Get version from pyproject.toml.
    
    Returns:
        str: Version string (e.g., "3.7.6")
    """
    try:
        # Try to get version from package metadata first (when installed)
        try:
            import importlib.metadata
            return importlib.metadata.version("telegram_bot_manager")
        except (ImportError, importlib.metadata.PackageNotFoundError):
            pass
        
        # Fall back to reading pyproject.toml directly
        project_root = Path(__file__).parent.parent
        pyproject_path = project_root / "pyproject.toml"
        
        if pyproject_path.exists():
            if sys.version_info >= (3, 11):
                import tomllib
                with open(pyproject_path, "rb") as f:
                    data = tomllib.load(f)
                    return data.get("project", {}).get("version", "unknown")
            else:
                # For Python < 3.11, parse manually (simple approach)
                with open(pyproject_path, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.strip().startswith('version = "'):
                            return line.split('"')[1]
        
        # Ultimate fallback
        return "3.7.6"
        
    except Exception:
        # If anything fails, return fallback version
        return "3.7.6"

def get_version_info():
    """
    Get detailed version information.
    
    Returns:
        dict: Version info with version, name, and description
    """
    return {
        "version": get_version(),
        "name": "Telegram Bot Manager",
        "description": "Complete Symlink Fix"
    }

def get_full_version():
    """
    Get full version string for display.
    
    Returns:
        str: Full version string (e.g., "v3.7.6 - Complete Symlink Fix")
    """
    info = get_version_info()
    return f"v{info['version']} - {info['description']}"

# Export version for direct import
__version__ = get_version()
VERSION = get_version()
FULL_VERSION = get_full_version()
