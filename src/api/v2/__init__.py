"""
API v2 module for Telegram Bot Manager

This module provides modern API v2 endpoints with enhanced features:
- Enhanced security and authentication
- Standardized JSON response format
- Comprehensive error handling  
- Filtering and pagination support

API v2 includes:
- System endpoints (health, info, stats, docs)
- Bot management endpoints (CRUD + advanced operations)
- Telegram integration endpoints (token validation)

Usage:
    from api.v2 import api_v2_system_bp, api_v2_bots_bp, api_v2_telegram_bp
    app.register_blueprint(api_v2_system_bp)
    app.register_blueprint(api_v2_bots_bp)
    app.register_blueprint(api_v2_telegram_bp)
"""

from .system import api_v2_system_bp
from .bots import api_v2_bots_bp
from .telegram import api_v2_telegram_bp

__all__ = ['api_v2_system_bp', 'api_v2_bots_bp', 'api_v2_telegram_bp']
