"""
CLI application entry point.

This module provides a command-line interface for the Telegram Bot Manager,
integrating with use cases and providing management commands.
"""

import logging
import argparse
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.usecases.bot_management import BotManagementUseCase
from core.usecases.conversation_management import ConversationManagementUseCase
from core.usecases.system_management import SystemManagementUseCase
from core.domain.bot import BotConfig

logger = logging.getLogger(__name__)


class CLIApplication:
    """Command-line interface for Telegram Bot Manager."""

    def __init__(
        self,
        bot_management_use_case: BotManagementUseCase,
        conversation_management_use_case: ConversationManagementUseCase,
        system_management_use_case: SystemManagementUseCase,
    ):
        """Initialize the CLI application."""
        self.bot_management_use_case = bot_management_use_case
        self.conversation_management_use_case = conversation_management_use_case
        self.system_management_use_case = system_management_use_case

    def run(self, args: Optional[list] = None):
        """Run the CLI application."""
        parser = self._create_parser()
        parsed_args = parser.parse_args(args)
        
        # Configure logging
        logging.basicConfig(
            level=getattr(logging, parsed_args.log_level.upper()),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Execute command
        if parsed_args.command == 'bot':
            self._handle_bot_command(parsed_args)
        elif parsed_args.command == 'system':
            self._handle_system_command(parsed_args)
        elif parsed_args.command == 'conversation':
            self._handle_conversation_command(parsed_args)
        else:
            parser.print_help()

    def _create_parser(self) -> argparse.ArgumentParser:
        """Create command line argument parser."""
        parser = argparse.ArgumentParser(
            description='Telegram Bot Manager CLI',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  %(prog)s bot list
  %(prog)s bot create --name "My Bot" --token "123:ABC" --openai-key "sk-..."
  %(prog)s bot start 1
  %(prog)s system health
  %(prog)s system backup create
            """
        )
        
        parser.add_argument(
            '--log-level',
            default='INFO',
            choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
            help='Logging level (default: INFO)'
        )
        
        subparsers = parser.add_subparsers(dest='command', help='Available commands')
        
        # Bot commands
        bot_parser = subparsers.add_parser('bot', help='Bot management commands')
        bot_subparsers = bot_parser.add_subparsers(dest='bot_action', help='Bot actions')
        
        # Bot list
        bot_subparsers.add_parser('list', help='List all bots')
        
        # Bot create
        bot_create = bot_subparsers.add_parser('create', help='Create a new bot')
        bot_create.add_argument('--name', required=True, help='Bot name')
        bot_create.add_argument('--token', required=True, help='Telegram bot token')
        bot_create.add_argument('--openai-key', required=True, help='OpenAI API key')
        bot_create.add_argument('--assistant-id', required=True, help='OpenAI Assistant ID')
        bot_create.add_argument('--context-limit', type=int, default=15, help='Group context limit')
        bot_create.add_argument('--enable-ai', action='store_true', default=True, help='Enable AI responses')
        bot_create.add_argument('--enable-voice', action='store_true', help='Enable voice responses')
        bot_create.add_argument('--voice-model', default='tts-1', choices=['tts-1', 'tts-1-hd'], help='Voice model')
        bot_create.add_argument('--voice-type', default='alloy', 
                               choices=['alloy', 'echo', 'fable', 'onyx', 'nova', 'shimmer'], 
                               help='Voice type')
        
        # Bot actions
        for action in ['start', 'stop', 'restart', 'delete', 'status']:
            bot_action = bot_subparsers.add_parser(action, help=f'{action.capitalize()} bot')
            bot_action.add_argument('bot_id', type=int, help='Bot ID')
        
        # Bot update
        bot_update = bot_subparsers.add_parser('update', help='Update bot configuration')
        bot_update.add_argument('bot_id', type=int, help='Bot ID')
        bot_update.add_argument('--name', help='Bot name')
        bot_update.add_argument('--token', help='Telegram bot token')
        bot_update.add_argument('--openai-key', help='OpenAI API key')
        bot_update.add_argument('--assistant-id', help='OpenAI Assistant ID')
        bot_update.add_argument('--context-limit', type=int, help='Group context limit')
        bot_update.add_argument('--enable-ai', action='store_true', help='Enable AI responses')
        bot_update.add_argument('--disable-ai', action='store_true', help='Disable AI responses')
        bot_update.add_argument('--enable-voice', action='store_true', help='Enable voice responses')
        bot_update.add_argument('--disable-voice', action='store_true', help='Disable voice responses')
        bot_update.add_argument('--voice-model', choices=['tts-1', 'tts-1-hd'], help='Voice model')
        bot_update.add_argument('--voice-type', 
                               choices=['alloy', 'echo', 'fable', 'onyx', 'nova', 'shimmer'], 
                               help='Voice type')
        
        # System commands
        system_parser = subparsers.add_parser('system', help='System management commands')
        system_subparsers = system_parser.add_subparsers(dest='system_action', help='System actions')
        
        for action in ['health', 'info', 'stats']:
            system_subparsers.add_parser(action, help=f'Get system {action}')
        
        # System updates
        system_updates = system_subparsers.add_parser('updates', help='Update management')
        system_updates.add_argument('action', choices=['check', 'apply'], help='Update action')
        system_updates.add_argument('--version', help='Version to apply (for apply action)')
        
        # System backups
        system_backups = system_subparsers.add_parser('backup', help='Backup management')
        system_backups.add_argument('action', choices=['list', 'create', 'restore', 'cleanup'], 
                                   help='Backup action')
        system_backups.add_argument('--backup-id', help='Backup ID (for restore action)')
        system_backups.add_argument('--keep-count', type=int, default=5, 
                                   help='Number of backups to keep (for cleanup action)')
        
        # Conversation commands
        conversation_parser = subparsers.add_parser('conversation', help='Conversation management commands')
        conversation_subparsers = conversation_parser.add_subparsers(dest='conversation_action', 
                                                                    help='Conversation actions')
        
        conversation_subparsers.add_parser('list', help='List conversations')
        conversation_clear = conversation_subparsers.add_parser('clear', help='Clear conversation')
        conversation_clear.add_argument('bot_id', type=int, help='Bot ID')
        conversation_clear.add_argument('chat_id', help='Chat ID')
        
        return parser

    def _handle_bot_command(self, args):
        """Handle bot-related commands."""
        if args.bot_action == 'list':
            self._list_bots()
        elif args.bot_action == 'create':
            self._create_bot(args)
        elif args.bot_action == 'start':
            self._start_bot(args.bot_id)
        elif args.bot_action == 'stop':
            self._stop_bot(args.bot_id)
        elif args.bot_action == 'restart':
            self._restart_bot(args.bot_id)
        elif args.bot_action == 'delete':
            self._delete_bot(args.bot_id)
        elif args.bot_action == 'status':
            self._get_bot_status(args.bot_id)
        elif args.bot_action == 'update':
            self._update_bot(args)
        else:
            print("Unknown bot action")

    def _handle_system_command(self, args):
        """Handle system-related commands."""
        if args.system_action == 'health':
            self._get_system_health()
        elif args.system_action == 'info':
            self._get_system_info()
        elif args.system_action == 'stats':
            self._get_system_stats()
        elif args.system_action == 'updates':
            if args.action == 'check':
                self._check_updates()
            elif args.action == 'apply':
                self._apply_update(args.version)
        elif args.system_action == 'backup':
            if args.action == 'list':
                self._list_backups()
            elif args.action == 'create':
                self._create_backup()
            elif args.action == 'restore':
                self._restore_backup(args.backup_id)
            elif args.action == 'cleanup':
                self._cleanup_backups(args.keep_count)
        else:
            print("Unknown system action")

    def _handle_conversation_command(self, args):
        """Handle conversation-related commands."""
        if args.conversation_action == 'list':
            self._list_conversations()
        elif args.conversation_action == 'clear':
            self._clear_conversation(args.bot_id, args.chat_id)
        else:
            print("Unknown conversation action")

    def _list_bots(self):
        """List all bots."""
        try:
            bots = self.bot_management_use_case.get_all_bots()
            if not bots:
                print("No bots found.")
                return
            
            print(f"\n{'ID':<5} {'Name':<20} {'Status':<10} {'Messages':<10} {'Voice':<8}")
            print("-" * 60)
            for bot in bots:
                voice_enabled = "Yes" if bot.config.enable_voice_responses else "No"
                print(f"{bot.id:<5} {bot.config.name:<20} {bot.status.value:<10} "
                      f"{bot.message_count:<10} {voice_enabled:<8}")
            print()
            
        except Exception as e:
            print(f"Error listing bots: {e}")

    async def _create_bot(self, args):
        """Create a new bot."""
        try:
            bot_config = BotConfig(
                name=args.name,
                telegram_token=args.token,
                openai_api_key=args.openai_key,
                assistant_id=args.assistant_id,
                group_context_limit=args.context_limit,
                enable_ai_responses=args.enable_ai,
                enable_voice_responses=args.enable_voice,
                voice_model=args.voice_model,
                voice_type=args.voice_type,
            )
            
            bot = await self.bot_management_use_case.create_bot(bot_config)
            print(f"Bot created successfully with ID: {bot.id}")
            
        except Exception as e:
            print(f"Error creating bot: {e}")

    def _start_bot(self, bot_id: int):
        """Start a bot."""
        try:
            success = self.bot_management_use_case.start_bot(bot_id)
            if success:
                print(f"Bot {bot_id} started successfully")
            else:
                print(f"Failed to start bot {bot_id}")
        except Exception as e:
            print(f"Error starting bot {bot_id}: {e}")

    def _stop_bot(self, bot_id: int):
        """Stop a bot."""
        try:
            success = self.bot_management_use_case.stop_bot(bot_id)
            if success:
                print(f"Bot {bot_id} stopped successfully")
            else:
                print(f"Failed to stop bot {bot_id}")
        except Exception as e:
            print(f"Error stopping bot {bot_id}: {e}")

    def _restart_bot(self, bot_id: int):
        """Restart a bot."""
        try:
            success = self.bot_management_use_case.restart_bot(bot_id)
            if success:
                print(f"Bot {bot_id} restarted successfully")
            else:
                print(f"Failed to restart bot {bot_id}")
        except Exception as e:
            print(f"Error restarting bot {bot_id}: {e}")

    def _delete_bot(self, bot_id: int):
        """Delete a bot."""
        try:
            success = self.bot_management_use_case.delete_bot(bot_id)
            if success:
                print(f"Bot {bot_id} deleted successfully")
            else:
                print(f"Failed to delete bot {bot_id}")
        except Exception as e:
            print(f"Error deleting bot {bot_id}: {e}")

    async def _get_bot_status(self, bot_id: int):
        """Get bot status."""
        try:
            status = await self.bot_management_use_case.get_bot_status(bot_id)
            if status:
                print(f"\nBot Status (ID: {bot_id}):")
                print(f"  Name: {status['name']}")
                print(f"  Status: {status['status']}")
                print(f"  Messages: {status['message_count']}")
                print(f"  Voice Messages: {status['voice_message_count']}")
                print(f"  Created: {status['created_at']}")
                if status['last_error']:
                    print(f"  Last Error: {status['last_error']}")
            else:
                print(f"Bot {bot_id} not found")
        except Exception as e:
            print(f"Error getting bot status {bot_id}: {e}")

    async def _update_bot(self, args):
        """Update bot configuration."""
        try:
            # Get current bot
            bot = self.bot_management_use_case.get_bot(args.bot_id)
            if not bot:
                print(f"Bot {args.bot_id} not found")
                return
            
            # Update configuration
            config = bot.config
            
            if args.name:
                config.name = args.name
            if args.token:
                config.telegram_token = args.token
            if args.openai_key:
                config.openai_api_key = args.openai_key
            if args.assistant_id:
                config.assistant_id = args.assistant_id
            if args.context_limit:
                config.group_context_limit = args.context_limit
            if args.enable_ai:
                config.enable_ai_responses = True
            if args.disable_ai:
                config.enable_ai_responses = False
            if args.enable_voice:
                config.enable_voice_responses = True
            if args.disable_voice:
                config.enable_voice_responses = False
            if args.voice_model:
                config.voice_model = args.voice_model
            if args.voice_type:
                config.voice_type = args.voice_type
            
            updated_bot = await self.bot_management_use_case.update_bot(args.bot_id, config)
            if updated_bot:
                print(f"Bot {args.bot_id} updated successfully")
            else:
                print(f"Failed to update bot {args.bot_id}")
                
        except Exception as e:
            print(f"Error updating bot {args.bot_id}: {e}")

    def _get_system_health(self):
        """Get system health."""
        try:
            health = self.system_management_use_case.get_system_health()
            print(f"\nSystem Health: {health['status'].upper()}")
            print(f"Timestamp: {health['timestamp']}")
            print("\nChecks:")
            for check, status in health['checks'].items():
                print(f"  {check}: {status}")
            print("\nMetrics:")
            for metric, value in health['metrics'].items():
                print(f"  {metric}: {value}")
            print()
        except Exception as e:
            print(f"Error getting system health: {e}")

    def _get_system_info(self):
        """Get system information."""
        try:
            info = self.system_management_use_case.get_system_info()
            print("\nSystem Information:")
            print(f"  Boot Time: {info['system']['boot_time']}")
            print(f"  CPU Cores: {info['system']['cpu_cores']}")
            print(f"  CPU Usage: {info['system']['cpu_percent']}%")
            print(f"  Memory Usage: {info['system']['memory']['used_percent']}%")
            print(f"  Disk Usage: {info['system']['disk']['used_percent']}%")
            print(f"\nApplication:")
            print(f"  Name: {info['application']['name']}")
            print(f"  Python Version: {info['application']['python_version']}")
            print(f"  Process Memory: {info['application']['process_memory_mb']} MB")
            print(f"  Uptime: {info['application']['uptime_seconds']:.1f} seconds")
            print(f"\nBots:")
            print(f"  Total: {info['bots']['total']}")
            print(f"  Running: {info['bots']['running']}")
            print(f"  Stopped: {info['bots']['stopped']}")
            print()
        except Exception as e:
            print(f"Error getting system info: {e}")

    def _get_system_stats(self):
        """Get system statistics."""
        try:
            stats = self.system_management_use_case.get_system_stats()
            print("\nSystem Statistics:")
            print(f"  CPU Usage: {stats['system']['cpu_percent']}%")
            print(f"  Memory Usage: {stats['system']['memory_percent']}%")
            print(f"  Disk Usage: {stats['system']['disk_percent']}%")
            print(f"\nApplication:")
            print(f"  Process CPU: {stats['application']['process_cpu_percent']}%")
            print(f"  Process Memory: {stats['application']['process_memory_mb']} MB")
            print(f"  Uptime: {stats['application']['uptime_seconds']:.1f} seconds")
            print(f"\nBots:")
            print(f"  Total: {stats['bots']['total']}")
            print(f"  Running: {stats['bots']['running']}")
            print(f"  Stopped: {stats['bots']['stopped']}")
            print()
        except Exception as e:
            print(f"Error getting system stats: {e}")

    def _check_updates(self):
        """Check for updates."""
        try:
            updates = self.system_management_use_case.check_updates()
            if updates.get('has_updates'):
                print(f"\nUpdates available!")
                print(f"Current version: {updates['current_version']}")
                print(f"Available version: {updates['available_version']}")
            else:
                print("\nNo updates available")
                print(f"Current version: {updates.get('current_version', 'unknown')}")
            print()
        except Exception as e:
            print(f"Error checking updates: {e}")

    def _apply_update(self, version: str):
        """Apply update."""
        try:
            if not version:
                print("Version not specified")
                return
            
            success = self.system_management_use_case.apply_update(version)
            if success:
                print(f"Update to version {version} applied successfully")
            else:
                print(f"Failed to apply update to version {version}")
        except Exception as e:
            print(f"Error applying update: {e}")

    def _list_backups(self):
        """List backups."""
        try:
            backups = self.system_management_use_case.get_backups()
            if not backups:
                print("No backups found")
                return
            
            print(f"\n{'ID':<20} {'Created':<20} {'Commit':<10} {'Branch':<10}")
            print("-" * 70)
            for backup in backups:
                created = backup['created_at'].strftime('%Y-%m-%d %H:%M:%S')
                print(f"{backup['id']:<20} {created:<20} {backup['commit']:<10} {backup['branch']:<10}")
            print()
        except Exception as e:
            print(f"Error listing backups: {e}")

    def _create_backup(self):
        """Create backup."""
        try:
            backup_id = self.system_management_use_case.create_backup()
            print(f"Backup created successfully: {backup_id}")
        except Exception as e:
            print(f"Error creating backup: {e}")

    def _restore_backup(self, backup_id: str):
        """Restore backup."""
        try:
            if not backup_id:
                print("Backup ID not specified")
                return
            
            success = self.system_management_use_case.restore_backup(backup_id)
            if success:
                print(f"Backup {backup_id} restored successfully")
            else:
                print(f"Failed to restore backup {backup_id}")
        except Exception as e:
            print(f"Error restoring backup: {e}")

    def _cleanup_backups(self, keep_count: int):
        """Cleanup old backups."""
        try:
            result = self.system_management_use_case.cleanup_old_backups(keep_count)
            print(f"Backup cleanup completed:")
            print(f"  Deleted: {result['deleted_count']}")
            print(f"  Kept: {result['kept_count']}")
            print(f"  Space freed: {result['total_size_freed']} bytes")
        except Exception as e:
            print(f"Error cleaning up backups: {e}")

    def _list_conversations(self):
        """List conversations."""
        try:
            print("Conversation listing not implemented in storage port")
        except Exception as e:
            print(f"Error listing conversations: {e}")

    def _clear_conversation(self, bot_id: int, chat_id: str):
        """Clear conversation."""
        try:
            success = self.conversation_management_use_case.clear_conversation(bot_id, chat_id)
            if success:
                print(f"Conversation {bot_id}:{chat_id} cleared successfully")
            else:
                print(f"Failed to clear conversation {bot_id}:{chat_id}")
        except Exception as e:
            print(f"Error clearing conversation: {e}")










