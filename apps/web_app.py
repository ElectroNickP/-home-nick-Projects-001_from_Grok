"""
Web application entry point.

This module provides a Flask-based web interface for the Telegram Bot Manager,
integrating with use cases and providing REST API endpoints.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime
from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from werkzeug.security import check_password_hash
import functools

from core.usecases.bot_management import BotManagementUseCase
from core.usecases.conversation_management import ConversationManagementUseCase
from core.usecases.system_management import SystemManagementUseCase
from core.domain.bot import BotConfig
from core.domain.config import SystemConfig, AdminBotConfig

logger = logging.getLogger(__name__)


def require_auth(f):
    """Decorator to require authentication."""
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('authenticated'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


class WebApplication:
    """Flask web application for Telegram Bot Manager."""

    def __init__(
        self,
        bot_management_use_case: BotManagementUseCase,
        conversation_management_use_case: ConversationManagementUseCase,
        system_management_use_case: SystemManagementUseCase,
        secret_key: str = "your-secret-key-here",
        username: str = "admin",
        password_hash: str = "pbkdf2:sha256:600000$your-hash-here",
    ):
        """Initialize the web application."""
        self.bot_management_use_case = bot_management_use_case
        self.conversation_management_use_case = conversation_management_use_case
        self.system_management_use_case = system_management_use_case
        
        self.app = Flask(__name__)
        self.app.secret_key = secret_key
        self.username = username
        self.password_hash = password_hash
        
        self._setup_routes()
        self._setup_error_handlers()

    def _setup_routes(self):
        """Setup Flask routes."""
        
        @self.app.route('/')
        @require_auth
        def index():
            """Main dashboard."""
            try:
                bots = self.bot_management_use_case.get_all_bots()
                system_health = self.system_management_use_case.get_system_health()
                
                return render_template('index.html', 
                                     bots=bots, 
                                     system_health=system_health)
            except Exception as e:
                logger.error(f"Error in index route: {e}")
                return render_template('error.html', error=str(e))

        @self.app.route('/login', methods=['GET', 'POST'])
        def login():
            """Login page."""
            if request.method == 'POST':
                username = request.form.get('username')
                password = request.form.get('password')
                
                if (username == self.username and 
                    check_password_hash(self.password_hash, password)):
                    session['authenticated'] = True
                    return redirect(url_for('index'))
                else:
                    return render_template('login.html', error="Invalid credentials")
            
            return render_template('login.html')

        @self.app.route('/logout')
        def logout():
            """Logout."""
            session.pop('authenticated', None)
            return redirect(url_for('login'))

        # API Routes
        @self.app.route('/api/v2/bots', methods=['GET'])
        @require_auth
        def get_bots():
            """Get all bots."""
            try:
                bots = self.bot_management_use_case.get_all_bots()
                return jsonify({
                    "success": True,
                    "data": [bot.to_dict() for bot in bots],
                    "total": len(bots)
                })
            except Exception as e:
                logger.error(f"Error getting bots: {e}")
                return jsonify({
                    "success": False,
                    "error": str(e)
                }), 500

        @self.app.route('/api/v2/bots', methods=['POST'])
        @require_auth
        async def create_bot():
            """Create a new bot."""
            try:
                data = request.get_json()
                if not data:
                    return jsonify({
                        "success": False,
                        "error": "No data provided"
                    }), 400

                # Create bot config from data
                bot_config = BotConfig(
                    name=data.get('name', ''),
                    telegram_token=data.get('telegram_token', ''),
                    openai_api_key=data.get('openai_api_key', ''),
                    assistant_id=data.get('assistant_id', ''),
                    group_context_limit=data.get('group_context_limit', 15),
                    enable_ai_responses=data.get('enable_ai_responses', True),
                    enable_voice_responses=data.get('enable_voice_responses', False),
                    voice_model=data.get('voice_model', 'tts-1'),
                    voice_type=data.get('voice_type', 'alloy'),
                )

                bot = await self.bot_management_use_case.create_bot(bot_config)
                
                return jsonify({
                    "success": True,
                    "data": bot.to_dict(),
                    "message": "Bot created successfully"
                }), 201

            except ValueError as e:
                return jsonify({
                    "success": False,
                    "error": str(e)
                }), 400
            except Exception as e:
                logger.error(f"Error creating bot: {e}")
                return jsonify({
                    "success": False,
                    "error": str(e)
                }), 500

        @self.app.route('/api/v2/bots/<int:bot_id>', methods=['GET'])
        @require_auth
        def get_bot(bot_id):
            """Get bot by ID."""
            try:
                bot = self.bot_management_use_case.get_bot(bot_id)
                if not bot:
                    return jsonify({
                        "success": False,
                        "error": "Bot not found"
                    }), 404

                return jsonify({
                    "success": True,
                    "data": bot.to_dict()
                })

            except Exception as e:
                logger.error(f"Error getting bot {bot_id}: {e}")
                return jsonify({
                    "success": False,
                    "error": str(e)
                }), 500

        @self.app.route('/api/v2/bots/<int:bot_id>', methods=['PUT'])
        @require_auth
        async def update_bot(bot_id):
            """Update bot."""
            try:
                data = request.get_json()
                if not data:
                    return jsonify({
                        "success": False,
                        "error": "No data provided"
                    }), 400

                # Create bot config from data
                bot_config = BotConfig(
                    name=data.get('name', ''),
                    telegram_token=data.get('telegram_token', ''),
                    openai_api_key=data.get('openai_api_key', ''),
                    assistant_id=data.get('assistant_id', ''),
                    group_context_limit=data.get('group_context_limit', 15),
                    enable_ai_responses=data.get('enable_ai_responses', True),
                    enable_voice_responses=data.get('enable_voice_responses', False),
                    voice_model=data.get('voice_model', 'tts-1'),
                    voice_type=data.get('voice_type', 'alloy'),
                )

                bot = await self.bot_management_use_case.update_bot(bot_id, bot_config)
                if not bot:
                    return jsonify({
                        "success": False,
                        "error": "Bot not found"
                    }), 404

                return jsonify({
                    "success": True,
                    "data": bot.to_dict(),
                    "message": "Bot updated successfully"
                })

            except ValueError as e:
                return jsonify({
                    "success": False,
                    "error": str(e)
                }), 400
            except Exception as e:
                logger.error(f"Error updating bot {bot_id}: {e}")
                return jsonify({
                    "success": False,
                    "error": str(e)
                }), 500

        @self.app.route('/api/v2/bots/<int:bot_id>', methods=['DELETE'])
        @require_auth
        def delete_bot(bot_id):
            """Delete bot."""
            try:
                success = self.bot_management_use_case.delete_bot(bot_id)
                if not success:
                    return jsonify({
                        "success": False,
                        "error": "Bot not found"
                    }), 404

                return jsonify({
                    "success": True,
                    "message": "Bot deleted successfully"
                })

            except Exception as e:
                logger.error(f"Error deleting bot {bot_id}: {e}")
                return jsonify({
                    "success": False,
                    "error": str(e)
                }), 500

        @self.app.route('/api/v2/bots/<int:bot_id>/start', methods=['POST'])
        @require_auth
        def start_bot(bot_id):
            """Start bot."""
            try:
                success = self.bot_management_use_case.start_bot(bot_id)
                if not success:
                    return jsonify({
                        "success": False,
                        "error": "Failed to start bot"
                    }), 400

                return jsonify({
                    "success": True,
                    "message": "Bot started successfully"
                })

            except Exception as e:
                logger.error(f"Error starting bot {bot_id}: {e}")
                return jsonify({
                    "success": False,
                    "error": str(e)
                }), 500

        @self.app.route('/api/v2/bots/<int:bot_id>/stop', methods=['POST'])
        @require_auth
        def stop_bot(bot_id):
            """Stop bot."""
            try:
                success = self.bot_management_use_case.stop_bot(bot_id)
                if not success:
                    return jsonify({
                        "success": False,
                        "error": "Failed to stop bot"
                    }), 400

                return jsonify({
                    "success": True,
                    "message": "Bot stopped successfully"
                })

            except Exception as e:
                logger.error(f"Error stopping bot {bot_id}: {e}")
                return jsonify({
                    "success": False,
                    "error": str(e)
                }), 500

        @self.app.route('/api/v2/bots/<int:bot_id>/restart', methods=['POST'])
        @require_auth
        def restart_bot(bot_id):
            """Restart bot."""
            try:
                success = self.bot_management_use_case.restart_bot(bot_id)
                if not success:
                    return jsonify({
                        "success": False,
                        "error": "Failed to restart bot"
                    }), 400

                return jsonify({
                    "success": True,
                    "message": "Bot restarted successfully"
                })

            except Exception as e:
                logger.error(f"Error restarting bot {bot_id}: {e}")
                return jsonify({
                    "success": False,
                    "error": str(e)
                }), 500

        @self.app.route('/api/v2/bots/<int:bot_id>/status', methods=['GET'])
        @require_auth
        async def get_bot_status(bot_id):
            """Get bot status."""
            try:
                status = await self.bot_management_use_case.get_bot_status(bot_id)
                if not status:
                    return jsonify({
                        "success": False,
                        "error": "Bot not found"
                    }), 404

                return jsonify({
                    "success": True,
                    "data": status
                })

            except Exception as e:
                logger.error(f"Error getting bot status {bot_id}: {e}")
                return jsonify({
                    "success": False,
                    "error": str(e)
                }), 500

        # System routes
        @self.app.route('/api/v2/system/health', methods=['GET'])
        def get_system_health():
            """Get system health."""
            try:
                health = self.system_management_use_case.get_system_health()
                return jsonify({
                    "success": True,
                    "data": health
                })

            except Exception as e:
                logger.error(f"Error getting system health: {e}")
                return jsonify({
                    "success": False,
                    "error": str(e)
                }), 500

        @self.app.route('/api/v2/system/info', methods=['GET'])
        def get_system_info():
            """Get system information."""
            try:
                info = self.system_management_use_case.get_system_info()
                return jsonify({
                    "success": True,
                    "data": info
                })

            except Exception as e:
                logger.error(f"Error getting system info: {e}")
                return jsonify({
                    "success": False,
                    "error": str(e)
                }), 500

        @self.app.route('/api/v2/system/stats', methods=['GET'])
        def get_system_stats():
            """Get system statistics."""
            try:
                stats = self.system_management_use_case.get_system_stats()
                return jsonify({
                    "success": True,
                    "data": stats
                })

            except Exception as e:
                logger.error(f"Error getting system stats: {e}")
                return jsonify({
                    "success": False,
                    "error": str(e)
                }), 500

        @self.app.route('/api/v2/system/updates/check', methods=['GET'])
        def check_updates():
            """Check for updates."""
            try:
                updates = self.system_management_use_case.check_updates()
                return jsonify({
                    "success": True,
                    "data": updates
                })

            except Exception as e:
                logger.error(f"Error checking updates: {e}")
                return jsonify({
                    "success": False,
                    "error": str(e)
                }), 500

        @self.app.route('/api/v2/system/updates/apply', methods=['POST'])
        @require_auth
        def apply_update():
            """Apply update."""
            try:
                data = request.get_json()
                version = data.get('version') if data else None
                
                if not version:
                    return jsonify({
                        "success": False,
                        "error": "Version not specified"
                    }), 400

                success = self.system_management_use_case.apply_update(version)
                if not success:
                    return jsonify({
                        "success": False,
                        "error": "Failed to apply update"
                    }), 500

                return jsonify({
                    "success": True,
                    "message": "Update applied successfully"
                })

            except Exception as e:
                logger.error(f"Error applying update: {e}")
                return jsonify({
                    "success": False,
                    "error": str(e)
                }), 500

        @self.app.route('/api/v2/system/backups', methods=['GET'])
        @require_auth
        def get_backups():
            """Get backups."""
            try:
                backups = self.system_management_use_case.get_backups()
                return jsonify({
                    "success": True,
                    "data": backups,
                    "count": len(backups)
                })

            except Exception as e:
                logger.error(f"Error getting backups: {e}")
                return jsonify({
                    "success": False,
                    "error": str(e)
                }), 500

        @self.app.route('/api/v2/system/backups', methods=['POST'])
        @require_auth
        def create_backup():
            """Create backup."""
            try:
                backup_id = self.system_management_use_case.create_backup()
                return jsonify({
                    "success": True,
                    "data": {"backup_id": backup_id},
                    "message": "Backup created successfully"
                })

            except Exception as e:
                logger.error(f"Error creating backup: {e}")
                return jsonify({
                    "success": False,
                    "error": str(e)
                }), 500

        @self.app.route('/api/v2/system/backups/<backup_id>/restore', methods=['POST'])
        @require_auth
        def restore_backup(backup_id):
            """Restore backup."""
            try:
                success = self.system_management_use_case.restore_backup(backup_id)
                if not success:
                    return jsonify({
                        "success": False,
                        "error": "Failed to restore backup"
                    }), 400

                return jsonify({
                    "success": True,
                    "message": "Backup restored successfully"
                })

            except Exception as e:
                logger.error(f"Error restoring backup: {e}")
                return jsonify({
                    "success": False,
                    "error": str(e)
                }), 500

    def _setup_error_handlers(self):
        """Setup error handlers."""
        
        @self.app.errorhandler(404)
        def not_found(error):
            return jsonify({
                "success": False,
                "error": "Not found"
            }), 404

        @self.app.errorhandler(500)
        def internal_error(error):
            return jsonify({
                "success": False,
                "error": "Internal server error"
            }), 500

    def run(self, host: str = '0.0.0.0', port: int = 5000, debug: bool = False):
        """Run the Flask application."""
        self.app.run(host=host, port=port, debug=debug)








