"""
Integration tests for migration and unified system.

These tests verify that the migration process and unified application
work correctly in real scenarios.
"""

import pytest
import tempfile
import shutil
import json
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.migration.migrate_v1_to_v2 import MigrationManager
from src.integration.unified_app import UnifiedApplication
from src.bridge.config_bridge import ConfigBridge
from src.bridge.bot_management_bridge import BotManagementBridge


class TestMigrationIntegration:
    """Test migration process integration."""
    
    @pytest.fixture
    def temp_project_dir(self):
        """Create temporary project directory for testing."""
        temp_dir = tempfile.mkdtemp()
        
        # Create src directory
        src_dir = Path(temp_dir) / "src"
        src_dir.mkdir()
        
        # Create sample bot_configs.json
        sample_config = {
            "bots": {
                "1": {
                    "id": 1,
                    "config": {
                        "bot_name": "Test Bot",
                        "telegram_token": "test_token_123",
                        "openai_api_key": "test_openai_key",
                        "assistant_id": "test_assistant",
                        "group_context_limit": 15,
                        "enable_ai_responses": True,
                        "enable_voice_responses": False,
                        "marketplace": {
                            "enabled": True,
                            "title": "Test Bot",
                            "description": "Test description",
                            "category": "test",
                            "username": "@testbot",
                            "tags": ["test"]
                        },
                        "voice_model": "tts-1",
                        "voice_type": "alloy"
                    },
                    "status": "stopped"
                }
            }
        }
        
        with open(src_dir / "bot_configs.json", "w") as f:
            json.dump(sample_config, f, indent=2)
        
        yield temp_dir
        
        # Cleanup
        shutil.rmtree(temp_dir)
    
    @patch('src.migration.migrate_v1_to_v2.legacy_config')
    def test_migration_manager_initialization(self, mock_legacy_config, temp_project_dir):
        """Test migration manager initialization."""
        # Setup mock
        mock_legacy_config.BOT_CONFIGS = {
            1: {
                "id": 1,
                "config": {
                    "bot_name": "Test Bot",
                    "telegram_token": "test_token",
                },
                "status": "stopped"
            }
        }
        mock_legacy_config.BOT_CONFIGS_LOCK = MagicMock()
        
        # Initialize migration manager
        migration_manager = MigrationManager(temp_project_dir)
        
        assert migration_manager.project_root == Path(temp_project_dir)
        assert migration_manager.backup_dir.exists()
        assert migration_manager.migration_state["phase"] == "initialized"
    
    @patch('src.migration.migrate_v1_to_v2.legacy_config')
    def test_create_backup(self, mock_legacy_config, temp_project_dir):
        """Test backup creation."""
        migration_manager = MigrationManager(temp_project_dir)
        
        # Create backup
        backup_id = migration_manager.create_backup()
        
        assert backup_id.startswith("backup_")
        assert migration_manager.migration_state["backup_id"] == backup_id
        
        # Verify backup exists
        backup_path = migration_manager.backup_dir / backup_id
        assert backup_path.exists()
        assert (backup_path / "manifest.json").exists()
        assert (backup_path / "config" / "bot_configs.json").exists()
    
    @patch('src.migration.migrate_v1_to_v2.legacy_config')
    @patch('src.bridge.config_bridge.legacy_config')
    def test_configuration_migration(self, mock_bridge_config, mock_migration_config, temp_project_dir):
        """Test configuration migration process."""
        # Setup mocks
        test_config = {
            1: {
                "id": 1,
                "config": {
                    "bot_name": "Test Bot",
                    "telegram_token": "test_token",
                    "openai_api_key": "test_key",
                    "assistant_id": "test_assistant",
                    "group_context_limit": 15,
                    "enable_ai_responses": True,
                    "enable_voice_responses": False,
                    "marketplace": {"enabled": True},
                    "voice_model": "tts-1",
                    "voice_type": "alloy"
                },
                "status": "stopped"
            }
        }
        
        mock_migration_config.BOT_CONFIGS = test_config
        mock_migration_config.BOT_CONFIGS_LOCK = MagicMock()
        mock_bridge_config.BOT_CONFIGS = test_config
        mock_bridge_config.BOT_CONFIGS_LOCK = MagicMock()
        
        # Initialize migration manager
        migration_manager = MigrationManager(temp_project_dir)
        
        # Initialize new system
        success = migration_manager.initialize_new_system()
        assert success
        
        # Migrate configurations
        success = migration_manager.migrate_configurations()
        assert success
        
        # Verify migration result
        assert migration_manager.migration_state["progress"] == 30
    
    @patch('src.migration.migrate_v1_to_v2.legacy_config')
    @patch('src.bridge.config_bridge.legacy_config')
    def test_migration_validation(self, mock_bridge_config, mock_migration_config, temp_project_dir):
        """Test migration validation."""
        # Setup mocks
        test_config = {
            1: {
                "id": 1,
                "config": {
                    "bot_name": "Test Bot",
                    "telegram_token": "test_token",
                    "openai_api_key": "test_key",
                    "assistant_id": "test_assistant",
                    "group_context_limit": 15,
                    "enable_ai_responses": True,
                    "enable_voice_responses": False,
                    "marketplace": {"enabled": True},
                    "voice_model": "tts-1",
                    "voice_type": "alloy"
                },
                "status": "stopped"
            }
        }
        
        mock_migration_config.BOT_CONFIGS = test_config
        mock_migration_config.BOT_CONFIGS_LOCK = MagicMock()
        mock_bridge_config.BOT_CONFIGS = test_config
        mock_bridge_config.BOT_CONFIGS_LOCK = MagicMock()
        
        # Initialize migration manager
        migration_manager = MigrationManager(temp_project_dir)
        
        # Initialize and migrate
        migration_manager.initialize_new_system()
        migration_manager.migrate_configurations()
        
        # Validate migration
        success = migration_manager.validate_migration()
        assert success
        
        # Check validation result
        assert migration_manager.migration_state["progress"] == 80


