"""
Legacy Configuration Adapter.

This adapter provides backward compatibility with the existing config_manager.py
while gradually migrating to the new external configuration system.
"""

import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional

from .external_config_manager import ExternalConfigManager
from .config_migrator import ConfigMigrator

logger = logging.getLogger(__name__)


class LegacyConfigAdapter:
    """
    Adapter to bridge old config_manager.py with new external config system.
    
    This allows existing code to work unchanged while providing a migration path.
    """
    
    def __init__(self, project_root: Optional[Path] = None):
        """Initialize the adapter."""
        self.project_root = project_root or Path.cwd()
        self.external_manager = ExternalConfigManager()
        self.migrator = ConfigMigrator(self.external_manager)
        
        # Legacy file paths
        self.legacy_config_file = self.project_root / "bot_configs.json"
        self.legacy_src_config_file = self.project_root / "src" / "bot_configs.json"
        
        self._migration_attempted = False
        self._use_external = self._should_use_external()
    
    def _should_use_external(self) -> bool:
        """Determine if we should use external config system."""
        # Check if external config is initialized and has data
        if self.external_manager.is_initialized():
            try:
                config = self.external_manager.load_config()
                # If external config has bots, use it
                if config.get("bots"):
                    return True
            except Exception as e:
                logger.warning(f"Failed to load external config: {e}")
        
        return False
    
    def _attempt_auto_migration(self) -> bool:
        """Attempt automatic migration from legacy config."""
        if self._migration_attempted:
            return False
        
        self._migration_attempted = True
        
        # Find legacy config file
        legacy_file = None
        if self.legacy_config_file.exists():
            legacy_file = self.legacy_config_file
        elif self.legacy_src_config_file.exists():
            legacy_file = self.legacy_src_config_file
        
        if not legacy_file:
            logger.info("No legacy config file found for migration")
            return False
        
        try:
            logger.info(f"Attempting auto-migration from {legacy_file}")
            success = self.external_manager.migrate_from_internal_config(legacy_file)
            
            if success:
                logger.info("Auto-migration completed successfully")
                self._use_external = True
                return True
            else:
                logger.warning("Auto-migration failed, falling back to legacy system")
                return False
                
        except Exception as e:
            logger.error(f"Auto-migration error: {e}")
            return False
    
    def load_configs(self) -> Dict[str, Any]:
        """Load configurations (mimics legacy load_configs function)."""
        if self._use_external or self._attempt_auto_migration():
            # Use external system
            try:
                config = self.external_manager.load_config()
                secrets = self.external_manager.load_secrets()
                
                # Transform to legacy format for compatibility
                return self._transform_to_legacy_format(config, secrets)
                
            except Exception as e:
                logger.error(f"Failed to load external config: {e}")
                # Fall back to legacy system
                return self._load_legacy_config()
        else:
            # Use legacy system
            return self._load_legacy_config()
    
    def save_configs(self, bot_configs: Dict[str, Any]) -> None:
        """Save configurations (mimics legacy save_configs function)."""
        if self._use_external:
            try:
                # Transform from legacy format
                config, secrets = self._transform_from_legacy_format(bot_configs)
                
                # Save to external system
                self.external_manager.save_config(config)
                if secrets:
                    existing_secrets = self.external_manager.load_secrets()
                    existing_secrets.update(secrets)
                    self.external_manager.save_secrets(existing_secrets)
                
                logger.debug("Configurations saved to external system")
                return
                
            except Exception as e:
                logger.error(f"Failed to save to external config: {e}")
                # Fall back to legacy save
        
        # Save using legacy system
        self._save_legacy_config(bot_configs)
    
    def _load_legacy_config(self) -> Dict[str, Any]:
        """Load configuration using legacy method."""
        import json
        
        config_file = self.legacy_config_file
        if not config_file.exists():
            config_file = self.legacy_src_config_file
        
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                logger.debug(f"Legacy config loaded from {config_file}")
                return data.get("bots", {})
            except Exception as e:
                logger.error(f"Failed to load legacy config: {e}")
        
        return {}
    
    def _save_legacy_config(self, bot_configs: Dict[str, Any]) -> None:
        """Save configuration using legacy method."""
        import json
        import threading
        
        config_file = self.legacy_config_file
        if not config_file.exists():
            config_file = self.legacy_src_config_file
        
        try:
            # Prepare data in legacy format
            data = {"bots": bot_configs}
            
            # Atomic write
            temp_file = config_file.with_suffix('.tmp')
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            temp_file.replace(config_file)
            
            logger.debug(f"Legacy config saved to {config_file}")
            
        except Exception as e:
            logger.error(f"Failed to save legacy config: {e}")
    
    def _transform_to_legacy_format(self, config: Dict[str, Any], secrets: Dict[str, str]) -> Dict[str, Any]:
        """Transform external config format to legacy format."""
        legacy_bots = {}
        
        for bot_id, bot_data in config.get("bots", {}).items():
            bot_config = bot_data.get("config", {}).copy()
            
            # Resolve secret references
            if "telegram_token_ref" in bot_config:
                token_ref = bot_config["telegram_token_ref"]
                if token_ref in secrets:
                    bot_config["telegram_token"] = secrets[token_ref]
                del bot_config["telegram_token_ref"]
            
            if "openai_api_key_ref" in bot_config:
                key_ref = bot_config["openai_api_key_ref"]
                if key_ref in secrets:
                    bot_config["openai_api_key"] = secrets[key_ref]
                del bot_config["openai_api_key_ref"]
            
            # Remove timestamps and other new fields for legacy compatibility
            bot_config.pop("created_at", None)
            bot_config.pop("updated_at", None)
            bot_config.pop("features", None)
            
            legacy_bots[bot_id] = {
                "id": bot_data.get("id"),
                "config": bot_config,
                "status": bot_data.get("status", "stopped")
            }
        
        return legacy_bots
    
    def _transform_from_legacy_format(self, legacy_bots: Dict[str, Any]) -> tuple[Dict[str, Any], Dict[str, str]]:
        """Transform legacy format to external config format."""
        from datetime import datetime
        
        config = self.external_manager._get_default_config()
        secrets = {}
        
        for bot_id, bot_data in legacy_bots.items():
            if "config" in bot_data:
                bot_config = bot_data["config"].copy()
                
                # Extract secrets
                if "telegram_token" in bot_config:
                    token_ref = f"bot_{bot_id}_telegram_token"
                    secrets[token_ref] = bot_config["telegram_token"]
                    bot_config["telegram_token_ref"] = token_ref
                    del bot_config["telegram_token"]
                
                if "openai_api_key" in bot_config:
                    key_ref = f"bot_{bot_id}_openai_key"
                    secrets[key_ref] = bot_config["openai_api_key"]
                    bot_config["openai_api_key_ref"] = key_ref
                    del bot_config["openai_api_key"]
                
                # Add new fields
                bot_config.setdefault("created_at", datetime.now().isoformat())
                bot_config["updated_at"] = datetime.now().isoformat()
                
                if "features" not in bot_config:
                    bot_config["features"] = {
                        "auto_responses": True,
                        "command_handling": True,
                        "file_processing": True,
                        "image_generation": False,
                        "web_search": False
                    }
                
                config["bots"][bot_id] = {
                    "id": bot_data.get("id", int(bot_id)),
                    "config": bot_config,
                    "status": bot_data.get("status", "stopped")
                }
        
        return config, secrets
    
    def get_config_status(self) -> Dict[str, Any]:
        """Get status of configuration system."""
        return {
            "using_external": self._use_external,
            "external_initialized": self.external_manager.is_initialized(),
            "legacy_file_exists": self.legacy_config_file.exists() or self.legacy_src_config_file.exists(),
            "migration_attempted": self._migration_attempted,
            "config_directory": str(self.external_manager.get_config_path())
        }
    
    def force_migration(self) -> bool:
        """Force migration to external config system."""
        try:
            # Find legacy config
            legacy_file = None
            if self.legacy_config_file.exists():
                legacy_file = self.legacy_config_file
            elif self.legacy_src_config_file.exists():
                legacy_file = self.legacy_src_config_file
            
            if not legacy_file:
                logger.warning("No legacy config file found to migrate")
                return False
            
            # Perform migration
            success = self.external_manager.migrate_from_internal_config(legacy_file)
            
            if success:
                self._use_external = True
                logger.info("Forced migration completed successfully")
            
            return success
            
        except Exception as e:
            logger.error(f"Forced migration failed: {e}")
            return False
    
    def get_external_manager(self) -> ExternalConfigManager:
        """Get the external config manager instance."""
        return self.external_manager
    
    def get_migrator(self) -> ConfigMigrator:
        """Get the config migrator instance."""
        return self.migrator


# Global instance for backward compatibility
_global_adapter: Optional[LegacyConfigAdapter] = None


def get_adapter() -> LegacyConfigAdapter:
    """Get the global legacy adapter instance."""
    global _global_adapter
    if _global_adapter is None:
        _global_adapter = LegacyConfigAdapter()
    return _global_adapter


# Compatibility functions for existing code
def load_configs() -> Dict[str, Any]:
    """Legacy compatibility function."""
    return get_adapter().load_configs()


def save_configs(bot_configs: Dict[str, Any]) -> None:
    """Legacy compatibility function."""
    get_adapter().save_configs(bot_configs)


def save_configs_async(bot_configs: Dict[str, Any]) -> None:
    """Legacy compatibility function (async version)."""
    import threading
    
    def save_task():
        save_configs(bot_configs)
    
    thread = threading.Thread(target=save_task, daemon=True)
    thread.start()





