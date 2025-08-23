"""
Telegram port definition for external telegram service integration.

This module defines the interface for telegram operations that can be
implemented by different telegram adapters (aiogram, python-telegram-bot, etc.).
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from core.domain.bot import BotConfig


class TelegramPort(ABC):
    """
    Port interface for Telegram bot operations.
    
    This interface defines the contract that telegram adapters must implement
    to integrate with the application's use cases.
    """
    
    @abstractmethod
    async def send_message(self, chat_id: int, message: str, **kwargs) -> Dict[str, Any]:
        """
        Send a text message to a chat.
        
        Args:
            chat_id: Telegram chat ID
            message: Message text to send
            **kwargs: Additional parameters (parse_mode, reply_markup, etc.)
            
        Returns:
            Dict containing message information
        """
        pass
    
    @abstractmethod
    async def send_voice_message(self, chat_id: int, voice_data: bytes, **kwargs) -> Dict[str, Any]:
        """
        Send a voice message to a chat.
        
        Args:
            chat_id: Telegram chat ID
            voice_data: Voice message data as bytes
            **kwargs: Additional parameters
            
        Returns:
            Dict containing message information
        """
        pass
    
    @abstractmethod
    async def get_bot_info(self) -> Dict[str, Any]:
        """
        Get information about the bot.
        
        Returns:
            Dict containing bot information (id, username, first_name, etc.)
        """
        pass
    
    @abstractmethod
    async def get_chat_info(self, chat_id: int) -> Dict[str, Any]:
        """
        Get information about a chat.
        
        Args:
            chat_id: Telegram chat ID
            
        Returns:
            Dict containing chat information
        """
        pass
    
    @abstractmethod
    async def get_user_info(self, user_id: int) -> Dict[str, Any]:
        """
        Get information about a user.
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            Dict containing user information
        """
        pass
    
    @abstractmethod
    async def set_webhook(self, url: str, **kwargs) -> bool:
        """
        Set webhook for the bot.
        
        Args:
            url: Webhook URL
            **kwargs: Additional webhook parameters
            
        Returns:
            True if webhook was set successfully
        """
        pass
    
    @abstractmethod
    async def delete_webhook(self) -> bool:
        """
        Delete webhook for the bot.
        
        Returns:
            True if webhook was deleted successfully
        """
        pass
    
    @abstractmethod
    async def get_updates(self, offset: Optional[int] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get updates from Telegram.
        
        Args:
            offset: Identifier of the first update to be returned
            limit: Limits the number of updates to be retrieved
            
        Returns:
            List of update objects
        """
        pass
    
    @abstractmethod
    async def answer_callback_query(self, callback_query_id: str, text: Optional[str] = None, **kwargs) -> bool:
        """
        Answer a callback query.
        
        Args:
            callback_query_id: Unique identifier for the query
            text: Text of the notification
            **kwargs: Additional parameters
            
        Returns:
            True if answered successfully
        """
        pass
    
    @abstractmethod
    async def edit_message_text(self, chat_id: int, message_id: int, text: str, **kwargs) -> Dict[str, Any]:
        """
        Edit a text message.
        
        Args:
            chat_id: Telegram chat ID
            message_id: Message ID to edit
            text: New text of the message
            **kwargs: Additional parameters
            
        Returns:
            Dict containing edited message information
        """
        pass
    
    @abstractmethod
    async def delete_message(self, chat_id: int, message_id: int) -> bool:
        """
        Delete a message.
        
        Args:
            chat_id: Telegram chat ID
            message_id: Message ID to delete
            
        Returns:
            True if message was deleted successfully
        """
        pass
    
    @abstractmethod
    async def get_file(self, file_id: str) -> Dict[str, Any]:
        """
        Get file information.
        
        Args:
            file_id: File identifier
            
        Returns:
            Dict containing file information
        """
        pass
    
    @abstractmethod
    async def download_file(self, file_path: str) -> bytes:
        """
        Download a file from Telegram servers.
        
        Args:
            file_path: File path on Telegram servers
            
        Returns:
            File content as bytes
        """
        pass
    
    @abstractmethod
    def configure(self, config: BotConfig) -> None:
        """
        Configure the telegram adapter with bot configuration.
        
        Args:
            config: Bot configuration object
        """
        pass
    
    @abstractmethod
    async def start_polling(self) -> None:
        """Start long polling for updates."""
        pass
    
    @abstractmethod
    async def stop_polling(self) -> None:
        """Stop long polling for updates.""" 
        pass
    
    @abstractmethod
    def is_polling(self) -> bool:
        """Check if polling is active."""
        pass






