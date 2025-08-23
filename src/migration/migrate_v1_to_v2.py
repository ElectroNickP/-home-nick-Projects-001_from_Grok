#!/usr/bin/env python3
"""
Migration script from V1 (monolithic) to V2 (hexagonal architecture).

This script provides safe migration utilities for transitioning the Telegram
Bot Manager from the old architecture to the new hexagonal architecture.
"""

import json
import logging
import shutil
import sys
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from bridge.config_bridge import ConfigBridge
from bridge.bot_management_bridge import BotManagementBridge

# Import adapters
from adapters.storage.json_adapter import JSONStorageAdapter

# Import use cases
from core.usecases.bot_management import BotManagementUseCase
from core.usecases.conversation_management import ConversationManagementUseCase
from core.usecases.system_management import SystemManagementUseCase

logger = logging.getLogger(__name__)


class MigrationManager:
    """
    Manages the migration process from V1 to V2 architecture.
    
    Provides safe, incremental migration with backup and rollback capabilities.
    """
    
    def __init__(self, project_root: Optional[str] = None):
        """Initialize the migration manager."""
        self.project_root = Path(project_root or os.getcwd())
        self.backup_dir = self.project_root / "migration_backups"
        self.migration_log_file = self.backup_dir / f"migration_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
        # Create backup directory
        self.backup_dir.mkdir(exist_ok=True)
        
        # Setup logging
        self._setup_logging()
        
        # Initialize components
        self.storage_adapter = None
        self.config_bridge = None
        self.bot_management_bridge = None
        
        # Migration state
        self.migration_state = {
            "phase": "initialized",
            "progress": 0,
            "start_time": None,
            "errors": [],
            "warnings": [],
            "backup_id": None
        }
        
        logger.info("MigrationManager initialized")
    
    def _setup_logging(self):
        """Setup dedicated logging for migration."""
        # Create migration logger
        migration_logger = logging.getLogger("migration")
        migration_logger.setLevel(logging.DEBUG)
        
        # Create file handler
        file_handler = logging.FileHandler(self.migration_log_file)
        file_handler.setLevel(logging.DEBUG)
        
        # Create console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter(
            '[%(asctime)s] %(levelname)s [%(name)s]: %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Add handlers
        migration_logger.addHandler(file_handler)
        migration_logger.addHandler(console_handler)
        
        logger.info(f"Migration logging configured: {self.migration_log_file}")
    
    def create_backup(self) -> str:
        """
        Create a backup of the current system state.
        
        Returns:
            Backup ID for referencing the backup
        """
        backup_id = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        backup_path = self.backup_dir / backup_id
        backup_path.mkdir()
        
        logger.info(f"Creating backup: {backup_id}")
        
        try:
            # Backup configuration files
            config_backup_dir = backup_path / "config"
            config_backup_dir.mkdir()
            
            # Backup bot_configs.json
            if (self.project_root / "src" / "bot_configs.json").exists():
                shutil.copy2(
                    self.project_root / "src" / "bot_configs.json",
                    config_backup_dir / "bot_configs.json"
                )
            
            # Backup core source files
            src_backup_dir = backup_path / "src"
            if (self.project_root / "src").exists():
                shutil.copytree(
                    self.project_root / "src",
                    src_backup_dir,
                    ignore=shutil.ignore_patterns('__pycache__', '*.pyc', '*.log')
                )
            
            # Backup apps directory
            apps_backup_dir = backup_path / "apps"
            if (self.project_root / "apps").exists():
                shutil.copytree(
                    self.project_root / "apps",
                    apps_backup_dir,
                    ignore=shutil.ignore_patterns('__pycache__', '*.pyc')
                )
            
            # Create backup manifest
            manifest = {
                "backup_id": backup_id,
                "timestamp": datetime.now().isoformat(),
                "project_root": str(self.project_root),
                "files_backed_up": [
                    "src/bot_configs.json",
                    "src/",
                    "apps/"
                ],
                "migration_version": "1.0.0"
            }
            
            with open(backup_path / "manifest.json", "w") as f:
                json.dump(manifest, f, indent=2)
            
            self.migration_state["backup_id"] = backup_id
            logger.info(f"Backup created successfully: {backup_id}")
            
            return backup_id
            
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            raise
    
    def initialize_new_system(self) -> bool:
        """
        Initialize the new hexagonal architecture components.
        
        Returns:
            True if initialization was successful
        """
        logger.info("Initializing new system components")
        
        try:
            # Initialize storage adapter
            self.storage_adapter = JSONStorageAdapter(
                config_file=str(self.project_root / "src" / "bot_configs.json")
            )
            
            # Initialize use cases
            bot_management_use_case = BotManagementUseCase(
                storage_port=self.storage_adapter,
                telegram_port=None,  # Will be initialized later
                updater_port=None
            )
            
            conversation_management_use_case = ConversationManagementUseCase(
                storage_port=self.storage_adapter
            )
            
            system_management_use_case = SystemManagementUseCase(
                storage_port=self.storage_adapter,
                updater_port=None
            )
            
            # Initialize bridges
            self.config_bridge = ConfigBridge(self.storage_adapter)
            self.bot_management_bridge = BotManagementBridge(bot_management_use_case)
            
            logger.info("New system components initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize new system: {e}")
            self.migration_state["errors"].append(f"Initialization failed: {str(e)}")
            return False
    
    def migrate_configurations(self) -> bool:
        """
        Migrate configurations from old format to new format.
        
        Returns:
            True if migration was successful
        """
        logger.info("Starting configuration migration")
        self.migration_state["phase"] = "migrating_configurations"
        
        try:
            # Migrate bot configurations
            migration_result = self.config_bridge.migrate_bot_configs()
            
            if not migration_result["success"]:
                logger.error("Configuration migration failed")
                self.migration_state["errors"].extend(migration_result["errors"])
                return False
            
            logger.info(
                f"Configuration migration completed: "
                f"{migration_result['migrated_bots']} bots migrated, "
                f"{migration_result['failed_bots']} failures"
            )
            
            # Update progress
            self.migration_state["progress"] = 30
            
            return True
            
        except Exception as e:
            logger.error(f"Configuration migration failed: {e}")
            self.migration_state["errors"].append(f"Configuration migration: {str(e)}")
            return False
    
    def validate_migration(self) -> bool:
        """
        Validate that the migration was successful.
        
        Returns:
            True if validation passed
        """
        logger.info("Validating migration")
        self.migration_state["phase"] = "validating"
        
        try:
            # Validate configurations
            validation_result = self.config_bridge.validate_migration()
            
            if not validation_result["success"]:
                logger.error("Migration validation failed")
                self.migration_state["errors"].extend(validation_result["discrepancies"])
                return False
            
            logger.info(
                f"Migration validation passed: "
                f"{validation_result['valid_bots']} valid bots, "
                f"{validation_result['invalid_bots']} invalid"
            )
            
            # Test bot management operations
            if not self._test_bot_management():
                return False
            
            # Update progress
            self.migration_state["progress"] = 80
            
            return True
            
        except Exception as e:
            logger.error(f"Migration validation failed: {e}")
            self.migration_state["errors"].append(f"Validation failed: {str(e)}")
            return False
    
    def _test_bot_management(self) -> bool:
        """Test bot management operations."""
        logger.info("Testing bot management operations")
        
        try:
            # Test list bots
            result = self.bot_management_bridge.list_bots()
            
            if not result.get("success", False):
                logger.error("Failed to list bots in new system")
                return False
            
            bots = result.get("bots", [])
            logger.info(f"Found {len(bots)} bots in new system")
            
            # Test get bot status for each bot
            for bot in bots[:3]:  # Test first 3 bots
                bot_id = bot.get("id")
                status_result = self.bot_management_bridge.get_bot_status(bot_id)
                
                if not status_result.get("success", False):
                    logger.warning(f"Failed to get status for bot {bot_id}")
                else:
                    logger.debug(f"Bot {bot_id} status: {status_result.get('status')}")
            
            return True
            
        except Exception as e:
            logger.error(f"Bot management test failed: {e}")
            return False
    
    def enable_new_system(self) -> bool:
        """
        Enable the new system for production use.
        
        Returns:
            True if successfully enabled
        """
        logger.info("Enabling new system")
        self.migration_state["phase"] = "enabling_new_system"
        
        try:
            # Enable new system in bridges
            self.bot_management_bridge.enable_new_system()
            self.config_bridge.enable_sync()
            
            # Test system status
            system_status = self.bot_management_bridge.get_system_status()
            
            if not system_status.get("unified_system", {}).get("operational", False):
                logger.error("New system is not operational")
                return False
            
            logger.info("New system enabled successfully")
            self.migration_state["progress"] = 90
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to enable new system: {e}")
            self.migration_state["errors"].append(f"Enable failed: {str(e)}")
            return False
    
    def finalize_migration(self) -> bool:
        """
        Finalize the migration process.
        
        Returns:
            True if finalization was successful
        """
        logger.info("Finalizing migration")
        self.migration_state["phase"] = "finalizing"
        
        try:
            # Perform final synchronization
            self.config_bridge.sync_configurations("both")
            
            # Create migration completion marker
            completion_marker = {
                "migration_completed": True,
                "completion_time": datetime.now().isoformat(),
                "migration_version": "1.0.0",
                "backup_id": self.migration_state["backup_id"],
                "new_system_enabled": True
            }
            
            with open(self.project_root / "migration_completed.json", "w") as f:
                json.dump(completion_marker, f, indent=2)
            
            self.migration_state["progress"] = 100
            self.migration_state["phase"] = "completed"
            
            logger.info("Migration finalized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to finalize migration: {e}")
            self.migration_state["errors"].append(f"Finalization failed: {str(e)}")
            return False
    
    def rollback_migration(self, backup_id: Optional[str] = None) -> bool:
        """
        Rollback the migration to the previous state.
        
        Args:
            backup_id: ID of the backup to restore (uses latest if None)
            
        Returns:
            True if rollback was successful
        """
        if backup_id is None:
            backup_id = self.migration_state.get("backup_id")
        
        if not backup_id:
            logger.error("No backup ID provided for rollback")
            return False
        
        logger.info(f"Rolling back migration using backup: {backup_id}")
        
        try:
            backup_path = self.backup_dir / backup_id
            
            if not backup_path.exists():
                logger.error(f"Backup not found: {backup_id}")
                return False
            
            # Restore configuration files
            if (backup_path / "config" / "bot_configs.json").exists():
                shutil.copy2(
                    backup_path / "config" / "bot_configs.json",
                    self.project_root / "src" / "bot_configs.json"
                )
            
            # Disable new system
            if self.bot_management_bridge:
                self.bot_management_bridge.disable_new_system()
            
            if self.config_bridge:
                self.config_bridge.disable_sync()
            
            # Remove migration completion marker
            completion_file = self.project_root / "migration_completed.json"
            if completion_file.exists():
                completion_file.unlink()
            
            logger.info("Migration rolled back successfully")
            return True
            
        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            return False
    
    def run_full_migration(self) -> bool:
        """
        Run the complete migration process.
        
        Returns:
            True if migration was successful
        """
        logger.info("Starting full migration process")
        self.migration_state["start_time"] = datetime.now()
        
        try:
            # Step 1: Create backup
            backup_id = self.create_backup()
            self.migration_state["progress"] = 10
            
            # Step 2: Initialize new system
            if not self.initialize_new_system():
                logger.error("Failed to initialize new system")
                return False
            self.migration_state["progress"] = 20
            
            # Step 3: Migrate configurations
            if not self.migrate_configurations():
                logger.error("Failed to migrate configurations")
                return False
            
            # Step 4: Validate migration
            if not self.validate_migration():
                logger.error("Migration validation failed")
                return False
            
            # Step 5: Enable new system
            if not self.enable_new_system():
                logger.error("Failed to enable new system")
                return False
            
            # Step 6: Finalize migration
            if not self.finalize_migration():
                logger.error("Failed to finalize migration")
                return False
            
            end_time = datetime.now()
            duration = end_time - self.migration_state["start_time"]
            
            logger.info(
                f"Migration completed successfully in {duration.total_seconds():.2f} seconds"
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            self.migration_state["errors"].append(f"Migration failed: {str(e)}")
            
            # Attempt rollback
            logger.info("Attempting automatic rollback")
            if self.rollback_migration():
                logger.info("Automatic rollback successful")
            else:
                logger.error("Automatic rollback failed")
            
            return False
    
    def get_migration_status(self) -> Dict[str, Any]:
        """Get current migration status."""
        return dict(self.migration_state)


def main():
    """Main migration entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Migrate Telegram Bot Manager to V2")
    parser.add_argument("--project-root", help="Project root directory")
    parser.add_argument("--backup-only", action="store_true", help="Create backup only")
    parser.add_argument("--rollback", help="Rollback to specified backup ID")
    parser.add_argument("--validate-only", action="store_true", help="Validate existing migration")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='[%(asctime)s] %(levelname)s: %(message)s'
    )
    
    # Initialize migration manager
    migration_manager = MigrationManager(args.project_root)
    
    try:
        if args.rollback:
            # Rollback migration
            success = migration_manager.rollback_migration(args.rollback)
            if success:
                print(f"✅ Rollback to {args.rollback} completed successfully")
                return 0
            else:
                print(f"❌ Rollback to {args.rollback} failed")
                return 1
        
        elif args.backup_only:
            # Create backup only
            backup_id = migration_manager.create_backup()
            print(f"✅ Backup created: {backup_id}")
            return 0
        
        elif args.validate_only:
            # Validate migration only
            if migration_manager.initialize_new_system():
                success = migration_manager.validate_migration()
                if success:
                    print("✅ Migration validation passed")
                    return 0
                else:
                    print("❌ Migration validation failed")
                    return 1
            else:
                print("❌ Failed to initialize system for validation")
                return 1
        
        else:
            # Run full migration
            success = migration_manager.run_full_migration()
            
            if success:
                print("✅ Migration completed successfully!")
                print("🎉 Telegram Bot Manager is now running on hexagonal architecture")
                return 0
            else:
                print("❌ Migration failed")
                status = migration_manager.get_migration_status()
                if status["errors"]:
                    print("Errors:")
                    for error in status["errors"]:
                        print(f"  • {error}")
                return 1
                
    except KeyboardInterrupt:
        print("\n🛑 Migration interrupted by user")
        return 1
    except Exception as e:
        print(f"💥 Migration crashed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())








