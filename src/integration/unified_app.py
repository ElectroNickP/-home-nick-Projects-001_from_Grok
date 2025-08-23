#!/usr/bin/env python3
"""
Unified Application Entry Point.

This module provides a unified entry point that combines the legacy Flask
application with the new hexagonal architecture components.
"""

import logging
import os
import sys
import json
from pathlib import Path
from typing import Dict, Any, Optional

from flask import Flask

# Add paths for imports
sys.path.append(str(Path(__file__).parent.parent))
sys.path.append(str(Path(__file__).parent.parent.parent))

# Import legacy components
import app as legacy_app
import config_manager as legacy_config
import bot_manager as legacy_bot_manager

# Import new architecture components
from core.entrypoints.factories import UseCaseFactory, EntryPointFactory
from core.entrypoints.config import Config
from adapters.storage.json_adapter import JSONStorageAdapter
from adapters.telegram.aiogram_adapter import AiogramTelegramAdapter
from adapters.updater.git_adapter import GitUpdaterAdapter

# Import bridge components
from bridge.config_bridge import ConfigBridge
from bridge.bot_management_bridge import BotManagementBridge

logger = logging.getLogger(__name__)


class UnifiedApplication:
    """
    Unified application that combines legacy and new architectures.
    
    This class provides a seamless integration between the old monolithic
    Flask application and the new hexagonal architecture components.
    """
    
    def __init__(self, config_path: Optional[str] = None, migration_mode: bool = True):
        """
        Initialize the unified application.
        
        Args:
            config_path: Path to configuration file
            migration_mode: Whether to run in migration mode (both systems)
        """
        self.config_path = config_path or "src/bot_configs.json"
        self.migration_mode = migration_mode
        
        # Application components
        self.legacy_app = None
        self.new_web_app = None
        self.new_cli_app = None
        self.unified_app = None
        
        # Adapters and bridges
        self.storage_adapter = None
        self.config_bridge = None
        self.bot_management_bridge = None
        
        # Use cases
        self.use_case_factory = None
        
        # System state
        self.is_initialized = False
        self.migration_completed = False
        
        logger.info("UnifiedApplication initialized")
    
    def initialize(self) -> bool:
        """
        Initialize all application components.
        
        Returns:
            True if initialization was successful
        """
        logger.info("Initializing unified application")
        
        try:
            # Check if migration is completed
            self._check_migration_status()
            
            # Initialize adapters
            if not self._initialize_adapters():
                return False
            
            # Initialize use cases
            if not self._initialize_use_cases():
                return False
            
            # Initialize bridges (if in migration mode)
            if self.migration_mode:
                if not self._initialize_bridges():
                    return False
            
            # Initialize legacy application
            if not self._initialize_legacy_app():
                return False
            
            # Initialize new applications
            if not self._initialize_new_apps():
                return False
            
            # Create unified Flask app
            if not self._create_unified_app():
                return False
            
            self.is_initialized = True
            logger.info("Unified application initialized successfully")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize unified application: {e}")
            return False
    
    def _check_migration_status(self):
        """Check if migration has been completed."""
        migration_file = Path("migration_completed.json")
        
        if migration_file.exists():
            try:
                with open(migration_file) as f:
                    migration_info = json.load(f)
                    self.migration_completed = migration_info.get("migration_completed", False)
                    
                if self.migration_completed:
                    logger.info("Migration completed - running in full new architecture mode")
                    self.migration_mode = False
                else:
                    logger.info("Migration not completed - running in hybrid mode")
                    
            except Exception as e:
                logger.warning(f"Failed to read migration status: {e}")
        else:
            logger.info("No migration file found - running in migration mode")
    
    def _initialize_adapters(self) -> bool:
        """Initialize storage and external adapters."""
        try:
            # Initialize storage adapter
            self.storage_adapter = JSONStorageAdapter(config_file=self.config_path)
            
            # Initialize telegram adapter (will be used by new system)
            telegram_adapter = AiogramTelegramAdapter()
            
            # Initialize updater adapter
            updater_adapter = GitUpdaterAdapter()
            
            logger.info("Adapters initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize adapters: {e}")
            return False
    
    def _initialize_use_cases(self) -> bool:
        """Initialize use case factory and use cases."""
        try:
            # Create configuration
            config = Config(
                storage_adapter=self.storage_adapter,
                telegram_adapter=None,  # Will be set when needed
                updater_adapter=None,   # Will be set when needed
                secret_key="your-secret-key-change-in-production",
                admin_username="admin",
                admin_password_hash="pbkdf2:sha256:600000$your-hash-here"
            )
            
            # Initialize use case factory
            self.use_case_factory = UseCaseFactory(config)
            
            logger.info("Use cases initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize use cases: {e}")
            return False
    
    def _initialize_bridges(self) -> bool:
        """Initialize bridge components for legacy integration."""
        try:
            # Initialize configuration bridge
            self.config_bridge = ConfigBridge(self.storage_adapter)
            
            # Initialize bot management bridge
            bot_management_use_case = self.use_case_factory.create_bot_management_use_case()
            self.bot_management_bridge = BotManagementBridge(bot_management_use_case)
            
            logger.info("Bridge components initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize bridges: {e}")
            return False
    
    def _initialize_legacy_app(self) -> bool:
        """Initialize the legacy Flask application."""
        try:
            # Load legacy configurations
            if not os.path.exists(legacy_config.CONFIG_FILE):
                with open(legacy_config.CONFIG_FILE, "w") as f:
                    json.dump({"bots": {}}, f)
            
            legacy_config.load_configs()
            
            # Get the legacy app instance
            self.legacy_app = legacy_app.app
            
            logger.info("Legacy application initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize legacy application: {e}")
            return False
    
    def _initialize_new_apps(self) -> bool:
        """Initialize new architecture applications."""
        try:
            # Initialize entry point factory
            entry_point_factory = EntryPointFactory(self.use_case_factory)
            
            # Create new web application
            self.new_web_app = entry_point_factory.create_web_application()
            
            # Create new CLI application
            self.new_cli_app = entry_point_factory.create_cli_application()
            
            logger.info("New applications initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize new applications: {e}")
            return False
    
    def _create_unified_app(self) -> bool:
        """Create the unified Flask application."""
        try:
            if self.migration_completed:
                # Use only new application
                self.unified_app = self.new_web_app.app
                logger.info("Using new application only (migration completed)")
            else:
                # Use legacy application with new routes
                self.unified_app = self.legacy_app
                
                # Register new routes with prefix
                self._register_new_routes()
                
                logger.info("Using unified application (migration mode)")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to create unified application: {e}")
            return False
    
    def _register_new_routes(self):
        """Register new architecture routes in legacy app."""
        try:
            # Register new web routes with /v2 prefix
            new_blueprint = self.new_web_app.create_blueprint(url_prefix='/v2')
            self.unified_app.register_blueprint(new_blueprint)
            
            # Add migration status endpoint
            @self.unified_app.route('/api/migration/status')
            def migration_status():
                if self.config_bridge and self.bot_management_bridge:
                    return {
                        "migration_mode": self.migration_mode,
                        "migration_completed": self.migration_completed,
                        "config_status": self.config_bridge.get_migration_status(),
                        "system_status": self.bot_management_bridge.get_system_status()
                    }
                else:
                    return {
                        "migration_mode": self.migration_mode,
                        "migration_completed": self.migration_completed,
                        "error": "Bridge components not initialized"
                    }
            
            # Add system switch endpoint
            @self.unified_app.route('/api/migration/switch', methods=['POST'])
            def switch_system():
                from flask import request, jsonify
                
                data = request.get_json() or {}
                use_new_system = data.get('use_new_system', True)
                
                if self.bot_management_bridge:
                    if use_new_system:
                        self.bot_management_bridge.enable_new_system()
                        self.config_bridge.enable_sync()
                        message = "Switched to new system"
                    else:
                        self.bot_management_bridge.disable_new_system()
                        self.config_bridge.disable_sync()
                        message = "Switched to legacy system"
                    
                    return jsonify({
                        "success": True,
                        "message": message,
                        "use_new_system": use_new_system
                    })
                else:
                    return jsonify({
                        "success": False,
                        "error": "Bridge components not available"
                    }), 500
            
            logger.info("New routes registered successfully")
            
        except Exception as e:
            logger.error(f"Failed to register new routes: {e}")
            raise
    
    def get_app(self) -> Flask:
        """
        Get the unified Flask application.
        
        Returns:
            Flask application instance
        """
        if not self.is_initialized:
            raise RuntimeError("Application not initialized")
        
        return self.unified_app
    
    def get_cli_app(self):
        """
        Get the CLI application.
        
        Returns:
            CLI application instance
        """
        if not self.is_initialized:
            raise RuntimeError("Application not initialized")
        
        return self.new_cli_app
    
    def start_bots(self) -> Dict[str, Any]:
        """
        Start all configured bots.
        
        Returns:
            Dict containing operation results
        """
        if self.migration_mode and self.bot_management_bridge:
            # Use unified bot management
            bot_list = self.bot_management_bridge.list_bots()
            
            if not bot_list.get("success", False):
                return {
                    "success": False,
                    "error": "Failed to get bot list"
                }
            
            started_count = 0
            failed_count = 0
            errors = []
            
            for bot in bot_list.get("bots", []):
                bot_id = bot.get("id")
                if bot.get("status") != "running":
                    try:
                        success, message = self.bot_management_bridge.start_bot(bot_id)
                        if success:
                            started_count += 1
                        else:
                            failed_count += 1
                            errors.append(f"Bot {bot_id}: {message}")
                    except Exception as e:
                        failed_count += 1
                        errors.append(f"Bot {bot_id}: {str(e)}")
            
            return {
                "success": failed_count == 0,
                "started_bots": started_count,
                "failed_bots": failed_count,
                "errors": errors
            }
        else:
            # Use legacy bot management
            try:
                legacy_bot_manager.start_all_bots()
                return {
                    "success": True,
                    "message": "Started all bots using legacy system"
                }
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Legacy bot start failed: {str(e)}"
                }
    
    def stop_bots(self) -> Dict[str, Any]:
        """
        Stop all running bots.
        
        Returns:
            Dict containing operation results
        """
        if self.migration_mode and self.bot_management_bridge:
            # Use unified bot management
            return self.bot_management_bridge.stop_all_bots()
        else:
            # Use legacy bot management
            try:
                result = legacy_bot_manager.stop_all_bots_for_update()
                return {
                    "success": result[0],
                    "message": result[1]
                }
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Legacy bot stop failed: {str(e)}"
                }
    
    def get_system_status(self) -> Dict[str, Any]:
        """
        Get comprehensive system status.
        
        Returns:
            Dict containing system status information
        """
        status = {
            "unified_app": {
                "initialized": self.is_initialized,
                "migration_mode": self.migration_mode,
                "migration_completed": self.migration_completed
            }
        }
        
        if self.migration_mode and self.bot_management_bridge:
            status["bot_management"] = self.bot_management_bridge.get_system_status()
        
        if self.migration_mode and self.config_bridge:
            status["configuration"] = self.config_bridge.get_migration_status()
        
        # Get bot count from appropriate system
        try:
            if self.migration_mode and self.bot_management_bridge:
                bot_list = self.bot_management_bridge.list_bots()
                if bot_list.get("success", False):
                    bots = bot_list.get("bots", [])
                    status["bots"] = {
                        "total": len(bots),
                        "running": len([b for b in bots if b.get("status") == "running"]),
                        "stopped": len([b for b in bots if b.get("status") == "stopped"])
                    }
            else:
                with legacy_config.BOT_CONFIGS_LOCK:
                    total_bots = len(legacy_config.BOT_CONFIGS)
                    running_bots = len([b for b in legacy_config.BOT_CONFIGS.values() 
                                      if b.get("status") == "running"])
                    status["bots"] = {
                        "total": total_bots,
                        "running": running_bots,
                        "stopped": total_bots - running_bots
                    }
        except Exception as e:
            status["bots"] = {"error": str(e)}
        
        return status
    
    def migrate_to_new_system(self) -> Dict[str, Any]:
        """
        Perform migration to new system.
        
        Returns:
            Dict containing migration results
        """
        if not self.migration_mode:
            return {
                "success": False,
                "error": "Not in migration mode"
            }
        
        try:
            from migration.migrate_v1_to_v2 import MigrationManager
            
            migration_manager = MigrationManager()
            success = migration_manager.run_full_migration()
            
            if success:
                self.migration_completed = True
                self.migration_mode = False
                
                # Reinitialize with new system only
                self._create_unified_app()
            
            return {
                "success": success,
                "status": migration_manager.get_migration_status()
            }
            
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }


