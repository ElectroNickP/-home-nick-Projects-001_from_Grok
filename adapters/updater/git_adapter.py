"""
Git-based implementation of AutoUpdaterPort interface.

This adapter provides auto-update functionality using Git operations.
It implements the AutoUpdaterPort protocol and handles all update operations.
"""

import logging
import subprocess
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List
from threading import Lock

from core.ports.updater import AutoUpdaterPort

logger = logging.getLogger(__name__)


class GitAutoUpdaterAdapter(AutoUpdaterPort):
    """Git-based implementation of AutoUpdaterPort interface."""

    def __init__(self, repo_path: str = ".", backup_dir: str = "backups"):
        """Initialize the adapter with repository path."""
        self.repo_path = Path(repo_path)
        self.backup_dir = Path(backup_dir)
        self._lock = Lock()
        self._update_state: Dict[str, Any] = {
            "status": "idle",
            "last_check": None,
            "current_version": None,
            "available_version": None,
            "backup_id": None,
        }
        
        # Ensure backup directory exists
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Git updater adapter initialized: {self.repo_path}")

    def _run_git_command(self, command: List[str], timeout: int = 30) -> str:
        """Run git command and return output."""
        try:
            result = subprocess.run(
                command,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            logger.error(f"Git command failed: {' '.join(command)} - {e.stderr}")
            raise
        except subprocess.TimeoutExpired:
            logger.error(f"Git command timeout: {' '.join(command)}")
            raise

    def _get_git_status(self) -> str:
        """Get git repository status."""
        try:
            return self._run_git_command(["git", "status", "--porcelain"])
        except subprocess.CalledProcessError:
            return "unknown"

    def check_updates(self) -> Dict[str, Any]:
        """Check for available updates."""
        with self._lock:
            try:
                # Fetch latest changes
                self._run_git_command(["git", "fetch", "origin"])
                
                # Get current commit
                current_commit = self._run_git_command(["git", "rev-parse", "HEAD"])
                
                # Get latest commit from remote
                latest_commit = self._run_git_command(["git", "rev-parse", "origin/main"])
                
                # Get version info
                version_info = self.get_version_info()
                
                has_updates = current_commit != latest_commit
                
                self._update_state.update({
                    "last_check": datetime.now().isoformat(),
                    "current_version": current_commit[:8],
                    "available_version": latest_commit[:8] if has_updates else current_commit[:8],
                })
                
                return {
                    "has_updates": has_updates,
                    "current_version": current_commit[:8],
                    "available_version": latest_commit[:8] if has_updates else current_commit[:8],
                    "version_info": version_info,
                    "git_status": self._get_git_status(),
                }
                
            except Exception as e:
                logger.error(f"Failed to check updates: {e}")
                return {
                    "has_updates": False,
                    "error": str(e),
                    "current_version": "unknown",
                    "available_version": "unknown",
                }

    def apply_update(self, version: str) -> bool:
        """Apply update to specified version."""
        with self._lock:
            try:
                self._update_state["status"] = "updating"
                
                # Create backup before update
                backup_id = self.create_backup()
                self._update_state["backup_id"] = backup_id
                
                # Reset to specified version
                self._run_git_command(["git", "reset", "--hard", version])
                
                # Pull latest changes
                self._run_git_command(["git", "pull", "origin", "main"])
                
                self._update_state["status"] = "completed"
                self._update_state["current_version"] = version[:8]
                
                logger.info(f"Update applied successfully to version: {version[:8]}")
                return True
                
            except Exception as e:
                self._update_state["status"] = "failed"
                logger.error(f"Failed to apply update: {e}")
                return False

    def create_backup(self) -> str:
        """Create backup of current state."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_id = f"backup_{timestamp}"
        backup_path = self.backup_dir / backup_id
        
        try:
            # Create backup directory
            backup_path.mkdir(parents=True, exist_ok=True)
            
            # Copy current repository state
            shutil.copytree(
                self.repo_path,
                backup_path / "repo",
                ignore=shutil.ignore_patterns(
                    "venv", "__pycache__", "*.pyc", ".git", "backups", "*.log"
                )
            )
            
            # Save current git info
            git_info = {
                "commit": self._run_git_command(["git", "rev-parse", "HEAD"]),
                "branch": self._run_git_command(["git", "branch", "--show-current"]),
                "status": self._get_git_status(),
                "timestamp": timestamp,
            }
            
            import json
            with open(backup_path / "git_info.json", 'w') as f:
                json.dump(git_info, f, indent=2)
            
            logger.info(f"Backup created: {backup_id}")
            return backup_id
            
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            raise

    def restore_backup(self, backup_id: str) -> bool:
        """Restore from backup."""
        backup_path = self.backup_dir / backup_id
        
        if not backup_path.exists():
            logger.error(f"Backup not found: {backup_id}")
            return False
        
        try:
            # Restore repository state
            repo_backup = backup_path / "repo"
            if repo_backup.exists():
                # Remove current files (except .git)
                for item in self.repo_path.iterdir():
                    if item.name != ".git":
                        if item.is_dir():
                            shutil.rmtree(item)
                        else:
                            item.unlink()
                
                # Copy backup files
                for item in repo_backup.iterdir():
                    if item.is_dir():
                        shutil.copytree(item, self.repo_path / item.name)
                    else:
                        shutil.copy2(item, self.repo_path / item.name)
            
            logger.info(f"Backup restored: {backup_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to restore backup: {e}")
            return False

    def get_update_status(self) -> Dict[str, Any]:
        """Get current update status."""
        return self._update_state.copy()

    def list_backups(self) -> List[Dict[str, Any]]:
        """List available backups."""
        backups = []
        
        for backup_dir in self.backup_dir.iterdir():
            if backup_dir.is_dir() and backup_dir.name.startswith("backup_"):
                try:
                    git_info_file = backup_dir / "git_info.json"
                    if git_info_file.exists():
                        import json
                        with open(git_info_file, 'r') as f:
                            git_info = json.load(f)
                        
                        backups.append({
                            "id": backup_dir.name,
                            "created_at": datetime.fromisoformat(git_info["timestamp"]),
                            "commit": git_info["commit"][:8],
                            "branch": git_info["branch"],
                            "status": git_info["status"],
                        })
                except Exception as e:
                    logger.warning(f"Failed to read backup info for {backup_dir.name}: {e}")
        
        # Sort by creation time (newest first)
        backups.sort(key=lambda x: x["created_at"], reverse=True)
        return backups

    def cleanup_old_backups(self, keep_count: int = 5) -> Dict[str, Any]:
        """Clean up old backups, keeping specified number."""
        backups = self.list_backups()
        
        if len(backups) <= keep_count:
            return {
                "deleted_count": 0,
                "kept_count": len(backups),
                "total_size_freed": 0
            }
        
        # Remove old backups
        deleted_count = 0
        total_size_freed = 0
        
        for backup in backups[keep_count:]:
            backup_path = self.backup_dir / backup["id"]
            try:
                # Calculate size before deletion
                size = sum(f.stat().st_size for f in backup_path.rglob('*') if f.is_file())
                
                shutil.rmtree(backup_path)
                deleted_count += 1
                total_size_freed += size
                
                logger.info(f"Deleted old backup: {backup['id']}")
            except Exception as e:
                logger.error(f"Failed to delete backup {backup['id']}: {e}")
        
        return {
            "deleted_count": deleted_count,
            "kept_count": keep_count,
            "total_size_freed": total_size_freed
        }

    def get_version_info(self) -> Dict[str, Any]:
        """Get version information."""
        try:
            commit_hash = self._run_git_command(["git", "rev-parse", "HEAD"])
            branch = self._run_git_command(["git", "branch", "--show-current"])
            git_status = self._get_git_status()
            
            return {
                "version": "3.6.0",  # This could be read from pyproject.toml
                "commit_hash": commit_hash[:8],
                "branch": branch,
                "git_status": "clean" if not git_status else "dirty",
                "build_date": datetime.now().isoformat(),
            }
        except Exception as e:
            logger.error(f"Failed to get version info: {e}")
            return {
                "version": "unknown",
                "commit_hash": "unknown",
                "branch": "unknown",
                "git_status": "unknown",
                "build_date": datetime.now().isoformat(),
            }

    def validate_update(self, version: str) -> bool:
        """Validate if update can be applied."""
        try:
            # Check if commit exists
            self._run_git_command(["git", "cat-file", "-e", version])
            return True
        except subprocess.CalledProcessError:
            return False

    def rollback_update(self) -> bool:
        """Rollback to previous version."""
        if not self._update_state.get("backup_id"):
            logger.error("No backup available for rollback")
            return False
        
        return self.restore_backup(self._update_state["backup_id"])