class TestUnifiedApplicationIntegration:
    """Test unified application integration."""
    
    @pytest.fixture
    def temp_config_file(self):
        """Create temporary config file."""
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        
        config_data = {
            "bots": {
                "1": {
                    "id": 1,
                    "config": {
                        "bot_name": "Test Bot",
                        "telegram_token": "test_token",
                        "openai_api_key": "test_key",
                        "assistant_id": "test_assistant",
                        "group_context_limit": 15,
                        "enable_ai_responses": True,
                        "enable_voice_responses": False,
                        "marketplace": {"enabled": True},
                        "voice_model": "tts-1",
                        "voice_type": "alloy"
                    },
                    "status": "stopped"
                }
            }
        }
        
        json.dump(config_data, temp_file, indent=2)
        temp_file.close()
        
        yield temp_file.name
        
        # Cleanup
        os.unlink(temp_file.name)
    
    @patch('src.integration.unified_app.legacy_config')
    @patch('src.integration.unified_app.legacy_app')
    def test_unified_app_initialization(self, mock_legacy_app, mock_legacy_config, temp_config_file):
        """Test unified application initialization."""
        # Setup mocks
        mock_legacy_config.CONFIG_FILE = temp_config_file
        mock_legacy_config.load_configs = MagicMock()
        mock_legacy_app.app = MagicMock()
        
        # Initialize unified app
        unified_app = UnifiedApplication(temp_config_file, migration_mode=True)
        
        success = unified_app.initialize()
        assert success
        assert unified_app.is_initialized
        assert unified_app.migration_mode
    
    @patch('src.integration.unified_app.legacy_config')
    @patch('src.integration.unified_app.legacy_app')
    def test_unified_app_migration_completed(self, mock_legacy_app, mock_legacy_config, temp_config_file):
        """Test unified app with completed migration."""
        # Create migration completion file
        completion_file = Path("migration_completed.json")
        completion_data = {
            "migration_completed": True,
            "completion_time": "2025-08-21T10:00:00",
            "migration_version": "1.0.0"
        }
        
        with open(completion_file, "w") as f:
            json.dump(completion_data, f)
        
        try:
            # Setup mocks
            mock_legacy_config.CONFIG_FILE = temp_config_file
            mock_legacy_config.load_configs = MagicMock()
            mock_legacy_app.app = MagicMock()
            
            # Initialize unified app
            unified_app = UnifiedApplication(temp_config_file, migration_mode=True)
            
            success = unified_app.initialize()
            assert success
            assert unified_app.migration_completed
            assert not unified_app.migration_mode  # Should be disabled
            
        finally:
            # Cleanup
            if completion_file.exists():
                completion_file.unlink()
    
    @patch('src.integration.unified_app.legacy_config')
    @patch('src.integration.unified_app.legacy_app')
    @patch('src.integration.unified_app.legacy_bot_manager')
    def test_unified_app_bot_management(self, mock_bot_manager, mock_legacy_app, mock_legacy_config, temp_config_file):
        """Test unified app bot management operations."""
        # Setup mocks
        mock_legacy_config.CONFIG_FILE = temp_config_file
        mock_legacy_config.load_configs = MagicMock()
        mock_legacy_config.BOT_CONFIGS = {
            1: {
                "id": 1,
                "config": {"bot_name": "Test Bot"},
                "status": "stopped"
            }
        }
        mock_legacy_config.BOT_CONFIGS_LOCK = MagicMock()
        
        mock_legacy_app.app = MagicMock()
        mock_bot_manager.start_all_bots = MagicMock()
        mock_bot_manager.stop_all_bots_for_update = MagicMock(return_value=(True, "Success"))
        
        # Initialize unified app
        unified_app = UnifiedApplication(temp_config_file, migration_mode=True)
        unified_app.initialize()
        
        # Test bot operations
        start_result = unified_app.start_bots()
        assert "success" in start_result
        
        stop_result = unified_app.stop_bots()
        assert "success" in stop_result
        
        status = unified_app.get_system_status()
        assert "unified_app" in status
        assert status["unified_app"]["initialized"]


