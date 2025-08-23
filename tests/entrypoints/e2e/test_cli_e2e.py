"""
End-to-End tests for CLI Entry Point.

Tests cover real command line interactions, user scenarios, and CLI behavior.
"""

import pytest
import subprocess
import tempfile
import os
import json
from click.testing import CliRunner
from tests.entrypoints.factories import test_data_factory


class TestCLIE2EAuthentication:
    """Test end-to-end authentication scenarios in CLI interface."""
    
    def test_cli_help_system(self, cli_runner):
        """Test CLI help system and command discovery."""
        # Test main help
        result = cli_runner.invoke(cli_app, ['--help'])
        assert result.exit_code == 0
        assert 'Usage:' in result.output
        assert 'Commands:' in result.output
        
        # Test bot command help
        result = cli_runner.invoke(cli_app, ['bot', '--help'])
        assert result.exit_code == 0
        assert 'bot' in result.output.lower()
        assert 'Commands:' in result.output
        
        # Test conversation command help
        result = cli_runner.invoke(cli_app, ['conversation', '--help'])
        assert result.exit_code == 0
        assert 'conversation' in result.output.lower()
        
        # Test system command help
        result = cli_runner.invoke(cli_app, ['system', '--help'])
        assert result.exit_code == 0
        assert 'system' in result.output.lower()
    
    def test_cli_version_command(self, cli_runner):
        """Test CLI version command."""
        result = cli_runner.invoke(cli_app, ['version'])
        assert result.exit_code == 0
        assert 'Telegram Bot Manager' in result.output
        assert 'Version:' in result.output
    
    def test_cli_status_command(self, cli_runner):
        """Test CLI status command."""
        result = cli_runner.invoke(cli_app, ['status'])
        assert result.exit_code == 0
        assert 'Status:' in result.output
        assert 'Bots:' in result.output
        assert 'Conversations:' in result.output


