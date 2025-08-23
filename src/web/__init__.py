"""
Web interface module for Telegram Bot Manager

This module provides web interface functionality including:
- Main dashboard
- Bot dialogs viewer
- Marketplace pages
- Static file serving

Usage:
    from web import web_bp
    app.register_blueprint(web_bp)
"""

from .routes import web_bp

__all__ = ['web_bp']





