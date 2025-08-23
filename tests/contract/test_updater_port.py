"""
Contract tests for AutoUpdaterPort interface.

Tests that verify any updater adapter correctly implements the AutoUpdaterPort contract.
"""

from datetime import datetime
from typing import Any

import pytest

from core.ports.updater import AutoUpdaterPort


class MockUpdaterAdapter(AutoUpdaterPort):
    """Mock implementation of AutoUpdaterPort for testing."""

    def __init__(self):
        self.update_state = {
            "status": "idle",
            "progress": 0,
            "message": "",
            "start_time": None,
            "error": None,
            "backup_id": None,
        }
        self.backup_counter = 0
        self.version_info = {
            "version": "3.6.0",
            "commit_hash": "abc123",
            "build_date": datetime.now(),
            "git_status": "clean",
        }

    def check_updates(self) -> dict[str, Any]:
        """Mock check for updates."""
        return {
            "has_updates": True,
            "current_version": "3.6.0",
            "latest_version": "3.6.1",
            "update_message": "Bug fixes and improvements",
            "commit_hash": "def456",
        }

    def apply_update(self, version: str) -> bool:
        """Mock apply update."""
        self.update_state["status"] = "updating"
        self.update_state["progress"] = 50
        self.update_state["message"] = f"Applying update to {version}"
        return True

    def create_backup(self) -> str:
        """Mock create backup."""
        self.backup_counter += 1
        backup_id = f"backup_{self.backup_counter}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.update_state["backup_id"] = backup_id
        return backup_id

    def restore_backup(self, backup_id: str) -> bool:
        """Mock restore backup."""
        return backup_id.startswith("backup_")

    def get_update_status(self) -> dict[str, Any]:
        """Mock get update status."""
        return self.update_state.copy()

    def list_backups(self) -> list[dict[str, Any]]:
        """Mock list backups."""
        return [
            {
                "id": "backup_1_20250127_100000",
                "created_at": datetime.now(),
                "size": 1024,
                "description": "Auto backup before update",
            },
            {
                "id": "backup_2_20250127_110000",
                "created_at": datetime.now(),
                "size": 2048,
                "description": "Manual backup",
            },
        ]

    def cleanup_old_backups(self, keep_count: int = 5) -> dict[str, Any]:
        """Mock cleanup old backups."""
        return {"deleted_count": 2, "kept_count": keep_count, "total_size_freed": 3072}

    def get_version_info(self) -> dict[str, Any]:
        """Mock get version info."""
        return self.version_info.copy()

    def validate_update(self, version: str) -> bool:
        """Mock validate update."""
        return version.startswith("3.")

    def rollback_update(self) -> bool:
        """Mock rollback update."""
        self.update_state["status"] = "rollback"
        self.update_state["progress"] = 25
        return True


@pytest.fixture
def updater_adapter() -> AutoUpdaterPort:
    """Provide a mock updater adapter for testing."""
    return MockUpdaterAdapter()


def test_check_updates_contract(updater_adapter: AutoUpdaterPort):
    """Test that check_updates method returns update information."""
    update_info = updater_adapter.check_updates()

    assert isinstance(update_info, dict)
    assert "has_updates" in update_info
    assert "current_version" in update_info
    assert "latest_version" in update_info
    assert "update_message" in update_info
    assert "commit_hash" in update_info

    assert isinstance(update_info["has_updates"], bool)
    assert isinstance(update_info["current_version"], str)
    assert isinstance(update_info["latest_version"], str)
    assert isinstance(update_info["update_message"], str)
    assert isinstance(update_info["commit_hash"], str)


def test_apply_update_contract(updater_adapter: AutoUpdaterPort):
    """Test that apply_update method returns boolean."""
    success = updater_adapter.apply_update("3.6.1")

    assert isinstance(success, bool)
    assert success is True


def test_create_backup_contract(updater_adapter: AutoUpdaterPort):
    """Test that create_backup method returns backup ID."""
    backup_id = updater_adapter.create_backup()

    assert isinstance(backup_id, str)
    assert backup_id.startswith("backup_")
    assert "_" in backup_id  # Should contain timestamp


def test_restore_backup_contract(updater_adapter: AutoUpdaterPort):
    """Test that restore_backup method returns boolean."""
    # Test valid backup
    success = updater_adapter.restore_backup("backup_1_20250127_100000")
    assert isinstance(success, bool)
    assert success is True

    # Test invalid backup
    success = updater_adapter.restore_backup("invalid_backup")
    assert isinstance(success, bool)
    assert success is False