class TestCLIE2EBotManagement:
    """Test end-to-end bot management scenarios in CLI interface."""
    
    def test_bot_list_command_e2e(self, cli_runner, mock_use_cases):
        """Test bot list command with real CLI interaction."""
        # Prepare bot data
        bots_data = [
            test_data_factory.create_bot_config(id=1, name="Test Bot 1", status="running"),
            test_data_factory.create_bot_config(id=2, name="Test Bot 2", status="stopped"),
            test_data_factory.create_bot_config(id=3, name="Test Bot 3", status="error")
        ]
        
        # Mock use case
        mock_use_cases['bot_management'].list_bots.return_value = {
            'success': True,
            'bots': bots_data,
            'total': 3
        }
        
        # Execute CLI command
        result = cli_runner.invoke(cli_app, ['bot', 'list'])
        
        # Verify output
        assert result.exit_code == 0
        assert 'Test Bot 1' in result.output
        assert 'Test Bot 2' in result.output
        assert 'Test Bot 3' in result.output
        assert 'running' in result.output
        assert 'stopped' in result.output
        assert 'error' in result.output
        
        # Verify use case was called
        mock_use_cases['bot_management'].list_bots.assert_called_once()
    
    def test_bot_list_json_format_e2e(self, cli_runner, mock_use_cases):
        """Test bot list command with JSON format."""
        # Prepare bot data
        bots_data = [
            test_data_factory.create_bot_config(id=1, name="Test Bot", status="running")
        ]
        
        # Mock use case
        mock_use_cases['bot_management'].list_bots.return_value = {
            'success': True,
            'bots': bots_data,
            'total': 1
        }
        
        # Execute CLI command with JSON format
        result = cli_runner.invoke(cli_app, ['bot', 'list', '--format', 'json'])
        
        # Verify JSON output
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data['success'] is True
        assert len(data['bots']) == 1
        assert data['bots'][0]['name'] == 'Test Bot'
    
    def test_bot_create_command_e2e(self, cli_runner, mock_use_cases):
        """Test bot create command with real CLI interaction."""
        # Prepare bot data
        bot_data = test_data_factory.create_bot_config(id=1, name="New Bot", status="created")
        
        # Mock use case
        mock_use_cases['bot_management'].create_bot.return_value = {
            'success': True,
            'bot': bot_data,
            'message': 'Bot created successfully'
        }
        
        # Execute CLI command
        result = cli_runner.invoke(cli_app, [
            'bot', 'create',
            '--name', 'New Bot',
            '--token', 'test_token_123',
            '--description', 'Test bot description'
        ])
        
        # Verify output
        assert result.exit_code == 0
        assert 'Bot created successfully' in result.output
        assert 'New Bot' in result.output
        
        # Verify use case was called
        mock_use_cases['bot_management'].create_bot.assert_called_once()
    
    def test_bot_create_interactive_e2e(self, cli_runner, mock_use_cases):
        """Test bot create command with interactive input."""
        # Prepare bot data
        bot_data = test_data_factory.create_bot_config(id=1, name="Interactive Bot", status="created")
        
        # Mock use case
        mock_use_cases['bot_management'].create_bot.return_value = {
            'success': True,
            'bot': bot_data,
            'message': 'Bot created successfully'
        }
        
        # Execute CLI command with interactive input
        result = cli_runner.invoke(cli_app, ['bot', 'create'], input='Interactive Bot\ntest_token_456\nInteractive bot description\n')
        
        # Verify output
        assert result.exit_code == 0
        assert 'Bot created successfully' in result.output
        assert 'Interactive Bot' in result.output
    
    def test_bot_show_command_e2e(self, cli_runner, mock_use_cases):
        """Test bot show command with real CLI interaction."""
        # Prepare bot data
        bot_data = test_data_factory.create_bot_config(id=1, name="Test Bot", status="running")
        
        # Mock use case
        mock_use_cases['bot_management'].get_bot.return_value = {
            'success': True,
            'bot': bot_data
        }
        
        # Execute CLI command
        result = cli_runner.invoke(cli_app, ['bot', 'show', '1'])
        
        # Verify output
        assert result.exit_code == 0
        assert 'Test Bot' in result.output
        assert 'running' in result.output
        assert 'ID: 1' in result.output
        
        # Verify use case was called
        mock_use_cases['bot_management'].get_bot.assert_called_once_with(1)
    
    def test_bot_management_actions_e2e(self, cli_runner, mock_use_cases):
        """Test bot management actions (start, stop, restart)."""
        # Test start bot
        mock_use_cases['bot_management'].start_bot.return_value = {
            'success': True,
            'message': 'Bot started successfully'
        }
        
        result = cli_runner.invoke(cli_app, ['bot', 'start', '1'])
        assert result.exit_code == 0
        assert 'Bot started successfully' in result.output
        
        # Test stop bot
        mock_use_cases['bot_management'].stop_bot.return_value = {
            'success': True,
            'message': 'Bot stopped successfully'
        }
        
        result = cli_runner.invoke(cli_app, ['bot', 'stop', '1'])
        assert result.exit_code == 0
        assert 'Bot stopped successfully' in result.output
        
        # Test restart bot
        mock_use_cases['bot_management'].restart_bot.return_value = {
            'success': True,
            'message': 'Bot restarted successfully'
        }
        
        result = cli_runner.invoke(cli_app, ['bot', 'restart', '1'])
        assert result.exit_code == 0
        assert 'Bot restarted successfully' in result.output
    
    def test_bot_stats_command_e2e(self, cli_runner, mock_use_cases):
        """Test bot stats command with real CLI interaction."""
        # Prepare stats data
        stats_data = {
            'messages_sent': 150,
            'messages_received': 200,
            'users_count': 25,
            'uptime': '2 days, 5 hours',
            'last_activity': '2025-08-21 10:30:00'
        }
        
        # Mock use case
        mock_use_cases['bot_management'].get_bot_stats.return_value = {
            'success': True,
            'stats': stats_data
        }
        
        # Execute CLI command
        result = cli_runner.invoke(cli_app, ['bot', 'stats', '1'])
        
        # Verify output
        assert result.exit_code == 0
        assert '150' in result.output  # messages_sent
        assert '25' in result.output   # users_count
        assert '2 days, 5 hours' in result.output  # uptime
        
        # Verify use case was called
        mock_use_cases['bot_management'].get_bot_stats.assert_called_once_with(1)


