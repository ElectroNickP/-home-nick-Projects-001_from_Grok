"""
System use case.

This module contains the system use case that orchestrates
system configuration and external adapters.
"""

import logging
from typing import Dict, Any, List

from core.domain.config import SystemConfig, AdminBotConfig
from core.ports.storage import ConfigStoragePort
from core.ports.updater import AutoUpdaterPort

logger = logging.getLogger(__name__)


class SystemUseCase:
    """Use case for managing system configuration and operations."""

    def __init__(self, storage_port: ConfigStoragePort, updater_port: AutoUpdaterPort):
        """Initialize the use case with storage and updater ports."""
        self.storage_port = storage_port
        self.updater_port = updater_port

    def get_system_config(self) -> SystemConfig:
        """Get current system configuration."""
        try:
            config_data = self.storage_port.read_config()
            system_config = SystemConfig.from_dict(config_data)
            logger.debug("Retrieved system configuration")
            return system_config
        except Exception as e:
            logger.error(f"Error getting system configuration: {e}")
            # Return default configuration on error
            return SystemConfig()

    def update_system_config(self, new_config: SystemConfig) -> None:
        """Update system configuration."""
        try:
            # Validate configuration
            errors = new_config.validate()
            if errors:
                raise ValueError(f"Invalid system configuration: {', '.join(errors)}")

            # Update configuration
            config_data = new_config.to_dict()
            self.storage_port.write_config(config_data)
            logger.info("System configuration updated successfully")
        except Exception as e:
            logger.error(f"Error updating system configuration: {e}")
            raise

    def get_admin_bot_config(self) -> AdminBotConfig:
        """Get admin bot configuration."""
        try:
            system_config = self.get_system_config()
            return system_config.admin_bot
        except Exception as e:
            logger.error(f"Error getting admin bot configuration: {e}")
            return AdminBotConfig()

    def update_admin_bot_config(self, new_config: AdminBotConfig) -> None:
        """Update admin bot configuration."""
        try:
            # Validate configuration
            errors = new_config.validate()
            if errors:
                raise ValueError(f"Invalid admin bot configuration: {', '.join(errors)}")

            # Update system configuration
            system_config = self.get_system_config()
            system_config.update_admin_bot_config(new_config)
            self.update_system_config(system_config)
            logger.info("Admin bot configuration updated successfully")
        except Exception as e:
            logger.error(f"Error updating admin bot configuration: {e}")
            raise

    def check_updates(self) -> Dict[str, Any]:
        """Check for system updates."""
        try:
            update_info = self.updater_port.check_updates()
            logger.debug("Checked for system updates")
            return update_info
        except Exception as e:
            logger.error(f"Error checking updates: {e}")
            return {
                "has_updates": False,
                "error": str(e),
                "current_version": "unknown",
                "available_version": "unknown",
            }

    def apply_update(self, version: str) -> bool:
        """Apply system update."""
        try:
            success = self.updater_port.apply_update(version)
            if success:
                logger.info(f"System update applied successfully: {version}")
            else:
                logger.error(f"Failed to apply system update: {version}")
            return success
        except Exception as e:
            logger.error(f"Error applying update {version}: {e}")
            return False

    def create_backup(self) -> str:
        """Create system backup."""
        try:
            backup_id = self.updater_port.create_backup()
            logger.info(f"System backup created: {backup_id}")
            return backup_id
        except Exception as e:
            logger.error(f"Error creating backup: {e}")
            raise

    def restore_backup(self, backup_id: str) -> bool:
        """Restore system from backup."""
        try:
            success = self.updater_port.restore_backup(backup_id)
            if success:
                logger.info(f"System restored from backup: {backup_id}")
            else:
                logger.error(f"Failed to restore from backup: {backup_id}")
            return success
        except Exception as e:
            logger.error(f"Error restoring backup {backup_id}: {e}")
            return False

    def get_update_status(self) -> Dict[str, Any]:
        """Get current update status."""
        try:
            status = self.updater_port.get_update_status()
            return status
        except Exception as e:
            logger.error(f"Error getting update status: {e}")
            return {
                "status": "error",
                "error": str(e),
            }

    def list_backups(self) -> List[Dict[str, Any]]:
        """List available backups."""
        try:
            backups = self.updater_port.list_backups()
            return backups
        except Exception as e:
            logger.error(f"Error listing backups: {e}")
            return []

    def cleanup_old_backups(self, keep_count: int = 5) -> Dict[str, Any]:
        """Clean up old backups."""
        try:
            result = self.updater_port.cleanup_old_backups(keep_count)
            logger.info(f"Backup cleanup completed: {result}")
            return result
        except Exception as e:
            logger.error(f"Error cleaning up backups: {e}")
            return {
                "deleted_count": 0,
                "kept_count": 0,
                "total_size_freed": 0,
                "error": str(e),
            }

    def get_version_info(self) -> Dict[str, Any]:
        """Get version information."""
        try:
            version_info = self.updater_port.get_version_info()
            return version_info
        except Exception as e:
            logger.error(f"Error getting version info: {e}")
            return {
                "version": "unknown",
                "commit_hash": "unknown",
                "branch": "unknown",
                "git_status": "unknown",
                "build_date": "unknown",
            }

    def validate_update(self, version: str) -> bool:
        """Validate if update can be applied."""
        try:
            is_valid = self.updater_port.validate_update(version)
            return is_valid
        except Exception as e:
            logger.error(f"Error validating update {version}: {e}")
            return False

    def rollback_update(self) -> bool:
        """Rollback to previous version."""
        try:
            success = self.updater_port.rollback_update()
            if success:
                logger.info("System update rolled back successfully")
            else:
                logger.error("Failed to rollback system update")
            return success
        except Exception as e:
            logger.error(f"Error rolling back update: {e}")
            return False

    def get_system_stats(self) -> Dict[str, Any]:
        """Get system statistics."""
        try:
            system_config = self.get_system_config()
            total_bots = self.storage_port.get_bot_count()
            running_bots = self.storage_port.get_running_bot_count()
            
            stats = {
                "total_bots": total_bots,
                "running_bots": running_bots,
                "stopped_bots": total_bots - running_bots,
                "system_config": system_config.to_dict(),
            }
            
            logger.debug("Retrieved system statistics")
            return stats
        except Exception as e:
            logger.error(f"Error getting system stats: {e}")
            return {
                "total_bots": 0,
                "running_bots": 0,
                "stopped_bots": 0,
                "error": str(e),
            }

    def is_admin_user(self, user_id: int) -> bool:
        """Check if user is admin."""
        try:
            admin_config = self.get_admin_bot_config()
            return admin_config.is_admin_user(user_id)
        except Exception as e:
            logger.error(f"Error checking admin status for user {user_id}: {e}")
            return False

    def add_admin_user(self, user_id: int) -> None:
        """Add admin user."""
        try:
            admin_config = self.get_admin_bot_config()
            admin_config.add_admin_user(user_id)
            self.update_admin_bot_config(admin_config)
            logger.info(f"Added admin user: {user_id}")
        except Exception as e:
            logger.error(f"Error adding admin user {user_id}: {e}")
            raise

    def remove_admin_user(self, user_id: int) -> None:
        """Remove admin user."""
        try:
            admin_config = self.get_admin_bot_config()
            admin_config.remove_admin_user(user_id)
            self.update_admin_bot_config(admin_config)
            logger.info(f"Removed admin user: {user_id}")
        except Exception as e:
            logger.error(f"Error removing admin user {user_id}: {e}")
            raise

    def get_notification_settings(self) -> Dict[str, bool]:
        """Get notification settings."""
        try:
            admin_config = self.get_admin_bot_config()
            return admin_config.notifications
        except Exception as e:
            logger.error(f"Error getting notification settings: {e}")
            return {
                "bot_status": True,
                "high_cpu": True,
                "errors": True,
                "weekly_stats": True,
            }

    def update_notification_settings(self, notifications: Dict[str, bool]) -> None:
        """Update notification settings."""
        try:
            admin_config = self.get_admin_bot_config()
            admin_config.notifications.update(notifications)
            self.update_admin_bot_config(admin_config)
            logger.info("Notification settings updated")
        except Exception as e:
            logger.error(f"Error updating notification settings: {e}")
            raise










