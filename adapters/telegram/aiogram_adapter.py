"""
Aiogram implementation of TelegramPort interface.

This adapter provides Telegram Bot API functionality using the aiogram library.
It implements the TelegramPort protocol and handles all Telegram-specific operations.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

from aiogram import Bot
from aiogram.types import Message, CallbackQuery, Update
from aiogram.exceptions import TelegramAPIError

from core.ports.telegram import TelegramPort

logger = logging.getLogger(__name__)


class AiogramTelegramAdapter(TelegramPort):
    """Aiogram-based implementation of TelegramPort interface."""

    def __init__(self, token: str):
        """Initialize the adapter with bot token."""
        self.token = token
        self.bot = Bot(token=token)
        self._is_initialized = False

    async def _ensure_initialized(self) -> None:
        """Ensure the bot is properly initialized."""
        if not self._is_initialized:
            try:
                await self.bot.get_me()
                self._is_initialized = True
                logger.info("Telegram bot adapter initialized successfully")
            except TelegramAPIError as e:
                logger.error(f"Failed to initialize Telegram bot: {e}")
                raise

    async def set_webhook(self, url: str, secret: str | None = None) -> None:
        """Set webhook for the bot."""
        await self._ensure_initialized()
        try:
            await self.bot.set_webhook(url=url, secret_token=secret)
            logger.info(f"Webhook set successfully: {url}")
        except TelegramAPIError as e:
            logger.error(f"Failed to set webhook: {e}")
            raise

    async def send_message(self, chat_id: str, text: str, **opts: Any) -> str:
        """Send text message to chat."""
        await self._ensure_initialized()
        try:
            message = await self.bot.send_message(
                chat_id=chat_id,
                text=text,
                **opts
            )
            logger.info(f"Message sent to {chat_id}: {text[:50]}...")
            return str(message.message_id)
        except TelegramAPIError as e:
            logger.error(f"Failed to send message: {e}")
            raise

    async def send_voice(self, chat_id: str, source: str, **opts: Any) -> str:
        """Send voice message to chat."""
        await self._ensure_initialized()
        try:
            with open(source, 'rb') as audio_file:
                message = await self.bot.send_voice(
                    chat_id=chat_id,
                    voice=audio_file,
                    **opts
                )
            logger.info(f"Voice message sent to {chat_id}: {source}")
            return str(message.message_id)
        except (TelegramAPIError, FileNotFoundError) as e:
            logger.error(f"Failed to send voice message: {e}")
            raise

    async def get_me(self) -> Dict[str, Any]:
        """Get bot information."""
        await self._ensure_initialized()
        try:
            bot_info = await self.bot.get_me()
            return {
                "id": bot_info.id,
                "username": bot_info.username,
                "first_name": bot_info.first_name,
                "can_join_groups": bot_info.can_join_groups,
                "can_read_all_group_messages": bot_info.can_read_all_group_messages,
                "supports_inline_queries": bot_info.supports_inline_queries,
            }
        except TelegramAPIError as e:
            logger.error(f"Failed to get bot info: {e}")
            raise

    @staticmethod
    async def validate_token(token: str) -> bool:
        """Validate Telegram bot token."""
        try:
            test_bot = Bot(token=token)
            await test_bot.get_me()
            await test_bot.session.close()
            return True
        except TelegramAPIError:
            return False

    async def get_updates(self, offset: Optional[int] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get bot updates."""
        await self._ensure_initialized()
        try:
            updates = await self.bot.get_updates(offset=offset, limit=limit)
            return [
                {
                    "update_id": update.update_id,
                    "message": update.message.model_dump() if update.message else None,
                    "callback_query": update.callback_query.model_dump() if update.callback_query else None,
                }
                for update in updates
            ]
        except TelegramAPIError as e:
            logger.error(f"Failed to get updates: {e}")
            raise

    async def answer_callback_query(self, callback_query_id: str, text: str | None = None) -> None:
        """Answer callback query."""
        await self._ensure_initialized()
        try:
            await self.bot.answer_callback_query(
                callback_query_id=callback_query_id,
                text=text
            )
            logger.info(f"Callback query answered: {callback_query_id}")
        except TelegramAPIError as e:
            logger.error(f"Failed to answer callback query: {e}")
            raise

    async def edit_message_text(self, chat_id: str, message_id: str, text: str, **opts: Any) -> None:
        """Edit message text."""
        await self._ensure_initialized()
        try:
            await self.bot.edit_message_text(
                chat_id=chat_id,
                message_id=int(message_id),
                text=text,
                **opts
            )
            logger.info(f"Message edited: {chat_id}:{message_id}")
        except TelegramAPIError as e:
            logger.error(f"Failed to edit message: {e}")
            raise

    async def close(self) -> None:
        """Close bot session."""
        if self._is_initialized:
            await self.bot.session.close()
            self._is_initialized = False
            logger.info("Telegram bot adapter closed")
