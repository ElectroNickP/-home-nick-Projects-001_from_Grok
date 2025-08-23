"""
Application layer for hexagonal architecture.

This module contains entry points and application-specific code
that orchestrates use cases and provides interfaces to external systems.
"""

from .web_app import WebApplication
from .cli_app import CLIApplication

__all__ = [
    "WebApplication",
    "CLIApplication",
]










