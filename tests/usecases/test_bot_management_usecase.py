"""
Tests for BotManagementUseCase.

This module contains tests for the bot management use case
that orchestrates bot domain entities and external adapters.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from core.usecases.bot_management import BotManagementUseCase
from core.domain.bot import Bot, BotConfig, BotStatus


class TestBotManagementUseCase:
    """Test BotManagementUseCase."""

    @pytest.fixture
    def mock_telegram_port(self):
        """Create mock telegram port."""
        mock = Mock()
        mock.validate_token = AsyncMock(return_value=True)
        mock.get_me = AsyncMock(return_value={
            "id": 123456789,
            "username": "test_bot",
            "first_name": "Test Bot"
        })
        return mock

    @pytest.fixture
    def mock_storage_port(self):
        """Create mock storage port."""
        mock = Mock()
        mock.get_bot_config = Mock(return_value=None)
        mock.get_all_bot_configs = Mock(return_value={})
        mock.add_bot_config = Mock()
        mock.update_bot_config = Mock()
        mock.delete_bot_config = Mock()
        mock.get_bot_count = Mock(return_value=0)
        mock.get_running_bot_count = Mock(return_value=0)
        return mock

    @pytest.fixture
    def use_case(self, mock_telegram_port, mock_storage_port):
        """Create use case instance."""
        return BotManagementUseCase(mock_telegram_port, mock_storage_port)

    @pytest.fixture
    def valid_bot_config(self):
        """Create valid bot configuration."""
        return BotConfig(
            name="Test Bot",
            telegram_token="5123456789:ABCdefGHIjklMNOpqrsTUVwxyz",
            openai_api_key="sk-test1234567890abcdefghijklmnopqrstuvwxyz",
            assistant_id="asst_test1234567890abcdefghijklmnopqrstuvwxyz",
        )

    @pytest.mark.asyncio
    async def test_create_bot_success(self, use_case, valid_bot_config, mock_storage_port):
        """Test successful bot creation."""
        # Act
        bot = await use_case.create_bot(valid_bot_config)

        # Assert
        assert bot is not None
        assert bot.id == 1
        assert bot.config.name == "Test Bot"
        assert bot.status == BotStatus.STOPPED
        mock_storage_port.add_bot_config.assert_called_once_with(1, bot.to_dict())

    @pytest.mark.asyncio
    async def test_create_bot_invalid_config(self, use_case):
        """Test bot creation with invalid configuration."""
        # Arrange
        invalid_config = BotConfig(
            name="",  # Invalid: empty name
            telegram_token="invalid_token",
            openai_api_key="invalid_key",
            assistant_id="invalid_assistant",
        )

        # Act & Assert
        with pytest.raises(ValueError, match="Invalid bot configuration"):
            await use_case.create_bot(invalid_config)

    @pytest.mark.asyncio
    async def test_create_bot_invalid_token(self, use_case, valid_bot_config, mock_telegram_port):
        """Test bot creation with invalid token."""
        # Arrange
        mock_telegram_port.validate_token = AsyncMock(return_value=False)

        # Act & Assert
        with pytest.raises(ValueError, match="Invalid Telegram token"):
            await use_case.create_bot(valid_bot_config)

    def test_get_bot_success(self, use_case, mock_storage_port):
        """Test getting bot by ID."""
        # Arrange
        bot_data = {
            "config": {
                "name": "Test Bot",
                "telegram_token": "5123456789:ABCdefGHIjklMNOpqrsTUVwxyz",
                "openai_api_key": "sk-test1234567890abcdefghijklmnopqrstuvwxyz",
                "assistant_id": "asst_test1234567890abcdefghijklmnopqrstuvwxyz",
                "group_context_limit": 15,
                "enable_ai_responses": True,
                "enable_voice_responses": False,
                "voice_model": "tts-1",
                "voice_type": "alloy",
            },
            "status": "stopped",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "last_error": None,
            "message_count": 0,
            "voice_message_count": 0,
        }
        mock_storage_port.get_bot_config.return_value = bot_data

        # Act
        bot = use_case.get_bot(1)

        # Assert
        assert bot is not None
        assert bot.id == 1
        assert bot.config.name == "Test Bot"
        mock_storage_port.get_bot_config.assert_called_once_with(1)

    def test_get_bot_not_found(self, use_case, mock_storage_port):
        """Test getting non-existent bot."""
        # Arrange
        mock_storage_port.get_bot_config.return_value = None

        # Act
        bot = use_case.get_bot(999)

        # Assert
        assert bot is None

    def test_get_all_bots(self, use_case, mock_storage_port):
        """Test getting all bots."""
        # Arrange
        bots_data = {
            1: {
                "config": {
                    "name": "Bot 1",
                    "telegram_token": "5123456789:ABCdefGHIjklMNOpqrsTUVwxyz",
                    "openai_api_key": "sk-test1234567890abcdefghijklmnopqrstuvwxyz",
                    "assistant_id": "asst_test1234567890abcdefghijklmnopqrstuvwxyz",
                    "group_context_limit": 15,
                    "enable_ai_responses": True,
                    "enable_voice_responses": False,
                    "voice_model": "tts-1",
                    "voice_type": "alloy",
                },
                "status": "running",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "last_error": None,
                "message_count": 10,
                "voice_message_count": 2,
            },
            2: {
                "config": {
                    "name": "Bot 2",
                    "telegram_token": "5123456789:DEFdefGHIjklMNOpqrsTUVwxyz",
                    "openai_api_key": "sk-test1234567890abcdefghijklmnopqrstuvwxyz",
                    "assistant_id": "asst_test1234567890abcdefghijklmnopqrstuvwxyz",
                    "group_context_limit": 15,
                    "enable_ai_responses": True,
                    "enable_voice_responses": False,
                    "voice_model": "tts-1",
                    "voice_type": "alloy",
                },
                "status": "stopped",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "last_error": None,
                "message_count": 5,
                "voice_message_count": 0,
            }
        }
        mock_storage_port.get_all_bot_configs.return_value = bots_data

        # Act
        bots = use_case.get_all_bots()

        # Assert
        assert len(bots) == 2
        assert bots[0].id == 1
        assert bots[0].config.name == "Bot 1"
        assert bots[0].status == BotStatus.RUNNING
        assert bots[1].id == 2
        assert bots[1].config.name == "Bot 2"
        assert bots[1].status == BotStatus.STOPPED

    @pytest.mark.asyncio
    async def test_update_bot_success(self, use_case, valid_bot_config, mock_storage_port):
        """Test successful bot update."""
        # Arrange
        existing_bot_data = {
            "config": {
                "name": "Old Bot",
                "telegram_token": "5123456789:ABCdefGHIjklMNOpqrsTUVwxyz",
                "openai_api_key": "sk-test1234567890abcdefghijklmnopqrstuvwxyz",
                "assistant_id": "asst_test1234567890abcdefghijklmnopqrstuvwxyz",
                "group_context_limit": 15,
                "enable_ai_responses": True,
                "enable_voice_responses": False,
                "voice_model": "tts-1",
                "voice_type": "alloy",
            },
            "status": "stopped",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "last_error": None,
            "message_count": 0,
            "voice_message_count": 0,
        }
        mock_storage_port.get_bot_config.return_value = existing_bot_data

        # Act
        updated_bot = await use_case.update_bot(1, valid_bot_config)

        # Assert
        assert updated_bot is not None
        assert updated_bot.config.name == "Test Bot"
        mock_storage_port.update_bot_config.assert_called_once_with(1, updated_bot.to_dict())

    @pytest.mark.asyncio
    async def test_update_bot_not_found(self, use_case, valid_bot_config, mock_storage_port):
        """Test updating non-existent bot."""
        # Arrange
        mock_storage_port.get_bot_config.return_value = None

        # Act & Assert
        with pytest.raises(ValueError, match="Bot 999 not found"):
            await use_case.update_bot(999, valid_bot_config)

    def test_delete_bot_success(self, use_case, mock_storage_port):
        """Test successful bot deletion."""
        # Arrange
        existing_bot_data = {
            "config": {
                "name": "Test Bot",
                "telegram_token": "5123456789:ABCdefGHIjklMNOpqrsTUVwxyz",
                "openai_api_key": "sk-test1234567890abcdefghijklmnopqrstuvwxyz",
                "assistant_id": "asst_test1234567890abcdefghijklmnopqrstuvwxyz",
                "group_context_limit": 15,
                "enable_ai_responses": True,
                "enable_voice_responses": False,
                "voice_model": "tts-1",
                "voice_type": "alloy",
            },
            "status": "stopped",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "last_error": None,
            "message_count": 0,
            "voice_message_count": 0,
        }
        mock_storage_port.get_bot_config.return_value = existing_bot_data

        # Act
        success = use_case.delete_bot(1)

        # Assert
        assert success is True
        mock_storage_port.delete_bot_config.assert_called_once_with(1)

    def test_delete_bot_not_found(self, use_case, mock_storage_port):
        """Test deleting non-existent bot."""
        # Arrange
        mock_storage_port.get_bot_config.return_value = None

        # Act
        success = use_case.delete_bot(999)

        # Assert
        assert success is False

    def test_start_bot_success(self, use_case, mock_storage_port):
        """Test successful bot start."""
        # Arrange
        existing_bot_data = {
            "config": {
                "name": "Test Bot",
                "telegram_token": "5123456789:ABCdefGHIjklMNOpqrsTUVwxyz",
                "openai_api_key": "sk-test1234567890abcdefghijklmnopqrstuvwxyz",
                "assistant_id": "asst_test1234567890abcdefghijklmnopqrstuvwxyz",
                "group_context_limit": 15,
                "enable_ai_responses": True,
                "enable_voice_responses": False,
                "voice_model": "tts-1",
                "voice_type": "alloy",
            },
            "status": "stopped",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "last_error": None,
            "message_count": 0,
            "voice_message_count": 0,
        }
        mock_storage_port.get_bot_config.return_value = existing_bot_data

        # Act
        success = use_case.start_bot(1)

        # Assert
        assert success is True
        mock_storage_port.update_bot_config.assert_called_once()

    def test_stop_bot_success(self, use_case, mock_storage_port):
        """Test successful bot stop."""
        # Arrange
        existing_bot_data = {
            "config": {
                "name": "Test Bot",
                "telegram_token": "5123456789:ABCdefGHIjklMNOpqrsTUVwxyz",
                "openai_api_key": "sk-test1234567890abcdefghijklmnopqrstuvwxyz",
                "assistant_id": "asst_test1234567890abcdefghijklmnopqrstuvwxyz",
                "group_context_limit": 15,
                "enable_ai_responses": True,
                "enable_voice_responses": False,
                "voice_model": "tts-1",
                "voice_type": "alloy",
            },
            "status": "running",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "last_error": None,
            "message_count": 10,
            "voice_message_count": 2,
        }
        mock_storage_port.get_bot_config.return_value = existing_bot_data

        # Act
        success = use_case.stop_bot(1)

        # Assert
        assert success is True
        mock_storage_port.update_bot_config.assert_called_once()

    def test_restart_bot_success(self, use_case, mock_storage_port):
        """Test successful bot restart."""
        # Arrange
        # First call returns running bot, second call returns stopped bot
        running_bot_data = {
            "config": {
                "name": "Test Bot",
                "telegram_token": "5123456789:ABCdefGHIjklMNOpqrsTUVwxyz",
                "openai_api_key": "sk-test1234567890abcdefghijklmnopqrstuvwxyz",
                "assistant_id": "asst_test1234567890abcdefghijklmnopqrstuvwxyz",
                "group_context_limit": 15,
                "enable_ai_responses": True,
                "enable_voice_responses": False,
                "voice_model": "tts-1",
                "voice_type": "alloy",
            },
            "status": "running",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "last_error": None,
            "message_count": 10,
            "voice_message_count": 2,
        }
        stopped_bot_data = {
            "config": {
                "name": "Test Bot",
                "telegram_token": "5123456789:ABCdefGHIjklMNOpqrsTUVwxyz",
                "openai_api_key": "sk-test1234567890abcdefghijklmnopqrstuvwxyz",
                "assistant_id": "asst_test1234567890abcdefghijklmnopqrstuvwxyz",
                "group_context_limit": 15,
                "enable_ai_responses": True,
                "enable_voice_responses": False,
                "voice_model": "tts-1",
                "voice_type": "alloy",
            },
            "status": "stopped",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "last_error": None,
            "message_count": 10,
            "voice_message_count": 2,
        }
        
        # Configure mock to return different data on subsequent calls
        mock_storage_port.get_bot_config.side_effect = [running_bot_data, stopped_bot_data]

        # Act
        success = use_case.restart_bot(1)

        # Assert
        assert success is True
        # Should be called twice: once for stop, once for start
        assert mock_storage_port.update_bot_config.call_count == 2

    @pytest.mark.asyncio
    async def test_get_bot_status_success(self, use_case, mock_storage_port, mock_telegram_port):
        """Test getting bot status."""
        # Arrange
        existing_bot_data = {
            "config": {
                "name": "Test Bot",
                "telegram_token": "5123456789:ABCdefGHIjklMNOpqrsTUVwxyz",
                "openai_api_key": "sk-test1234567890abcdefghijklmnopqrstuvwxyz",
                "assistant_id": "asst_test1234567890abcdefghijklmnopqrstuvwxyz",
                "group_context_limit": 15,
                "enable_ai_responses": True,
                "enable_voice_responses": False,
                "voice_model": "tts-1",
                "voice_type": "alloy",
            },
            "status": "running",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "last_error": None,
            "message_count": 10,
            "voice_message_count": 2,
        }
        mock_storage_port.get_bot_config.return_value = existing_bot_data

        # Act
        status = await use_case.get_bot_status(1)

        # Assert
        assert status is not None
        assert status["id"] == 1
        assert status["name"] == "Test Bot"
        assert status["status"] == "running"
        assert status["message_count"] == 10
        assert status["voice_message_count"] == 2
        assert status["telegram_info"] is not None

    def test_get_running_bots(self, use_case, mock_storage_port):
        """Test getting running bots."""
        # Arrange
        bots_data = {
            1: {
                "config": {
                    "name": "Bot 1",
                    "telegram_token": "5123456789:ABCdefGHIjklMNOpqrsTUVwxyz",
                    "openai_api_key": "sk-test1234567890abcdefghijklmnopqrstuvwxyz",
                    "assistant_id": "asst_test1234567890abcdefghijklmnopqrstuvwxyz",
                    "group_context_limit": 15,
                    "enable_ai_responses": True,
                    "enable_voice_responses": False,
                    "voice_model": "tts-1",
                    "voice_type": "alloy",
                },
                "status": "running",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "last_error": None,
                "message_count": 10,
                "voice_message_count": 2,
            },
            2: {
                "config": {
                    "name": "Bot 2",
                    "telegram_token": "5123456789:DEFdefGHIjklMNOpqrsTUVwxyz",
                    "openai_api_key": "sk-test1234567890abcdefghijklmnopqrstuvwxyz",
                    "assistant_id": "asst_test1234567890abcdefghijklmnopqrstuvwxyz",
                    "group_context_limit": 15,
                    "enable_ai_responses": True,
                    "enable_voice_responses": False,
                    "voice_model": "tts-1",
                    "voice_type": "alloy",
                },
                "status": "stopped",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "last_error": None,
                "message_count": 5,
                "voice_message_count": 0,
            }
        }
        mock_storage_port.get_all_bot_configs.return_value = bots_data

        # Act
        running_bots = use_case.get_running_bots()

        # Assert
        assert len(running_bots) == 1
        assert running_bots[0].id == 1
        assert running_bots[0].status == BotStatus.RUNNING

    def test_get_stopped_bots(self, use_case, mock_storage_port):
        """Test getting stopped bots."""
        # Arrange
        bots_data = {
            1: {
                "config": {
                    "name": "Bot 1",
                    "telegram_token": "5123456789:ABCdefGHIjklMNOpqrsTUVwxyz",
                    "openai_api_key": "sk-test1234567890abcdefghijklmnopqrstuvwxyz",
                    "assistant_id": "asst_test1234567890abcdefghijklmnopqrstuvwxyz",
                    "group_context_limit": 15,
                    "enable_ai_responses": True,
                    "enable_voice_responses": False,
                    "voice_model": "tts-1",
                    "voice_type": "alloy",
                },
                "status": "running",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "last_error": None,
                "message_count": 10,
                "voice_message_count": 2,
            },
            2: {
                "config": {
                    "name": "Bot 2",
                    "telegram_token": "5123456789:DEFdefGHIjklMNOpqrsTUVwxyz",
                    "openai_api_key": "sk-test1234567890abcdefghijklmnopqrstuvwxyz",
                    "assistant_id": "asst_test1234567890abcdefghijklmnopqrstuvwxyz",
                    "group_context_limit": 15,
                    "enable_ai_responses": True,
                    "enable_voice_responses": False,
                    "voice_model": "tts-1",
                    "voice_type": "alloy",
                },
                "status": "stopped",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "last_error": None,
                "message_count": 5,
                "voice_message_count": 0,
            }
        }
        mock_storage_port.get_all_bot_configs.return_value = bots_data

        # Act
        stopped_bots = use_case.get_stopped_bots()

        # Assert
        assert len(stopped_bots) == 1
        assert stopped_bots[0].id == 2
        assert stopped_bots[0].status == BotStatus.STOPPED

    def test_get_bot_count(self, use_case, mock_storage_port):
        """Test getting bot count."""
        # Arrange
        mock_storage_port.get_bot_count.return_value = 5

        # Act
        count = use_case.get_bot_count()

        # Assert
        assert count == 5
        mock_storage_port.get_bot_count.assert_called_once()

    def test_get_running_bot_count(self, use_case, mock_storage_port):
        """Test getting running bot count."""
        # Arrange
        mock_storage_port.get_running_bot_count.return_value = 3

        # Act
        count = use_case.get_running_bot_count()

        # Assert
        assert count == 3
        mock_storage_port.get_running_bot_count.assert_called_once()
