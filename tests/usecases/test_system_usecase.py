"""
Tests for SystemUseCase.

This module contains tests for the system use case
that orchestrates system configuration and external adapters.
"""

import pytest
from unittest.mock import Mock, AsyncMock
from datetime import datetime

from core.usecases.system import SystemUseCase
from core.domain.config import SystemConfig, AdminBotConfig


class TestSystemUseCase:
    """Test SystemUseCase."""

    @pytest.fixture
    def mock_storage_port(self):
        """Create mock storage port."""
        mock = Mock()
        mock.read_config = Mock(return_value={
            "version": "3.6.0",
            "debug_mode": False,
            "log_level": "INFO",
            "max_bots": 100,
            "auto_update_enabled": True,
            "backup_retention_days": 30,
            "admin_bot": {
                "enabled": False,
                "token": "",
                "admin_users": [],
                "notifications": {
                    "bot_status": True,
                    "high_cpu": True,
                    "errors": True,
                    "weekly_stats": True,
                }
            },
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        })
        mock.write_config = Mock()
        return mock

    @pytest.fixture
    def mock_updater_port(self):
        """Create mock updater port."""
        mock = Mock()
        mock.check_updates = Mock(return_value={
            "has_updates": False,
            "current_version": "abc123",
            "available_version": "abc123",
            "version_info": {
                "version": "3.6.0",
                "commit_hash": "abc123",
                "branch": "main",
                "git_status": "clean",
                "build_date": datetime.now().isoformat(),
            }
        })
        mock.apply_update = Mock(return_value=True)
        mock.create_backup = Mock(return_value="backup_20240101_120000")
        mock.restore_backup = Mock(return_value=True)
        mock.get_update_status = Mock(return_value={
            "status": "idle",
            "last_check": datetime.now().isoformat(),
            "current_version": "abc123",
            "available_version": "abc123",
            "backup_id": None,
        })
        mock.list_backups = Mock(return_value=[])
        mock.cleanup_old_backups = Mock(return_value={
            "deleted_count": 0,
            "kept_count": 5,
            "total_size_freed": 0
        })
        mock.get_version_info = Mock(return_value={
            "version": "3.6.0",
            "commit_hash": "abc123",
            "branch": "main",
            "git_status": "clean",
            "build_date": datetime.now().isoformat(),
        })
        mock.validate_update = Mock(return_value=True)
        mock.rollback_update = Mock(return_value=True)
        return mock

    @pytest.fixture
    def use_case(self, mock_storage_port, mock_updater_port):
        """Create use case instance."""
        return SystemUseCase(mock_storage_port, mock_updater_port)

    def test_get_system_config(self, use_case, mock_storage_port):
        """Test getting system configuration."""
        # Act
        config = use_case.get_system_config()

        # Assert
        assert config is not None
        assert config.version == "3.6.0"
        assert config.debug_mode is False
        assert config.log_level == "INFO"
        assert config.max_bots == 100
        assert config.auto_update_enabled is True
        assert config.backup_retention_days == 30
        mock_storage_port.read_config.assert_called_once()

    def test_update_system_config(self, use_case, mock_storage_port):
        """Test updating system configuration."""
        # Arrange
        new_config = SystemConfig(
            version="3.7.0",
            debug_mode=True,
            log_level="DEBUG",
            max_bots=200,
            auto_update_enabled=False,
            backup_retention_days=60,
        )

        # Act
        use_case.update_system_config(new_config)

        # Assert
        mock_storage_port.write_config.assert_called_once()
        call_args = mock_storage_port.write_config.call_args[0][0]
        assert call_args["version"] == "3.7.0"
        assert call_args["debug_mode"] is True
        assert call_args["log_level"] == "DEBUG"
        assert call_args["max_bots"] == 200
        assert call_args["auto_update_enabled"] is False
        assert call_args["backup_retention_days"] == 60

    def test_update_system_config_invalid(self, use_case):
        """Test updating system configuration with invalid data."""
        # Arrange
        invalid_config = SystemConfig(
            version="",  # Invalid: empty version
            max_bots=0,  # Invalid: non-positive
            backup_retention_days=0,  # Invalid: non-positive
        )

        # Act & Assert
        with pytest.raises(ValueError, match="Invalid system configuration"):
            use_case.update_system_config(invalid_config)

    def test_get_admin_bot_config(self, use_case, mock_storage_port):
        """Test getting admin bot configuration."""
        # Act
        admin_config = use_case.get_admin_bot_config()

        # Assert
        assert admin_config is not None
        assert admin_config.enabled is False
        assert admin_config.token == ""
        assert len(admin_config.admin_users) == 0
        assert admin_config.notifications["bot_status"] is True
        assert admin_config.notifications["high_cpu"] is True
        assert admin_config.notifications["errors"] is True
        assert admin_config.notifications["weekly_stats"] is True

    def test_update_admin_bot_config(self, use_case, mock_storage_port):
        """Test updating admin bot configuration."""
        # Arrange
        new_admin_config = AdminBotConfig(
            enabled=True,
            token="5123456789:ABCdefGHIjklMNOpqrsTUVwxyz",
            admin_users=[123456789, 987654321],
            notifications={
                "bot_status": True,
                "high_cpu": False,
                "errors": True,
                "weekly_stats": False,
            }
        )

        # Act
        use_case.update_admin_bot_config(new_admin_config)

        # Assert
        mock_storage_port.write_config.assert_called_once()
        call_args = mock_storage_port.write_config.call_args[0][0]
        admin_bot_config = call_args["admin_bot"]
        assert admin_bot_config["enabled"] is True
        assert admin_bot_config["token"] == "5123456789:ABCdefGHIjklMNOpqrsTUVwxyz"
        assert admin_bot_config["admin_users"] == [123456789, 987654321]
        assert admin_bot_config["notifications"]["bot_status"] is True
        assert admin_bot_config["notifications"]["high_cpu"] is False
        assert admin_bot_config["notifications"]["errors"] is True
        assert admin_bot_config["notifications"]["weekly_stats"] is False

    def test_update_admin_bot_config_invalid(self, use_case):
        """Test updating admin bot configuration with invalid data."""
        # Arrange
        invalid_admin_config = AdminBotConfig(
            enabled=True,
            token="",  # Invalid: empty token when enabled
            admin_users=[],  # Invalid: no admin users when enabled
        )

        # Act & Assert
        with pytest.raises(ValueError, match="Invalid admin bot configuration"):
            use_case.update_admin_bot_config(invalid_admin_config)

    def test_check_updates(self, use_case, mock_updater_port):
        """Test checking for system updates."""
        # Act
        update_info = use_case.check_updates()

        # Assert
        assert update_info is not None
        assert update_info["has_updates"] is False
        assert update_info["current_version"] == "abc123"
        assert update_info["available_version"] == "abc123"
        assert "version_info" in update_info
        mock_updater_port.check_updates.assert_called_once()

    def test_apply_update(self, use_case, mock_updater_port):
        """Test applying system update."""
        # Arrange
        version = "def456"

        # Act
        success = use_case.apply_update(version)

        # Assert
        assert success is True
        mock_updater_port.apply_update.assert_called_once_with(version)

    def test_create_backup(self, use_case, mock_updater_port):
        """Test creating system backup."""
        # Act
        backup_id = use_case.create_backup()

        # Assert
        assert backup_id == "backup_20240101_120000"
        mock_updater_port.create_backup.assert_called_once()

    def test_restore_backup(self, use_case, mock_updater_port):
        """Test restoring system backup."""
        # Arrange
        backup_id = "backup_20240101_120000"

        # Act
        success = use_case.restore_backup(backup_id)

        # Assert
        assert success is True
        mock_updater_port.restore_backup.assert_called_once_with(backup_id)

    def test_get_update_status(self, use_case, mock_updater_port):
        """Test getting update status."""
        # Act
        status = use_case.get_update_status()

        # Assert
        assert status is not None
        assert status["status"] == "idle"
        assert "last_check" in status
        assert status["current_version"] == "abc123"
        assert status["available_version"] == "abc123"
        mock_updater_port.get_update_status.assert_called_once()

    def test_list_backups(self, use_case, mock_updater_port):
        """Test listing system backups."""
        # Arrange
        mock_backups = [
            {
                "id": "backup_20240101_120000",
                "created_at": datetime.now(),
                "commit": "abc123",
                "branch": "main",
                "status": "clean",
            }
        ]
        mock_updater_port.list_backups.return_value = mock_backups

        # Act
        backups = use_case.list_backups()

        # Assert
        assert len(backups) == 1
        assert backups[0]["id"] == "backup_20240101_120000"
        mock_updater_port.list_backups.assert_called_once()

    def test_cleanup_old_backups(self, use_case, mock_updater_port):
        """Test cleaning up old backups."""
        # Arrange
        keep_count = 3

        # Act
        result = use_case.cleanup_old_backups(keep_count)

        # Assert
        assert result is not None
        assert result["deleted_count"] == 0
        assert result["kept_count"] == 5
        assert result["total_size_freed"] == 0
        mock_updater_port.cleanup_old_backups.assert_called_once_with(keep_count)

    def test_get_version_info(self, use_case, mock_updater_port):
        """Test getting version information."""
        # Act
        version_info = use_case.get_version_info()

        # Assert
        assert version_info is not None
        assert version_info["version"] == "3.6.0"
        assert version_info["commit_hash"] == "abc123"
        assert version_info["branch"] == "main"
        assert version_info["git_status"] == "clean"
        assert "build_date" in version_info
        mock_updater_port.get_version_info.assert_called_once()

    def test_validate_update(self, use_case, mock_updater_port):
        """Test validating update."""
        # Arrange
        version = "def456"

        # Act
        is_valid = use_case.validate_update(version)

        # Assert
        assert is_valid is True
        mock_updater_port.validate_update.assert_called_once_with(version)

    def test_rollback_update(self, use_case, mock_updater_port):
        """Test rolling back update."""
        # Act
        success = use_case.rollback_update()

        # Assert
        assert success is True
        mock_updater_port.rollback_update.assert_called_once()

    def test_get_system_stats(self, use_case, mock_storage_port):
        """Test getting system statistics."""
        # Arrange
        mock_storage_port.get_bot_count.return_value = 5
        mock_storage_port.get_running_bot_count.return_value = 3

        # Act
        stats = use_case.get_system_stats()

        # Assert
        assert stats is not None
        assert stats["total_bots"] == 5
        assert stats["running_bots"] == 3
        assert stats["stopped_bots"] == 2
        assert "system_config" in stats
        mock_storage_port.get_bot_count.assert_called_once()
        mock_storage_port.get_running_bot_count.assert_called_once()

    def test_is_admin_user(self, use_case, mock_storage_port):
        """Test checking if user is admin."""
        # Arrange
        mock_storage_port.read_config.return_value = {
            "admin_bot": {
                "enabled": True,
                "token": "5123456789:ABCdefGHIjklMNOpqrsTUVwxyz",
                "admin_users": [123456789, 987654321],
                "notifications": {
                    "bot_status": True,
                    "high_cpu": True,
                    "errors": True,
                    "weekly_stats": True,
                }
            }
        }

        # Act & Assert
        assert use_case.is_admin_user(123456789) is True
        assert use_case.is_admin_user(987654321) is True
        assert use_case.is_admin_user(555555555) is False

    def test_add_admin_user(self, use_case, mock_storage_port):
        """Test adding admin user."""
        # Arrange
        user_id = 555555555

        # Act
        use_case.add_admin_user(user_id)

        # Assert
        mock_storage_port.write_config.assert_called_once()
        call_args = mock_storage_port.write_config.call_args[0][0]
        admin_users = call_args["admin_bot"]["admin_users"]
        assert user_id in admin_users

    def test_remove_admin_user(self, use_case, mock_storage_port):
        """Test removing admin user."""
        # Arrange
        mock_storage_port.read_config.return_value = {
            "admin_bot": {
                "enabled": True,
                "token": "5123456789:ABCdefGHIjklMNOpqrsTUVwxyz",
                "admin_users": [123456789, 987654321],
                "notifications": {
                    "bot_status": True,
                    "high_cpu": True,
                    "errors": True,
                    "weekly_stats": True,
                }
            }
        }
        user_id = 123456789

        # Act
        use_case.remove_admin_user(user_id)

        # Assert
        mock_storage_port.write_config.assert_called_once()
        call_args = mock_storage_port.write_config.call_args[0][0]
        admin_users = call_args["admin_bot"]["admin_users"]
        assert user_id not in admin_users
        assert 987654321 in admin_users  # Other admin should remain

    def test_get_notification_settings(self, use_case, mock_storage_port):
        """Test getting notification settings."""
        # Act
        notifications = use_case.get_notification_settings()

        # Assert
        assert notifications is not None
        assert notifications["bot_status"] is True
        assert notifications["high_cpu"] is True
        assert notifications["errors"] is True
        assert notifications["weekly_stats"] is True

    def test_update_notification_settings(self, use_case, mock_storage_port):
        """Test updating notification settings."""
        # Arrange
        new_notifications = {
            "bot_status": True,
            "high_cpu": False,
            "errors": True,
            "weekly_stats": False,
        }

        # Act
        use_case.update_notification_settings(new_notifications)

        # Assert
        mock_storage_port.write_config.assert_called_once()
        call_args = mock_storage_port.write_config.call_args[0][0]
        notifications = call_args["admin_bot"]["notifications"]
        assert notifications["bot_status"] is True
        assert notifications["high_cpu"] is False
        assert notifications["errors"] is True
        assert notifications["weekly_stats"] is False

    def test_system_config_validation(self, use_case):
        """Test system configuration validation."""
        # Test valid config
        valid_config = SystemConfig(
            version="3.6.0",
            max_bots=100,
            backup_retention_days=30,
        )
        errors = valid_config.validate()
        assert len(errors) == 0

        # Test invalid config
        invalid_config = SystemConfig(
            version="",  # Invalid: empty version
            max_bots=0,  # Invalid: non-positive
            backup_retention_days=0,  # Invalid: non-positive
        )
        errors = invalid_config.validate()
        assert len(errors) > 0
        assert any("System version is required" in error for error in errors)
        assert any("Maximum bots must be positive" in error for error in errors)
        assert any("Backup retention days must be positive" in error for error in errors)

    def test_admin_bot_config_validation(self, use_case):
        """Test admin bot configuration validation."""
        # Test valid config
        valid_config = AdminBotConfig(
            enabled=False,  # No validation when disabled
            token="",
            admin_users=[],
        )
        errors = valid_config.validate()
        assert len(errors) == 0

        # Test invalid enabled config
        invalid_config = AdminBotConfig(
            enabled=True,
            token="",  # Invalid: empty token when enabled
            admin_users=[],  # Invalid: no admin users when enabled
        )
        errors = invalid_config.validate()
        assert len(errors) > 0
        assert any("Admin bot token is required when enabled" in error for error in errors)
        assert any("At least one admin user is required when enabled" in error for error in errors)

        # Test invalid token format
        invalid_token_config = AdminBotConfig(
            enabled=True,
            token="invalid_token",  # Invalid: wrong format
            admin_users=[123456789],
        )
        errors = invalid_token_config.validate()
        assert len(errors) > 0
        assert any("Invalid admin bot token format" in error for error in errors)










