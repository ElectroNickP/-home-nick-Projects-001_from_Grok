"""
External Configuration Manager for Telegram Bot Manager.

This module provides professional configuration management with:
- External storage (outside project directory)
- Secrets management (separate from configs)
- Schema validation
- Configuration migrations
- Backup/restore functionality
- Version control for configs
"""

import json
import logging
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import jsonschema
from threading import Lock
import yaml

logger = logging.getLogger(__name__)


class ExternalConfigManager:
    """Professional configuration manager with external storage."""
    
    # Default paths
    DEFAULT_CONFIG_DIR = Path.home() / ".telegram-bot-manager"
    CONFIGS_DIR = "configs"
    SECRETS_DIR = "secrets"  
    BACKUPS_DIR = "backups"
    SCHEMAS_DIR = "schemas"
    
    # File names
    MAIN_CONFIG_FILE = "bots.json"
    SECRETS_FILE = "secrets.env"
    VERSION_FILE = "version.json"
    
    # Current schema version
    CURRENT_VERSION = "2.0.0"
    
    def __init__(self, config_dir: Optional[Path] = None):
        """Initialize external config manager."""
        self.config_dir = config_dir or self.DEFAULT_CONFIG_DIR
        self.configs_path = self.config_dir / self.CONFIGS_DIR
        self.secrets_path = self.config_dir / self.SECRETS_DIR
        self.backups_path = self.config_dir / self.BACKUPS_DIR
        self.schemas_path = self.config_dir / self.SCHEMAS_DIR
        
        self._lock = Lock()
        self._config_cache: Optional[Dict[str, Any]] = None
        self._secrets_cache: Optional[Dict[str, str]] = None
        
        # Initialize directory structure
        self._init_directories()
        self._load_schemas()
        
        logger.info(f"External config manager initialized: {self.config_dir}")
    
    def _init_directories(self) -> None:
        """Initialize external configuration directories."""
        directories = [
            self.config_dir,
            self.configs_path,
            self.secrets_path,
            self.backups_path,
            self.schemas_path
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Ensured directory exists: {directory}")
    
    def _load_schemas(self) -> None:
        """Load JSON schemas for validation."""
        try:
            # Load bot config schema
            bot_schema_path = self.schemas_path / "bot_config_schema.json"
            if bot_schema_path.exists():
                with open(bot_schema_path, 'r', encoding='utf-8') as f:
                    self.bot_config_schema = json.load(f)
            else:
                logger.warning(f"Bot config schema not found: {bot_schema_path}")
                self.bot_config_schema = None
            
            # Load secrets schema
            secrets_schema_path = self.schemas_path / "secrets_schema.json"
            if secrets_schema_path.exists():
                with open(secrets_schema_path, 'r', encoding='utf-8') as f:
                    self.secrets_schema = json.load(f)
            else:
                logger.warning(f"Secrets schema not found: {secrets_schema_path}")
                self.secrets_schema = None
                
        except Exception as e:
            logger.error(f"Failed to load schemas: {e}")
            self.bot_config_schema = None
            self.secrets_schema = None
    
    def _validate_config(self, config: Dict[str, Any]) -> None:
        """Validate configuration against schema."""
        if not self.bot_config_schema:
            logger.warning("No schema available for config validation")
            return
        
        try:
            jsonschema.validate(config, self.bot_config_schema)
            logger.debug("Configuration validation passed")
        except jsonschema.ValidationError as e:
            logger.error(f"Configuration validation failed: {e.message}")
            raise ValueError(f"Invalid configuration: {e.message}")
    
    def _validate_secrets(self, secrets: Dict[str, Any]) -> None:
        """Validate secrets against schema."""
        if not self.secrets_schema:
            logger.warning("No schema available for secrets validation")
            return
        
        try:
            jsonschema.validate(secrets, self.secrets_schema)
            logger.debug("Secrets validation passed")
        except jsonschema.ValidationError as e:
            logger.error(f"Secrets validation failed: {e.message}")
            raise ValueError(f"Invalid secrets: {e.message}")
    
    def _create_backup(self, backup_type: str = "auto") -> Path:
        """Create backup of current configuration."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{backup_type}_backup_{timestamp}"
        backup_path = self.backups_path / backup_name
        backup_path.mkdir(exist_ok=True)
        
        # Backup configs
        if self.configs_path.exists():
            shutil.copytree(self.configs_path, backup_path / "configs", dirs_exist_ok=True)
        
        # Backup secrets (encrypted if possible)
        if self.secrets_path.exists():
            shutil.copytree(self.secrets_path, backup_path / "secrets", dirs_exist_ok=True)
        
        # Create backup metadata
        metadata = {
            "timestamp": timestamp,
            "type": backup_type,
            "version": self.get_config_version(),
            "files_count": len(list(backup_path.rglob("*")))
        }
        
        with open(backup_path / "metadata.json", 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)
        
        logger.info(f"Backup created: {backup_path}")
        return backup_path
    
    def get_config_version(self) -> str:
        """Get current configuration version."""
        version_file = self.configs_path / self.VERSION_FILE
        if version_file.exists():
            try:
                with open(version_file, 'r', encoding='utf-8') as f:
                    version_data = json.load(f)
                return version_data.get("version", "1.0.0")
            except Exception as e:
                logger.error(f"Failed to read version file: {e}")
        return "1.0.0"
    
    def _set_config_version(self, version: str) -> None:
        """Set configuration version."""
        version_file = self.configs_path / self.VERSION_FILE
        version_data = {
            "version": version,
            "updated_at": datetime.now().isoformat(),
            "manager_version": self.CURRENT_VERSION
        }
        
        with open(version_file, 'w', encoding='utf-8') as f:
            json.dump(version_data, f, indent=2)
    
    def load_config(self, use_cache: bool = True) -> Dict[str, Any]:
        """Load main configuration."""
        if use_cache and self._config_cache is not None:
            return self._config_cache.copy()
        
        config_file = self.configs_path / self.MAIN_CONFIG_FILE
        
        with self._lock:
            if config_file.exists():
                try:
                    with open(config_file, 'r', encoding='utf-8') as f:
                        config = json.load(f)
                    
                    # Validate configuration
                    self._validate_config(config)
                    
                    self._config_cache = config
                    logger.debug(f"Configuration loaded from {config_file}")
                    return config.copy()
                    
                except Exception as e:
                    logger.error(f"Failed to load configuration: {e}")
                    # Return default config structure
                    default_config = self._get_default_config()
                    self._config_cache = default_config
                    return default_config
            else:
                # Create default configuration
                default_config = self._get_default_config()
                self.save_config(default_config)
                return default_config
    
    def save_config(self, config: Dict[str, Any], create_backup: bool = True) -> None:
        """Save main configuration."""
        if create_backup:
            self._create_backup("pre_save")
        
        # Validate before saving
        self._validate_config(config)
        
        config_file = self.configs_path / self.MAIN_CONFIG_FILE
        
        with self._lock:
            # Add metadata
            config["metadata"] = {
                "version": self.CURRENT_VERSION,
                "updated_at": datetime.now().isoformat(),
                "backup_created": create_backup
            }
            
            # Save to temporary file first
            temp_file = config_file.with_suffix('.tmp')
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            # Atomic replace
            temp_file.replace(config_file)
            
            # Update version
            self._set_config_version(self.CURRENT_VERSION)
            
            # Update cache
            self._config_cache = config
            
            logger.info(f"Configuration saved to {config_file}")
    
    def load_secrets(self) -> Dict[str, str]:
        """Load secrets from environment file."""
        if self._secrets_cache is not None:
            return self._secrets_cache.copy()
        
        secrets_file = self.secrets_path / self.SECRETS_FILE
        secrets = {}
        
        if secrets_file.exists():
            try:
                with open(secrets_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            secrets[key.strip()] = value.strip().strip('"\'')
                
                logger.debug(f"Secrets loaded from {secrets_file}")
                self._secrets_cache = secrets
                
            except Exception as e:
                logger.error(f"Failed to load secrets: {e}")
        
        return secrets
    
    def save_secrets(self, secrets: Dict[str, str], create_backup: bool = True) -> None:
        """Save secrets to environment file."""
        if create_backup:
            self._create_backup("secrets_backup")
        
        secrets_file = self.secrets_path / self.SECRETS_FILE
        
        with self._lock:
            with open(secrets_file, 'w', encoding='utf-8') as f:
                f.write(f"# Telegram Bot Manager Secrets\n")
                f.write(f"# Generated: {datetime.now().isoformat()}\n")
                f.write(f"# WARNING: Keep this file secure!\n\n")
                
                for key, value in secrets.items():
                    f.write(f"{key}={value}\n")
            
            # Set file permissions (readable only by owner)
            os.chmod(secrets_file, 0o600)
            
            self._secrets_cache = secrets
            logger.info(f"Secrets saved to {secrets_file}")
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration structure."""
        return {
            "version": self.CURRENT_VERSION,
            "bots": {},
            "global_settings": {
                "max_bots": 10,
                "log_level": "INFO",
                "auto_backup": True,
                "backup_retention_days": 30
            },
            "admin_bot": {
                "enabled": False,
                "token_ref": "admin_bot_token",
                "admin_users": [],
                "notifications": {
                    "bot_status": True,
                    "high_cpu": True,
                    "errors": True,
                    "weekly_stats": True
                }
            }
        }
    
    def migrate_from_internal_config(self, internal_config_path: Union[str, Path]) -> bool:
        """Migrate configuration from internal project files."""
        try:
            internal_path = Path(internal_config_path)
            if not internal_path.exists():
                logger.warning(f"Internal config file not found: {internal_path}")
                return False
            
            # Load old configuration
            with open(internal_path, 'r', encoding='utf-8') as f:
                old_config = json.load(f)
            
            # Create backup
            self._create_backup("migration")
            
            # Transform configuration
            new_config = self._transform_old_config(old_config)
            
            # Save new configuration
            self.save_config(new_config, create_backup=False)
            
            logger.info(f"Successfully migrated config from {internal_path}")
            return True
            
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            return False
    
    def _transform_old_config(self, old_config: Dict[str, Any]) -> Dict[str, Any]:
        """Transform old configuration format to new format."""
        new_config = self._get_default_config()
        
        # Migrate bots
        if "bots" in old_config:
            for bot_id, bot_data in old_config["bots"].items():
                if "config" in bot_data:
                    bot_config = bot_data["config"].copy()
                    
                    # Transform token references
                    if "telegram_token" in bot_config:
                        token_ref = f"bot_{bot_id}_telegram_token"
                        bot_config["telegram_token_ref"] = token_ref
                        del bot_config["telegram_token"]
                    
                    if "openai_api_key" in bot_config:
                        key_ref = f"bot_{bot_id}_openai_key"
                        bot_config["openai_api_key_ref"] = key_ref
                        del bot_config["openai_api_key"]
                    
                    # Add timestamps
                    bot_config["created_at"] = datetime.now().isoformat()
                    bot_config["updated_at"] = datetime.now().isoformat()
                    
                    new_config["bots"][bot_id] = {
                        "id": bot_data.get("id", int(bot_id)),
                        "config": bot_config,
                        "status": bot_data.get("status", "stopped")
                    }
        
        return new_config
    
    def list_backups(self) -> List[Dict[str, Any]]:
        """List available backups."""
        backups = []
        
        if not self.backups_path.exists():
            return backups
        
        for backup_dir in self.backups_path.iterdir():
            if backup_dir.is_dir():
                metadata_file = backup_dir / "metadata.json"
                if metadata_file.exists():
                    try:
                        with open(metadata_file, 'r', encoding='utf-8') as f:
                            metadata = json.load(f)
                        metadata["path"] = str(backup_dir)
                        backups.append(metadata)
                    except Exception as e:
                        logger.error(f"Failed to read backup metadata: {e}")
        
        # Sort by timestamp (newest first)
        backups.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return backups
    
    def restore_backup(self, backup_path: Union[str, Path]) -> bool:
        """Restore configuration from backup."""
        try:
            backup_path = Path(backup_path)
            if not backup_path.exists():
                logger.error(f"Backup path not found: {backup_path}")
                return False
            
            # Create backup of current state
            self._create_backup("pre_restore")
            
            # Restore configs
            backup_configs = backup_path / "configs"
            if backup_configs.exists():
                if self.configs_path.exists():
                    shutil.rmtree(self.configs_path)
                shutil.copytree(backup_configs, self.configs_path)
            
            # Restore secrets
            backup_secrets = backup_path / "secrets"
            if backup_secrets.exists():
                if self.secrets_path.exists():
                    shutil.rmtree(self.secrets_path)
                shutil.copytree(backup_secrets, self.secrets_path)
            
            # Clear caches
            self._config_cache = None
            self._secrets_cache = None
            
            logger.info(f"Successfully restored from backup: {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"Restore failed: {e}")
            return False
    
    def cleanup_old_backups(self, retention_days: int = 30) -> int:
        """Clean up old backups based on retention policy."""
        if not self.backups_path.exists():
            return 0
        
        cutoff_date = datetime.now().timestamp() - (retention_days * 24 * 3600)
        removed_count = 0
        
        for backup_dir in self.backups_path.iterdir():
            if backup_dir.is_dir():
                # Check modification time
                if backup_dir.stat().st_mtime < cutoff_date:
                    try:
                        shutil.rmtree(backup_dir)
                        removed_count += 1
                        logger.debug(f"Removed old backup: {backup_dir}")
                    except Exception as e:
                        logger.error(f"Failed to remove backup {backup_dir}: {e}")
        
        logger.info(f"Cleaned up {removed_count} old backups")
        return removed_count
    
    def get_config_path(self) -> Path:
        """Get path to external configuration directory."""
        return self.config_dir
    
    def is_initialized(self) -> bool:
        """Check if external configuration is properly initialized."""
        required_dirs = [self.configs_path, self.secrets_path, self.backups_path]
        return all(dir_path.exists() for dir_path in required_dirs)






