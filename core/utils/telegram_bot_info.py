"""
Telegram Bot Information Utility.

This utility provides functions to automatically fetch bot information
from Telegram API, including bot name, username, and other details.
"""

import logging
import requests
from typing import Dict, Optional, Any

logger = logging.getLogger(__name__)


class TelegramBotInfoFetcher:
    """Fetches bot information from Telegram Bot API."""
    
    @staticmethod
    def get_bot_info(token: str) -> Optional[Dict[str, Any]]:
        """
        Fetch bot information using Telegram Bot API getMe method.
        
        Args:
            token: Telegram bot token
            
        Returns:
            Dict with bot info or None if failed
        """
        if not token or not isinstance(token, str):
            logger.error("Invalid token provided")
            return None
        
        # Validate token format
        if not TelegramBotInfoFetcher._is_valid_token_format(token):
            logger.error("Invalid token format")
            return None
        
        try:
            url = f"https://api.telegram.org/bot{token}/getMe"
            
            # Make request with timeout
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if not data.get("ok"):
                logger.error(f"Telegram API error: {data.get('description', 'Unknown error')}")
                return None
            
            bot_info = data.get("result", {})
            logger.info(f"Successfully fetched bot info for @{bot_info.get('username', 'unknown')}")
            
            return bot_info
            
        except requests.exceptions.Timeout:
            logger.error("Request timeout while fetching bot info")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error while fetching bot info: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error while fetching bot info: {e}")
            return None
    
    @staticmethod
    def get_bot_display_name(token: str) -> Optional[str]:
        """
        Get bot display name from Telegram API.
        Tries to get first_name, then username, then fallback.
        
        Args:
            token: Telegram bot token
            
        Returns:
            Bot display name or None if failed
        """
        bot_info = TelegramBotInfoFetcher.get_bot_info(token)
        
        if not bot_info:
            return None
        
        # Priority: first_name > username > id-based fallback
        if bot_info.get("first_name"):
            return bot_info["first_name"]
        elif bot_info.get("username"):
            return f"@{bot_info['username']}"
        elif bot_info.get("id"):
            return f"Bot {bot_info['id']}"
        else:
            return None
    
    @staticmethod
    def get_bot_username(token: str) -> Optional[str]:
        """
        Get bot username from Telegram API.
        
        Args:
            token: Telegram bot token
            
        Returns:
            Bot username (with @) or None if failed
        """
        bot_info = TelegramBotInfoFetcher.get_bot_info(token)
        
        if not bot_info:
            return None
        
        username = bot_info.get("username")
        if username:
            return f"@{username}" if not username.startswith("@") else username
        
        return None
    
    @staticmethod
    def validate_token_and_get_info(token: str) -> Dict[str, Any]:
        """
        Validate token and get comprehensive bot information.
        
        Args:
            token: Telegram bot token
            
        Returns:
            Dict with validation status and bot info
        """
        result = {
            "valid": False,
            "bot_info": None,
            "display_name": None,
            "username": None,
            "error": None
        }
        
        if not token:
            result["error"] = "Token is empty"
            return result
        
        if not TelegramBotInfoFetcher._is_valid_token_format(token):
            result["error"] = "Invalid token format (should be: bot_id:token)"
            return result
        
        bot_info = TelegramBotInfoFetcher.get_bot_info(token)
        
        if not bot_info:
            result["error"] = "Failed to fetch bot information from Telegram"
            return result
        
        # Token is valid and bot exists
        result["valid"] = True
        result["bot_info"] = bot_info
        result["display_name"] = TelegramBotInfoFetcher.get_bot_display_name(token)
        result["username"] = TelegramBotInfoFetcher.get_bot_username(token)
        
        return result
    
    @staticmethod
    def _is_valid_token_format(token: str) -> bool:
        """
        Check if token has valid format: bot_id:token_part
        
        Args:
            token: Token to validate
            
        Returns:
            True if format is valid
        """
        if not token or ":" not in token:
            return False
        
        parts = token.split(":", 1)
        if len(parts) != 2:
            return False
        
        bot_id, token_part = parts
        
        # Bot ID should be numeric
        if not bot_id.isdigit():
            return False
        
        # Token part should be alphanumeric + some special chars
        if not token_part or len(token_part) < 10:
            return False
        
        return True
    
    @staticmethod
    def suggest_bot_name(token: str, fallback_name: str = "Новый бот") -> str:
        """
        Suggest a bot name based on Telegram API info or provide fallback.
        
        Args:
            token: Telegram bot token
            fallback_name: Fallback name if API call fails
            
        Returns:
            Suggested bot name
        """
        display_name = TelegramBotInfoFetcher.get_bot_display_name(token)
        
        if display_name:
            return display_name
        
        # If we can't get from API, try to extract from token
        if TelegramBotInfoFetcher._is_valid_token_format(token):
            bot_id = token.split(":")[0]
            return f"Bot {bot_id}"
        
        return fallback_name


# Convenience functions for backward compatibility
def get_bot_info_from_token(token: str) -> Optional[Dict[str, Any]]:
    """Get bot info from token (convenience function)."""
    return TelegramBotInfoFetcher.get_bot_info(token)


def get_bot_name_from_token(token: str) -> Optional[str]:
    """Get bot display name from token (convenience function)."""
    return TelegramBotInfoFetcher.get_bot_display_name(token)


def validate_telegram_token(token: str) -> Dict[str, Any]:
    """Validate Telegram token and get info (convenience function)."""
    return TelegramBotInfoFetcher.validate_token_and_get_info(token)





