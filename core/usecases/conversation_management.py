"""
Conversation management use cases.

This module contains business logic for managing conversations
between users and bots, including message history and context.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from core.domain.conversation import Conversation, Message, ConversationKey
from core.ports.storage import ConfigStoragePort

logger = logging.getLogger(__name__)


class ConversationManagementUseCase:
    """Use case for managing conversations."""

    def __init__(self, storage_port: ConfigStoragePort):
        """Initialize the use case with required ports."""
        self.storage_port = storage_port

    def get_conversation(self, bot_id: int, chat_id: str) -> Optional[Conversation]:
        """Get conversation by bot ID and chat ID."""
        try:
            key = ConversationKey(bot_id=bot_id, chat_id=chat_id)
            conversation_key = str(key)
            
            cache_data = self.storage_port.get_conversation_cache(conversation_key)
            if not cache_data:
                return None
            
            return Conversation.from_dict(cache_data)
            
        except Exception as e:
            logger.error(f"Failed to get conversation {bot_id}:{chat_id}: {e}")
            return None

    def create_conversation(self, bot_id: int, chat_id: str) -> Conversation:
        """Create a new conversation."""
        try:
            key = ConversationKey(bot_id=bot_id, chat_id=chat_id)
            conversation = Conversation(key=key)
            
            # Save to cache
            self.storage_port.set_conversation_cache(str(key), conversation.to_dict())
            
            logger.info(f"Conversation created: {bot_id}:{chat_id}")
            return conversation
            
        except Exception as e:
            logger.error(f"Failed to create conversation {bot_id}:{chat_id}: {e}")
            raise

    def add_message(self, bot_id: int, chat_id: str, role: str, content: str) -> bool:
        """Add a message to conversation."""
        try:
            conversation = self.get_conversation(bot_id, chat_id)
            if not conversation:
                conversation = self.create_conversation(bot_id, chat_id)
            
            conversation.add_message(role, content)
            
            # Save to cache
            self.storage_port.set_conversation_cache(
                str(conversation.key), 
                conversation.to_dict()
            )
            
            logger.debug(f"Message added to conversation {bot_id}:{chat_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add message to conversation {bot_id}:{chat_id}: {e}")
            return False

    def add_user_message(self, bot_id: int, chat_id: str, content: str) -> bool:
        """Add a user message to conversation."""
        return self.add_message(bot_id, chat_id, "user", content)

    def add_assistant_message(self, bot_id: int, chat_id: str, content: str) -> bool:
        """Add an assistant message to conversation."""
        return self.add_message(bot_id, chat_id, "assistant", content)

    def get_conversation_context(self, bot_id: int, chat_id: str, limit: int = 15) -> List[Dict[str, str]]:
        """Get conversation context for AI processing."""
        try:
            conversation = self.get_conversation(bot_id, chat_id)
            if not conversation:
                return []
            
            return conversation.get_context_for_ai(limit)
            
        except Exception as e:
            logger.error(f"Failed to get conversation context {bot_id}:{chat_id}: {e}")
            return []

    def get_recent_messages(self, bot_id: int, chat_id: str, limit: int = 10) -> List[Message]:
        """Get recent messages from conversation."""
        try:
            conversation = self.get_conversation(bot_id, chat_id)
            if not conversation:
                return []
            
            return conversation.get_recent_messages(limit)
            
        except Exception as e:
            logger.error(f"Failed to get recent messages {bot_id}:{chat_id}: {e}")
            return []

    def clear_conversation(self, bot_id: int, chat_id: str) -> bool:
        """Clear all messages from conversation."""
        try:
            conversation = self.get_conversation(bot_id, chat_id)
            if not conversation:
                return True  # Nothing to clear
            
            conversation.clear_messages()
            
            # Save to cache
            self.storage_port.set_conversation_cache(
                str(conversation.key), 
                conversation.to_dict()
            )
            
            logger.info(f"Conversation cleared: {bot_id}:{chat_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to clear conversation {bot_id}:{chat_id}: {e}")
            return False

    def delete_conversation(self, bot_id: int, chat_id: str) -> bool:
        """Delete conversation completely."""
        try:
            key = ConversationKey(bot_id=bot_id, chat_id=chat_id)
            conversation_key = str(key)
            
            self.storage_port.clear_conversation_cache(conversation_key)
            
            logger.info(f"Conversation deleted: {bot_id}:{chat_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete conversation {bot_id}:{chat_id}: {e}")
            return False

    def get_conversation_stats(self, bot_id: int, chat_id: str) -> Optional[Dict[str, Any]]:
        """Get conversation statistics."""
        try:
            conversation = self.get_conversation(bot_id, chat_id)
            if not conversation:
                return None
            
            return {
                "bot_id": conversation.key.bot_id,
                "chat_id": conversation.key.chat_id,
                "message_count": conversation.message_count,
                "created_at": conversation.created_at.isoformat(),
                "updated_at": conversation.updated_at.isoformat(),
                "is_empty": conversation.is_empty(),
            }
            
        except Exception as e:
            logger.error(f"Failed to get conversation stats {bot_id}:{chat_id}: {e}")
            return None

    def get_all_conversations_for_bot(self, bot_id: int) -> List[Conversation]:
        """Get all conversations for a specific bot."""
        try:
            # This would require additional storage methods to get all conversations
            # For now, we'll return an empty list as this is not implemented in the storage port
            logger.warning("get_all_conversations_for_bot not implemented in storage port")
            return []
            
        except Exception as e:
            logger.error(f"Failed to get conversations for bot {bot_id}: {e}")
            return []

    def cleanup_old_conversations(self, max_age_hours: int = 24) -> int:
        """Clean up old conversations."""
        try:
            # This would require additional storage methods to iterate over all conversations
            # For now, we'll return 0 as this is not implemented in the storage port
            logger.warning("cleanup_old_conversations not implemented in storage port")
            return 0
            
        except Exception as e:
            logger.error(f"Failed to cleanup old conversations: {e}")
            return 0









