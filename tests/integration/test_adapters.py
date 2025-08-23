"""
Integration tests for adapters.

These tests verify that adapters correctly implement their port interfaces
and work with real external dependencies.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import AsyncMock, patch

from adapters.telegram.aiogram_adapter import AiogramTelegramAdapter
from adapters.storage.json_adapter import JsonConfigStorageAdapter
from adapters.updater.git_adapter import GitAutoUpdaterAdapter

from core.domain.bot import Bot, BotConfig, BotStatus
from core.domain.conversation import Conversation, ConversationKey, Message
from core.domain.config import SystemConfig, AdminBotConfig


class TestJsonConfigStorageAdapter:
    """Test JSON storage adapter."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for tests."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def storage_adapter(self, temp_dir):
        """Create storage adapter for testing."""
        config_file = Path(temp_dir) / "test_config.json"
        backup_dir = Path(temp_dir) / "backups"
        return JsonConfigStorageAdapter(str(config_file), str(backup_dir))
    
    def test_read_write_config(self, storage_adapter):
        """Test reading and writing configuration."""
        # Test initial empty config
        config = storage_adapter.read_config()
        assert "bots" in config
        assert "conversations" in config
        assert "admin_bot" in config
        
        # Test writing config
        test_config = {"test_key": "test_value"}
        storage_adapter.write_config(test_config)
        
        # Test reading updated config
        updated_config = storage_adapter.read_config()
        assert updated_config["test_key"] == "test_value"
    
    def test_bot_config_operations(self, storage_adapter):
        """Test bot configuration operations."""
        bot_id = 1
        bot_config = {
            "name": "Test Bot",
            "telegram_token": "5123456789:ABCdefGHIjklMNOpqrsTUVwxyz",
            "openai_api_key": "sk-test1234567890abcdefghijklmnopqrstuvwxyz",
            "assistant_id": "asst_test1234567890abcdefghijklmnopqrstuvwxyz",
        }
        
        # Test adding bot config
        storage_adapter.add_bot_config(bot_id, bot_config)
        
        # Test getting bot config
        retrieved_config = storage_adapter.get_bot_config(bot_id)
        assert retrieved_config is not None
        assert retrieved_config["name"] == "Test Bot"
        
        # Test updating bot config
        updated_config = bot_config.copy()
        updated_config["name"] = "Updated Bot"
        storage_adapter.update_bot_config(bot_id, updated_config)
        
        retrieved_config = storage_adapter.get_bot_config(bot_id)
        assert retrieved_config["name"] == "Updated Bot"
        
        # Test getting all bot configs
        all_configs = storage_adapter.get_all_bot_configs()
        assert bot_id in all_configs
        assert all_configs[bot_id]["name"] == "Updated Bot"
        
        # Test bot counts
        assert storage_adapter.get_bot_count() == 1
        assert storage_adapter.get_running_bot_count() == 0  # No enabled bots
        
        # Test deleting bot config
        storage_adapter.delete_bot_config(bot_id)
        assert storage_adapter.get_bot_config(bot_id) is None
        assert storage_adapter.get_bot_count() == 0
    
    def test_conversation_cache_operations(self, storage_adapter):
        """Test conversation cache operations."""
        conversation_key = "1:123456789"
        conversation_data = {
            "messages": [
                {"role": "user", "content": "Hello", "timestamp": "2025-01-27T10:00:00"}
            ]
        }
        
        # Test setting conversation cache
        storage_adapter.set_conversation_cache(conversation_key, conversation_data)
        
        # Test getting conversation cache
        retrieved_data = storage_adapter.get_conversation_cache(conversation_key)
        assert retrieved_data is not None
        assert retrieved_data["messages"][0]["content"] == "Hello"
        
        # Test clearing conversation cache
        storage_adapter.clear_conversation_cache(conversation_key)
        assert storage_adapter.get_conversation_cache(conversation_key) is None
    
    def test_backup_operations(self, storage_adapter):
        """Test backup operations."""
        # Add some test data
        storage_adapter.write_config({"test_data": "value"})
        
        # Test creating backup
        backup_id = storage_adapter.backup_configs()
        assert backup_id.startswith("backup_")
        
        # Test restoring backup
        success = storage_adapter.restore_configs(backup_id)
        assert success is True
        
        # Test restoring non-existent backup
        success = storage_adapter.restore_configs("non_existent_backup")
        assert success is False


