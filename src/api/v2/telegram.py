"""
API v2 Telegram Integration Routes for Telegram Bot Manager

This module handles Telegram-specific API v2 endpoints:
- POST /api/v2/telegram/validate-token - validate Telegram bot token

Extracted from monolithic app.py during refactoring.
"""

import logging
import os
import sys
from flask import Blueprint, request

from shared.auth import api_v2_auth_required
from shared.utils import api_response

logger = logging.getLogger(__name__)

# Create API v2 telegram blueprint
api_v2_telegram_bp = Blueprint('api_v2_telegram', __name__, url_prefix='/api/v2')


@api_v2_telegram_bp.route("/telegram/validate-token", methods=["POST"])
@api_v2_auth_required
def validate_telegram_token_v2():
    """
    Validate Telegram token and get bot information
    
    Expected JSON payload:
    {
        "token": "1234567890:ABC..."
    }
    
    Returns:
        JSON with validation result and bot info if valid
    """
    try:
        data = request.get_json()
        if not data or 'token' not in data:
            return api_response(error="Token is required", status_code=400)
        
        token = data['token'].strip()
        if not token:
            return api_response(error="Token cannot be empty", status_code=400)
        
        # Basic token format validation
        if not token or ':' not in token or len(token.split(':')) != 2:
            return api_response(error="Invalid token format", status_code=400)
        
        # Import telegram bot info utility
        try:
            # Add project root to path for imports
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
            sys.path.append(project_root)
            from core.utils.telegram_bot_info import TelegramBotInfoFetcher
        except ImportError as e:
            logger.error(f"Failed to import TelegramBotInfoFetcher: {e}")
            return api_response(
                error="Telegram validation service unavailable", 
                status_code=503
            )
        
        # Validate token and get bot info
        result = TelegramBotInfoFetcher.validate_token_and_get_info(token)
        
        if not result['valid']:
            logger.warning(f"Invalid Telegram token validation attempt")
            return api_response(
                error=result.get('error', 'Invalid token'),
                status_code=400
            )
        
        # Return bot information
        bot_data = {
            "valid": True,
            "bot_info": result['bot_info'],
            "display_name": result['display_name'],
            "username": result['username']
        }
        
        logger.info(f"Successfully validated Telegram token for bot: {result.get('username', 'unknown')}")
        return api_response(data=bot_data, message="Token validated successfully")
        
    except Exception as e:
        logger.error(f"Token validation failed: {e}")
        return api_response(
            error="Failed to validate token",
            status_code=500
        )
