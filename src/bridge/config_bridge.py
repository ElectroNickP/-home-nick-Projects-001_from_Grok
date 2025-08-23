"""
Configuration Bridge for integrating old and new configuration systems.

This module provides a bridge between the existing config_manager and the new
hexagonal architecture's configuration system.
"""

import json
import logging
import threading
from typing import Dict, List, Optional, Any
from pathlib import Path

from core.domain.bot import BotConfig
from core.domain.config import SystemConfig, AdminBotConfig, MarketplaceConfig
from core.ports.storage import StoragePort

# Import existing config manager
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import config_manager as legacy_config

logger = logging.getLogger(__name__)


class ConfigBridge:
    """
    Bridge between legacy config_manager and new configuration system.
    
    This class provides seamless integration between the old global-variable-based
    configuration system and the new hexagonal architecture's configuration system.
    """
    
    def __init__(self, storage_port: StoragePort):
        """Initialize the configuration bridge."""
        self.storage_port = storage_port
        self._migration_lock = threading.Lock()
        self._sync_enabled = True
        
        logger.info("ConfigBridge initialized")
    
    def migrate_bot_configs(self) -> Dict[str, Any]:
        """
        Migrate bot configurations from legacy format to new format.
        
        Returns:
            Dict containing migration results and statistics
        """
        with self._migration_lock:
            logger.info("Starting bot configuration migration")
            
            migration_result = {
                "success": True,
                "migrated_bots": 0,
                "failed_bots": 0,
                "errors": [],
                "warnings": []
            }
            
            try:
                # Load legacy configurations
                with legacy_config.BOT_CONFIGS_LOCK:
                    legacy_bots = dict(legacy_config.BOT_CONFIGS)
                
                logger.info(f"Found {len(legacy_bots)} bots to migrate")
                
                # Convert each bot configuration
                for bot_id, legacy_bot_data in legacy_bots.items():
                    try:
                        # Convert legacy format to new format
                        new_bot_config = self._convert_legacy_bot_config(
                            bot_id, legacy_bot_data
                        )
                        
                        # Store in new system
                        self.storage_port.save_bot_config(bot_id, new_bot_config)
                        
                        migration_result["migrated_bots"] += 1
                        logger.debug(f"Successfully migrated bot {bot_id}")
                        
                    except Exception as e:
                        migration_result["failed_bots"] += 1
                        error_msg = f"Failed to migrate bot {bot_id}: {str(e)}"
                        migration_result["errors"].append(error_msg)
                        logger.error(error_msg)
                
                # Migrate system configuration
                self._migrate_system_config()
                
                logger.info(
                    f"Migration completed: {migration_result['migrated_bots']} "
                    f"success, {migration_result['failed_bots']} failures"
                )
                
            except Exception as e:
                migration_result["success"] = False
                migration_result["errors"].append(f"Migration failed: {str(e)}")
                logger.error(f"Bot configuration migration failed: {e}")
            
            return migration_result
    
    def _convert_legacy_bot_config(self, bot_id: int, legacy_data: Dict) -> BotConfig:
        """Convert legacy bot configuration to new format."""
        legacy_config_data = legacy_data.get("config", {})
        
        # Extract marketplace configuration
        marketplace_data = legacy_config_data.get("marketplace", {})
        marketplace_config = MarketplaceConfig(
            enabled=marketplace_data.get("enabled", False),
            title=marketplace_data.get("title", ""),
            description=marketplace_data.get("description", ""),
            category=marketplace_data.get("category", "general"),
            username=marketplace_data.get("username", ""),
            tags=marketplace_data.get("tags", [])
        )
        
        # Create new bot configuration
        bot_config = BotConfig(
            id=bot_id,
            name=legacy_config_data.get("bot_name", f"Bot {bot_id}"),
            token=legacy_config_data.get("telegram_token", ""),
            openai_api_key=legacy_config_data.get("openai_api_key", ""),
            assistant_id=legacy_config_data.get("assistant_id", ""),
            group_context_limit=legacy_config_data.get("group_context_limit", 15),
            enable_ai_responses=legacy_config_data.get("enable_ai_responses", True),
            enable_voice_responses=legacy_config_data.get("enable_voice_responses", False),
            marketplace=marketplace_config,
            voice_model=legacy_config_data.get("voice_model", "tts-1"),
            voice_type=legacy_config_data.get("voice_type", "alloy"),
            status=legacy_data.get("status", "stopped")
        )
        
        return bot_config
    
    def _migrate_system_config(self):
        """Migrate system configuration."""
        try:
            # Extract admin bot configuration
            admin_config = AdminBotConfig(
                enabled=legacy_config.ADMIN_BOT_CONFIG.get("enabled", False),
                token=legacy_config.ADMIN_BOT_CONFIG.get("token", ""),
                admin_users=legacy_config.ADMIN_BOT_CONFIG.get("admin_users", []),
                notifications=legacy_config.ADMIN_BOT_CONFIG.get("notifications", {})
            )
            
            # Create system configuration
            system_config = SystemConfig(
                admin_bot=admin_config,
                logging_level="INFO",
                secret_key="your-secret-key-change-in-production"
            )
            
            # Store system configuration
            self.storage_port.save_system_config(system_config)
            
            logger.info("System configuration migrated successfully")
            
        except Exception as e:
            logger.error(f"Failed to migrate system configuration: {e}")
            raise
    
    def sync_configurations(self, direction: str = "both") -> bool:
        """
        Synchronize configurations between old and new systems.
        
        Args:
            direction: "to_new", "to_legacy", or "both"
        
        Returns:
            True if synchronization was successful
        """
        if not self._sync_enabled:
            return True
        
        try:
            if direction in ["to_new", "both"]:
                self._sync_legacy_to_new()
            
            if direction in ["to_legacy", "both"]:
                self._sync_new_to_legacy()
            
            return True
            
        except Exception as e:
            logger.error(f"Configuration synchronization failed: {e}")
            return False
    
    def _sync_legacy_to_new(self):
        """Sync from legacy system to new system."""
        logger.debug("Syncing configurations from legacy to new system")
        
        with legacy_config.BOT_CONFIGS_LOCK:
            for bot_id, legacy_data in legacy_config.BOT_CONFIGS.items():
                try:
                    # Convert and save to new system
                    new_config = self._convert_legacy_bot_config(bot_id, legacy_data)
                    self.storage_port.save_bot_config(bot_id, new_config)
                    
                except Exception as e:
                    logger.warning(f"Failed to sync bot {bot_id} to new system: {e}")
    
    def _sync_new_to_legacy(self):
        """Sync from new system to legacy system."""
        logger.debug("Syncing configurations from new to legacy system")
        
        try:
            # Get all bot configs from new system
            new_bot_configs = self.storage_port.list_bot_configs()
            
            with legacy_config.BOT_CONFIGS_LOCK:
                for bot_id, new_config in new_bot_configs.items():
                    try:
                        # Convert to legacy format
                        legacy_data = self._convert_new_to_legacy_config(new_config)
                        legacy_config.BOT_CONFIGS[bot_id] = legacy_data
                        
                    except Exception as e:
                        logger.warning(f"Failed to sync bot {bot_id} to legacy system: {e}")
                
                # Save legacy configurations
                legacy_config.save_configs()
                
        except Exception as e:
            logger.error(f"Failed to sync from new to legacy system: {e}")
    
    def _convert_new_to_legacy_config(self, new_config: BotConfig) -> Dict:
        """Convert new bot configuration to legacy format."""
        return {
            "id": new_config.id,
            "config": {
                "bot_name": new_config.name,
                "telegram_token": new_config.token,
                "openai_api_key": new_config.openai_api_key,
                "assistant_id": new_config.assistant_id,
                "group_context_limit": new_config.group_context_limit,
                "enable_ai_responses": new_config.enable_ai_responses,
                "enable_voice_responses": new_config.enable_voice_responses,
                "marketplace": {
                    "enabled": new_config.marketplace.enabled,
                    "title": new_config.marketplace.title,
                    "description": new_config.marketplace.description,
                    "category": new_config.marketplace.category,
                    "username": new_config.marketplace.username,
                    "tags": new_config.marketplace.tags
                },
                "voice_model": new_config.voice_model,
                "voice_type": new_config.voice_type
            },
            "status": new_config.status,
            "thread": None,
            "loop": None,
            "stop_event": None
        }
    
    def validate_migration(self) -> Dict[str, Any]:
        """
        Validate that migration was successful by comparing configurations.
        
        Returns:
            Dict containing validation results
        """
        validation_result = {
            "success": True,
            "total_bots": 0,
            "valid_bots": 0,
            "invalid_bots": 0,
            "discrepancies": []
        }
        
        try:
            # Compare legacy and new configurations
            with legacy_config.BOT_CONFIGS_LOCK:
                legacy_bots = dict(legacy_config.BOT_CONFIGS)
            
            new_bots = self.storage_port.list_bot_configs()
            
            validation_result["total_bots"] = len(legacy_bots)
            
            for bot_id, legacy_data in legacy_bots.items():
                if bot_id not in new_bots:
                    validation_result["discrepancies"].append(
                        f"Bot {bot_id} exists in legacy but not in new system"
                    )
                    validation_result["invalid_bots"] += 1
                    continue
                
                # Compare configurations
                new_config = new_bots[bot_id]
                if self._configs_match(legacy_data, new_config):
                    validation_result["valid_bots"] += 1
                else:
                    validation_result["discrepancies"].append(
                        f"Bot {bot_id} configurations don't match"
                    )
                    validation_result["invalid_bots"] += 1
            
            # Check for bots that exist only in new system
            for bot_id in new_bots:
                if bot_id not in legacy_bots:
                    validation_result["discrepancies"].append(
                        f"Bot {bot_id} exists in new but not in legacy system"
                    )
            
            validation_result["success"] = (validation_result["invalid_bots"] == 0)
            
            logger.info(
                f"Validation completed: {validation_result['valid_bots']} valid, "
                f"{validation_result['invalid_bots']} invalid"
            )
            
        except Exception as e:
            validation_result["success"] = False
            validation_result["discrepancies"].append(f"Validation failed: {str(e)}")
            logger.error(f"Migration validation failed: {e}")
        
        return validation_result
    
    def _configs_match(self, legacy_data: Dict, new_config: BotConfig) -> bool:
        """Check if legacy and new configurations match."""
        try:
            legacy_config_data = legacy_data.get("config", {})
            
            # Compare basic fields
            return (
                legacy_config_data.get("bot_name") == new_config.name and
                legacy_config_data.get("telegram_token") == new_config.token and
                legacy_config_data.get("openai_api_key") == new_config.openai_api_key and
                legacy_config_data.get("assistant_id") == new_config.assistant_id and
                legacy_config_data.get("group_context_limit") == new_config.group_context_limit and
                legacy_config_data.get("enable_ai_responses") == new_config.enable_ai_responses and
                legacy_config_data.get("enable_voice_responses") == new_config.enable_voice_responses
            )
        except Exception:
            return False
    
    def enable_sync(self):
        """Enable automatic synchronization."""
        self._sync_enabled = True
        logger.info("Configuration synchronization enabled")
    
    def disable_sync(self):
        """Disable automatic synchronization."""
        self._sync_enabled = False
        logger.info("Configuration synchronization disabled")
    
    def get_migration_status(self) -> Dict[str, Any]:
        """Get current migration status."""
        try:
            # Count bots in both systems
            with legacy_config.BOT_CONFIGS_LOCK:
                legacy_count = len(legacy_config.BOT_CONFIGS)
            
            new_count = len(self.storage_port.list_bot_configs())
            
            return {
                "legacy_bots": legacy_count,
                "new_bots": new_count,
                "sync_enabled": self._sync_enabled,
                "migration_needed": legacy_count != new_count
            }
            
        except Exception as e:
            logger.error(f"Failed to get migration status: {e}")
            return {
                "error": str(e),
                "sync_enabled": self._sync_enabled
            }








