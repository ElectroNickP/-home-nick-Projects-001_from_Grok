"""
System management use cases.

This module contains business logic for system-wide operations,
including configuration management, updates, and monitoring.
"""

import logging
import psutil
from typing import Dict, List, Optional, Any
from datetime import datetime

from core.domain.config import SystemConfig, AdminBotConfig
from core.ports.storage import ConfigStoragePort
from core.ports.updater import AutoUpdaterPort

logger = logging.getLogger(__name__)


class SystemManagementUseCase:
    """Use case for system management."""

    def __init__(
        self,
        storage_port: ConfigStoragePort,
        updater_port: AutoUpdaterPort,
    ):
        """Initialize the use case with required ports."""
        self.storage_port = storage_port
        self.updater_port = updater_port

    def get_system_config(self) -> SystemConfig:
        """Get system configuration."""
        try:
            config_data = self.storage_port.read_config()
            system_config_data = config_data.get("system_config", {})
            
            return SystemConfig.from_dict(system_config_data)
            
        except Exception as e:
            logger.error(f"Failed to get system config: {e}")
            # Return default config
            return SystemConfig()

    def update_system_config(self, new_config: SystemConfig) -> bool:
        """Update system configuration."""
        try:
            # Validate configuration
            errors = new_config.validate()
            if errors:
                raise ValueError(f"Invalid system configuration: {', '.join(errors)}")

            # Save to storage
            self.storage_port.write_config({
                "system_config": new_config.to_dict()
            })
            
            logger.info("System configuration updated successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update system config: {e}")
            return False

    def get_admin_bot_config(self) -> AdminBotConfig:
        """Get admin bot configuration."""
        try:
            config_data = self.storage_port.read_config()
            admin_bot_data = config_data.get("admin_bot", {})
            
            return AdminBotConfig.from_dict(admin_bot_data)
            
        except Exception as e:
            logger.error(f"Failed to get admin bot config: {e}")
            # Return default config
            return AdminBotConfig()

    def update_admin_bot_config(self, new_config: AdminBotConfig) -> bool:
        """Update admin bot configuration."""
        try:
            # Validate configuration
            errors = new_config.validate()
            if errors:
                raise ValueError(f"Invalid admin bot configuration: {', '.join(errors)}")

            # Save to storage
            self.storage_port.write_config({
                "admin_bot": new_config.to_dict()
            })
            
            logger.info("Admin bot configuration updated successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update admin bot config: {e}")
            return False

    def get_system_health(self) -> Dict[str, Any]:
        """Get system health status."""
        try:
            # Get system metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Get bot statistics
            total_bots = self.storage_port.get_bot_count()
            running_bots = self.storage_port.get_running_bot_count()
            
            # Determine overall health
            health_status = "healthy"
            if cpu_percent > 80 or memory.percent > 80 or disk.percent > 90:
                health_status = "warning"
            if cpu_percent > 95 or memory.percent > 95 or disk.percent > 95:
                health_status = "critical"
            
            return {
                "status": health_status,
                "timestamp": datetime.now().isoformat(),
                "checks": {
                    "cpu": "healthy" if cpu_percent < 80 else "warning",
                    "memory": "healthy" if memory.percent < 80 else "warning",
                    "disk": "healthy" if disk.percent < 90 else "warning",
                    "bots": "healthy" if running_bots > 0 else "warning",
                },
                "metrics": {
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory.percent,
                    "disk_percent": disk.percent,
                    "total_bots": total_bots,
                    "running_bots": running_bots,
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get system health: {e}")
            return {
                "status": "error",
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }

    def get_system_info(self) -> Dict[str, Any]:
        """Get detailed system information."""
        try:
            # System information
            boot_time = datetime.fromtimestamp(psutil.boot_time())
            cpu_count = psutil.cpu_count()
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Application information
            process = psutil.Process()
            process_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            # Bot information
            total_bots = self.storage_port.get_bot_count()
            running_bots = self.storage_port.get_running_bot_count()
            
            return {
                "system": {
                    "boot_time": boot_time.strftime("%Y-%m-%d %H:%M:%S"),
                    "cpu_cores": cpu_count,
                    "cpu_percent": psutil.cpu_percent(interval=1),
                    "memory": {
                        "total_gb": round(memory.total / 1024 / 1024 / 1024, 2),
                        "available_gb": round(memory.available / 1024 / 1024 / 1024, 2),
                        "used_percent": memory.percent,
                    },
                    "disk": {
                        "total_gb": round(disk.total / 1024 / 1024 / 1024, 2),
                        "free_gb": round(disk.free / 1024 / 1024 / 1024, 2),
                        "used_percent": disk.percent,
                    }
                },
                "application": {
                    "name": "Telegram Bot Manager",
                    "python_version": f"{psutil.sys.version_info.major}.{psutil.sys.version_info.minor}.{psutil.sys.version_info.micro}",
                    "process_memory_mb": round(process_memory, 1),
                    "uptime_seconds": (datetime.now() - boot_time).total_seconds(),
                },
                "bots": {
                    "total": total_bots,
                    "running": running_bots,
                    "stopped": total_bots - running_bots,
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get system info: {e}")
            return {"error": str(e)}

    def get_system_stats(self) -> Dict[str, Any]:
        """Get system statistics."""
        try:
            # Current metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Bot statistics
            total_bots = self.storage_port.get_bot_count()
            running_bots = self.storage_port.get_running_bot_count()
            
            # Process information
            process = psutil.Process()
            process_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            return {
                "system": {
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory.percent,
                    "disk_percent": disk.percent,
                },
                "application": {
                    "process_cpu_percent": process.cpu_percent(),
                    "process_memory_mb": round(process_memory, 1),
                    "uptime_seconds": (datetime.now() - datetime.fromtimestamp(psutil.boot_time())).total_seconds(),
                    "files": {
                        "config_size_kb": 0,  # Would need to implement file size checking
                        "log_size_kb": 0,     # Would need to implement file size checking
                    }
                },
                "bots": {
                    "total": total_bots,
                    "running": running_bots,
                    "stopped": total_bots - running_bots,
                    "voice_enabled": 0,  # Would need to implement this
                    "voice_disabled": total_bots,  # Would need to implement this
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get system stats: {e}")
            return {"error": str(e)}

    def check_updates(self) -> Dict[str, Any]:
        """Check for system updates."""
        try:
            return self.updater_port.check_updates()
            
        except Exception as e:
            logger.error(f"Failed to check updates: {e}")
            return {
                "has_updates": False,
                "error": str(e),
                "current_version": "unknown",
                "available_version": "unknown",
            }

    def apply_update(self, version: str) -> bool:
        """Apply system update."""
        try:
            return self.updater_port.apply_update(version)
            
        except Exception as e:
            logger.error(f"Failed to apply update: {e}")
            return False

    def create_backup(self) -> str:
        """Create system backup."""
        try:
            return self.updater_port.create_backup()
            
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            raise

    def restore_backup(self, backup_id: str) -> bool:
        """Restore system from backup."""
        try:
            return self.updater_port.restore_backup(backup_id)
            
        except Exception as e:
            logger.error(f"Failed to restore backup: {e}")
            return False

    def get_backups(self) -> List[Dict[str, Any]]:
        """Get list of available backups."""
        try:
            return self.updater_port.list_backups()
            
        except Exception as e:
            logger.error(f"Failed to get backups: {e}")
            return []

    def cleanup_old_backups(self, keep_count: int = 5) -> Dict[str, Any]:
        """Clean up old backups."""
        try:
            return self.updater_port.cleanup_old_backups(keep_count)
            
        except Exception as e:
            logger.error(f"Failed to cleanup old backups: {e}")
            return {
                "deleted_count": 0,
                "kept_count": 0,
                "total_size_freed": 0,
                "error": str(e)
            }

    def get_version_info(self) -> Dict[str, Any]:
        """Get version information."""
        try:
            return self.updater_port.get_version_info()
            
        except Exception as e:
            logger.error(f"Failed to get version info: {e}")
            return {
                "version": "unknown",
                "commit_hash": "unknown",
                "branch": "unknown",
                "git_status": "unknown",
                "build_date": datetime.now().isoformat(),
                "error": str(e)
            }










