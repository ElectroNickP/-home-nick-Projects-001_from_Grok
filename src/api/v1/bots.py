"""
API v1 Bot Management Routes for Telegram Bot Manager

This module handles legacy API v1 endpoints for bot management:
- GET/POST /api/bots
- GET/PUT/DELETE /api/bots/<id>
- POST /api/bots/<id>/start
- POST /api/bots/<id>/stop

Extracted from monolithic app.py during refactoring.
"""

import logging
import os
import sys
from flask import Blueprint, request, jsonify

import config_manager as cm
import bot_manager as bm
from shared.auth import api_login_required
from shared.utils import serialize_bot_entry

logger = logging.getLogger(__name__)

# Create API v1 bots blueprint
api_v1_bots_bp = Blueprint('api_v1_bots', __name__, url_prefix='/api')


@api_v1_bots_bp.route("/bots", methods=["GET"])
@api_login_required
def get_all_bots():
    """
    Get all bots (API v1 compatibility)
    
    Returns:
        JSON list of all bot configurations
    """
    try:
        with cm.BOT_CONFIGS_LOCK:
            bots = []
            for bot_id, bot_data in cm.BOT_CONFIGS.items():
                if bot_data is not None:
                    # Extract actual config from bot_data, avoiding double nesting
                    if "config" in bot_data and isinstance(bot_data["config"], dict):
                        actual_config = bot_data["config"]
                    else:
                        # Fallback: use bot_data directly as config (excluding system fields)
                        actual_config = {
                            k: v
                            for k, v in bot_data.items()
                            if k not in ["thread", "loop", "stop_event", "status", "id"]
                        }

                    bot_entry = {
                        "id": bot_id,
                        "config": actual_config,
                        "status": bot_data.get("status", "stopped"),
                    }
                    bots.append(serialize_bot_entry(bot_entry))
            return jsonify(bots)
    except Exception as e:
        logger.error(f"Error in get_all_bots: {e}")
        return jsonify({"error": str(e)}), 500


@api_v1_bots_bp.route("/bots/<int:bot_id>", methods=["GET"])
@api_login_required
def get_bot(bot_id):
    """
    Get specific bot configuration
    
    Args:
        bot_id: ID of the bot to retrieve
        
    Returns:
        JSON bot configuration or 404 if not found
    """
    with cm.BOT_CONFIGS_LOCK:
        if bot_id not in cm.BOT_CONFIGS:
            return jsonify({"error": "Бот не найден"}), 404
        return jsonify(serialize_bot_entry(cm.BOT_CONFIGS[bot_id]))


@api_v1_bots_bp.route("/bots", methods=["POST"])
@api_login_required  
def create_bot():
    """
    Create new bot configuration
    
    Expected JSON payload with required fields:
    - bot_name
    - telegram_token
    - openai_api_key
    - assistant_id
    
    Returns:
        JSON bot configuration with 201 status
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "JSON payload required"}), 400
        
        # Auto-fill bot name from Telegram token if not provided
        if not data.get("bot_name") and data.get("telegram_token"):
            try:
                # Add project root to path for imports
                sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
                from core.utils.telegram_bot_info import TelegramBotInfoFetcher
                suggested_name = TelegramBotInfoFetcher.suggest_bot_name(
                    data["telegram_token"], 
                    fallback_name="Новый бот"
                )
                data["bot_name"] = suggested_name
                logger.info(f"Auto-generated bot name: {suggested_name}")
            except ImportError as e:
                logger.warning(f"Could not auto-generate bot name: {e}")
        
        # Validate required fields
        required = ["bot_name", "telegram_token", "openai_api_key", "assistant_id"]
        missing_fields = [field for field in required if field not in data]
        if missing_fields:
            return jsonify({
                "error": "Missing required fields", 
                "missing": missing_fields
            }), 400

        # Auto-fill marketplace username if marketplace is enabled and token is available
        if data.get("marketplace", {}).get("enabled", False) and data.get("telegram_token"):
            marketplace_config = data.get("marketplace", {})
            if not marketplace_config.get("username"):
                try:
                    # Add project root to path for imports
                    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
                    from core.utils.telegram_bot_info import TelegramBotInfoFetcher
                    bot_info = TelegramBotInfoFetcher.get_bot_info(data["telegram_token"])
                    if bot_info and bot_info.get("username"):
                        marketplace_config["username"] = bot_info["username"]
                        data["marketplace"] = marketplace_config
                        logger.info(f"Auto-filled marketplace username: @{bot_info['username']}")
                except ImportError as e:
                    logger.warning(f"Could not auto-fill marketplace username: {e}")
                except Exception as e:
                    logger.warning(f"Error fetching bot username: {e}")

        # Set default values if not provided
        defaults = {
            "group_context_limit": 15,
            "enable_voice_responses": False,
            "voice_model": "tts-1",
            "voice_type": "alloy",
            "enable_ai_responses": True,
            "marketplace": {
                "enabled": False,
                "title": "",
                "description": "",
                "category": "other",
                "username": "",
                "website": "",
                "image_url": "",
                "tags": [],
                "featured": False,
                "rating": 0.0,
                "total_users": 0,
                "last_updated": None,
            }
        }
        
        for key, default_value in defaults.items():
            if key not in data:
                data[key] = default_value

        # Create bot entry
        with cm.BOT_CONFIGS_LOCK:
            bot_id = cm.NEXT_BOT_ID
            cm.NEXT_BOT_ID += 1
            bot_entry = {
                "id": bot_id,
                "config": data,
                "status": "stopped",
                "thread": None,
                "loop": None,
                "stop_event": None,
            }
            cm.BOT_CONFIGS[bot_id] = bot_entry

        # Save configuration asynchronously
        cm.save_configs_async()
        logger.info(f"Created new bot with ID {bot_id}: {data['bot_name']}")
        return jsonify(serialize_bot_entry(bot_entry)), 201
        
    except Exception as e:
        logger.error(f"Error creating bot: {e}")
        return jsonify({"error": "Internal server error"}), 500


@api_v1_bots_bp.route("/bots/<int:bot_id>", methods=["PUT"])
@api_login_required
def update_bot(bot_id):
    """
    Update existing bot configuration
    
    Args:
        bot_id: ID of the bot to update
        
    Returns:
        JSON updated bot configuration or error
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "JSON payload required"}), 400
            
        with cm.BOT_CONFIGS_LOCK:
            if bot_id not in cm.BOT_CONFIGS:
                return jsonify({"error": "Бот не найден"}), 404
                
            # Check if bot is running
            if cm.BOT_CONFIGS[bot_id].get("status") == "running":
                return jsonify({
                    "error": "Остановите бота перед редактированием"
                }), 400
                
            # Update configuration
            cm.BOT_CONFIGS[bot_id]["config"].update(data)

        # Save configuration asynchronously
        cm.save_configs_async()
        logger.info(f"Updated bot {bot_id} configuration")
        return jsonify(serialize_bot_entry(cm.BOT_CONFIGS[bot_id]))
        
    except Exception as e:
        logger.error(f"Error updating bot {bot_id}: {e}")
        return jsonify({"error": "Internal server error"}), 500


