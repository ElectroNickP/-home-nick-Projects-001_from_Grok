"""
Bot management use cases.

This module contains business logic for managing Telegram bots,
including creation, configuration, starting, stopping, and monitoring.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from core.domain.bot import Bot, BotConfig, BotStatus
from core.ports.telegram import TelegramPort
from core.ports.storage import ConfigStoragePort

logger = logging.getLogger(__name__)


class BotManagementUseCase:
    """Use case for managing Telegram bots."""

    def __init__(
        self,
        telegram_port: TelegramPort,
        storage_port: ConfigStoragePort,
    ):
        """Initialize the use case with required ports."""
        self.telegram_port = telegram_port
        self.storage_port = storage_port

    async def create_bot(self, bot_config: BotConfig) -> Bot:
        """Create a new bot with the given configuration."""
        try:
            # Validate bot configuration
            errors = bot_config.validate()
            if errors:
                raise ValueError(f"Invalid bot configuration: {', '.join(errors)}")

            # Validate Telegram token
            if not await self.telegram_port.validate_token(bot_config.telegram_token):
                raise ValueError("Invalid Telegram token")

            # Generate bot ID
            bot_id = self._generate_bot_id()
            
            # Create bot entity
            bot = Bot(id=bot_id, config=bot_config)
            
            # Save to storage
            self.storage_port.add_bot_config(bot_id, bot.to_dict())
            
            logger.info(f"Bot created successfully: {bot_id} - {bot_config.name}")
            return bot
            
        except Exception as e:
            logger.error(f"Failed to create bot: {e}")
            raise

    def get_bot(self, bot_id: int) -> Optional[Bot]:
        """Get bot by ID."""
        try:
            config_data = self.storage_port.get_bot_config(bot_id)
            if not config_data:
                return None
            
            return Bot.from_dict(bot_id, config_data)
            
        except Exception as e:
            logger.error(f"Failed to get bot {bot_id}: {e}")
            return None

    def get_all_bots(self) -> List[Bot]:
        """Get all bots."""
        try:
            configs = self.storage_port.get_all_bot_configs()
            return [
                Bot.from_dict(bot_id, config_data)
                for bot_id, config_data in configs.items()
            ]
        except Exception as e:
            logger.error(f"Failed to get all bots: {e}")
            return []

    async def update_bot(self, bot_id: int, new_config: BotConfig) -> Optional[Bot]:
        """Update bot configuration."""
        try:
            # Validate new configuration
            errors = new_config.validate()
            if errors:
                raise ValueError(f"Invalid bot configuration: {', '.join(errors)}")

            # Validate Telegram token
            if not await self.telegram_port.validate_token(new_config.telegram_token):
                raise ValueError("Invalid Telegram token")

            # Get existing bot
            bot = self.get_bot(bot_id)
            if not bot:
                raise ValueError(f"Bot {bot_id} not found")

            # Update configuration
            bot.update_config(new_config)
            
            # Save to storage
            self.storage_port.update_bot_config(bot_id, bot.to_dict())
            
            logger.info(f"Bot {bot_id} updated successfully")
            return bot
            
        except Exception as e:
            logger.error(f"Failed to update bot {bot_id}: {e}")
            raise

    def delete_bot(self, bot_id: int) -> bool:
        """Delete bot by ID."""
        try:
            # Check if bot exists
            bot = self.get_bot(bot_id)
            if not bot:
                return False

            # Stop bot if running
            if bot.is_running():
                self.stop_bot(bot_id)

            # Delete from storage
            self.storage_port.delete_bot_config(bot_id)
            
            logger.info(f"Bot {bot_id} deleted successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete bot {bot_id}: {e}")
            return False

    def start_bot(self, bot_id: int) -> bool:
        """Start a bot."""
        try:
            bot = self.get_bot(bot_id)
            if not bot:
                raise ValueError(f"Bot {bot_id} not found")

            if bot.is_running():
                logger.warning(f"Bot {bot_id} is already running")
                return True

            # Start the bot
            bot.start()
            
            # Save updated status
            self.storage_port.update_bot_config(bot_id, bot.to_dict())
            
            logger.info(f"Bot {bot_id} started successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start bot {bot_id}: {e}")
            return False

    def stop_bot(self, bot_id: int) -> bool:
        """Stop a bot."""
        try:
            bot = self.get_bot(bot_id)
            if not bot:
                raise ValueError(f"Bot {bot_id} not found")

            if not bot.is_running():
                logger.warning(f"Bot {bot_id} is already stopped")
                return True

            # Stop the bot
            bot.stop()
            
            # Save updated status
            self.storage_port.update_bot_config(bot_id, bot.to_dict())
            
            logger.info(f"Bot {bot_id} stopped successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop bot {bot_id}: {e}")
            return False

    def restart_bot(self, bot_id: int) -> bool:
        """Restart a bot."""
        try:
            # Stop bot
            if not self.stop_bot(bot_id):
                return False

            # Start bot
            return self.start_bot(bot_id)
            
        except Exception as e:
            logger.error(f"Failed to restart bot {bot_id}: {e}")
            return False

    async def get_bot_status(self, bot_id: int) -> Optional[Dict[str, Any]]:
        """Get detailed bot status."""
        try:
            bot = self.get_bot(bot_id)
            if not bot:
                return None

            # Get bot info from Telegram
            try:
                bot_info = await self.telegram_port.get_me()
            except Exception as e:
                logger.warning(f"Failed to get Telegram bot info: {e}")
                bot_info = None

            return {
                "id": bot.id,
                "name": bot.config.name,
                "status": bot.status.value,
                "created_at": bot.created_at.isoformat(),
                "updated_at": bot.updated_at.isoformat(),
                "last_error": bot.last_error,
                "message_count": bot.message_count,
                "voice_message_count": bot.voice_message_count,
                "telegram_info": bot_info,
            }
            
        except Exception as e:
            logger.error(f"Failed to get bot status {bot_id}: {e}")
            return None

    def get_running_bots(self) -> List[Bot]:
        """Get all running bots."""
        return [bot for bot in self.get_all_bots() if bot.is_running()]

    def get_stopped_bots(self) -> List[Bot]:
        """Get all stopped bots."""
        return [bot for bot in self.get_all_bots() if not bot.is_running()]

    def get_bot_count(self) -> int:
        """Get total number of bots."""
        return self.storage_port.get_bot_count()

    def get_running_bot_count(self) -> int:
        """Get number of running bots."""
        return self.storage_port.get_running_bot_count()

    def _generate_bot_id(self) -> int:
        """Generate a unique bot ID."""
        existing_bots = self.get_all_bots()
        if not existing_bots:
            return 1
        
        max_id = max(bot.id for bot in existing_bots)
        return max_id + 1