class TestGitAutoUpdaterAdapter:
    """Test Git auto-updater adapter."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for tests."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def git_adapter(self, temp_dir):
        """Create git adapter for testing."""
        # Initialize git repository
        import subprocess
        subprocess.run(["git", "init"], cwd=temp_dir, check=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=temp_dir, check=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=temp_dir, check=True)
        
        # Create initial commit
        test_file = Path(temp_dir) / "README.md"
        test_file.write_text("# Test Repository")
        subprocess.run(["git", "add", "."], cwd=temp_dir, check=True)
        subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=temp_dir, check=True)
        
        backup_dir = Path(temp_dir) / "backups"
        return GitAutoUpdaterAdapter(temp_dir, str(backup_dir))

    @patch('subprocess.run')
    def test_check_updates(self, mock_run, git_adapter):
        """Test checking for updates."""
        # Mock git commands
        mock_run.side_effect = [
            type('Response', (), {'stdout': 'abc123\n', 'stderr': ''})(),  # fetch
            type('Response', (), {'stdout': 'abc123\n', 'stderr': ''})(),  # current commit
            type('Response', (), {'stdout': 'def456\n', 'stderr': ''})(),  # latest commit
            type('Response', (), {'stdout': 'abc123\n', 'stderr': ''})(),  # version info commit
            type('Response', (), {'stdout': 'main\n', 'stderr': ''})(),    # version info branch
            type('Response', (), {'stdout': '\n', 'stderr': ''})(),        # version info status
        ]

        result = git_adapter.check_updates()

        assert "has_updates" in result
        assert "current_version" in result
        assert "available_version" in result
        # version_info is included in the result when check_updates succeeds
        assert result.get("has_updates") is not None
    
    def test_create_backup(self, git_adapter, temp_dir):
        """Test creating backup."""
        # Create some test files
        test_file = Path(temp_dir) / "test.txt"
        test_file.write_text("test content")
        
        backup_id = git_adapter.create_backup()
        assert backup_id.startswith("backup_")
        
        # Check backup directory exists
        backup_path = Path(git_adapter.backup_dir) / backup_id
        assert backup_path.exists()
        assert (backup_path / "repo").exists()
    
    def test_get_version_info(self, git_adapter):
        """Test getting version info."""
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = [
                type('Response', (), {'stdout': 'abc123\n', 'stderr': ''})(),  # commit hash
                type('Response', (), {'stdout': 'main\n', 'stderr': ''})(),    # branch
                type('Response', (), {'stdout': '\n', 'stderr': ''})(),        # status
            ]
            
            version_info = git_adapter.get_version_info()
            
            assert "version" in version_info
            assert "commit_hash" in version_info
            assert "branch" in version_info
            assert "git_status" in version_info
    
    def test_list_backups(self, git_adapter):
        """Test listing backups."""
        # Create a test backup
        backup_id = git_adapter.create_backup()
        
        backups = git_adapter.list_backups()
        assert len(backups) >= 1
        
        # Check backup info
        backup = backups[0]
        assert "id" in backup
        assert "created_at" in backup
        assert "commit" in backup
        assert "branch" in backup


class TestAiogramTelegramAdapter:
    """Test Aiogram Telegram adapter."""
    
    @pytest.fixture
    def telegram_adapter(self):
        """Create telegram adapter for testing."""
        with patch('aiogram.Bot') as mock_bot_class:
            mock_bot = AsyncMock()
            mock_bot.get_me = AsyncMock()
            mock_bot_class.return_value = mock_bot
            return AiogramTelegramAdapter("5123456789:ABCdefGHIjklMNOpqrsTUVwxyz")
    
    @pytest.mark.asyncio
    async def test_validate_token(self):
        """Test token validation."""
        with patch('adapters.telegram.aiogram_adapter.Bot') as mock_bot_class:
            mock_bot = AsyncMock()
            mock_bot.get_me = AsyncMock()
            mock_bot.session.close = AsyncMock()
            mock_bot_class.return_value = mock_bot
            
            # Test valid token
            is_valid = await AiogramTelegramAdapter.validate_token("5123456789:ABCdefGHIjklMNOpqrsTUVwxyz")
            assert is_valid is True
            
            # Test invalid token
            from aiogram.exceptions import TelegramAPIError
            mock_bot.get_me.side_effect = TelegramAPIError(method="getMe", message="Invalid token")
            is_valid = await AiogramTelegramAdapter.validate_token("5123456789:INVALIDtoken")
            assert is_valid is False
    
    @pytest.mark.asyncio
    async def test_get_me(self, telegram_adapter):
        """Test getting bot information."""
        with patch.object(telegram_adapter, '_ensure_initialized', new_callable=AsyncMock):
            with patch.object(telegram_adapter.bot, 'get_me') as mock_get_me:
                mock_bot_info = type('BotInfo', (), {
                    'id': 123456789,
                    'username': 'test_bot',
                    'first_name': 'Test Bot',
                    'can_join_groups': True,
                    'can_read_all_group_messages': False,
                    'supports_inline_queries': False,
                })()
                mock_get_me.return_value = mock_bot_info
                
                bot_info = await telegram_adapter.get_me()
                
                assert bot_info["id"] == 123456789
                assert bot_info["username"] == "test_bot"
                assert bot_info["first_name"] == "Test Bot"
    
    @pytest.mark.asyncio
    async def test_send_message(self, telegram_adapter):
        """Test sending message."""
        with patch.object(telegram_adapter, '_ensure_initialized', new_callable=AsyncMock):
            with patch.object(telegram_adapter.bot, 'send_message') as mock_send:
                mock_message = type('Message', (), {'message_id': 123})()
                mock_send.return_value = mock_message
                
                message_id = await telegram_adapter.send_message("123456789", "Hello, world!")
                
                assert message_id == "123"
                mock_send.assert_called_once_with(
                    chat_id="123456789",
                    text="Hello, world!"
                )


class TestDomainEntities:
    """Test domain entities."""
    
    def test_bot_entity(self):
        """Test Bot domain entity."""
        config = BotConfig(
            name="Test Bot",
            telegram_token="5123456789:ABCdefGHIjklMNOpqrsTUVwxyz",
            openai_api_key="sk-test1234567890abcdefghijklmnopqrstuvwxyz",
            assistant_id="asst_test1234567890abcdefghijklmnopqrstuvwxyz",
        )
        
        bot = Bot(id=1, config=config)
        
        # Test initial state
        assert bot.status == BotStatus.STOPPED
        assert bot.message_count == 0
        assert bot.voice_message_count == 0
        
        # Test starting bot
        bot.start()
        assert bot.status == BotStatus.RUNNING
        assert bot.is_running() is True
        
        # Test stopping bot
        bot.stop()
        assert bot.status == BotStatus.STOPPED
        assert bot.is_running() is False
        
        # Test error handling
        bot.set_error("Test error")
        assert bot.status == BotStatus.ERROR
        assert bot.last_error == "Test error"
        
        # Test message counting
        bot.increment_message_count()
        bot.increment_voice_message_count()
        assert bot.message_count == 1
        assert bot.voice_message_count == 1
    
    def test_conversation_entity(self):
        """Test Conversation domain entity."""
        key = ConversationKey(bot_id=1, chat_id="123456789")
        conversation = Conversation(key=key)
        
        # Test initial state
        assert conversation.is_empty() is True
        assert conversation.message_count == 0
        
        # Test adding messages
        conversation.add_user_message("Hello")
        conversation.add_assistant_message("Hi there!")
        
        assert conversation.message_count == 2
        assert conversation.is_empty() is False
        
        # Test getting recent messages
        recent = conversation.get_recent_messages(1)
        assert len(recent) == 1
        assert recent[0].content == "Hi there!"
        
        # Test getting context for AI
        context = conversation.get_context_for_ai()
        assert len(context) == 2
        assert context[0]["role"] == "user"
        assert context[1]["role"] == "assistant"
        
        # Test clearing messages
        conversation.clear_messages()
        assert conversation.is_empty() is True
        assert conversation.message_count == 0
    
    def test_system_config_entity(self):
        """Test SystemConfig domain entity."""
        config = SystemConfig()
        
        # Test initial state
        assert config.version == "3.6.0"
        assert config.max_bots == 100
        assert config.auto_update_enabled is True
        
        # Test validation
        errors = config.validate()
        assert len(errors) == 0
        
        # Test admin bot config
        admin_config = AdminBotConfig(
            enabled=True,
            token="5123456789:ABCdefGHIjklMNOpqrsTUVwxyz",
            admin_users=[123456789]
        )
        
        config.update_admin_bot_config(admin_config)
        assert config.admin_bot.enabled is True
        assert config.admin_bot.is_admin_user(123456789) is True