class TestBridgeIntegration:
    """Test bridge component integration."""
    
    @pytest.fixture
    def mock_storage_adapter(self):
        """Create mock storage adapter."""
        adapter = MagicMock()
        adapter.list_bot_configs.return_value = {
            1: MagicMock(
                id=1,
                name="Test Bot",
                token="test_token",
                status="stopped"
            )
        }
        adapter.save_bot_config = MagicMock()
        adapter.save_system_config = MagicMock()
        return adapter
    
    @patch('src.bridge.config_bridge.legacy_config')
    def test_config_bridge_sync(self, mock_legacy_config, mock_storage_adapter):
        """Test configuration bridge synchronization."""
        # Setup mock
        mock_legacy_config.BOT_CONFIGS = {
            1: {
                "id": 1,
                "config": {
                    "bot_name": "Test Bot",
                    "telegram_token": "test_token",
                    "openai_api_key": "test_key",
                    "assistant_id": "test_assistant",
                    "group_context_limit": 15,
                    "enable_ai_responses": True,
                    "enable_voice_responses": False,
                    "marketplace": {"enabled": True},
                    "voice_model": "tts-1",
                    "voice_type": "alloy"
                },
                "status": "stopped"
            }
        }
        mock_legacy_config.BOT_CONFIGS_LOCK = MagicMock()
        mock_legacy_config.save_configs = MagicMock()
        
        # Initialize bridge
        config_bridge = ConfigBridge(mock_storage_adapter)
        
        # Test synchronization
        success = config_bridge.sync_configurations("both")
        assert success
        
        # Verify calls
        mock_storage_adapter.save_bot_config.assert_called()
    
    def test_bot_management_bridge_operations(self, mock_storage_adapter):
        """Test bot management bridge operations."""
        # Create mock use case
        mock_use_case = MagicMock()
        mock_use_case.start_bot.return_value = {"success": True, "message": "Bot started"}
        mock_use_case.stop_bot.return_value = {"success": True, "message": "Bot stopped"}
        mock_use_case.list_bots.return_value = {
            "success": True,
            "bots": [{"id": 1, "name": "Test Bot", "status": "stopped"}],
            "total": 1
        }
        mock_use_case.get_bot.return_value = {
            "success": True,
            "bot": {"id": 1, "name": "Test Bot", "status": "stopped"}
        }
        
        # Initialize bridge
        bot_bridge = BotManagementBridge(mock_use_case)
        
        # Test operations
        success, message = bot_bridge.start_bot(1)
        assert success
        assert "started" in message.lower()
        
        success, message = bot_bridge.stop_bot(1)
        assert success
        assert "stopped" in message.lower()
        
        success, message = bot_bridge.restart_bot(1)
        assert success
        assert "restarted" in message.lower()
        
        status = bot_bridge.get_bot_status(1)
        assert status["success"]
        
        bot_list = bot_bridge.list_bots()
        assert bot_list["success"]
        assert len(bot_list["bots"]) == 1


