"""
JSON file implementation of ConfigStoragePort interface.

This adapter provides configuration storage functionality using JSON files.
It implements the ConfigStoragePort protocol and handles all storage operations.
"""

import json
import logging
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional
from threading import Lock

from core.ports.storage import ConfigStoragePort

logger = logging.getLogger(__name__)


class JsonConfigStorageAdapter(ConfigStoragePort):
    """JSON file-based implementation of ConfigStoragePort interface."""

    def __init__(self, config_file: str = "bot_configs.json", backup_dir: str = "backups"):
        """Initialize the adapter with config file path."""
        self.config_file = Path(config_file)
        self.backup_dir = Path(backup_dir)
        self._lock = Lock()
        self._cache: Optional[Dict[str, Any]] = None
        
        # Ensure directories exist
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"JSON storage adapter initialized: {self.config_file}")

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file with caching."""
        if self._cache is not None:
            return self._cache.copy()
        
        with self._lock:
            if self.config_file.exists():
                try:
                    with open(self.config_file, 'r', encoding='utf-8') as f:
                        self._cache = json.load(f)
                    logger.debug(f"Configuration loaded from {self.config_file}")
                except (json.JSONDecodeError, IOError) as e:
                    logger.error(f"Failed to load config: {e}")
                    self._cache = {"bots": {}, "conversations": {}, "admin_bot": {}}
            else:
                self._cache = {"bots": {}, "conversations": {}, "admin_bot": {}}
                logger.info(f"Created new config file: {self.config_file}")
            
            return self._cache.copy()

    def _save_config(self, config: Dict[str, Any]) -> None:
        """Save configuration to file."""
        with self._lock:
            try:
                # Create backup before saving
                if self.config_file.exists():
                    backup_path = self.backup_dir / f"config_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                    shutil.copy2(self.config_file, backup_path)
                    logger.debug(f"Backup created: {backup_path}")
                
                # Save new config
                with open(self.config_file, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=2, ensure_ascii=False)
                
                self._cache = config
                logger.debug(f"Configuration saved to {self.config_file}")
            except IOError as e:
                logger.error(f"Failed to save config: {e}")
                raise

    def read_config(self) -> Dict[str, Any]:
        """Read configuration from storage."""
        return self._load_config()

    def write_config(self, patch: Dict[str, Any]) -> None:
        """Write configuration patch to storage."""
        config = self._load_config()
        config.update(patch)
        self._save_config(config)

    def get_bot_config(self, bot_id: int) -> Optional[Dict[str, Any]]:
        """Get specific bot configuration."""
        config = self._load_config()
        return config.get("bots", {}).get(str(bot_id))

    def update_bot_config(self, bot_id: int, config: Dict[str, Any]) -> None:
        """Update specific bot configuration."""
        full_config = self._load_config()
        if "bots" not in full_config:
            full_config["bots"] = {}
        
        full_config["bots"][str(bot_id)] = config
        self._save_config(full_config)
        logger.info(f"Bot config updated: {bot_id}")

    def delete_bot_config(self, bot_id: int) -> None:
        """Delete specific bot configuration."""
        full_config = self._load_config()
        if "bots" in full_config and str(bot_id) in full_config["bots"]:
            del full_config["bots"][str(bot_id)]
            self._save_config(full_config)
            logger.info(f"Bot config deleted: {bot_id}")

    def add_bot_config(self, bot_id: int, config: Dict[str, Any]) -> None:
        """Add new bot configuration."""
        self.update_bot_config(bot_id, config)

    def get_all_bot_configs(self) -> Dict[int, Dict[str, Any]]:
        """Get all bot configurations."""
        config = self._load_config()
        bots = config.get("bots", {})
        return {int(bot_id): bot_config for bot_id, bot_config in bots.items()}

    def get_bot_count(self) -> int:
        """Get total number of bots."""
        config = self._load_config()
        return len(config.get("bots", {}))

    def get_running_bot_count(self) -> int:
        """Get number of running bots."""
        config = self._load_config()
        bots = config.get("bots", {})
        return sum(1 for bot in bots.values() if bot.get("enabled", False))

    def clear_all_configs(self) -> None:
        """Clear all configurations."""
        self._save_config({"bots": {}, "conversations": {}, "admin_bot": {}})
        logger.info("All configurations cleared")

    def backup_configs(self) -> str:
        """Create backup of configurations."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_id = f"backup_{timestamp}"
        backup_path = self.backup_dir / f"{backup_id}.json"
        
        try:
            config = self._load_config()
            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Backup created: {backup_id}")
            return backup_id
        except IOError as e:
            logger.error(f"Failed to create backup: {e}")
            raise

    def restore_configs(self, backup_id: str) -> bool:
        """Restore configurations from backup."""
        backup_path = self.backup_dir / f"{backup_id}.json"
        
        if not backup_path.exists():
            logger.error(f"Backup not found: {backup_id}")
            return False
        
        try:
            with open(backup_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            self._save_config(config)
            logger.info(f"Configurations restored from: {backup_id}")
            return True
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Failed to restore backup: {e}")
            return False

    def get_conversation_cache(self, conversation_key: str) -> Optional[Dict[str, Any]]:
        """Get conversation cache."""
        config = self._load_config()
        conversations = config.get("conversations", {})
        return conversations.get(conversation_key)

    def set_conversation_cache(self, conversation_key: str, data: Dict[str, Any]) -> None:
        """Set conversation cache."""
        config = self._load_config()
        if "conversations" not in config:
            config["conversations"] = {}
        
        config["conversations"][conversation_key] = data
        self._save_config(config)

    def clear_conversation_cache(self, conversation_key: str) -> None:
        """Clear conversation cache."""
        config = self._load_config()
        if "conversations" in config and conversation_key in config["conversations"]:
            del config["conversations"][conversation_key]
            self._save_config(config)

    def invalidate_cache(self) -> None:
        """Invalidate internal cache."""
        self._cache = None
        logger.debug("Cache invalidated")