@api_v1_bots_bp.route("/bots/<int:bot_id>", methods=["DELETE"])
@api_login_required  
def delete_bot(bot_id):
    """
    Delete bot configuration
    
    Args:
        bot_id: ID of the bot to delete
        
    Returns:
        JSON success response or error
    """
    try:
        with cm.BOT_CONFIGS_LOCK:
            if bot_id not in cm.BOT_CONFIGS:
                return jsonify({"error": "Бот не найден"}), 404
                
            # Check if bot is running
            if cm.BOT_CONFIGS[bot_id].get("status") == "running":
                return jsonify({
                    "error": "Остановите бота перед удалением"
                }), 400
                
            # Delete bot configuration
            bot_name = cm.BOT_CONFIGS[bot_id]["config"].get("bot_name", f"Bot {bot_id}")
            del cm.BOT_CONFIGS[bot_id]

        # Save configuration asynchronously
        cm.save_configs_async()
        logger.info(f"Deleted bot {bot_id} ({bot_name})")
        return jsonify({"success": True, "message": f"Бот {bot_name} удален"})
        
    except Exception as e:
        logger.error(f"Error deleting bot {bot_id}: {e}")
        return jsonify({"error": "Internal server error"}), 500


@api_v1_bots_bp.route("/bots/<int:bot_id>/start", methods=["POST"])
@api_login_required
def start_bot(bot_id):
    """
    Start bot thread
    
    Args:
        bot_id: ID of the bot to start
        
    Returns:
        JSON success response or error
    """
    try:
        success, message = bm.start_bot_thread(bot_id)
        if success:
            logger.info(f"Started bot {bot_id}")
            return jsonify({"success": True, "message": "Бот запущен"})
        else:
            logger.warning(f"Failed to start bot {bot_id}: {message}")
            return jsonify({"error": message}), 400
            
    except Exception as e:
        logger.error(f"Error starting bot {bot_id}: {e}")
        return jsonify({"error": "Internal server error"}), 500


@api_v1_bots_bp.route("/bots/<int:bot_id>/stop", methods=["POST"]) 
@api_login_required
def stop_bot(bot_id):
    """
    Stop bot thread
    
    Args:
        bot_id: ID of the bot to stop
        
    Returns:
        JSON success response or error
    """
    try:
        success, message = bm.stop_bot_thread(bot_id)
        if success:
            logger.info(f"Stopped bot {bot_id}")
            return jsonify({"success": True, "message": "Бот остановлен"})
        else:
            logger.warning(f"Failed to stop bot {bot_id}: {message}")
            return jsonify({"error": message}), 400
            
    except Exception as e:
        logger.error(f"Error stopping bot {bot_id}: {e}")
        return jsonify({"error": "Internal server error"}), 500
