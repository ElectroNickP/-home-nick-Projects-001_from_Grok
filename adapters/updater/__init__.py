"""
Auto-update adapters for hexagonal architecture.

This module contains implementations of AutoUpdaterPort interface
that handle system auto-updates and backups.
"""

from .git_adapter import GitAutoUpdaterAdapter

__all__ = [
    "GitAutoUpdaterAdapter",
]









