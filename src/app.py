#!/usr/bin/env python3
"""
Telegram Bot Manager - Refactored Application Factory

This is the new modularized version of the Flask application.
"""

import logging
import sys
from datetime import timedelta
from flask import Flask, send_from_directory

# Import new modular components
from api.auth import auth_bp
from api.v1 import api_v1_bots_bp, api_v1_system_bp, api_v1_admin_bp, api_v1_marketplace_bp  
from api.v2 import api_v2_system_bp, api_v2_bots_bp, api_v2_telegram_bp
from api.v2.uploads import api_v2_uploads_bp
from web import web_bp
from shared.utils import datetime_filter, find_free_port

# Import configuration and bot managers
import config_manager as cm
import bot_manager as bm

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
    handlers=[logging.FileHandler("bot.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


def create_app():
    """Application factory for Flask app"""
    # Load bot configurations from file
    logger.info("🔄 Loading bot configurations...")
    try:
        cm.load_configs()
        logger.info(f"📋 Loaded {len(cm.BOT_CONFIGS)} bot(s) from configuration file")
        
        # Temporarily disable auto-starting bots to fix startup issues
        # TODO: Re-enable after fixing the startup flow
        # bm.start_all_bots()
        logger.info("⚠️ Auto-start bots disabled during startup troubleshooting")
        
    except Exception as e:
        logger.error(f"❌ Failed to load configurations: {e}")
        logger.info("📋 Continuing with empty configuration")
    
    app = Flask(__name__, template_folder="templates")
    
    # TODO: Move to environment variable (security issue from audit)
    app.secret_key = "your-secret-key-change-in-production"
    
    # Configure Jinja2 filters
    app.jinja_env.filters["datetime"] = datetime_filter

    # Session configuration
    app.config.update(
        SESSION_COOKIE_SECURE=False,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        PERMANENT_SESSION_LIFETIME=timedelta(hours=24),
        SESSION_COOKIE_NAME="electronick_session"
    )
    
    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(web_bp)
    app.register_blueprint(api_v1_bots_bp)
    app.register_blueprint(api_v1_system_bp)
    app.register_blueprint(api_v1_admin_bp)
    app.register_blueprint(api_v1_marketplace_bp)
    app.register_blueprint(api_v2_system_bp)
    app.register_blueprint(api_v2_bots_bp)
    app.register_blueprint(api_v2_telegram_bp)
    app.register_blueprint(api_v2_uploads_bp)
    
    # Add route for serving uploaded files
    @app.route('/static/uploads/<path:filename>')
    def uploaded_file(filename):
        """Serve uploaded files from uploads directory"""
        from pathlib import Path
        uploads_dir = Path(__file__).parent / 'static' / 'uploads'
        return send_from_directory(uploads_dir, filename)
    
    logger.info("✅ Flask app created with modular structure")
    logger.info("📋 Registered blueprints: auth, web, api_v1_bots, api_v1_system, api_v1_admin, api_v1_marketplace, api_v2_system, api_v2_bots, api_v2_telegram")
    logger.info("✅ API v1 completed!")
    logger.info("🚀 API v2 system module extracted!")
    logger.info("🚀 API v2 bots module extracted!")
    logger.info("🚀 API v2 telegram module extracted!")
    logger.info("🎉 ALL API MODULES EXTRACTED! REFACTORING COMPLETE!")
    return app


if __name__ == "__main__":
    app = create_app()
    port = find_free_port(start_port=5000)
    app.run(host="0.0.0.0", port=port, debug=True)
