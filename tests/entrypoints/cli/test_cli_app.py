"""
Unit tests for CLI application (CLI Entry Point).

Tests cover CLI application creation, command registration,
help system, and basic functionality.
"""

import pytest
from unittest.mock import Mock, patch
from click.testing import CliRunner
from core.entrypoints.cli.cli_app import create_cli_app
from core.entrypoints.config import EntryPointConfig
from core.entrypoints.factories import EntryPointFactory


class TestCLIAppCreation:
    """Test CLI application creation and configuration."""
    
    def test_create_cli_app_returns_click_group(self, test_config: EntryPointConfig, entry_point_factory: EntryPointFactory):
        """Test that create_cli_app returns a Click group."""
        cli_app = create_cli_app(test_config, entry_point_factory)
        
        assert cli_app.name == 'telegram-bot-manager'
        assert hasattr(cli_app, 'commands')
    
    def test_cli_app_has_required_commands(self, test_config: EntryPointConfig, entry_point_factory: EntryPointFactory):
        """Test that CLI app has all required commands."""
        cli_app = create_cli_app(test_config, entry_point_factory)
        
        command_names = [cmd.name for cmd in cli_app.commands.values()]
        expected_commands = ['version', 'status', 'info', 'bot', 'conversation', 'system']
        
        for command_name in expected_commands:
            assert command_name in command_names
    
    def test_cli_app_help_available(self, cli_runner: CliRunner, test_config: EntryPointConfig, entry_point_factory: EntryPointFactory):
        """Test that CLI help is available."""
        cli_app = create_cli_app(test_config, entry_point_factory)
        
        result = cli_runner.invoke(cli_app, ['--help'])
        
        assert result.exit_code == 0
        assert 'Usage:' in result.output
        assert 'Commands:' in result.output


class TestCLIAppCommands:
    """Test individual CLI commands."""
    
    def test_version_command(self, cli_runner: CliRunner, test_config: EntryPointConfig, entry_point_factory: EntryPointFactory):
        """Test version command."""
        cli_app = create_cli_app(test_config, entry_point_factory)
        
        result = cli_runner.invoke(cli_app, ['version'])
        
        assert result.exit_code == 0
        assert '3.6.0' in result.output
    
    def test_status_command(self, cli_runner: CliRunner, test_config: EntryPointConfig, entry_point_factory: EntryPointFactory):
        """Test status command."""
        cli_app = create_cli_app(test_config, entry_point_factory)
        
        result = cli_runner.invoke(cli_app, ['status'])
        
        assert result.exit_code == 0
        assert 'status' in result.output.lower()
    
    def test_info_command(self, cli_runner: CliRunner, test_config: EntryPointConfig, entry_point_factory: EntryPointFactory):
        """Test info command."""
        cli_app = create_cli_app(test_config, entry_point_factory)
        
        result = cli_runner.invoke(cli_app, ['info'])
        
        assert result.exit_code == 0
        assert 'info' in result.output.lower()


