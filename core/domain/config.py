"""
System configuration domain entities.

This module contains system configuration entities and related domain logic
that represents system-wide settings and admin bot configuration.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional


@dataclass
class AdminBotConfig:
    """Admin bot configuration value object."""
    
    enabled: bool = False
    token: str = ""
    admin_users: List[int] = field(default_factory=list)
    notifications: Dict[str, bool] = field(default_factory=lambda: {
        "bot_status": True,
        "high_cpu": True,
        "errors": True,
        "weekly_stats": True,
    })
    
    def validate(self) -> List[str]:
        """Validate admin bot configuration and return list of errors."""
        errors = []
        
        if self.enabled and not self.token:
            errors.append("Admin bot token is required when enabled")
        
        if self.enabled and not self.admin_users:
            errors.append("At least one admin user is required when enabled")
        
        if self.token and not self.token.startswith("5"):
            errors.append("Invalid admin bot token format")
        
        return errors
    
    def is_admin_user(self, user_id: int) -> bool:
        """Check if user is an admin."""
        return user_id in self.admin_users
    
    def add_admin_user(self, user_id: int) -> None:
        """Add admin user."""
        if user_id not in self.admin_users:
            self.admin_users.append(user_id)
    
    def remove_admin_user(self, user_id: int) -> None:
        """Remove admin user."""
        if user_id in self.admin_users:
            self.admin_users.remove(user_id)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "enabled": self.enabled,
            "token": self.token,
            "admin_users": self.admin_users,
            "notifications": self.notifications,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AdminBotConfig":
        """Create configuration from dictionary."""
        return cls(
            enabled=data.get("enabled", False),
            token=data.get("token", ""),
            admin_users=data.get("admin_users", []),
            notifications=data.get("notifications", {
                "bot_status": True,
                "high_cpu": True,
                "errors": True,
                "weekly_stats": True,
            }),
        )


@dataclass
class SystemConfig:
    """System configuration domain entity."""
    
    version: str = "3.6.0"
    debug_mode: bool = False
    log_level: str = "INFO"
    max_bots: int = 100
    auto_update_enabled: bool = True
    backup_retention_days: int = 30
    admin_bot: AdminBotConfig = field(default_factory=AdminBotConfig)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def validate(self) -> List[str]:
        """Validate system configuration and return list of errors."""
        errors = []
        
        if not self.version:
            errors.append("System version is required")
        
        if self.max_bots <= 0:
            errors.append("Maximum bots must be positive")
        
        if self.backup_retention_days <= 0:
            errors.append("Backup retention days must be positive")
        
        # Validate admin bot config
        admin_errors = self.admin_bot.validate()
        errors.extend(admin_errors)
        
        return errors
    
    def update_admin_bot_config(self, new_config: AdminBotConfig) -> None:
        """Update admin bot configuration."""
        errors = new_config.validate()
        if errors:
            raise ValueError(f"Invalid admin bot configuration: {', '.join(errors)}")
        
        self.admin_bot = new_config
        self.updated_at = datetime.now()
    
    def is_auto_update_enabled(self) -> bool:
        """Check if auto-update is enabled."""
        return self.auto_update_enabled
    
    def get_backup_retention_days(self) -> int:
        """Get backup retention period in days."""
        return self.backup_retention_days
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert system configuration to dictionary."""
        return {
            "version": self.version,
            "debug_mode": self.debug_mode,
            "log_level": self.log_level,
            "max_bots": self.max_bots,
            "auto_update_enabled": self.auto_update_enabled,
            "backup_retention_days": self.backup_retention_days,
            "admin_bot": self.admin_bot.to_dict(),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SystemConfig":
        """Create system configuration from dictionary."""
        return cls(
            version=data.get("version", "3.6.0"),
            debug_mode=data.get("debug_mode", False),
            log_level=data.get("log_level", "INFO"),
            max_bots=data.get("max_bots", 100),
            auto_update_enabled=data.get("auto_update_enabled", True),
            backup_retention_days=data.get("backup_retention_days", 30),
            admin_bot=AdminBotConfig.from_dict(data.get("admin_bot", {})),
            created_at=datetime.fromisoformat(data.get("created_at", datetime.now().isoformat())),
            updated_at=datetime.fromisoformat(data.get("updated_at", datetime.now().isoformat())),
        )









