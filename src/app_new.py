#!/usr/bin/env python3
"""
Telegram Bot Manager - Refactored Application Factory

This is the new modularized version of the Flask application.
"""

import logging
import sys
from datetime import timedelta
from flask import Flask

# Import new modular components
from api.auth import auth_bp
from web import web_bp
from shared.utils import datetime_filter, find_free_port

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
    handlers=[logging.FileHandler("bot.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


def create_app():
    """Application factory for Flask app"""
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
    
    logger.info("✅ Flask app created with modular structure")
    return app


if __name__ == "__main__":
    app = create_app()
    port = find_free_port(start_port=5000)
    app.run(host="0.0.0.0", port=port, debug=True)




