"""
Contract tests for ConfigStoragePort interface.

Tests that verify any storage adapter correctly implements the ConfigStoragePort contract.
"""

from typing import Any

import pytest

from core.ports.storage import ConfigStoragePort


class MockStorageAdapter(ConfigStoragePort):
    """Mock implementation of ConfigStoragePort for testing."""

    def __init__(self):
        self.config_data = {
            "bots": {
                1: {"id": 1, "name": "TestBot", "telegram_token": "test_token", "status": "stopped"}
            },
            "conversations": {},
            "admin_bot": {"enabled": False, "token": "", "admin_users": []},
        }
        self.backup_id_counter = 0

    def read_config(self) -> dict[str, Any]:
        """Mock config reading."""
        return self.config_data.copy()

    def write_config(self, patch: dict[str, Any]) -> None:
        """Mock config writing."""
        self.config_data.update(patch)

    def get_bot_config(self, bot_id: int) -> dict[str, Any] | None:
        """Mock get bot config."""
        return self.config_data.get("bots", {}).get(bot_id)

    def update_bot_config(self, bot_id: int, config: dict[str, Any]) -> None:
        """Mock update bot config."""
        if "bots" not in self.config_data:
            self.config_data["bots"] = {}
        self.config_data["bots"][bot_id] = config

    def delete_bot_config(self, bot_id: int) -> None:
        """Mock delete bot config."""
        if "bots" in self.config_data and bot_id in self.config_data["bots"]:
            del self.config_data["bots"][bot_id]

    def add_bot_config(self, bot_id: int, config: dict[str, Any]) -> None:
        """Mock add bot config."""
        self.update_bot_config(bot_id, config)

    def get_all_bot_configs(self) -> dict[int, dict[str, Any]]:
        """Mock get all bot configs."""
        return self.config_data.get("bots", {}).copy()

    def get_bot_count(self) -> int:
        """Mock get bot count."""
        return len(self.config_data.get("bots", {}))

    def get_running_bot_count(self) -> int:
        """Mock get running bot count."""
        running_count = 0
        for bot_config in self.config_data.get("bots", {}).values():
            if bot_config.get("status") == "running":
                running_count += 1
        return running_count

    def clear_all_configs(self) -> None:
        """Mock clear all configs."""
        self.config_data = {"bots": {}, "conversations": {}, "admin_bot": {"enabled": False}}

    def backup_configs(self) -> str:
        """Mock backup configs."""
        self.backup_id_counter += 1
        return f"backup_{self.backup_id_counter}"

    def restore_configs(self, backup_id: str) -> bool:
        """Mock restore configs."""
        return backup_id.startswith("backup_")

    def get_conversation_cache(self, conversation_key: str) -> dict[str, Any] | None:
        """Mock get conversation cache."""
        return self.config_data.get("conversations", {}).get(conversation_key)

    def set_conversation_cache(self, conversation_key: str, data: dict[str, Any]) -> None:
        """Mock set conversation cache."""
        if "conversations" not in self.config_data:
            self.config_data["conversations"] = {}
        self.config_data["conversations"][conversation_key] = data

    def clear_conversation_cache(self, conversation_key: str) -> None:
        """Mock clear conversation cache."""
        if (
            "conversations" in self.config_data
            and conversation_key in self.config_data["conversations"]
        ):
            del self.config_data["conversations"][conversation_key]


@pytest.fixture
def storage_adapter() -> ConfigStoragePort:
    """Provide a mock storage adapter for testing."""
    return MockStorageAdapter()


def test_read_config_contract(storage_adapter: ConfigStoragePort):
    """Test that read_config method returns dictionary."""
    config = storage_adapter.read_config()

    assert isinstance(config, dict)
    assert "bots" in config
    assert "conversations" in config
    assert "admin_bot" in config


def test_write_config_contract(storage_adapter: ConfigStoragePort):
    """Test that write_config method can update configuration."""
    original_config = storage_adapter.read_config()

    # Write new config
    patch = {"test_key": "test_value"}
    storage_adapter.write_config(patch)

    # Verify config was updated
    updated_config = storage_adapter.read_config()
    assert updated_config["test_key"] == "test_value"
    assert len(updated_config) > len(original_config)


def test_get_bot_config_contract(storage_adapter: ConfigStoragePort):
    """Test that get_bot_config method returns bot config or None."""
    # Test existing bot
    bot_config = storage_adapter.get_bot_config(1)
    assert isinstance(bot_config, dict)
    assert bot_config["id"] == 1
    assert bot_config["name"] == "TestBot"

    # Test non-existing bot
    bot_config = storage_adapter.get_bot_config(999)
    assert bot_config is None


