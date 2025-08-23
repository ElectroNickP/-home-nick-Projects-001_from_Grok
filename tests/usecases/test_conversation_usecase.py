"""
Tests for ConversationUseCase.

This module contains tests for the conversation use case
that orchestrates conversation domain entities and external adapters.
"""

import pytest
from unittest.mock import Mock, AsyncMock
from datetime import datetime

from core.usecases.conversation import ConversationUseCase
from core.domain.conversation import Conversation, ConversationKey, Message


class TestConversationUseCase:
    """Test ConversationUseCase."""

    @pytest.fixture
    def mock_storage_port(self):
        """Create mock storage port."""
        mock = Mock()
        # Create a simple in-memory cache for testing
        cache = {}
        
        def get_conversation_cache(key):
            return cache.get(key)
        
        def set_conversation_cache(key, data):
            cache[key] = data
        
        def clear_conversation_cache(key):
            if key in cache:
                del cache[key]
        
        mock.get_conversation_cache = Mock(side_effect=get_conversation_cache)
        mock.set_conversation_cache = Mock(side_effect=set_conversation_cache)
        mock.clear_conversation_cache = Mock(side_effect=clear_conversation_cache)
        return mock

    @pytest.fixture
    def use_case(self, mock_storage_port):
        """Create use case instance."""
        return ConversationUseCase(mock_storage_port)

    @pytest.fixture
    def conversation_key(self):
        """Create conversation key."""
        return ConversationKey(bot_id=1, chat_id="123456789")

    @pytest.fixture
    def sample_conversation_data(self):
        """Create sample conversation data."""
        return {
            "key": "1:123456789",
            "messages": [
                {
                    "role": "user",
                    "content": "Hello",
                    "timestamp": datetime.now().isoformat()
                },
                {
                    "role": "assistant",
                    "content": "Hi there!",
                    "timestamp": datetime.now().isoformat()
                }
            ],
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "message_count": 2
        }

    def test_get_conversation_existing(self, use_case, mock_storage_port, conversation_key, sample_conversation_data):
        """Test getting existing conversation."""
        # Arrange
        # Set up the cache with existing conversation data
        mock_storage_port.set_conversation_cache(str(conversation_key), sample_conversation_data)

        # Act
        conversation = use_case.get_conversation(conversation_key)

        # Assert
        assert conversation is not None
        assert conversation.key == conversation_key
        assert len(conversation.messages) == 2
        assert conversation.message_count == 2
        mock_storage_port.get_conversation_cache.assert_called_with("1:123456789")

    def test_get_conversation_new(self, use_case, mock_storage_port, conversation_key):
        """Test getting new conversation."""
        # Arrange
        mock_storage_port.get_conversation_cache.return_value = None

        # Act
        conversation = use_case.get_conversation(conversation_key)

        # Assert
        assert conversation is not None
        assert conversation.key == conversation_key
        assert len(conversation.messages) == 0
        assert conversation.message_count == 0
        assert conversation.is_empty()

    def test_add_user_message(self, use_case, mock_storage_port, conversation_key):
        """Test adding user message to conversation."""
        # Arrange
        mock_storage_port.get_conversation_cache.return_value = None

        # Act
        use_case.add_user_message(conversation_key, "Hello, bot!")

        # Assert
        # Get the conversation after adding message
        conversation = use_case.get_conversation(conversation_key)
        assert len(conversation.messages) == 1
        assert conversation.messages[0].role == "user"
        assert conversation.messages[0].content == "Hello, bot!"
        assert conversation.message_count == 1
        mock_storage_port.set_conversation_cache.assert_called()

    def test_add_assistant_message(self, use_case, mock_storage_port, conversation_key):
        """Test adding assistant message to conversation."""
        # Arrange
        mock_storage_port.get_conversation_cache.return_value = None

        # Act
        use_case.add_assistant_message(conversation_key, "Hello, user!")

        # Assert
        # Get the conversation after adding message
        conversation = use_case.get_conversation(conversation_key)
        assert len(conversation.messages) == 1
        assert conversation.messages[0].role == "assistant"
        assert conversation.messages[0].content == "Hello, user!"
        assert conversation.message_count == 1
        mock_storage_port.set_conversation_cache.assert_called()

    def test_get_recent_messages(self, use_case, mock_storage_port, conversation_key, sample_conversation_data):
        """Test getting recent messages from conversation."""
        # Arrange
        # Set up the cache with existing conversation data
        mock_storage_port.set_conversation_cache(str(conversation_key), sample_conversation_data)

        # Act
        recent_messages = use_case.get_recent_messages(conversation_key, limit=1)

        # Assert
        assert len(recent_messages) == 1
        assert recent_messages[0].role == "assistant"
        assert recent_messages[0].content == "Hi there!"

    def test_get_context_for_ai(self, use_case, mock_storage_port, conversation_key, sample_conversation_data):
        """Test getting conversation context formatted for AI processing."""
        # Arrange
        # Set up the cache with existing conversation data
        mock_storage_port.set_conversation_cache(str(conversation_key), sample_conversation_data)

        # Act
        context = use_case.get_context_for_ai(conversation_key, limit=10)

        # Assert
        assert len(context) == 2
        assert context[0]["role"] == "user"
        assert context[0]["content"] == "Hello"
        assert context[1]["role"] == "assistant"
        assert context[1]["content"] == "Hi there!"

    def test_clear_conversation(self, use_case, mock_storage_port, conversation_key, sample_conversation_data):
        """Test clearing conversation."""
        # Arrange
        mock_storage_port.get_conversation_cache.return_value = sample_conversation_data

        # Act
        use_case.clear_conversation(conversation_key)

        # Assert
        # Get the conversation after clearing
        conversation = use_case.get_conversation(conversation_key)
        assert len(conversation.messages) == 0
        assert conversation.message_count == 0
        assert conversation.is_empty()
        mock_storage_port.set_conversation_cache.assert_called()

    def test_get_last_message(self, use_case, mock_storage_port, conversation_key, sample_conversation_data):
        """Test getting last message from conversation."""
        # Arrange
        # Set up the cache with existing conversation data
        mock_storage_port.set_conversation_cache(str(conversation_key), sample_conversation_data)

        # Act
        last_message = use_case.get_last_message(conversation_key)

        # Assert
        assert last_message is not None
        assert last_message.role == "assistant"
        assert last_message.content == "Hi there!"

    def test_get_last_user_message(self, use_case, mock_storage_port, conversation_key, sample_conversation_data):
        """Test getting last user message from conversation."""
        # Arrange
        # Set up the cache with existing conversation data
        mock_storage_port.set_conversation_cache(str(conversation_key), sample_conversation_data)

        # Act
        last_user_message = use_case.get_last_user_message(conversation_key)

        # Assert
        assert last_user_message is not None
        assert last_user_message.role == "user"
        assert last_user_message.content == "Hello"

    def test_get_last_assistant_message(self, use_case, mock_storage_port, conversation_key, sample_conversation_data):
        """Test getting last assistant message from conversation."""
        # Arrange
        # Set up the cache with existing conversation data
        mock_storage_port.set_conversation_cache(str(conversation_key), sample_conversation_data)

        # Act
        last_assistant_message = use_case.get_last_assistant_message(conversation_key)

        # Assert
        assert last_assistant_message is not None
        assert last_assistant_message.role == "assistant"
        assert last_assistant_message.content == "Hi there!"

    def test_get_last_message_empty_conversation(self, use_case, mock_storage_port, conversation_key):
        """Test getting last message from empty conversation."""
        # Arrange
        mock_storage_port.get_conversation_cache.return_value = None

        # Act
        conversation = use_case.get_conversation(conversation_key)
        last_message = use_case.get_last_message(conversation_key)

        # Assert
        assert last_message is None

    def test_get_last_user_message_empty_conversation(self, use_case, mock_storage_port, conversation_key):
        """Test getting last user message from empty conversation."""
        # Arrange
        mock_storage_port.get_conversation_cache.return_value = None

        # Act
        conversation = use_case.get_conversation(conversation_key)
        last_user_message = use_case.get_last_user_message(conversation_key)

        # Assert
        assert last_user_message is None

    def test_get_last_assistant_message_empty_conversation(self, use_case, mock_storage_port, conversation_key):
        """Test getting last assistant message from empty conversation."""
        # Arrange
        mock_storage_port.get_conversation_cache.return_value = None

        # Act
        conversation = use_case.get_conversation(conversation_key)
        last_assistant_message = use_case.get_last_assistant_message(conversation_key)

        # Assert
        assert last_assistant_message is None

    def test_conversation_persistence(self, use_case, mock_storage_port, conversation_key):
        """Test that conversation changes are persisted to storage."""
        # Arrange
        mock_storage_port.get_conversation_cache.return_value = None

        # Act
        conversation = use_case.get_conversation(conversation_key)
        use_case.add_user_message(conversation_key, "Test message")

        # Assert
        mock_storage_port.set_conversation_cache.assert_called_once()
        call_args = mock_storage_port.set_conversation_cache.call_args
        assert call_args[0][0] == "1:123456789"  # conversation key
        assert call_args[0][1]["message_count"] == 1

    def test_conversation_key_from_string(self, use_case, mock_storage_port):
        """Test creating conversation key from string."""
        # Arrange
        mock_storage_port.get_conversation_cache.return_value = None

        # Act
        conversation_key = ConversationKey.from_string("1:123456789")
        conversation = use_case.get_conversation(conversation_key)

        # Assert
        assert conversation_key.bot_id == 1
        assert conversation_key.chat_id == "123456789"
        assert str(conversation_key) == "1:123456789"

    def test_conversation_key_invalid_format(self, use_case, mock_storage_port):
        """Test creating conversation key from invalid string."""
        # Act & Assert
        with pytest.raises(ValueError, match="Invalid conversation key format"):
            ConversationKey.from_string("invalid_format")

    def test_conversation_with_multiple_messages(self, use_case, mock_storage_port, conversation_key):
        """Test conversation with multiple messages."""
        # Arrange
        mock_storage_port.get_conversation_cache.return_value = None

        # Act
        use_case.add_user_message(conversation_key, "Message 1")
        use_case.add_assistant_message(conversation_key, "Response 1")
        use_case.add_user_message(conversation_key, "Message 2")
        use_case.add_assistant_message(conversation_key, "Response 2")

        # Assert
        # Get the conversation after adding messages
        conversation = use_case.get_conversation(conversation_key)
        assert len(conversation.messages) == 4
        assert conversation.message_count == 4
        assert conversation.messages[0].content == "Message 1"
        assert conversation.messages[1].content == "Response 1"
        assert conversation.messages[2].content == "Message 2"
        assert conversation.messages[3].content == "Response 2"

    def test_get_recent_messages_with_limit(self, use_case, mock_storage_port, conversation_key):
        """Test getting recent messages with specific limit."""
        # Arrange
        mock_storage_port.get_conversation_cache.return_value = None

        # Act
        for i in range(10):
            use_case.add_user_message(conversation_key, f"Message {i}")
            use_case.add_assistant_message(conversation_key, f"Response {i}")

        recent_messages = use_case.get_recent_messages(conversation_key, limit=5)

        # Assert
        assert len(recent_messages) == 5
        # We have 20 messages total (10 pairs): Message 0, Response 0, ..., Message 9, Response 9
        # The last 5 messages (indices 15-19) are: Response 7, Message 8, Response 8, Message 9, Response 9
        assert recent_messages[0].content == "Response 7"
        assert recent_messages[1].content == "Message 8"
        assert recent_messages[2].content == "Response 8"
        assert recent_messages[3].content == "Message 9"
        assert recent_messages[4].content == "Response 9"

    def test_conversation_timestamps(self, use_case, mock_storage_port, conversation_key):
        """Test that conversation timestamps are properly set."""
        # Arrange
        mock_storage_port.get_conversation_cache.return_value = None

        # Act
        conversation = use_case.get_conversation(conversation_key)
        use_case.add_user_message(conversation_key, "Test message")

        # Assert
        assert conversation.created_at is not None
        assert conversation.updated_at is not None
        assert conversation.updated_at >= conversation.created_at

    def test_conversation_to_dict(self, use_case, mock_storage_port, conversation_key):
        """Test converting conversation to dictionary."""
        # Arrange
        mock_storage_port.get_conversation_cache.return_value = None

        # Act
        use_case.add_user_message(conversation_key, "Test message")
        conversation = use_case.get_conversation(conversation_key)
        conversation_dict = conversation.to_dict()

        # Assert
        assert conversation_dict["key"] == "1:123456789"
        assert len(conversation_dict["messages"]) == 1
        assert conversation_dict["message_count"] == 1
        assert "created_at" in conversation_dict
        assert "updated_at" in conversation_dict
