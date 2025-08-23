"""
API v2 Bot Management Routes for Telegram Bot Manager

This module handles modern API v2 bot endpoints:
- GET /api/v2/bots - list bots with filtering and pagination
- POST /api/v2/bots - create new bot with validation
- GET /api/v2/bots/<id> - get specific bot
- PUT /api/v2/bots/<id> - update bot configuration
- DELETE /api/v2/bots/<id> - delete bot
- GET /api/v2/bots/<id>/status - get detailed bot status
- POST /api/v2/bots/<id>/start - start bot
- POST /api/v2/bots/<id>/stop - stop bot
- POST /api/v2/bots/<id>/restart - restart bot

Extracted from monolithic app.py during refactoring.
"""

import logging
import os
import sys
from datetime import datetime, UTC
from flask import Blueprint, request

import config_manager as cm
import bot_manager as bm
from shared.auth import api_v2_auth_required
from shared.utils import api_response, validate_input_data, serialize_bot_enhanced

logger = logging.getLogger(__name__)

# Create API v2 bots blueprint
api_v2_bots_bp = Blueprint('api_v2_bots', __name__, url_prefix='/api/v2')


@api_v2_bots_bp.route("/bots", methods=["GET"])
@api_v2_auth_required
def get_all_bots_v2():
    """
    Get all bots with filtering and pagination
    
    Query parameters:
    - page: Page number (default: 1)
    - per_page: Items per page (default: 50, max: 100)
    - status: Filter by bot status
    - search: Search in bot names
    
    Returns:
        JSON with paginated bot list and metadata
    """
    try:
        # Query parameters
        page = request.args.get("page", 1, type=int)
        per_page = min(request.args.get("per_page", 50, type=int), 100)
        status_filter = request.args.get("status")
        search = request.args.get("search", "").strip()

        with cm.BOT_CONFIGS_LOCK:
            all_bots = list(cm.BOT_CONFIGS.values())

        # Apply filters
        filtered_bots = all_bots

        if status_filter:
            filtered_bots = [bot for bot in filtered_bots if bot.get("status") == status_filter]

        if search:
            filtered_bots = [
                bot for bot in filtered_bots 
                if search.lower() in bot["config"]["bot_name"].lower()
            ]

        # Sort by ID
        filtered_bots.sort(key=lambda x: x["id"])

        # Pagination
        total = len(filtered_bots)
        start_index = (page - 1) * per_page
        end_index = start_index + per_page
        bots_page = filtered_bots[start_index:end_index]

        # Enhanced serialization
        serialized_bots = [serialize_bot_enhanced(bot) for bot in bots_page]

        response_data = {
            "bots": serialized_bots,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": total,
                "pages": (total + per_page - 1) // per_page,
                "has_next": end_index < total,
                "has_prev": page > 1,
            },
        }

        return api_response(response_data, f"Retrieved {len(serialized_bots)} bots")

    except Exception as e:
        logger.error(f"Error getting bots: {e}")
        return api_response(error="Failed to retrieve bots", status_code=500)


@api_v2_bots_bp.route("/bots/<int:bot_id>", methods=["GET"])
@api_v2_auth_required
def get_bot_v2(bot_id):
    """
    Get a specific bot by ID
    
    Args:
        bot_id: ID of the bot to retrieve
        
    Returns:
        JSON with enhanced bot details
    """
    try:
        with cm.BOT_CONFIGS_LOCK:
            if bot_id not in cm.BOT_CONFIGS:
                return api_response(error="Bot not found", status_code=404)

            bot_entry = cm.BOT_CONFIGS[bot_id]

        response_data = serialize_bot_enhanced(bot_entry)
        return api_response(response_data, "Bot retrieved successfully")

    except Exception as e:
        logger.error(f"Error getting bot {bot_id}: {e}")
        return api_response(error="Failed to retrieve bot", status_code=500)


@api_v2_bots_bp.route("/bots/<int:bot_id>/status", methods=["GET"])
@api_v2_auth_required
def get_bot_status_v2(bot_id):
    """
    Get detailed bot status
    
    Args:
        bot_id: ID of the bot to get status for
        
    Returns:
        JSON with detailed runtime status information
    """
    try:
        with cm.BOT_CONFIGS_LOCK:
            if bot_id not in cm.BOT_CONFIGS:
                return api_response(error="Bot not found", status_code=404)

            bot_entry = cm.BOT_CONFIGS[bot_id]

        status_info = {
            "bot_id": bot_id,
            "status": bot_entry.get("status", "stopped"),
            "bot_name": bot_entry["config"]["bot_name"],
            "runtime": {
                "has_thread": bot_entry.get("thread") is not None,
                "has_loop": bot_entry.get("loop") is not None,
                "has_stop_event": bot_entry.get("stop_event") is not None,
            },
            "config": {
                "voice_enabled": bot_entry["config"].get("enable_voice_responses", False),
                "voice_model": bot_entry["config"].get("voice_model", "tts-1"),
                "voice_type": bot_entry["config"].get("voice_type", "alloy"),
                "context_limit": bot_entry["config"].get("group_context_limit", 15),
            },
        }

        return api_response(status_info, "Bot status retrieved")

    except Exception as e:
        logger.error(f"Error getting bot status {bot_id}: {e}")
        return api_response(error="Failed to get bot status", status_code=500)