def test_update_bot_config_contract(storage_adapter: ConfigStoragePort):
    """Test that update_bot_config method can update bot configuration."""
    new_config = {"id": 2, "name": "UpdatedBot", "telegram_token": "new_token", "status": "running"}

    storage_adapter.update_bot_config(2, new_config)

    # Verify config was updated
    updated_config = storage_adapter.get_bot_config(2)
    assert updated_config == new_config


def test_delete_bot_config_contract(storage_adapter: ConfigStoragePort):
    """Test that delete_bot_config method can remove bot configuration."""
    # Verify bot exists
    assert storage_adapter.get_bot_config(1) is not None

    # Delete bot
    storage_adapter.delete_bot_config(1)

    # Verify bot was deleted
    assert storage_adapter.get_bot_config(1) is None


def test_add_bot_config_contract(storage_adapter: ConfigStoragePort):
    """Test that add_bot_config method can add new bot configuration."""
    new_config = {"id": 3, "name": "NewBot", "telegram_token": "new_token", "status": "stopped"}

    storage_adapter.add_bot_config(3, new_config)

    # Verify bot was added
    added_config = storage_adapter.get_bot_config(3)
    assert added_config == new_config


def test_get_all_bot_configs_contract(storage_adapter: ConfigStoragePort):
    """Test that get_all_bot_configs method returns all bot configurations."""
    all_configs = storage_adapter.get_all_bot_configs()

    assert isinstance(all_configs, dict)
    assert 1 in all_configs
    assert all_configs[1]["name"] == "TestBot"


def test_get_bot_count_contract(storage_adapter: ConfigStoragePort):
    """Test that get_bot_count method returns correct count."""
    count = storage_adapter.get_bot_count()

    assert isinstance(count, int)
    assert count >= 0

    # Add a bot and verify count increases
    original_count = count
    storage_adapter.add_bot_config(4, {"id": 4, "name": "CountBot"})
    new_count = storage_adapter.get_bot_count()
    assert new_count == original_count + 1


def test_get_running_bot_count_contract(storage_adapter: ConfigStoragePort):
    """Test that get_running_bot_count method returns correct count."""
    running_count = storage_adapter.get_running_bot_count()

    assert isinstance(running_count, int)
    assert running_count >= 0

    # Start a bot and verify running count increases
    original_count = running_count
    storage_adapter.update_bot_config(1, {"id": 1, "name": "TestBot", "status": "running"})
    new_count = storage_adapter.get_running_bot_count()
    assert new_count == original_count + 1


def test_clear_all_configs_contract(storage_adapter: ConfigStoragePort):
    """Test that clear_all_configs method removes all configurations."""
    # Verify configs exist
    assert storage_adapter.get_bot_count() > 0

    # Clear all configs
    storage_adapter.clear_all_configs()

    # Verify all configs were cleared
    assert storage_adapter.get_bot_count() == 0


def test_backup_configs_contract(storage_adapter: ConfigStoragePort):
    """Test that backup_configs method returns backup ID."""
    backup_id = storage_adapter.backup_configs()

    assert isinstance(backup_id, str)
    assert backup_id.startswith("backup_")


def test_restore_configs_contract(storage_adapter: ConfigStoragePort):
    """Test that restore_configs method returns boolean."""
    # Test valid backup
    success = storage_adapter.restore_configs("backup_1")
    assert isinstance(success, bool)
    assert success is True

    # Test invalid backup
    success = storage_adapter.restore_configs("invalid_backup")
    assert isinstance(success, bool)
    assert success is False


def test_conversation_cache_contract(storage_adapter: ConfigStoragePort):
    """Test conversation cache methods."""
    conversation_key = "test_conversation"
    conversation_data = {
        "messages": [{"role": "user", "content": "Hello"}],
        "timestamp": "2025-01-27T10:00:00Z",
    }

    # Test set conversation cache
    storage_adapter.set_conversation_cache(conversation_key, conversation_data)

    # Test get conversation cache
    cached_data = storage_adapter.get_conversation_cache(conversation_key)
    assert cached_data == conversation_data

    # Test clear conversation cache
    storage_adapter.clear_conversation_cache(conversation_key)
    cached_data = storage_adapter.get_conversation_cache(conversation_key)
    assert cached_data is None


def test_storage_port_contract():
    """Main contract test function."""
    adapter = MockStorageAdapter()

    # Verify all required methods exist
    required_methods = [
        "read_config",
        "write_config",
        "get_bot_config",
        "update_bot_config",
        "delete_bot_config",
        "add_bot_config",
        "get_all_bot_configs",
        "get_bot_count",
        "get_running_bot_count",
        "clear_all_configs",
        "backup_configs",
        "restore_configs",
        "get_conversation_cache",
        "set_conversation_cache",
        "clear_conversation_cache",
    ]

    for method_name in required_methods:
        assert hasattr(adapter, method_name), f"Missing method: {method_name}"
        method = getattr(adapter, method_name)
        assert callable(method), f"Method {method_name} is not callable"









