"""
API v1 module for Telegram Bot Manager

This module provides legacy API v1 endpoints for backward compatibility.

API v1 includes:
- Bot management endpoints (CRUD operations)
- System endpoints (version, updates, backups)
- Admin bot endpoints (administrative bot management)
- Marketplace endpoints (public bot directory)

Usage:
    from api.v1 import api_v1_bots_bp, api_v1_system_bp, api_v1_admin_bp, api_v1_marketplace_bp
    app.register_blueprint(api_v1_bots_bp)
    app.register_blueprint(api_v1_system_bp)
    app.register_blueprint(api_v1_admin_bp)
    app.register_blueprint(api_v1_marketplace_bp)
"""

from .bots import api_v1_bots_bp
from .system import api_v1_system_bp
from .admin import admin_bp as api_v1_admin_bp
from .marketplace import marketplace_bp as api_v1_marketplace_bp

__all__ = ['api_v1_bots_bp', 'api_v1_system_bp', 'api_v1_admin_bp', 'api_v1_marketplace_bp']