def create_app(config_path: Optional[str] = None, migration_mode: bool = True) -> Flask:
    """
    Factory function to create the unified application.
    
    Args:
        config_path: Path to configuration file
        migration_mode: Whether to run in migration mode
        
    Returns:
        Flask application instance
    """
    unified_app = UnifiedApplication(config_path, migration_mode)
    
    if not unified_app.initialize():
        raise RuntimeError("Failed to initialize unified application")
    
    return unified_app.get_app()


def main():
    """Main entry point for the unified application."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Telegram Bot Manager - Unified Application")
    parser.add_argument("--config", help="Configuration file path")
    parser.add_argument("--port", type=int, default=5000, help="Port to run on")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("--no-migration", action="store_true", help="Disable migration mode")
    parser.add_argument("--migrate", action="store_true", help="Run migration and exit")
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format='[%(asctime)s] %(levelname)s: %(message)s'
    )
    
    try:
        # Create unified application
        migration_mode = not args.no_migration
        unified_app = UnifiedApplication(args.config, migration_mode)
        
        if not unified_app.initialize():
            logger.error("Failed to initialize application")
            return 1
        
        if args.migrate:
            # Run migration and exit
            logger.info("Running migration...")
            result = unified_app.migrate_to_new_system()
            
            if result["success"]:
                logger.info("Migration completed successfully")
                return 0
            else:
                logger.error(f"Migration failed: {result.get('error')}")
                return 1
        
        # Start bots
        logger.info("Starting configured bots...")
        start_result = unified_app.start_bots()
        
        if start_result["success"]:
            logger.info(f"Started {start_result.get('started_bots', 0)} bots")
        else:
            logger.warning(f"Bot startup issues: {start_result.get('error')}")
        
        # Get Flask app
        app = unified_app.get_app()
        
        # Print system information
        logger.info("🚀 Telegram Bot Manager - Unified Application Starting...")
        logger.info(f"🌐 Web Interface: http://{args.host}:{args.port}/")
        
        if migration_mode:
            logger.info(f"🔄 Migration Mode: Active")
            logger.info(f"📚 New API: http://{args.host}:{args.port}/v2/")
            logger.info(f"📊 Migration Status: http://{args.host}:{args.port}/api/migration/status")
        else:
            logger.info(f"✅ New Architecture: Fully Active")
        
        # Start Flask application
        app.run(
            host=args.host,
            port=args.port,
            debug=args.debug
        )
        
        return 0
        
    except KeyboardInterrupt:
        logger.info("Application stopped by user")
        return 0
    except Exception as e:
        logger.error(f"Application failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())






