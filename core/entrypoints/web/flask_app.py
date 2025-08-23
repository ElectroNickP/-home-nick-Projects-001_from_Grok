"""
Flask web application for Telegram Bot Manager.

This module provides the web interface using Flask framework.
"""

import logging

from flask import Flask, redirect, render_template, request, session, url_for
from flask_session import Session
from werkzeug.exceptions import HTTPException

from ..usecases import BotManagementUseCase, ConversationUseCase, SystemUseCase
from .routes import bot_bp, conversation_bp, system_bp


class FlaskApp:
    """Flask web application for Telegram Bot Manager."""

    def __init__(
        self,
        bot_usecase: BotManagementUseCase,
        conversation_usecase: ConversationUseCase,
        system_usecase: SystemUseCase,
        config: dict | None = None,
    ):
        """Initialize Flask application with use cases."""
        self.bot_usecase = bot_usecase
        self.conversation_usecase = conversation_usecase
        self.system_usecase = system_usecase
        self.config = config or {}
        self.logger = logging.getLogger(__name__)

        # Create Flask app
        self.app = Flask(__name__)
        self._configure_app()
        self._register_blueprints()
        self._register_error_handlers()
        self._register_middleware()

    def _configure_app(self):
        """Configure Flask application."""
        # Basic configuration
        self.app.config.update({
            'SECRET_KEY': self.config.get('secret_key', 'your-secret-key-here'),
            'SESSION_TYPE': 'filesystem',
            'SESSION_FILE_DIR': '/tmp/flask_session',
            'SESSION_FILE_THRESHOLD': 500,
            'SESSION_FILE_MODE': 384,
            'PERMANENT_SESSION_LIFETIME': self.config.get('session_timeout', 3600),
        })

        # Initialize session
        Session(self.app)

    def _register_blueprints(self):
        """Register Flask blueprints."""
        # Pass use cases to blueprints
        bot_bp.usecase = self.bot_usecase
        conversation_bp.usecase = self.conversation_usecase
        system_bp.usecase = self.system_usecase

        # Register blueprints
        self.app.register_blueprint(bot_bp, url_prefix='/bots')
        self.app.register_blueprint(conversation_bp, url_prefix='/conversations')
        self.app.register_blueprint(system_bp, url_prefix='/system')

    def _register_error_handlers(self):
        """Register error handlers."""
        @self.app.errorhandler(404)
        def not_found(error):
            return render_template('error.html', error=error), 404

        @self.app.errorhandler(500)
        def internal_error(error):
            self.logger.error(f"Internal server error: {error}")
            return render_template('error.html', error=error), 500

        @self.app.errorhandler(HTTPException)
        def handle_exception(e):
            return render_template('error.html', error=e), e.code

    def _register_middleware(self):
        """Register middleware."""
        @self.app.before_request
        def before_request():
            """Handle requests before processing."""
            # Log request
            self.logger.info(f"{request.method} {request.path}")

            # Check authentication for protected routes
            if self._is_protected_route(request.path):
                if not self._is_authenticated():
                    return redirect(url_for('login'))

        @self.app.after_request
        def after_request(response):
            """Handle responses after processing."""
            # Add security headers
            response.headers['X-Content-Type-Options'] = 'nosniff'
            response.headers['X-Frame-Options'] = 'DENY'
            response.headers['X-XSS-Protection'] = '1; mode=block'
            return response

    def _is_protected_route(self, path: str) -> bool:
        """Check if route requires authentication."""
        protected_prefixes = ['/bots', '/conversations', '/system']
        return any(path.startswith(prefix) for prefix in protected_prefixes)

    def _is_authenticated(self) -> bool:
        """Check if user is authenticated."""
        return session.get('authenticated', False)

    def run(self, host: str = "0.0.0.0", port: int = 5000, debug: bool = False):
        """Run Flask application."""
        self.logger.info(f"Starting Flask app on {host}:{port}")
        self.app.run(host=host, port=port, debug=debug)

    def get_app(self) -> Flask:
        """Get Flask application instance."""
        return self.app


# Global Flask app instance
flask_app: FlaskApp | None = None


def create_app(
    bot_usecase: BotManagementUseCase,
    conversation_usecase: ConversationUseCase,
    system_usecase: SystemUseCase,
    config: dict | None = None,
) -> FlaskApp:
    """Create Flask application instance."""
    global flask_app
    flask_app = FlaskApp(bot_usecase, conversation_usecase, system_usecase, config)
    return flask_app


def get_app() -> FlaskApp:
    """Get Flask application instance."""
    if flask_app is None:
        raise RuntimeError("Flask app not initialized. Call create_app() first.")
    return flask_app