class TestCLIBotCommands:
    """Test bot-related CLI commands."""
    
    def test_bot_list_command(self, cli_runner: CliRunner, test_config: EntryPointConfig, entry_point_factory: EntryPointFactory, mock_use_cases):
        """Test bot list command."""
        from tests.entrypoints.factories import test_data_factory
        
        cli_app = create_cli_app(test_config, entry_point_factory)
        
        # Mock the use case response
        mock_use_cases['bot_management'].get_all_bots.return_value = [
            test_data_factory.create_bot_config(id=1, name="Test Bot 1"),
            test_data_factory.create_bot_config(id=2, name="Test Bot 2")
        ]
        
        result = cli_runner.invoke(cli_app, ['bot', 'list'])
        
        assert result.exit_code == 0
        assert 'Test Bot 1' in result.output
        assert 'Test Bot 2' in result.output
        mock_use_cases['bot_management'].get_all_bots.assert_called_once()
    
    def test_bot_show_command(self, cli_runner: CliRunner, test_config: EntryPointConfig, entry_point_factory: EntryPointFactory, mock_use_cases):
        """Test bot show command."""
        from tests.entrypoints.factories import test_data_factory
        
        cli_app = create_cli_app(test_config, entry_point_factory)
        
        bot_data = test_data_factory.create_bot_config(id=1, name="Test Bot")
        mock_use_cases['bot_management'].get_bot.return_value = bot_data
        
        result = cli_runner.invoke(cli_app, ['bot', 'show', '1'])
        
        assert result.exit_code == 0
        assert 'Test Bot' in result.output
        mock_use_cases['bot_management'].get_bot.assert_called_once_with(1)
    
    def test_bot_create_command(self, cli_runner: CliRunner, test_config: EntryPointConfig, entry_point_factory: EntryPointFactory, mock_use_cases):
        """Test bot create command."""
        from tests.entrypoints.factories import test_data_factory
        
        cli_app = create_cli_app(test_config, entry_point_factory)
        
        bot_data = test_data_factory.create_bot_config(id=1, name="New Bot")
        mock_use_cases['bot_management'].create_bot.return_value = bot_data
        
        result = cli_runner.invoke(cli_app, [
            'bot', 'create',
            '--name', 'New Bot',
            '--telegram-token', 'test_token',
            '--openai-api-key', 'test_key',
            '--assistant-id', 'test_assistant'
        ])
        
        assert result.exit_code == 0
        assert 'New Bot' in result.output
        mock_use_cases['bot_management'].create_bot.assert_called_once()
    
    def test_bot_update_command(self, cli_runner: CliRunner, test_config: EntryPointConfig, entry_point_factory: EntryPointFactory, mock_use_cases):
        """Test bot update command."""
        from tests.entrypoints.factories import test_data_factory
        
        cli_app = create_cli_app(test_config, entry_point_factory)
        
        bot_data = test_data_factory.create_bot_config(id=1, name="Updated Bot")
        mock_use_cases['bot_management'].update_bot.return_value = bot_data
        
        result = cli_runner.invoke(cli_app, [
            'bot', 'update', '1',
            '--name', 'Updated Bot'
        ])
        
        assert result.exit_code == 0
        assert 'Updated Bot' in result.output
        mock_use_cases['bot_management'].update_bot.assert_called_once()
    
    def test_bot_delete_command(self, cli_runner: CliRunner, test_config: EntryPointConfig, entry_point_factory: EntryPointFactory, mock_use_cases):
        """Test bot delete command."""
        cli_app = create_cli_app(test_config, entry_point_factory)
        
        mock_use_cases['bot_management'].delete_bot.return_value = True
        
        result = cli_runner.invoke(cli_app, ['bot', 'delete', '1'])
        
        assert result.exit_code == 0
        assert 'deleted' in result.output.lower()
        mock_use_cases['bot_management'].delete_bot.assert_called_once_with(1)
    
    def test_bot_start_command(self, cli_runner: CliRunner, test_config: EntryPointConfig, entry_point_factory: EntryPointFactory, mock_use_cases):
        """Test bot start command."""
        cli_app = create_cli_app(test_config, entry_point_factory)
        
        mock_use_cases['bot_management'].start_bot.return_value = True
        
        result = cli_runner.invoke(cli_app, ['bot', 'start', '1'])
        
        assert result.exit_code == 0
        assert 'started' in result.output.lower()
        mock_use_cases['bot_management'].start_bot.assert_called_once_with(1)
    
    def test_bot_stop_command(self, cli_runner: CliRunner, test_config: EntryPointConfig, entry_point_factory: EntryPointFactory, mock_use_cases):
        """Test bot stop command."""
        cli_app = create_cli_app(test_config, entry_point_factory)
        
        mock_use_cases['bot_management'].stop_bot.return_value = True
        
        result = cli_runner.invoke(cli_app, ['bot', 'stop', '1'])
        
        assert result.exit_code == 0
        assert 'stopped' in result.output.lower()
        mock_use_cases['bot_management'].stop_bot.assert_called_once_with(1)
    
    def test_bot_restart_command(self, cli_runner: CliRunner, test_config: EntryPointConfig, entry_point_factory: EntryPointFactory, mock_use_cases):
        """Test bot restart command."""
        cli_app = create_cli_app(test_config, entry_point_factory)
        
        mock_use_cases['bot_management'].restart_bot.return_value = True
        
        result = cli_runner.invoke(cli_app, ['bot', 'restart', '1'])
        
        assert result.exit_code == 0
        assert 'restarted' in result.output.lower()
        mock_use_cases['bot_management'].restart_bot.assert_called_once_with(1)
    
    def test_bot_status_command(self, cli_runner: CliRunner, test_config: EntryPointConfig, entry_point_factory: EntryPointFactory, mock_use_cases):
        """Test bot status command."""
        from tests.entrypoints.factories import test_data_factory
        
        cli_app = create_cli_app(test_config, entry_point_factory)
        
        bot_data = test_data_factory.create_bot_config(id=1, status="running")
        mock_use_cases['bot_management'].get_bot.return_value = bot_data
        
        result = cli_runner.invoke(cli_app, ['bot', 'status', '1'])
        
        assert result.exit_code == 0
        assert 'running' in result.output.lower()
        mock_use_cases['bot_management'].get_bot.assert_called_once_with(1)
    
    def test_bot_stats_command(self, cli_runner: CliRunner, test_config: EntryPointConfig, entry_point_factory: EntryPointFactory, mock_use_cases):
        """Test bot stats command."""
        cli_app = create_cli_app(test_config, entry_point_factory)
        
        stats_data = {
            'messages_processed': 100,
            'users_count': 50,
            'uptime': 3600
        }
        mock_use_cases['bot_management'].get_bot_stats.return_value = stats_data
        
        result = cli_runner.invoke(cli_app, ['bot', 'stats', '1'])
        
        assert result.exit_code == 0
        assert '100' in result.output
        assert '50' in result.output
        mock_use_cases['bot_management'].get_bot_stats.assert_called_once_with(1)


