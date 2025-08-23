"""
Core ports (interfaces) for hexagonal architecture.

This module defines the interface contracts that external adapters must implement.
The core business logic depends on these abstractions, not concrete implementations.
"""

from .storage import ConfigStoragePort
from .telegram import TelegramPort
from .updater import AutoUpdaterPort

__all__ = [
    "TelegramPort",
    "ConfigStoragePort",
    "AutoUpdaterPort",
]

