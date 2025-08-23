"""
System schemas for FastAPI application.

This module contains Pydantic models for system-related API requests and responses.
"""


from pydantic import BaseModel, Field


class SystemConfigRequest(BaseModel):
    """Request model for system configuration."""
    auto_update_enabled: bool = Field(..., description="Enable auto updates")
    backup_enabled: bool = Field(..., description="Enable backups")
    backup_interval_hours: int = Field(..., description="Backup interval in hours")
    max_backups: int = Field(..., description="Maximum number of backups")
    log_level: str = Field(..., description="Log level")
    notification_email: str | None = Field(None, description="Notification email")


class SystemConfigResponse(BaseModel):
    """Response model for system configuration."""
    auto_update_enabled: bool = Field(..., description="Enable auto updates")
    backup_enabled: bool = Field(..., description="Enable backups")
    backup_interval_hours: int = Field(..., description="Backup interval in hours")
    max_backups: int = Field(..., description="Maximum number of backups")
    log_level: str = Field(..., description="Log level")
    notification_email: str | None = Field(None, description="Notification email")


class SystemStatusResponse(BaseModel):
    """Response model for system status."""
    total_bots: int = Field(..., description="Total number of bots")
    running_bots: int = Field(..., description="Number of running bots")
    stopped_bots: int = Field(..., description="Number of stopped bots")
    uptime: str = Field(..., description="System uptime")
    memory_usage: str = Field(..., description="Memory usage")
    cpu_usage: str = Field(..., description="CPU usage")
    disk_usage: str = Field(..., description="Disk usage")
    network_connections: str = Field(..., description="Network connections")


class BackupResponse(BaseModel):
    """Response model for backup operations."""
    backup_path: str = Field(..., description="Backup file path")
    size: str = Field(..., description="Backup size")
    created_at: str = Field(..., description="Creation timestamp")


class UpdateResponse(BaseModel):
    """Response model for update operations."""
    success: bool = Field(..., description="Update success status")
    message: str = Field(..., description="Update message")
    version: str | None = Field(None, description="New version")









