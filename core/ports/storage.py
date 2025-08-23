"""
Configuration storage port interface.

Defines the contract for configuration storage operations that external adapters must implement.
"""

from typing import Any, Protocol


class ConfigStoragePort(Protocol):
    """Interface for configuration storage operations."""

    def read_config(self) -> dict[str, Any]:
        """Read all configuration data.

        Returns:
            Configuration dictionary
        """
        ...

    def write_config(self, patch: dict[str, Any]) -> None:
        """Write configuration data.

        Args:
            patch: Configuration data to write
        """
        ...

    def get_bot_config(self, bot_id: int) -> dict[str, Any] | None:
        """Get configuration for specific bot.

        Args:
            bot_id: Bot ID

        Returns:
            Bot configuration or None if not found
        """
        ...

    def update_bot_config(self, bot_id: int, config: dict[str, Any]) -> None:
        """Update configuration for specific bot.

        Args:
            bot_id: Bot ID
            config: New configuration
        """
        ...

    def delete_bot_config(self, bot_id: int) -> None:
        """Delete configuration for specific bot.

        Args:
            bot_id: Bot ID
        """
        ...

    def add_bot_config(self, bot_id: int, config: dict[str, Any]) -> None:
        """Add new bot configuration.

        Args:
            bot_id: Bot ID
            config: Bot configuration
        """
        ...

    def get_all_bot_configs(self) -> dict[int, dict[str, Any]]:
        """Get all bot configurations.

        Returns:
            Dictionary of bot configurations
        """
        ...

    def get_bot_count(self) -> int:
        """Get total number of bots.

        Returns:
            Number of bots
        """
        ...

    def get_running_bot_count(self) -> int:
        """Get number of running bots.

        Returns:
            Number of running bots
        """
        ...

    def clear_all_configs(self) -> None:
        """Clear all configurations."""
        ...

    def backup_configs(self) -> str:
        """Create backup of configurations.

        Returns:
            Backup ID
        """
        ...

    def restore_configs(self, backup_id: str) -> bool:
        """Restore configurations from backup.

        Args:
            backup_id: Backup ID

        Returns:
            True if restore successful
        """
        ...

    def get_conversation_cache(self, conversation_key: str) -> dict[str, Any] | None:
        """Get conversation cache.

        Args:
            conversation_key: Conversation key

        Returns:
            Conversation data or None
        """
        ...

    def set_conversation_cache(self, conversation_key: str, data: dict[str, Any]) -> None:
        """Set conversation cache.

        Args:
            conversation_key: Conversation key
            data: Conversation data
        """
        ...

    def clear_conversation_cache(self, conversation_key: str) -> None:
        """Clear conversation cache.

        Args:
            conversation_key: Conversation key
        """
        ...










