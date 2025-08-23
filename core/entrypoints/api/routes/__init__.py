"""
API routes for FastAPI application.

This module contains all the route handlers for the REST API interface.
"""

from .bot_api import bot_router
from .conversation_api import conversation_router
from .system_api import system_router

__all__ = ["bot_router", "conversation_router", "system_router"]


