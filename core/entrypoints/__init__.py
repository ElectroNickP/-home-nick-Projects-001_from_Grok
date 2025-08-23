"""
Entry points for hexagonal architecture.

This module contains the entry points that connect external interfaces
(web, CLI, API) with the application use cases.
"""

from .api import APIApp
from .cli import CLIApp
from .web import FlaskApp

__all__ = [
    "FlaskApp",
    "CLIApp",
    "APIApp",
]