class TestCLIE2EConversationManagement:
    """Test end-to-end conversation management scenarios in CLI interface."""
    
    def test_conversation_list_command_e2e(self, cli_runner, mock_use_cases):
        """Test conversation list command with real CLI interaction."""
        # Prepare conversation data
        conversations_data = [
            test_data_factory.create_conversation(id=1, bot_id=1, user_id=1001),
            test_data_factory.create_conversation(id=2, bot_id=1, user_id=1002),
            test_data_factory.create_conversation(id=3, bot_id=2, user_id=1003)
        ]
        
        # Mock use case
        mock_use_cases['conversation'].list_conversations.return_value = {
            'success': True,
            'conversations': conversations_data,
            'total': 3
        }
        
        # Execute CLI command
        result = cli_runner.invoke(cli_app, ['conversation', 'list'])
        
        # Verify output
        assert result.exit_code == 0
        assert 'conversation' in result.output.lower()
        assert '3' in result.output  # total count
        
        # Verify use case was called
        mock_use_cases['conversation'].list_conversations.assert_called_once()
    
    def test_conversation_show_command_e2e(self, cli_runner, mock_use_cases):
        """Test conversation show command with real CLI interaction."""
        # Prepare conversation with messages
        conversation = test_data_factory.create_conversation(id=1, bot_id=1, user_id=1001)
        messages = test_data_factory.create_messages(5, conversation_id=1)
        conversation['messages'] = messages
        
        # Mock use case
        mock_use_cases['conversation'].get_conversation.return_value = {
            'success': True,
            'conversation': conversation
        }
        
        # Execute CLI command
        result = cli_runner.invoke(cli_app, ['conversation', 'show', '1'])
        
        # Verify output
        assert result.exit_code == 0
        assert 'conversation' in result.output.lower()
        assert '5' in result.output  # message count
        
        # Verify use case was called
        mock_use_cases['conversation'].get_conversation.assert_called_once_with(1)
    
    def test_conversation_messages_command_e2e(self, cli_runner, mock_use_cases):
        """Test conversation messages command with real CLI interaction."""
        # Prepare messages data
        messages = test_data_factory.create_messages(10, conversation_id=1)
        
        # Mock use case
        mock_use_cases['conversation'].get_conversation_messages.return_value = {
            'success': True,
            'messages': messages,
            'total': 10
        }
        
        # Execute CLI command
        result = cli_runner.invoke(cli_app, ['conversation', 'messages', '1'])
        
        # Verify output
        assert result.exit_code == 0
        assert 'message' in result.output.lower()
        assert '10' in result.output  # message count
        
        # Verify use case was called
        mock_use_cases['conversation'].get_conversation_messages.assert_called_once_with(1)
    
    def test_conversation_clear_command_e2e(self, cli_runner, mock_use_cases):
        """Test conversation clear command with real CLI interaction."""
        # Mock use case
        mock_use_cases['conversation'].clear_conversation.return_value = {
            'success': True,
            'message': 'Conversation cleared successfully',
            'conversation_id': 1
        }
        
        # Execute CLI command with force flag
        result = cli_runner.invoke(cli_app, ['conversation', 'clear', '1', '--force'])
        
        # Verify output
        assert result.exit_code == 0
        assert 'Conversation cleared successfully' in result.output
        
        # Verify use case was called
        mock_use_cases['conversation'].clear_conversation.assert_called_once_with(1)
    
    def test_conversation_clear_interactive_e2e(self, cli_runner, mock_use_cases):
        """Test conversation clear command with interactive confirmation."""
        # Mock use case
        mock_use_cases['conversation'].clear_conversation.return_value = {
            'success': True,
            'message': 'Conversation cleared successfully',
            'conversation_id': 1
        }
        
        # Execute CLI command with interactive confirmation
        result = cli_runner.invoke(cli_app, ['conversation', 'clear', '1'], input='y\n')
        
        # Verify output
        assert result.exit_code == 0
        assert 'Conversation cleared successfully' in result.output
    
    def test_conversation_stats_command_e2e(self, cli_runner, mock_use_cases):
        """Test conversation stats command with real CLI interaction."""
        # Prepare stats data
        stats_data = {
            'total_messages': 50,
            'user_messages': 30,
            'bot_messages': 20,
            'avg_response_time': '2.5s',
            'last_activity': '2025-08-21 10:30:00'
        }
        
        # Mock use case
        mock_use_cases['conversation'].get_conversation_stats.return_value = {
            'success': True,
            'stats': stats_data
        }
        
        # Execute CLI command
        result = cli_runner.invoke(cli_app, ['conversation', 'stats', '1'])
        
        # Verify output
        assert result.exit_code == 0
        assert '50' in result.output  # total_messages
        assert '2.5s' in result.output  # avg_response_time
        
        # Verify use case was called
        mock_use_cases['conversation'].get_conversation_stats.assert_called_once_with(1)


