"""
Web routes for Flask application.

This module contains all the route handlers for the web interface.
"""

from .bot_routes import bot_bp
from .conversation_routes import conversation_bp
from .system_routes import system_bp

__all__ = ["bot_bp", "conversation_bp", "system_bp"]









