"""
System API routes for FastAPI application.

This module provides REST API endpoints for system management operations.
"""

import logging
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, status

from ...usecases import SystemUseCase
from ..schemas import (
    SystemConfigRequest, SystemConfigResponse, SystemStatusResponse,
    BackupResponse, UpdateResponse
)
from ...domain.entities import SystemConfig, AdminBotConfig


# Create router
system_router = APIRouter()
system_router.usecase: Optional[SystemUseCase] = None

logger = logging.getLogger(__name__)


@system_router.get("/status", response_model=SystemStatusResponse)
async def get_system_status():
    """Get system status."""
    try:
        stats = system_router.usecase.get_system_stats()
        
        return SystemStatusResponse(
            total_bots=stats.get('total_bots', 0),
            running_bots=stats.get('running_bots', 0),
            stopped_bots=stats.get('stopped_bots', 0),
            uptime=stats.get('uptime', 'Unknown'),
            memory_usage=stats.get('memory_usage', 'Unknown'),
            cpu_usage=stats.get('cpu_usage', 'Unknown'),
            disk_usage=stats.get('disk_usage', 'Unknown'),
            network_connections=stats.get('network_connections', 'Unknown')
        )
        
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get system status"
        )


@system_router.get("/config", response_model=SystemConfigResponse)
async def get_system_config():
    """Get system configuration."""
    try:
        config = system_router.usecase.get_system_config()
        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="System configuration not found"
            )
        
        return SystemConfigResponse(
            auto_update_enabled=config.auto_update_enabled,
            backup_enabled=config.backup_enabled,
            backup_interval_hours=config.backup_interval_hours,
            max_backups=config.max_backups,
            log_level=config.log_level,
            notification_email=config.notification_email
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting system config: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get system configuration"
        )


@system_router.put("/config", response_model=SystemConfigResponse)
async def update_system_config(config_request: SystemConfigRequest):
    """Update system configuration."""
    try:
        system_config = SystemConfig(
            auto_update_enabled=config_request.auto_update_enabled,
            backup_enabled=config_request.backup_enabled,
            backup_interval_hours=config_request.backup_interval_hours,
            max_backups=config_request.max_backups,
            log_level=config_request.log_level,
            notification_email=config_request.notification_email
        )
        
        success = system_router.usecase.update_system_config(system_config)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update system configuration"
            )
        
        return SystemConfigResponse(
            auto_update_enabled=system_config.auto_update_enabled,
            backup_enabled=system_config.backup_enabled,
            backup_interval_hours=system_config.backup_interval_hours,
            max_backups=system_config.max_backups,
            log_level=system_config.log_level,
            notification_email=system_config.notification_email
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating system config: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update system configuration"
        )


@system_router.post("/backup", response_model=BackupResponse)
async def create_backup():
    """Create system backup."""
    try:
        backup_path = system_router.usecase.create_backup()
        if not backup_path:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create backup"
            )
        
        return BackupResponse(
            backup_path=backup_path,
            size="Unknown",  # Would need to get actual file size
            created_at="Unknown"  # Would need to get actual timestamp
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating backup: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create backup"
        )


@system_router.get("/backups")
async def list_backups():
    """List system backups."""
    try:
        backups = system_router.usecase.list_backups()
        
        backup_responses = []
        for backup in backups:
            backup_responses.append(BackupResponse(
                backup_path=backup.get('filename', ''),
                size=backup.get('size', 'Unknown'),
                created_at=backup.get('created', 'Unknown')
            ))
        
        return {
            "backups": backup_responses,
            "total": len(backup_responses)
        }
        
    except Exception as e:
        logger.error(f"Error listing backups: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list backups"
        )


@system_router.post("/backups/{backup_file}/restore")
async def restore_backup(backup_file: str):
    """Restore system from backup."""
    try:
        success = system_router.usecase.restore_backup(backup_file)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to restore backup"
            )
        
        return {
            "message": f"System restored successfully from {backup_file}",
            "backup_file": backup_file
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error restoring backup {backup_file}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to restore backup"
        )


@system_router.post("/update", response_model=UpdateResponse)
async def apply_update():
    """Apply system update."""
    try:
        success = system_router.usecase.apply_update()
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to apply update"
            )
        
        return UpdateResponse(
            success=True,
            message="System update applied successfully",
            version=None  # Would need to get actual version
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error applying update: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to apply update"
        )


@system_router.get("/update/check")
async def check_updates():
    """Check for available updates."""
    try:
        update_info = system_router.usecase.check_updates()
        if not update_info:
            return {
                "update_available": False,
                "current_version": "Unknown",
                "latest_version": "Unknown",
                "changelog": None
            }
        
        return {
            "update_available": update_info.get('update_available', False),
            "current_version": update_info.get('current_version', 'Unknown'),
            "latest_version": update_info.get('latest_version', 'Unknown'),
            "changelog": update_info.get('changelog')
        }
        
    except Exception as e:
        logger.error(f"Error checking updates: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check for updates"
        )


@system_router.post("/cleanup")
async def cleanup_backups():
    """Clean up old backups."""
    try:
        success = system_router.usecase.cleanup_old_backups()
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to clean up old backups"
            )
        
        return {
            "message": "Old backups cleaned up successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cleaning up backups: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to clean up old backups"
        )


@system_router.get("/validate")
async def validate_system():
    """Validate system configuration."""
    try:
        # Check system config
        config = system_router.usecase.get_system_config()
        config_valid = config is not None
        
        # Check admin bot config
        admin_config = system_router.usecase.get_admin_bot_config()
        admin_config_valid = admin_config is not None
        
        # Check system stats
        try:
            stats = system_router.usecase.get_system_stats()
            stats_valid = True
        except Exception:
            stats_valid = False
        
        return {
            "system_config_valid": config_valid,
            "admin_config_valid": admin_config_valid,
            "system_stats_valid": stats_valid,
            "overall_valid": config_valid and admin_config_valid and stats_valid
        }
        
    except Exception as e:
        logger.error(f"Error validating system: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to validate system"
        )


@system_router.get("/info")
async def get_system_info():
    """Get detailed system information."""
    try:
        config = system_router.usecase.get_system_config()
        admin_config = system_router.usecase.get_admin_bot_config()
        stats = system_router.usecase.get_system_stats()
        
        return {
            "system_config": {
                "auto_update_enabled": config.auto_update_enabled if config else None,
                "backup_enabled": config.backup_enabled if config else None,
                "backup_interval_hours": config.backup_interval_hours if config else None,
                "max_backups": config.max_backups if config else None,
                "log_level": config.log_level if config else None,
                "notification_email": config.notification_email if config else None
            },
            "admin_bot_config": {
                "enabled": admin_config.enabled if admin_config else None,
                "username": admin_config.username if admin_config else None,
                "webhook_url": admin_config.webhook_url if admin_config else None
            },
            "system_stats": stats
        }
        
    except Exception as e:
        logger.error(f"Error getting system info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get system information"
        )