class TestFullIntegrationScenario:
    """Test complete integration scenarios."""
    
    @pytest.fixture
    def integration_environment(self):
        """Set up complete integration test environment."""
        temp_dir = tempfile.mkdtemp()
        
        # Create project structure
        src_dir = Path(temp_dir) / "src"
        src_dir.mkdir()
        
        # Create sample configuration
        config_data = {
            "bots": {
                "1": {
                    "id": 1,
                    "config": {
                        "bot_name": "Integration Test Bot",
                        "telegram_token": "test_token_integration",
                        "openai_api_key": "test_openai_integration",
                        "assistant_id": "test_assistant_integration",
                        "group_context_limit": 15,
                        "enable_ai_responses": True,
                        "enable_voice_responses": False,
                        "marketplace": {
                            "enabled": True,
                            "title": "Integration Bot",
                            "description": "Bot for integration testing",
                            "category": "test",
                            "username": "@integrationbot",
                            "tags": ["integration", "test"]
                        },
                        "voice_model": "tts-1",
                        "voice_type": "alloy"
                    },
                    "status": "stopped"
                },
                "2": {
                    "id": 2,
                    "config": {
                        "bot_name": "Second Test Bot",
                        "telegram_token": "test_token_2",
                        "openai_api_key": "test_openai_2",
                        "assistant_id": "test_assistant_2",
                        "group_context_limit": 10,
                        "enable_ai_responses": False,
                        "enable_voice_responses": True,
                        "marketplace": {"enabled": False},
                        "voice_model": "tts-1-hd",
                        "voice_type": "nova"
                    },
                    "status": "running"
                }
            }
        }
        
        config_file = src_dir / "bot_configs.json"
        with open(config_file, "w") as f:
            json.dump(config_data, f, indent=2)
        
        yield {
            "temp_dir": temp_dir,
            "config_file": str(config_file),
            "config_data": config_data
        }
        
        # Cleanup
        shutil.rmtree(temp_dir)
    
    @patch('src.migration.migrate_v1_to_v2.legacy_config')
    @patch('src.bridge.config_bridge.legacy_config')
    @patch('src.integration.unified_app.legacy_config')
    @patch('src.integration.unified_app.legacy_app')
    @patch('src.integration.unified_app.legacy_bot_manager')
    def test_complete_migration_workflow(self, mock_bot_manager, mock_unified_app, 
                                       mock_unified_config, mock_bridge_config,
                                       mock_migration_config, integration_environment):
        """Test complete migration workflow from start to finish."""
        # Setup environment
        temp_dir = integration_environment["temp_dir"]
        config_file = integration_environment["config_file"]
        config_data = integration_environment["config_data"]
        
        # Setup mocks
        for mock_config in [mock_migration_config, mock_bridge_config, mock_unified_config]:
            mock_config.BOT_CONFIGS = config_data["bots"]
            mock_config.BOT_CONFIGS_LOCK = MagicMock()
            mock_config.CONFIG_FILE = config_file
            mock_config.load_configs = MagicMock()
            mock_config.save_configs = MagicMock()
            mock_config.ADMIN_BOT_CONFIG = {
                "enabled": False,
                "token": "",
                "admin_users": [],
                "notifications": {}
            }
        
        mock_unified_app.app = MagicMock()
        mock_bot_manager.start_all_bots = MagicMock()
        mock_bot_manager.stop_all_bots_for_update = MagicMock(return_value=(True, "Success"))
        
        # Step 1: Initialize migration manager
        migration_manager = MigrationManager(temp_dir)
        
        # Step 2: Create backup
        backup_id = migration_manager.create_backup()
        assert backup_id
        
        # Step 3: Initialize new system
        success = migration_manager.initialize_new_system()
        assert success
        
        # Step 4: Migrate configurations
        success = migration_manager.migrate_configurations()
        assert success
        
        # Step 5: Validate migration
        success = migration_manager.validate_migration()
        assert success
        
        # Step 6: Initialize unified application
        unified_app = UnifiedApplication(config_file, migration_mode=True)
        success = unified_app.initialize()
        assert success
        
        # Step 7: Test unified operations
        system_status = unified_app.get_system_status()
        assert system_status["unified_app"]["initialized"]
        
        # Step 8: Test bot management through unified system
        start_result = unified_app.start_bots()
        assert "success" in start_result
        
        stop_result = unified_app.stop_bots()
        assert "success" in stop_result
        
        # Step 9: Finalize migration
        success = migration_manager.finalize_migration()
        assert success
        
        # Verify migration completion marker
        completion_file = Path(temp_dir) / "migration_completed.json"
        assert completion_file.exists()
        
        with open(completion_file) as f:
            completion_data = json.load(f)
            assert completion_data["migration_completed"]
            assert completion_data["backup_id"] == backup_id







