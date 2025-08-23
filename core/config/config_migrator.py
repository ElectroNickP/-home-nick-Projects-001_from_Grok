"""
Configuration Migration Utility for Telegram Bot Manager.

This utility helps migrate configurations between versions and provides
tools for updating configuration structure safely.
"""

import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class ConfigMigrator:
    """Handles configuration migrations between versions."""
    
    def __init__(self, external_config_manager):
        """Initialize migrator with external config manager."""
        self.config_manager = external_config_manager
        self.migration_history: List[Dict[str, Any]] = []
    
    def detect_current_version(self, config: Dict[str, Any]) -> str:
        """Detect configuration version."""
        # Check for version field
        if "version" in config:
            return config["version"]
        
        # Check metadata
        if "metadata" in config and "version" in config["metadata"]:
            return config["metadata"]["version"]
        
        # Detect by structure patterns
        if self._is_legacy_v1_structure(config):
            return "1.0.0"
        
        # Default to oldest known version
        return "1.0.0"
    
    def _is_legacy_v1_structure(self, config: Dict[str, Any]) -> bool:
        """Check if config has legacy v1.x structure."""
        if "bots" not in config:
            return False
        
        # Check for direct token storage (security issue in v1)
        for bot_data in config["bots"].values():
            if isinstance(bot_data, dict) and "config" in bot_data:
                bot_config = bot_data["config"]
                if "telegram_token" in bot_config or "openai_api_key" in bot_config:
                    return True
        
        return False
    
    def needs_migration(self, config: Dict[str, Any]) -> bool:
        """Check if configuration needs migration."""
        current_version = self.detect_current_version(config)
        target_version = self.config_manager.CURRENT_VERSION
        
        return self._compare_versions(current_version, target_version) < 0
    
    def _compare_versions(self, version1: str, version2: str) -> int:
        """Compare two version strings. Returns -1, 0, or 1."""
        def version_to_tuple(v):
            return tuple(map(int, v.split('.')))
        
        v1_tuple = version_to_tuple(version1)
        v2_tuple = version_to_tuple(version2)
        
        if v1_tuple < v2_tuple:
            return -1
        elif v1_tuple > v2_tuple:
            return 1
        else:
            return 0
    
    def migrate_config(self, config: Dict[str, Any], target_version: Optional[str] = None) -> Tuple[Dict[str, Any], Dict[str, str]]:
        """
        Migrate configuration to target version.
        
        Returns:
            Tuple of (migrated_config, extracted_secrets)
        """
        if target_version is None:
            target_version = self.config_manager.CURRENT_VERSION
        
        current_version = self.detect_current_version(config)
        logger.info(f"Migrating config from {current_version} to {target_version}")
        
        # Create migration record
        migration_record = {
            "timestamp": datetime.now().isoformat(),
            "from_version": current_version,
            "to_version": target_version,
            "steps": []
        }
        
        migrated_config = config.copy()
        extracted_secrets = {}
        
        # Apply migration steps based on version path
        if self._compare_versions(current_version, "2.0.0") < 0:
            migrated_config, secrets = self._migrate_to_v2(migrated_config)
            extracted_secrets.update(secrets)
            migration_record["steps"].append("v1_to_v2_security_enhancement")
        
        # Future migrations can be added here
        # if self._compare_versions(current_version, "3.0.0") < 0:
        #     migrated_config = self._migrate_to_v3(migrated_config)
        #     migration_record["steps"].append("v2_to_v3_feature_update")
        
        # Update version in config
        migrated_config["version"] = target_version
        migrated_config["migration_history"] = self.migration_history + [migration_record]
        
        logger.info(f"Migration completed: {len(migration_record['steps'])} steps applied")
        return migrated_config, extracted_secrets
    
    def _migrate_to_v2(self, config: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, str]]:
        """Migrate from v1.x to v2.0.0 (security and structure improvements)."""
        migrated = config.copy()
        secrets = {}
        
        # Ensure required structure
        if "global_settings" not in migrated:
            migrated["global_settings"] = {
                "max_bots": 10,
                "log_level": "INFO",
                "auto_backup": True,
                "backup_retention_days": 30
            }
        
        if "admin_bot" not in migrated:
            migrated["admin_bot"] = {
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
        
        # Migrate bot configurations
        if "bots" in migrated:
            for bot_id, bot_data in migrated["bots"].items():
                if "config" in bot_data:
                    bot_config = bot_data["config"]
                    
                    # Extract and reference tokens
                    if "telegram_token" in bot_config:
                        token = bot_config["telegram_token"]
                        token_ref = f"bot_{bot_id}_telegram_token"
                        secrets[token_ref] = token
                        bot_config["telegram_token_ref"] = token_ref
                        del bot_config["telegram_token"]
                    
                    # Extract and reference API keys
                    if "openai_api_key" in bot_config:
                        api_key = bot_config["openai_api_key"]
                        key_ref = f"bot_{bot_id}_openai_key"
                        secrets[key_ref] = api_key
                        bot_config["openai_api_key_ref"] = key_ref
                        del bot_config["openai_api_key"]
                    
                    # Add timestamps if missing
                    if "created_at" not in bot_config:
                        bot_config["created_at"] = datetime.now().isoformat()
                    if "updated_at" not in bot_config:
                        bot_config["updated_at"] = datetime.now().isoformat()
                    
                    # Normalize marketplace config
                    if "marketplace" in bot_config:
                        marketplace = bot_config["marketplace"]
                        if isinstance(marketplace, dict):
                            # Ensure all required fields exist
                            marketplace.setdefault("enabled", False)
                            marketplace.setdefault("title", "")
                            marketplace.setdefault("description", "")
                            marketplace.setdefault("category", "other")
                            marketplace.setdefault("tags", [])
                            marketplace.setdefault("featured", False)
                            marketplace.setdefault("rating", 0.0)
                            marketplace.setdefault("total_users", 0)
                    
                    # Add default features section
                    if "features" not in bot_config:
                        bot_config["features"] = {
                            "auto_responses": True,
                            "command_handling": True,
                            "file_processing": True,
                            "image_generation": False,
                            "web_search": False
                        }
        
        return migrated, secrets
    
    def backup_before_migration(self, config: Dict[str, Any]) -> Path:
        """Create a backup before migration."""
        return self.config_manager._create_backup("pre_migration")
    
    def validate_migration(self, old_config: Dict[str, Any], new_config: Dict[str, Any]) -> List[str]:
        """Validate that migration was successful."""
        issues = []
        
        # Check that no bots were lost
        old_bots = old_config.get("bots", {})
        new_bots = new_config.get("bots", {})
        
        if len(old_bots) != len(new_bots):
            issues.append(f"Bot count mismatch: {len(old_bots)} -> {len(new_bots)}")
        
        # Check bot configurations
        for bot_id in old_bots:
            if bot_id not in new_bots:
                issues.append(f"Bot {bot_id} was lost during migration")
                continue
            
            old_bot = old_bots[bot_id]
            new_bot = new_bots[bot_id]
            
            # Check essential fields
            if old_bot.get("id") != new_bot.get("id"):
                issues.append(f"Bot {bot_id} ID mismatch")
            
            # Check config migration
            old_config_data = old_bot.get("config", {})
            new_config_data = new_bot.get("config", {})
            
            # Bot name should be preserved
            old_name = old_config_data.get("bot_name", "")
            new_name = new_config_data.get("bot_name", "")
            if old_name and old_name != new_name:
                issues.append(f"Bot {bot_id} name changed: '{old_name}' -> '{new_name}'")
        
        # Check structure
        required_sections = ["version", "bots", "global_settings", "admin_bot"]
        for section in required_sections:
            if section not in new_config:
                issues.append(f"Missing required section: {section}")
        
        return issues
    
    def generate_migration_report(self, old_config: Dict[str, Any], new_config: Dict[str, Any], 
                                secrets: Dict[str, str]) -> str:
        """Generate a detailed migration report."""
        report = []
        report.append("=== CONFIGURATION MIGRATION REPORT ===")
        report.append(f"Timestamp: {datetime.now().isoformat()}")
        report.append("")
        
        # Version info
        old_version = self.detect_current_version(old_config)
        new_version = new_config.get("version", "unknown")
        report.append(f"Version: {old_version} -> {new_version}")
        report.append("")
        
        # Migration summary
        old_bots = old_config.get("bots", {})
        new_bots = new_config.get("bots", {})
        
        report.append("=== MIGRATION SUMMARY ===")
        report.append(f"Bots migrated: {len(old_bots)} -> {len(new_bots)}")
        report.append(f"Secrets extracted: {len(secrets)} items")
        report.append("")
        
        # Security improvements
        if secrets:
            report.append("=== SECURITY IMPROVEMENTS ===")
            report.append("The following sensitive data was moved to secure storage:")
            for key in secrets:
                if "token" in key.lower():
                    report.append(f"  - {key}: Telegram bot token")
                elif "key" in key.lower():
                    report.append(f"  - {key}: API key")
                else:
                    report.append(f"  - {key}: Credential")
            report.append("")
        
        # Bot details
        report.append("=== BOT MIGRATION DETAILS ===")
        for bot_id, bot_data in new_bots.items():
            config_data = bot_data.get("config", {})
            bot_name = config_data.get("bot_name", f"Bot {bot_id}")
            
            report.append(f"Bot {bot_id} ({bot_name}):")
            report.append(f"  Status: {bot_data.get('status', 'unknown')}")
            
            if "telegram_token_ref" in config_data:
                report.append(f"  Token reference: {config_data['telegram_token_ref']}")
            if "openai_api_key_ref" in config_data:
                report.append(f"  API key reference: {config_data['openai_api_key_ref']}")
            
            features = config_data.get("features", {})
            if features:
                enabled_features = [k for k, v in features.items() if v]
                report.append(f"  Features: {', '.join(enabled_features) if enabled_features else 'none'}")
            
            report.append("")
        
        # Validation results
        validation_issues = self.validate_migration(old_config, new_config)
        if validation_issues:
            report.append("=== VALIDATION ISSUES ===")
            for issue in validation_issues:
                report.append(f"  WARNING: {issue}")
            report.append("")
        else:
            report.append("=== VALIDATION PASSED ===")
            report.append("No issues detected in migration.")
            report.append("")
        
        # Next steps
        report.append("=== NEXT STEPS ===")
        report.append("1. Review the migrated configuration")
        report.append("2. Verify all bots start correctly with new config")
        report.append("3. Test bot functionality")
        report.append("4. Remove old configuration files if everything works")
        report.append("")
        
        return "\n".join(report)
    
    def rollback_migration(self, backup_path: Path) -> bool:
        """Rollback to a previous configuration."""
        try:
            success = self.config_manager.restore_backup(backup_path)
            if success:
                logger.info(f"Successfully rolled back to backup: {backup_path}")
            return success
        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            return False