class TestCLIConversationCommands:
    """Test conversation-related CLI commands."""
    
    def test_conversation_list_command(self, cli_runner: CliRunner, test_config: EntryPointConfig, entry_point_factory: EntryPointFactory, mock_use_cases):
        """Test conversation list command."""
        from tests.entrypoints.factories import test_data_factory
        
        cli_app = create_cli_app(test_config, entry_point_factory)
        
        conversations = [
            test_data_factory.create_conversation(key="conv1"),
            test_data_factory.create_conversation(key="conv2")
        ]
        mock_use_cases['conversation'].get_all_conversations.return_value = conversations
        
        result = cli_runner.invoke(cli_app, ['conversation', 'list'])
        
        assert result.exit_code == 0
        assert 'conv1' in result.output
        assert 'conv2' in result.output
        mock_use_cases['conversation'].get_all_conversations.assert_called_once()
    
    def test_conversation_show_command(self, cli_runner: CliRunner, test_config: EntryPointConfig, entry_point_factory: EntryPointFactory, mock_use_cases):
        """Test conversation show command."""
        from tests.entrypoints.factories import test_data_factory
        
        cli_app = create_cli_app(test_config, entry_point_factory)
        
        conversation = test_data_factory.create_conversation(key="test_conv")
        mock_use_cases['conversation'].get_conversation.return_value = conversation
        
        result = cli_runner.invoke(cli_app, ['conversation', 'show', 'test_conv'])
        
        assert result.exit_code == 0
        assert 'test_conv' in result.output
        mock_use_cases['conversation'].get_conversation.assert_called_once_with('test_conv')
    
    def test_conversation_clear_command(self, cli_runner: CliRunner, test_config: EntryPointConfig, entry_point_factory: EntryPointFactory, mock_use_cases):
        """Test conversation clear command."""
        cli_app = create_cli_app(test_config, entry_point_factory)
        
        mock_use_cases['conversation'].clear_conversation.return_value = True
        
        result = cli_runner.invoke(cli_app, ['conversation', 'clear', 'test_conv'])
        
        assert result.exit_code == 0
        assert 'cleared' in result.output.lower()
        mock_use_cases['conversation'].clear_conversation.assert_called_once_with('test_conv')
    
    def test_conversation_messages_command(self, cli_runner: CliRunner, test_config: EntryPointConfig, entry_point_factory: EntryPointFactory, mock_use_cases):
        """Test conversation messages command."""
        from tests.entrypoints.factories import test_data_factory
        
        cli_app = create_cli_app(test_config, entry_point_factory)
        
        messages = test_data_factory.create_messages(3)
        mock_use_cases['conversation'].get_conversation_messages.return_value = messages
        
        result = cli_runner.invoke(cli_app, ['conversation', 'messages', 'test_conv'])
        
        assert result.exit_code == 0
        assert 'Message 1' in result.output
        assert 'Message 2' in result.output
        assert 'Message 3' in result.output
        mock_use_cases['conversation'].get_conversation_messages.assert_called_once_with('test_conv')