class TestCLIE2ESystemManagement:
    """Test end-to-end system management scenarios in CLI interface."""
    
    def test_system_status_command_e2e(self, cli_runner, mock_use_cases):
        """Test system status command with real CLI interaction."""
        # Prepare system status data
        status_data = test_data_factory.create_system_status()
        
        # Mock use case
        mock_use_cases['system'].get_system_status.return_value = {
            'success': True,
            'status': status_data
        }
        
        # Execute CLI command
        result = cli_runner.invoke(cli_app, ['system', 'status'])
        
        # Verify output
        assert result.exit_code == 0
        assert 'system' in result.output.lower()
        assert 'status' in result.output.lower()
        
        # Verify use case was called
        mock_use_cases['system'].get_system_status.assert_called_once()
    
    def test_system_backup_commands_e2e(self, cli_runner, mock_use_cases):
        """Test system backup commands with real CLI interaction."""
        # Test backup list
        backups_data = [
            test_data_factory.create_backup_info(id=1, name="backup_2025_08_21"),
            test_data_factory.create_backup_info(id=2, name="backup_2025_08_20")
        ]
        
        mock_use_cases['system'].list_backups.return_value = {
            'success': True,
            'backups': backups_data,
            'total': 2
        }
        
        result = cli_runner.invoke(cli_app, ['system', 'backup', 'list'])
        assert result.exit_code == 0
        assert 'backup' in result.output.lower()
        
        # Test backup create
        backup_data = test_data_factory.create_backup_info()
        mock_use_cases['system'].create_backup.return_value = {
            'success': True,
            'backup': backup_data,
            'message': 'Backup created successfully'
        }
        
        result = cli_runner.invoke(cli_app, ['system', 'backup', 'create', '--description', 'E2E test backup'])
        assert result.exit_code == 0
        assert 'Backup created successfully' in result.output
        
        # Test backup restore
        mock_use_cases['system'].restore_backup.return_value = {
            'success': True,
            'message': 'Backup restored successfully'
        }
        
        result = cli_runner.invoke(cli_app, ['system', 'backup', 'restore', '1', '--force'])
        assert result.exit_code == 0
        assert 'Backup restored successfully' in result.output
    
    def test_system_config_commands_e2e(self, cli_runner, mock_use_cases):
        """Test system config commands with real CLI interaction."""
        # Test config show
        config_data = {
            'database_url': 'sqlite:///test.db',
            'log_level': 'INFO',
            'max_bots': 10,
            'backup_retention_days': 30
        }
        
        mock_use_cases['system'].get_system_config.return_value = {
            'success': True,
            'config': config_data
        }
        
        result = cli_runner.invoke(cli_app, ['system', 'config', 'show'])
        assert result.exit_code == 0
        assert 'sqlite' in result.output
        assert 'INFO' in result.output
        
        # Test config update
        mock_use_cases['system'].update_system_config.return_value = {
            'success': True,
            'message': 'Configuration updated successfully'
        }
        
        result = cli_runner.invoke(cli_app, [
            'system', 'config', 'update',
            '--log-level', 'DEBUG',
            '--max-bots', '15'
        ])
        assert result.exit_code == 0
        assert 'Configuration updated successfully' in result.output
    
    def test_system_update_commands_e2e(self, cli_runner, mock_use_cases):
        """Test system update commands with real CLI interaction."""
        # Test update check
        update_data = test_data_factory.create_update_info()
        mock_use_cases['system'].check_for_updates.return_value = {
            'success': True,
            'update_available': True,
            'update_info': update_data
        }
        
        result = cli_runner.invoke(cli_app, ['system', 'update', 'check'])
        assert result.exit_code == 0
        assert 'update' in result.output.lower()
        
        # Test update apply
        mock_use_cases['system'].apply_update.return_value = {
            'success': True,
            'message': 'Update applied successfully'
        }
        
        result = cli_runner.invoke(cli_app, ['system', 'update', 'apply', '--force'])
        assert result.exit_code == 0
        assert 'Update applied successfully' in result.output
    
    def test_system_logs_command_e2e(self, cli_runner, mock_use_cases):
        """Test system logs command with real CLI interaction."""
        # Prepare logs data
        logs_data = [
            {'timestamp': '2025-08-21 10:30:00', 'level': 'INFO', 'message': 'System started'},
            {'timestamp': '2025-08-21 10:31:00', 'level': 'INFO', 'message': 'Bot 1 started'},
            {'timestamp': '2025-08-21 10:32:00', 'level': 'ERROR', 'message': 'Connection failed'}
        ]
        
        # Mock use case
        mock_use_cases['system'].get_system_logs.return_value = {
            'success': True,
            'logs': logs_data,
            'total': 3
        }
        
        # Execute CLI command
        result = cli_runner.invoke(cli_app, ['system', 'logs'])
        
        # Verify output
        assert result.exit_code == 0
        assert 'System started' in result.output
        assert 'Connection failed' in result.output
        
        # Verify use case was called
        mock_use_cases['system'].get_system_logs.assert_called_once()


