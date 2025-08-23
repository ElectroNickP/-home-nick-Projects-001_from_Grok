"""
Domain ports imports for entry points.

This module provides convenient imports for domain ports used by entry points.
"""

from core.ports.telegram import TelegramPort
from core.ports.storage import ConfigStoragePort
from core.ports.updater import AutoUpdaterPort

__all__ = [
    'TelegramPort',
    'ConfigStoragePort', 
    'AutoUpdaterPort'
]








