"""
Authentication module for Telegram Bot Manager

This module provides authentication functionality including:
- User login/logout
- Session management
- API authentication

Usage:
    from api.auth import auth_bp
    app.register_blueprint(auth_bp)
"""

from .routes import auth_bp

__all__ = ['auth_bp']



