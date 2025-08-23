"""
Auto-update port interface.

Defines the contract for auto-update operations that external adapters must implement.
"""

from typing import Any, Protocol


class AutoUpdaterPort(Protocol):
    """Interface for auto-update operations."""

    def check_updates(self) -> dict[str, Any]:
        """Check for available updates.

        Returns:
            Update information dictionary with keys:
            - has_updates: bool
            - current_version: str
            - latest_version: str
            - update_message: str
            - commit_hash: str
        """
        ...

    def apply_update(self, version: str) -> bool:
        """Apply update to specified version.

        Args:
            version: Target version

        Returns:
            True if update successful
        """
        ...

    def create_backup(self) -> str:
        """Create backup before update.

        Returns:
            Backup ID
        """
        ...

    def restore_backup(self, backup_id: str) -> bool:
        """Restore from backup.

        Args:
            backup_id: Backup ID

        Returns:
            True if restore successful
        """
        ...

    def get_update_status(self) -> dict[str, Any]:
        """Get current update status.

        Returns:
            Status dictionary with keys:
            - status: str (idle, checking, backing_up, updating, restarting, completed, failed)
            - progress: int (0-100)
            - message: str
            - start_time: datetime
            - error: str or None
        """
        ...

    def list_backups(self) -> list[dict[str, Any]]:
        """List available backups.

        Returns:
            List of backup dictionaries with keys:
            - id: str
            - created_at: datetime
            - size: int
            - description: str
        """
        ...

    def cleanup_old_backups(self, keep_count: int = 5) -> dict[str, Any]:
        """Clean up old backups.

        Args:
            keep_count: Number of backups to keep

        Returns:
            Cleanup result dictionary
        """
        ...

    def get_version_info(self) -> dict[str, Any]:
        """Get version information.

        Returns:
            Version information dictionary with keys:
            - version: str
            - commit_hash: str
            - build_date: datetime
            - git_status: str
        """
        ...

    def validate_update(self, version: str) -> bool:
        """Validate update before applying.

        Args:
            version: Version to validate

        Returns:
            True if update is valid
        """
        ...

    def rollback_update(self) -> bool:
        """Rollback last update.

        Returns:
            True if rollback successful
        """
        ...










