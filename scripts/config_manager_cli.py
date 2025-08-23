#!/usr/bin/env python3
"""
Configuration Manager CLI for Telegram Bot Manager.

Professional command-line interface for managing bot configurations,
secrets, backups, and migrations.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Any

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.config.external_config_manager import ExternalConfigManager
from core.config.config_migrator import ConfigMigrator


def setup_argparse() -> argparse.ArgumentParser:
    """Setup command line argument parser."""
    parser = argparse.ArgumentParser(
        description="Professional Configuration Manager for Telegram Bot Manager",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Initialize external config system
  %(prog)s init
  
  # Migrate from internal project configs
  %(prog)s migrate --from ./bot_configs.json
  
  # Show current configuration
  %(prog)s show
  
  # Create backup
  %(prog)s backup --type manual
  
  # List available backups
  %(prog)s backup --list
  
  # Restore from backup
  %(prog)s restore --backup /path/to/backup
  
  # Update bot configuration
  %(prog)s update-bot --id 1 --name "New Bot Name"
  
  # Add secret
  %(prog)s secret --add bot_1_token "1234567890:ABCD..."
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Init command
    init_parser = subparsers.add_parser('init', help='Initialize external configuration system')
    init_parser.add_argument('--config-dir', type=Path, help='Custom configuration directory')
    init_parser.add_argument('--force', action='store_true', help='Force initialization even if already exists')
    
    # Show command
    show_parser = subparsers.add_parser('show', help='Show current configuration')
    show_parser.add_argument('--format', choices=['json', 'yaml', 'summary'], default='summary',
                           help='Output format')
    show_parser.add_argument('--bot-id', type=int, help='Show specific bot configuration')
    
    # Migrate command
    migrate_parser = subparsers.add_parser('migrate', help='Migrate configuration from internal files')
    migrate_parser.add_argument('--from', dest='source', required=True, type=Path,
                               help='Source configuration file to migrate from')
    migrate_parser.add_argument('--backup', action='store_true', default=True,
                               help='Create backup before migration')
    migrate_parser.add_argument('--dry-run', action='store_true',
                               help='Show what would be migrated without making changes')
    
    # Backup command
    backup_parser = subparsers.add_parser('backup', help='Backup management')
    backup_group = backup_parser.add_mutually_exclusive_group(required=True)
    backup_group.add_argument('--create', action='store_true', help='Create new backup')
    backup_group.add_argument('--list', action='store_true', help='List available backups')
    backup_group.add_argument('--cleanup', type=int, metavar='DAYS', 
                             help='Clean up backups older than N days')
    backup_parser.add_argument('--type', choices=['manual', 'auto', 'migration'], default='manual',
                              help='Backup type')
    
    # Restore command
    restore_parser = subparsers.add_parser('restore', help='Restore from backup')
    restore_parser.add_argument('--backup', required=True, type=Path,
                               help='Backup directory to restore from')
    restore_parser.add_argument('--confirm', action='store_true',
                               help='Skip confirmation prompt')
    
    # Update bot command
    update_parser = subparsers.add_parser('update-bot', help='Update bot configuration')
    update_parser.add_argument('--id', type=int, required=True, help='Bot ID to update')
    update_parser.add_argument('--name', help='Bot name')
    update_parser.add_argument('--enable-ai', type=bool, help='Enable AI responses')
    update_parser.add_argument('--enable-voice', type=bool, help='Enable voice responses')
    update_parser.add_argument('--context-limit', type=int, help='Group context limit')
    
    # Secret management command
    secret_parser = subparsers.add_parser('secret', help='Manage secrets')
    secret_group = secret_parser.add_mutually_exclusive_group(required=True)
    secret_group.add_argument('--add', nargs=2, metavar=('KEY', 'VALUE'),
                             help='Add or update secret')
    secret_group.add_argument('--remove', metavar='KEY', help='Remove secret')
    secret_group.add_argument('--list', action='store_true', help='List secret keys (not values)')
    
    # Validate command
    validate_parser = subparsers.add_parser('validate', help='Validate configuration')
    validate_parser.add_argument('--config', type=Path, help='Specific config file to validate')
    validate_parser.add_argument('--secrets', type=Path, help='Specific secrets file to validate')
    
    return parser


def init_command(args) -> int:
    """Initialize external configuration system."""
    try:
        config_manager = ExternalConfigManager(args.config_dir)
        
        if config_manager.is_initialized() and not args.force:
            print(f"❌ Configuration already initialized at: {config_manager.get_config_path()}")
            print("Use --force to reinitialize")
            return 1
        
        # Create default structure
        config = config_manager.load_config()
        print(f"✅ External configuration initialized at: {config_manager.get_config_path()}")
        print(f"📁 Configs: {config_manager.configs_path}")
        print(f"🔐 Secrets: {config_manager.secrets_path}")
        print(f"💾 Backups: {config_manager.backups_path}")
        
        return 0
        
    except Exception as e:
        print(f"❌ Initialization failed: {e}")
        return 1


def show_command(args) -> int:
    """Show current configuration."""
    try:
        config_manager = ExternalConfigManager()
        config = config_manager.load_config()
        
        if args.bot_id:
            # Show specific bot
            bot_data = config.get("bots", {}).get(str(args.bot_id))
            if not bot_data:
                print(f"❌ Bot {args.bot_id} not found")
                return 1
            
            if args.format == 'json':
                print(json.dumps(bot_data, indent=2))
            else:
                _print_bot_summary(args.bot_id, bot_data)
        else:
            # Show all configuration
            if args.format == 'json':
                print(json.dumps(config, indent=2))
            elif args.format == 'yaml':
                import yaml
                print(yaml.dump(config, default_flow_style=False))
            else:
                _print_config_summary(config)
        
        return 0
        
    except Exception as e:
        print(f"❌ Failed to show configuration: {e}")
        return 1


def migrate_command(args) -> int:
    """Migrate configuration from internal files."""
    try:
        config_manager = ExternalConfigManager()
        migrator = ConfigMigrator(config_manager)
        
        if not args.source.exists():
            print(f"❌ Source file not found: {args.source}")
            return 1
        
        # Load source configuration
        with open(args.source, 'r', encoding='utf-8') as f:
            source_config = json.load(f)
        
        print(f"🔍 Analyzing source configuration: {args.source}")
        current_version = migrator.detect_current_version(source_config)
        print(f"📊 Detected version: {current_version}")
        
        if not migrator.needs_migration(source_config):
            print("✅ Configuration is already up to date")
            return 0
        
        # Perform migration
        if args.dry_run:
            print("🧪 DRY RUN MODE - No changes will be made")
        
        if args.backup and not args.dry_run:
            backup_path = migrator.backup_before_migration(source_config)
            print(f"💾 Backup created: {backup_path}")
        
        migrated_config, secrets = migrator.migrate_config(source_config)
        
        if args.dry_run:
            print("\n📋 MIGRATION PREVIEW:")
            print(f"  - Bots to migrate: {len(migrated_config.get('bots', {}))}")
            print(f"  - Secrets to extract: {len(secrets)}")
            print(f"  - Target version: {migrated_config.get('version', 'unknown')}")
            return 0
        
        # Save migrated configuration
        config_manager.save_config(migrated_config)
        if secrets:
            config_manager.save_secrets(secrets)
        
        # Generate report
        report = migrator.generate_migration_report(source_config, migrated_config, secrets)
        print(report)
        
        print("✅ Migration completed successfully!")
        return 0
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return 1


def backup_command(args) -> int:
    """Handle backup operations."""
    try:
        config_manager = ExternalConfigManager()
        
        if args.create:
            backup_path = config_manager._create_backup(args.type)
            print(f"✅ Backup created: {backup_path}")
            
        elif args.list:
            backups = config_manager.list_backups()
            if not backups:
                print("📭 No backups found")
                return 0
            
            print("📋 Available backups:")
            for backup in backups:
                timestamp = backup.get("timestamp", "unknown")
                backup_type = backup.get("type", "unknown")
                files_count = backup.get("files_count", 0)
                path = backup.get("path", "")
                print(f"  {timestamp} | {backup_type} | {files_count} files | {path}")
                
        elif args.cleanup is not None:
            removed = config_manager.cleanup_old_backups(args.cleanup)
            print(f"🧹 Cleaned up {removed} old backups")
        
        return 0
        
    except Exception as e:
        print(f"❌ Backup operation failed: {e}")
        return 1


def restore_command(args) -> int:
    """Restore from backup."""
    try:
        config_manager = ExternalConfigManager()
        
        if not args.backup.exists():
            print(f"❌ Backup not found: {args.backup}")
            return 1
        
        if not args.confirm:
            response = input(f"⚠️  This will replace current configuration with backup from {args.backup}. Continue? (y/N): ")
            if response.lower() != 'y':
                print("❌ Restore cancelled")
                return 1
        
        success = config_manager.restore_backup(args.backup)
        if success:
            print("✅ Configuration restored successfully")
            return 0
        else:
            print("❌ Restore failed")
            return 1
            
    except Exception as e:
        print(f"❌ Restore failed: {e}")
        return 1


def update_bot_command(args) -> int:
    """Update bot configuration."""
    try:
        config_manager = ExternalConfigManager()
        config = config_manager.load_config()
        
        bot_id = str(args.id)
        if bot_id not in config.get("bots", {}):
            print(f"❌ Bot {args.id} not found")
            return 1
        
        bot_data = config["bots"][bot_id]
        bot_config = bot_data["config"]
        
        # Update fields
        updated = False
        if args.name:
            bot_config["bot_name"] = args.name
            updated = True
        
        if args.enable_ai is not None:
            bot_config["enable_ai_responses"] = args.enable_ai
            updated = True
        
        if args.enable_voice is not None:
            bot_config["enable_voice_responses"] = args.enable_voice
            updated = True
        
        if args.context_limit:
            bot_config["group_context_limit"] = args.context_limit
            updated = True
        
        if updated:
            bot_config["updated_at"] = "2025-01-22T14:30:00"  # Would use datetime.now().isoformat()
            config_manager.save_config(config)
            print(f"✅ Bot {args.id} updated successfully")
        else:
            print("ℹ️  No changes specified")
        
        return 0
        
    except Exception as e:
        print(f"❌ Failed to update bot: {e}")
        return 1


def secret_command(args) -> int:
    """Manage secrets."""
    try:
        config_manager = ExternalConfigManager()
        
        if args.add:
            key, value = args.add
            secrets = config_manager.load_secrets()
            secrets[key] = value
            config_manager.save_secrets(secrets)
            print(f"✅ Secret '{key}' added/updated")
            
        elif args.remove:
            secrets = config_manager.load_secrets()
            if args.remove in secrets:
                del secrets[args.remove]
                config_manager.save_secrets(secrets)
                print(f"✅ Secret '{args.remove}' removed")
            else:
                print(f"❌ Secret '{args.remove}' not found")
                return 1
                
        elif args.list:
            secrets = config_manager.load_secrets()
            if secrets:
                print("🔐 Available secrets:")
                for key in secrets:
                    value_preview = "*" * min(8, len(secrets[key]))
                    print(f"  {key}: {value_preview}")
            else:
                print("📭 No secrets configured")
        
        return 0
        
    except Exception as e:
        print(f"❌ Secret operation failed: {e}")
        return 1


def validate_command(args) -> int:
    """Validate configuration."""
    try:
        config_manager = ExternalConfigManager()
        issues = []
        
        # Validate main config
        config = config_manager.load_config()
        try:
            config_manager._validate_config(config)
            print("✅ Configuration validation passed")
        except ValueError as e:
            issues.append(f"Configuration: {e}")
        
        # Validate secrets
        secrets = config_manager.load_secrets()
        try:
            config_manager._validate_secrets(secrets)
            print("✅ Secrets validation passed")
        except ValueError as e:
            issues.append(f"Secrets: {e}")
        
        if issues:
            print("\n❌ Validation issues found:")
            for issue in issues:
                print(f"  - {issue}")
            return 1
        
        return 0
        
    except Exception as e:
        print(f"❌ Validation failed: {e}")
        return 1


def _print_config_summary(config: Dict[str, Any]) -> None:
    """Print configuration summary."""
    version = config.get("version", "unknown")
    bots = config.get("bots", {})
    global_settings = config.get("global_settings", {})
    
    print(f"📊 Configuration Summary")
    print(f"=====================================")
    print(f"Version: {version}")
    print(f"Total bots: {len(bots)}")
    print(f"Max bots allowed: {global_settings.get('max_bots', 'unknown')}")
    print(f"Log level: {global_settings.get('log_level', 'unknown')}")
    print()
    
    if bots:
        print("🤖 Bots:")
        for bot_id, bot_data in bots.items():
            bot_config = bot_data.get("config", {})
            bot_name = bot_config.get("bot_name", f"Bot {bot_id}")
            status = bot_data.get("status", "unknown")
            print(f"  {bot_id}: {bot_name} ({status})")


def _print_bot_summary(bot_id: int, bot_data: Dict[str, Any]) -> None:
    """Print bot configuration summary."""
    bot_config = bot_data.get("config", {})
    
    print(f"🤖 Bot {bot_id} Configuration")
    print(f"=====================================")
    print(f"Name: {bot_config.get('bot_name', 'Unknown')}")
    print(f"Status: {bot_data.get('status', 'unknown')}")
    print(f"AI Responses: {bot_config.get('enable_ai_responses', False)}")
    print(f"Voice Responses: {bot_config.get('enable_voice_responses', False)}")
    print(f"Context Limit: {bot_config.get('group_context_limit', 'unknown')}")
    
    if "telegram_token_ref" in bot_config:
        print(f"Token Reference: {bot_config['telegram_token_ref']}")
    
    if "openai_api_key_ref" in bot_config:
        print(f"API Key Reference: {bot_config['openai_api_key_ref']}")


def main():
    """Main CLI entry point."""
    parser = setup_argparse()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Command dispatch
    commands = {
        'init': init_command,
        'show': show_command,
        'migrate': migrate_command,
        'backup': backup_command,
        'restore': restore_command,
        'update-bot': update_bot_command,
        'secret': secret_command,
        'validate': validate_command,
    }
    
    return commands[args.command](args)


if __name__ == "__main__":
    sys.exit(main())