class TestCLIE2EErrorHandling:
    """Test end-to-end error handling scenarios in CLI interface."""
    
    def test_command_not_found_e2e(self, cli_runner):
        """Test handling of non-existent commands."""
        result = cli_runner.invoke(cli_app, ['nonexistent', 'command'])
        assert result.exit_code == 2  # Click error code for command not found
        assert 'No such command' in result.output
    
    def test_invalid_arguments_e2e(self, cli_runner):
        """Test handling of invalid arguments."""
        result = cli_runner.invoke(cli_app, ['bot', 'show', 'invalid_id'])
        assert result.exit_code == 1
        assert 'error' in result.output.lower()
    
    def test_missing_required_arguments_e2e(self, cli_runner):
        """Test handling of missing required arguments."""
        result = cli_runner.invoke(cli_app, ['bot', 'show'])
        assert result.exit_code == 2  # Click error code for missing argument
        assert 'Missing argument' in result.output
    
    def test_use_case_exception_handling_e2e(self, cli_runner, mock_use_cases):
        """Test handling of use case exceptions in CLI."""
        # Mock use case to raise exception
        mock_use_cases['bot_management'].list_bots.side_effect = Exception("Database connection failed")
        
        # Execute CLI command
        result = cli_runner.invoke(cli_app, ['bot', 'list'])
        
        # Verify error handling
        assert result.exit_code == 1
        assert 'Database connection failed' in result.output or 'error' in result.output.lower()


class TestCLIE2EOutputFormats:
    """Test end-to-end output format scenarios in CLI interface."""
    
    def test_json_output_format_e2e(self, cli_runner, mock_use_cases):
        """Test JSON output format for various commands."""
        # Prepare test data
        bots_data = [test_data_factory.create_bot_config(id=1, name="Test Bot", status="running")]
        mock_use_cases['bot_management'].list_bots.return_value = {
            'success': True,
            'bots': bots_data,
            'total': 1
        }
        
        # Test bot list with JSON format
        result = cli_runner.invoke(cli_app, ['bot', 'list', '--format', 'json'])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data['success'] is True
        assert len(data['bots']) == 1
        
        # Test conversation list with JSON format
        conversations_data = [test_data_factory.create_conversation(id=1, bot_id=1)]
        mock_use_cases['conversation'].list_conversations.return_value = {
            'success': True,
            'conversations': conversations_data,
            'total': 1
        }
        
        result = cli_runner.invoke(cli_app, ['conversation', 'list', '--format', 'json'])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data['success'] is True
        assert len(data['conversations']) == 1
    
    def test_csv_output_format_e2e(self, cli_runner, mock_use_cases):
        """Test CSV output format for various commands."""
        # Prepare test data
        bots_data = [test_data_factory.create_bot_config(id=1, name="Test Bot", status="running")]
        mock_use_cases['bot_management'].list_bots.return_value = {
            'success': True,
            'bots': bots_data,
            'total': 1
        }
        
        # Test bot list with CSV format
        result = cli_runner.invoke(cli_app, ['bot', 'list', '--format', 'csv'])
        assert result.exit_code == 0
        assert 'id,name,status' in result.output
        assert '1,Test Bot,running' in result.output
    
    def test_table_output_format_e2e(self, cli_runner, mock_use_cases):
        """Test table output format for various commands."""
        # Prepare test data
        bots_data = [test_data_factory.create_bot_config(id=1, name="Test Bot", status="running")]
        mock_use_cases['bot_management'].list_bots.return_value = {
            'success': True,
            'bots': bots_data,
            'total': 1
        }
        
        # Test bot list with table format
        result = cli_runner.invoke(cli_app, ['bot', 'list', '--format', 'table'])
        assert result.exit_code == 0
        assert 'ID' in result.output
        assert 'Name' in result.output
        assert 'Status' in result.output
        assert 'Test Bot' in result.output