@api_v2_bots_bp.route("/bots", methods=["POST"])
@api_v2_auth_required
def create_bot_v2():
    """
    Create a new bot via API v2
    
    Expected JSON payload with required fields:
    - bot_name: Name of the bot
    - telegram_token: Telegram bot token
    - openai_api_key: OpenAI API key
    - assistant_id: OpenAI assistant ID
    
    Returns:
        JSON bot configuration with 201 status
    """
    try:
        data = request.get_json()
        if not data:
            return api_response(error="JSON data required", status_code=400)

        # Auto-fill bot name from Telegram token if not provided
        if not data.get("bot_name") and data.get("telegram_token"):
            try:
                # Add project root to path for imports
                project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
                sys.path.append(project_root)
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
        missing = [field for field in required if field not in data]
        if missing:
            return api_response(
                error=f"Missing required fields: {', '.join(missing)}", 
                status_code=400
            )

        # Validate input data for security
        is_valid, validation_message = validate_input_data(data)
        if not is_valid:
            return api_response(error=validation_message, status_code=400)

        # Auto-fill marketplace username if marketplace is enabled and token is available
        if data.get("marketplace", {}).get("enabled", False) and data.get("telegram_token"):
            marketplace_config = data.get("marketplace", {})
            if not marketplace_config.get("username"):
                try:
                    # Add project root to path for imports
                    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
                    sys.path.append(project_root)
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
            },
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
                "created_at": datetime.now(UTC).isoformat() + "Z",
                "last_updated": datetime.now(UTC).isoformat() + "Z",
            }
            cm.BOT_CONFIGS[bot_id] = bot_entry

        # Save configuration asynchronously
        cm.save_configs_async()

        response_data = {
            "bot_id": bot_id,
            "config": data,
            "status": "stopped",
            "created_at": bot_entry["created_at"],
        }

        logger.info(f"Created new bot via API v2: {bot_id} ({data['bot_name']})")
        return api_response(response_data, "Bot created successfully", status_code=201)

    except Exception as e:
        logger.error(f"Error creating bot: {e}")
        return api_response(error="Failed to create bot", status_code=500)


@api_v2_bots_bp.route("/bots/<int:bot_id>", methods=["PUT"])
@api_v2_auth_required
def update_bot_v2(bot_id):
    """
    Update bot configuration via API v2
    
    Args:
        bot_id: ID of the bot to update
        
    Returns:
        JSON updated bot configuration
    """
    try:
        data = request.get_json()
        if not data:
            return api_response(error="JSON data required", status_code=400)

        with cm.BOT_CONFIGS_LOCK:
            if bot_id not in cm.BOT_CONFIGS:
                return api_response(error="Bot not found", status_code=404)

            # Check if bot is running - allow only marketplace settings for running bots
            if cm.BOT_CONFIGS[bot_id].get("status") == "running":
                # Check if only marketplace settings are being updated
                marketplace_only = all(
                    key.startswith("marketplace.") or key == "marketplace"
                    for key in data.keys()
                )
                if not marketplace_only:
                    return api_response(
                        error="Stop bot before editing configuration (marketplace settings can be changed while running)", 
                        status_code=400
                    )

            # Extract config data if nested structure is sent
            if "config" in data:
                config_data = data["config"]
                # Update bot name if provided
                if "name" in data:
                    cm.BOT_CONFIGS[bot_id]["name"] = data["name"]
            else:
                config_data = data
            
            # Auto-fill marketplace username if marketplace is enabled and token is available
            if config_data.get("marketplace", {}).get("enabled", False) and config_data.get("telegram_token"):
                marketplace_config = config_data.get("marketplace", {})
                if not marketplace_config.get("username"):
                    try:
                        # Add project root to path for imports
                        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
                        sys.path.append(project_root)
                        from core.utils.telegram_bot_info import TelegramBotInfoFetcher
                        bot_info = TelegramBotInfoFetcher.get_bot_info(config_data["telegram_token"])
                        if bot_info and bot_info.get("username"):
                            marketplace_config["username"] = bot_info["username"]
                            config_data["marketplace"] = marketplace_config
                            logger.info(f"Auto-filled marketplace username for bot {bot_id}: @{bot_info['username']}")
                    except ImportError as e:
                        logger.warning(f"Could not auto-fill marketplace username for bot {bot_id}: {e}")
                    except Exception as e:
                        logger.warning(f"Error fetching bot username for bot {bot_id}: {e}")
            
            # Validate input data for security  
            is_valid, validation_message = validate_input_data(config_data)
            if not is_valid:
                return api_response(error=validation_message, status_code=400)

            # Update configuration
            cm.BOT_CONFIGS[bot_id]["config"].update(config_data)
            cm.BOT_CONFIGS[bot_id]["last_updated"] = datetime.now(UTC).isoformat() + "Z"

        # Save configuration asynchronously
        cm.save_configs_async()

        response_data = serialize_bot_enhanced(cm.BOT_CONFIGS[bot_id])
        logger.info(f"Updated bot {bot_id} configuration via API v2")
        return api_response(response_data, "Bot updated successfully")

    except Exception as e:
        logger.error(f"Error updating bot {bot_id}: {e}")
        return api_response(error="Failed to update bot", status_code=500)