class TestCLISystemCommands:
    """Test system-related CLI commands."""
    
    def test_system_status_command(self, cli_runner: CliRunner, test_config: EntryPointConfig, entry_point_factory: EntryPointFactory, mock_use_cases):
        """Test system status command."""
        from tests.entrypoints.factories import test_data_factory
        
        cli_app = create_cli_app(test_config, entry_point_factory)
        
        status_data = test_data_factory.create_system_status()
        mock_use_cases['system'].get_system_status.return_value = status_data
        
        result = cli_runner.invoke(cli_app, ['system', 'status'])
        
        assert result.exit_code == 0
        assert 'running' in result.output.lower()
        mock_use_cases['system'].get_system_status.assert_called_once()
    
    def test_system_config_command(self, cli_runner: CliRunner, test_config: EntryPointConfig, entry_point_factory: EntryPointFactory, mock_use_cases):
        """Test system config command."""
        cli_app = create_cli_app(test_config, entry_point_factory)
        
        config_data = {'version': '3.6.0', 'debug': True}
        mock_use_cases['system'].get_system_config.return_value = config_data
        
        result = cli_runner.invoke(cli_app, ['system', 'config'])
        
        assert result.exit_code == 0
        assert '3.6.0' in result.output
        mock_use_cases['system'].get_system_config.assert_called_once()
    
    def test_system_backup_command(self, cli_runner: CliRunner, test_config: EntryPointConfig, entry_point_factory: EntryPointFactory, mock_use_cases):
        """Test system backup command."""
        cli_app = create_cli_app(test_config, entry_point_factory)
        
        backup_id = 'backup_20250101_000000'
        mock_use_cases['system'].create_backup.return_value = backup_id
        
        result = cli_runner.invoke(cli_app, ['system', 'backup'])
        
        assert result.exit_code == 0
        assert backup_id in result.output
        mock_use_cases['system'].create_backup.assert_called_once()
    
    def test_system_backups_command(self, cli_runner: CliRunner, test_config: EntryPointConfig, entry_point_factory: EntryPointFactory, mock_use_cases):
        """Test system backups command."""
        from tests.entrypoints.factories import test_data_factory
        
        cli_app = create_cli_app(test_config, entry_point_factory)
        
        backups = [
            test_data_factory.create_backup_info(id='backup1'),
            test_data_factory.create_backup_info(id='backup2')
        ]
        mock_use_cases['system'].get_backups.return_value = backups
        
        result = cli_runner.invoke(cli_app, ['system', 'backups'])
        
        assert result.exit_code == 0
        assert 'backup1' in result.output
        assert 'backup2' in result.output
        mock_use_cases['system'].get_backups.assert_called_once()
    
    def test_system_restore_command(self, cli_runner: CliRunner, test_config: EntryPointConfig, entry_point_factory: EntryPointFactory, mock_use_cases):
        """Test system restore command."""
        cli_app = create_cli_app(test_config, entry_point_factory)
        
        mock_use_cases['system'].restore_backup.return_value = True
        
        result = cli_runner.invoke(cli_app, ['system', 'restore', 'backup1'])
        
        assert result.exit_code == 0
        assert 'restored' in result.output.lower()
        mock_use_cases['system'].restore_backup.assert_called_once_with('backup1')
    
    def test_system_update_command(self, cli_runner: CliRunner, test_config: EntryPointConfig, entry_point_factory: EntryPointFactory, mock_use_cases):
        """Test system update command."""
        cli_app = create_cli_app(test_config, entry_point_factory)
        
        mock_use_cases['system'].update_system.return_value = True
        
        result = cli_runner.invoke(cli_app, ['system', 'update'])
        
        assert result.exit_code == 0
        assert 'updated' in result.output.lower()
        mock_use_cases['system'].update_system.assert_called_once()