def test_get_update_status_contract(updater_adapter: AutoUpdaterPort):
    """Test that get_update_status method returns status information."""
    status = updater_adapter.get_update_status()

    assert isinstance(status, dict)
    assert "status" in status
    assert "progress" in status
    assert "message" in status
    assert "start_time" in status
    assert "error" in status
    assert "backup_id" in status

    assert isinstance(status["status"], str)
    assert isinstance(status["progress"], int)
    assert isinstance(status["message"], str)
    assert status["progress"] >= 0 and status["progress"] <= 100


def test_list_backups_contract(updater_adapter: AutoUpdaterPort):
    """Test that list_backups method returns list of backups."""
    backups = updater_adapter.list_backups()

    assert isinstance(backups, list)

    if backups:  # If there are backups
        backup = backups[0]
        assert isinstance(backup, dict)
        assert "id" in backup
        assert "created_at" in backup
        assert "size" in backup
        assert "description" in backup

        assert isinstance(backup["id"], str)
        assert isinstance(backup["created_at"], datetime)
        assert isinstance(backup["size"], int)
        assert isinstance(backup["description"], str)


def test_cleanup_old_backups_contract(updater_adapter: AutoUpdaterPort):
    """Test that cleanup_old_backups method returns cleanup result."""
    result = updater_adapter.cleanup_old_backups(keep_count=3)

    assert isinstance(result, dict)
    assert "deleted_count" in result
    assert "kept_count" in result
    assert "total_size_freed" in result

    assert isinstance(result["deleted_count"], int)
    assert isinstance(result["kept_count"], int)
    assert isinstance(result["total_size_freed"], int)

    assert result["deleted_count"] >= 0
    assert result["kept_count"] >= 0
    assert result["total_size_freed"] >= 0


def test_get_version_info_contract(updater_adapter: AutoUpdaterPort):
    """Test that get_version_info method returns version information."""
    version_info = updater_adapter.get_version_info()

    assert isinstance(version_info, dict)
    assert "version" in version_info
    assert "commit_hash" in version_info
    assert "build_date" in version_info
    assert "git_status" in version_info

    assert isinstance(version_info["version"], str)
    assert isinstance(version_info["commit_hash"], str)
    assert isinstance(version_info["build_date"], datetime)
    assert isinstance(version_info["git_status"], str)


def test_validate_update_contract(updater_adapter: AutoUpdaterPort):
    """Test that validate_update method returns boolean."""
    # Test valid version
    is_valid = updater_adapter.validate_update("3.6.1")
    assert isinstance(is_valid, bool)
    assert is_valid is True

    # Test invalid version
    is_valid = updater_adapter.validate_update("invalid_version")
    assert isinstance(is_valid, bool)
    assert is_valid is False


def test_rollback_update_contract(updater_adapter: AutoUpdaterPort):
    """Test that rollback_update method returns boolean."""
    success = updater_adapter.rollback_update()

    assert isinstance(success, bool)
    assert success is True


def test_updater_port_contract():
    """Main contract test function."""
    adapter = MockUpdaterAdapter()

    # Verify all required methods exist
    required_methods = [
        "check_updates",
        "apply_update",
        "create_backup",
        "restore_backup",
        "get_update_status",
        "list_backups",
        "cleanup_old_backups",
        "get_version_info",
        "validate_update",
        "rollback_update",
    ]

    for method_name in required_methods:
        assert hasattr(adapter, method_name), f"Missing method: {method_name}"
        method = getattr(adapter, method_name)
        assert callable(method), f"Method {method_name} is not callable"


def test_update_status_transitions(updater_adapter: AutoUpdaterPort):
    """Test that update status transitions work correctly."""
    # Initial state
    status = updater_adapter.get_update_status()
    assert status["status"] == "idle"
    assert status["progress"] == 0

    # Create backup
    backup_id = updater_adapter.create_backup()
    status = updater_adapter.get_update_status()
    assert status["backup_id"] == backup_id

    # Apply update
    success = updater_adapter.apply_update("3.6.1")
    assert success is True
    status = updater_adapter.get_update_status()
    assert status["status"] == "updating"
    assert status["progress"] == 50

    # Rollback
    success = updater_adapter.rollback_update()
    assert success is True
    status = updater_adapter.get_update_status()
    assert status["status"] == "rollback"
    assert status["progress"] == 25









