"""
Conversation use case.

This module contains the conversation use case that orchestrates
conversation domain entities and external adapters.
"""

import logging
from typing import List, Dict, Any, Optional

from core.domain.conversation import Conversation, ConversationKey, Message
from core.ports.storage import ConfigStoragePort

logger = logging.getLogger(__name__)


class ConversationUseCase:
    """Use case for managing conversations."""

    def __init__(self, storage_port: ConfigStoragePort):
        """Initialize the use case with storage port."""
        self.storage_port = storage_port

    def get_conversation(self, conversation_key: ConversationKey) -> Conversation:
        """Get or create conversation for the given key."""
        try:
            # Try to get existing conversation from cache
            cached_data = self.storage_port.get_conversation_cache(str(conversation_key))
            
            if cached_data:
                conversation = Conversation.from_dict(cached_data)
                logger.debug(f"Retrieved conversation: {conversation_key}")
                return conversation
            else:
                # Create new conversation
                conversation = Conversation(key=conversation_key)
                logger.debug(f"Created new conversation: {conversation_key}")
                return conversation
                
        except Exception as e:
            logger.error(f"Error getting conversation {conversation_key}: {e}")
            # Return new conversation on error
            return Conversation(key=conversation_key)

    def add_user_message(self, conversation_key: ConversationKey, content: str) -> None:
        """Add user message to conversation."""
        try:
            conversation = self.get_conversation(conversation_key)
            conversation.add_user_message(content)
            self._persist_conversation(conversation)
            logger.debug(f"Added user message to {conversation_key}")
        except Exception as e:
            logger.error(f"Error adding user message to {conversation_key}: {e}")

    def add_assistant_message(self, conversation_key: ConversationKey, content: str) -> None:
        """Add assistant message to conversation."""
        try:
            conversation = self.get_conversation(conversation_key)
            conversation.add_assistant_message(content)
            self._persist_conversation(conversation)
            logger.debug(f"Added assistant message to {conversation_key}")
        except Exception as e:
            logger.error(f"Error adding assistant message to {conversation_key}: {e}")

    def get_recent_messages(self, conversation_key: ConversationKey, limit: int = 10) -> List[Message]:
        """Get recent messages from conversation."""
        try:
            conversation = self.get_conversation(conversation_key)
            return conversation.get_recent_messages(limit)
        except Exception as e:
            logger.error(f"Error getting recent messages from {conversation_key}: {e}")
            return []

    def get_context_for_ai(self, conversation_key: ConversationKey, limit: int = 15) -> List[Dict[str, str]]:
        """Get conversation context formatted for AI processing."""
        try:
            conversation = self.get_conversation(conversation_key)
            return conversation.get_context_for_ai(limit)
        except Exception as e:
            logger.error(f"Error getting AI context from {conversation_key}: {e}")
            return []

    def clear_conversation(self, conversation_key: ConversationKey) -> None:
        """Clear all messages from conversation."""
        try:
            conversation = self.get_conversation(conversation_key)
            conversation.clear_messages()
            self._persist_conversation(conversation)
            logger.debug(f"Cleared conversation: {conversation_key}")
        except Exception as e:
            logger.error(f"Error clearing conversation {conversation_key}: {e}")

    def get_last_message(self, conversation_key: ConversationKey) -> Optional[Message]:
        """Get the last message in conversation."""
        try:
            conversation = self.get_conversation(conversation_key)
            return conversation.get_last_message()
        except Exception as e:
            logger.error(f"Error getting last message from {conversation_key}: {e}")
            return None

    def get_last_user_message(self, conversation_key: ConversationKey) -> Optional[Message]:
        """Get the last user message in conversation."""
        try:
            conversation = self.get_conversation(conversation_key)
            return conversation.get_last_user_message()
        except Exception as e:
            logger.error(f"Error getting last user message from {conversation_key}: {e}")
            return None

    def get_last_assistant_message(self, conversation_key: ConversationKey) -> Optional[Message]:
        """Get the last assistant message in conversation."""
        try:
            conversation = self.get_conversation(conversation_key)
            return conversation.get_last_assistant_message()
        except Exception as e:
            logger.error(f"Error getting last assistant message from {conversation_key}: {e}")
            return None

    def _persist_conversation(self, conversation: Conversation) -> None:
        """Persist conversation to storage."""
        try:
            conversation_data = conversation.to_dict()
            self.storage_port.set_conversation_cache(str(conversation.key), conversation_data)
        except Exception as e:
            logger.error(f"Error persisting conversation {conversation.key}: {e}")