class TestCLIErrorHandling:
    """Test CLI error handling."""
    
    def test_bot_not_found_error(self, cli_runner: CliRunner, test_config: EntryPointConfig, entry_point_factory: EntryPointFactory, mock_use_cases):
        """Test error when bot not found."""
        cli_app = create_cli_app(test_config, entry_point_factory)
        
        mock_use_cases['bot_management'].get_bot.return_value = None
        
        result = cli_runner.invoke(cli_app, ['bot', 'show', '999'])
        
        assert result.exit_code != 0
        assert 'not found' in result.output.lower()
    
    def test_conversation_not_found_error(self, cli_runner: CliRunner, test_config: EntryPointConfig, entry_point_factory: EntryPointFactory, mock_use_cases):
        """Test error when conversation not found."""
        cli_app = create_cli_app(test_config, entry_point_factory)
        
        mock_use_cases['conversation'].get_conversation.return_value = None
        
        result = cli_runner.invoke(cli_app, ['conversation', 'show', 'nonexistent'])
        
        assert result.exit_code != 0
        assert 'not found' in result.output.lower()
    
    def test_validation_error(self, cli_runner: CliRunner, test_config: EntryPointConfig, entry_point_factory: EntryPointFactory, mock_use_cases):
        """Test validation error handling."""
        cli_app = create_cli_app(test_config, entry_point_factory)
        
        mock_use_cases['bot_management'].create_bot.side_effect = ValueError("Invalid token")
        
        result = cli_runner.invoke(cli_app, [
            'bot', 'create',
            '--name', 'Test Bot',
            '--telegram-token', 'invalid_token'
        ])
        
        assert result.exit_code != 0
        assert 'Invalid token' in result.output
    
    def test_server_error(self, cli_runner: CliRunner, test_config: EntryPointConfig, entry_point_factory: EntryPointFactory, mock_use_cases):
        """Test server error handling."""
        cli_app = create_cli_app(test_config, entry_point_factory)
        
        mock_use_cases['bot_management'].get_all_bots.side_effect = Exception("Database error")
        
        result = cli_runner.invoke(cli_app, ['bot', 'list'])
        
        assert result.exit_code != 0
        assert 'error' in result.output.lower()


class TestCLIOutputFormats:
    """Test CLI output formats."""
    
    def test_json_output_format(self, cli_runner: CliRunner, test_config: EntryPointConfig, entry_point_factory: EntryPointFactory, mock_use_cases):
        """Test JSON output format."""
        from tests.entrypoints.factories import test_data_factory
        import json
        
        cli_app = create_cli_app(test_config, entry_point_factory)
        
        bot_data = test_data_factory.create_bot_config(id=1, name="Test Bot")
        mock_use_cases['bot_management'].get_bot.return_value = bot_data
        
        result = cli_runner.invoke(cli_app, ['bot', 'show', '1', '--format', 'json'])
        
        assert result.exit_code == 0
        # Try to parse JSON output
        try:
            json.loads(result.output)
        except json.JSONDecodeError:
            pytest.fail("Output is not valid JSON")
    
    def test_csv_output_format(self, cli_runner: CliRunner, test_config: EntryPointConfig, entry_point_factory: EntryPointFactory, mock_use_cases):
        """Test CSV output format."""
        from tests.entrypoints.factories import test_data_factory
        
        cli_app = create_cli_app(test_config, entry_point_factory)
        
        bots_data = [
            test_data_factory.create_bot_config(id=1, name="Bot 1"),
            test_data_factory.create_bot_config(id=2, name="Bot 2")
        ]
        mock_use_cases['bot_management'].get_all_bots.return_value = bots_data
        
        result = cli_runner.invoke(cli_app, ['bot', 'list', '--format', 'csv'])
        
        assert result.exit_code == 0
        assert ',' in result.output  # Should contain CSV delimiters
        assert 'Bot 1' in result.output
        assert 'Bot 2' in result.output
    
    def test_table_output_format(self, cli_runner: CliRunner, test_config: EntryPointConfig, entry_point_factory: EntryPointFactory, mock_use_cases):
        """Test table output format."""
        from tests.entrypoints.factories import test_data_factory
        
        cli_app = create_cli_app(test_config, entry_point_factory)
        
        bots_data = [
            test_data_factory.create_bot_config(id=1, name="Bot 1"),
            test_data_factory.create_bot_config(id=2, name="Bot 2")
        ]
        mock_use_cases['bot_management'].get_all_bots.return_value = bots_data
        
        result = cli_runner.invoke(cli_app, ['bot', 'list', '--format', 'table'])
        
        assert result.exit_code == 0
        assert 'Bot 1' in result.output
        assert 'Bot 2' in result.output
        assert '|' in result.output  # Should contain table separators