@api_v2_bots_bp.route("/bots/<int:bot_id>", methods=["DELETE"])
@api_v2_auth_required
def delete_bot_v2(bot_id):
    """
    Delete bot configuration via API v2
    
    Args:
        bot_id: ID of the bot to delete
        
    Returns:
        JSON success response
    """
    try:
        with cm.BOT_CONFIGS_LOCK:
            if bot_id not in cm.BOT_CONFIGS:
                return api_response(error="Bot not found", status_code=404)

            # Check if bot is running
            if cm.BOT_CONFIGS[bot_id].get("status") == "running":
                return api_response(
                    error="Stop bot before deletion", 
                    status_code=400
                )

            # Get bot name for logging
            bot_name = cm.BOT_CONFIGS[bot_id]["config"].get("bot_name", f"Bot {bot_id}")
            
            # Delete bot configuration
            del cm.BOT_CONFIGS[bot_id]

        # Save configuration asynchronously
        cm.save_configs_async()

        logger.info(f"Deleted bot {bot_id} ({bot_name}) via API v2")
        return api_response(
            {"bot_id": bot_id, "bot_name": bot_name}, 
            "Bot deleted successfully"
        )

    except Exception as e:
        logger.error(f"Error deleting bot {bot_id}: {e}")
        return api_response(error="Failed to delete bot", status_code=500)


@api_v2_bots_bp.route("/bots/<int:bot_id>/start", methods=["POST"])
@api_v2_auth_required
def start_bot_v2(bot_id):
    """
    Start bot thread via API v2
    
    Args:
        bot_id: ID of the bot to start
        
    Returns:
        JSON success response with status
    """
    try:
        success, message = bm.start_bot_thread(bot_id)
        if success:
            logger.info(f"Started bot {bot_id} via API v2")
            return api_response(
                {"bot_id": bot_id, "status": "running"}, 
                "Bot started successfully"
            )
        else:
            logger.warning(f"Failed to start bot {bot_id} via API v2: {message}")
            return api_response(error=message, status_code=400)

    except Exception as e:
        logger.error(f"Error starting bot {bot_id}: {e}")
        return api_response(error="Failed to start bot", status_code=500)


@api_v2_bots_bp.route("/bots/<int:bot_id>/stop", methods=["POST"])
@api_v2_auth_required
def stop_bot_v2(bot_id):
    """
    Stop bot thread via API v2
    
    Args:
        bot_id: ID of the bot to stop
        
    Returns:
        JSON success response with status
    """
    try:
        success, message = bm.stop_bot_thread(bot_id)
        if success:
            logger.info(f"Stopped bot {bot_id} via API v2")
            return api_response(
                {"bot_id": bot_id, "status": "stopped"}, 
                "Bot stopped successfully"
            )
        else:
            logger.warning(f"Failed to stop bot {bot_id} via API v2: {message}")
            return api_response(error=message, status_code=400)

    except Exception as e:
        logger.error(f"Error stopping bot {bot_id}: {e}")
        return api_response(error="Failed to stop bot", status_code=500)


@api_v2_bots_bp.route("/bots/<int:bot_id>/restart", methods=["POST"])
@api_v2_auth_required
def restart_bot_v2(bot_id):
    """
    Restart bot thread via API v2 (stop + start)
    
    Args:
        bot_id: ID of the bot to restart
        
    Returns:
        JSON success response with status
    """
    try:
        # Stop the bot first
        stop_success, stop_message = bm.stop_bot_thread(bot_id)
        if not stop_success:
            logger.warning(f"Failed to stop bot {bot_id} for restart: {stop_message}")
            return api_response(error=f"Failed to stop bot: {stop_message}", status_code=400)

        # Start the bot
        start_success, start_message = bm.start_bot_thread(bot_id)
        if start_success:
            logger.info(f"Restarted bot {bot_id} via API v2")
            return api_response(
                {"bot_id": bot_id, "status": "running"}, 
                "Bot restarted successfully"
            )
        else:
            logger.error(f"Failed to start bot {bot_id} after stop: {start_message}")
            return api_response(error=f"Failed to restart bot: {start_message}", status_code=400)

    except Exception as e:
        logger.error(f"Error restarting bot {bot_id}: {e}")
        return api_response(error="Failed to restart bot", status_code=500)