class TestCLIE2EInteractiveFeatures:
    """Test end-to-end interactive features in CLI interface."""
    
    def test_interactive_bot_creation_e2e(self, cli_runner, mock_use_cases):
        """Test interactive bot creation with prompts."""
        # Prepare bot data
        bot_data = test_data_factory.create_bot_config(id=1, name="Interactive Bot", status="created")
        mock_use_cases['bot_management'].create_bot.return_value = {
            'success': True,
            'bot': bot_data,
            'message': 'Bot created successfully'
        }
        
        # Execute CLI command with interactive input
        result = cli_runner.invoke(cli_app, ['bot', 'create'], input='Interactive Bot\ntest_token_789\nInteractive bot description\n')
        
        # Verify output
        assert result.exit_code == 0
        assert 'Bot created successfully' in result.output
        assert 'Interactive Bot' in result.output
    
    def test_interactive_confirmation_e2e(self, cli_runner, mock_use_cases):
        """Test interactive confirmation for destructive actions."""
        # Mock use case
        mock_use_cases['bot_management'].delete_bot.return_value = {
            'success': True,
            'message': 'Bot deleted successfully'
        }
        
        # Execute CLI command with interactive confirmation
        result = cli_runner.invoke(cli_app, ['bot', 'delete', '1'], input='y\n')
        
        # Verify output
        assert result.exit_code == 0
        assert 'Bot deleted successfully' in result.output
    
    def test_interactive_cancellation_e2e(self, cli_runner, mock_use_cases):
        """Test interactive cancellation for destructive actions."""
        # Execute CLI command with interactive cancellation
        result = cli_runner.invoke(cli_app, ['bot', 'delete', '1'], input='n\n')
        
        # Verify output
        assert result.exit_code == 0
        assert 'cancelled' in result.output.lower() or 'aborted' in result.output.lower()


class TestCLIE2EPerformance:
    """Test end-to-end performance scenarios in CLI interface."""
    
    def test_command_execution_time_e2e(self, cli_runner, mock_use_cases):
        """Test command execution time."""
        import time
        
        # Prepare test data
        bots_data = [test_data_factory.create_bot_config(id=1, name="Test Bot", status="running")]
        mock_use_cases['bot_management'].list_bots.return_value = {
            'success': True,
            'bots': bots_data,
            'total': 1
        }
        
        # Measure execution time
        start_time = time.time()
        result = cli_runner.invoke(cli_app, ['bot', 'list'])
        execution_time = time.time() - start_time
        
        # Verify execution time is reasonable (less than 1 second)
        assert execution_time < 1.0, f"Command execution time {execution_time}s exceeds 1s"
        assert result.exit_code == 0
    
    def test_large_data_handling_e2e(self, cli_runner, mock_use_cases):
        """Test handling of large data sets."""
        # Prepare large dataset
        bots_data = [
            test_data_factory.create_bot_config(id=i, name=f"Bot {i}", status="running")
            for i in range(1, 101)  # 100 bots
        ]
        
        mock_use_cases['bot_management'].list_bots.return_value = {
            'success': True,
            'bots': bots_data,
            'total': 100
        }
        
        # Execute CLI command
        result = cli_runner.invoke(cli_app, ['bot', 'list'])
        
        # Verify output
        assert result.exit_code == 0
        assert '100' in result.output  # total count
        assert 'Bot 1' in result.output
        assert 'Bot 100' in result.output






