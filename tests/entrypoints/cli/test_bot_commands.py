"""
Unit tests for bot commands (CLI Entry Point).

Tests cover all bot-related CLI commands including
list, show, create, update, delete, start, stop, restart, status, stats.
"""

import pytest
import json
from unittest.mock import Mock, patch
from click.testing import CliRunner
from tests.entrypoints.factories import test_data_factory


class TestBotListCommand:
    """Test bot list command functionality."""
    
    def test_bot_list_empty(self, cli_runner, mock_use_cases):
        """Test bot list command with no bots."""
        mock_use_cases['bot_management'].list_bots.return_value = []
        
        result = cli_runner.invoke(cli_runner.app, ['bot', 'list'])
        
        assert result.exit_code == 0
        assert 'No bots found' in result.output
        mock_use_cases['bot_management'].list_bots.assert_called_once()
    
    def test_bot_list_populated(self, cli_runner, mock_use_cases):
        """Test bot list command with bots."""
        bots = [
            test_data_factory.create_bot_config(id=1, name='Test Bot 1'),
            test_data_factory.create_bot_config(id=2, name='Test Bot 2')
        ]
        mock_use_cases['bot_management'].list_bots.return_value = bots
        
        result = cli_runner.invoke(cli_runner.app, ['bot', 'list'])
        
        assert result.exit_code == 0
        assert 'Test Bot 1' in result.output
        assert 'Test Bot 2' in result.output
        assert 'ID' in result.output
        assert 'Name' in result.output
        assert 'Status' in result.output
    
    def test_bot_list_json_format(self, cli_runner, mock_use_cases):
        """Test bot list command with JSON output."""
        bots = [test_data_factory.create_bot_config(id=1, name='Test Bot')]
        mock_use_cases['bot_management'].list_bots.return_value = bots
        
        result = cli_runner.invoke(cli_runner.app, ['bot', 'list', '--format', 'json'])
        
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]['name'] == 'Test Bot'
    
    def test_bot_list_csv_format(self, cli_runner, mock_use_cases):
        """Test bot list command with CSV output."""
        bots = [test_data_factory.create_bot_config(id=1, name='Test Bot')]
        mock_use_cases['bot_management'].list_bots.return_value = bots
        
        result = cli_runner.invoke(cli_runner.app, ['bot', 'list', '--format', 'csv'])
        
        assert result.exit_code == 0
        assert 'id,name,status' in result.output.lower()
        assert 'test bot' in result.output.lower()
    
    def test_bot_list_with_filters(self, cli_runner, mock_use_cases):
        """Test bot list command with filters."""
        bots = [test_data_factory.create_bot_config(id=1, name='Active Bot', status='active')]
        mock_use_cases['bot_management'].list_bots.return_value = bots
        
        result = cli_runner.invoke(cli_runner.app, ['bot', 'list', '--status', 'active'])
        
        assert result.exit_code == 0
        assert 'Active Bot' in result.output
        mock_use_cases['bot_management'].list_bots.assert_called_once_with(status='active')


class TestBotShowCommand:
    """Test bot show command functionality."""
    
    def test_bot_show_success(self, cli_runner, mock_use_cases):
        """Test bot show command with valid bot ID."""
        bot = test_data_factory.create_bot_config(id=1, name='Test Bot')
        mock_use_cases['bot_management'].get_bot.return_value = bot
        
        result = cli_runner.invoke(cli_runner.app, ['bot', 'show', '1'])
        
        assert result.exit_code == 0
        assert 'Test Bot' in result.output
        assert 'ID: 1' in result.output
        assert 'Token:' in result.output
        assert 'Status:' in result.output
        mock_use_cases['bot_management'].get_bot.assert_called_once_with(1)
    
    def test_bot_show_not_found(self, cli_runner, mock_use_cases):
        """Test bot show command with non-existent bot."""
        mock_use_cases['bot_management'].get_bot.return_value = None
        
        result = cli_runner.invoke(cli_runner.app, ['bot', 'show', '999'])
        
        assert result.exit_code == 1
        assert 'Bot not found' in result.output
        assert 'Error:' in result.output
    
    def test_bot_show_invalid_id(self, cli_runner):
        """Test bot show command with invalid ID."""
        result = cli_runner.invoke(cli_runner.app, ['bot', 'show', 'invalid'])
        
        assert result.exit_code == 2  # Click parameter error
        assert 'Invalid value' in result.output
    
    def test_bot_show_json_format(self, cli_runner, mock_use_cases):
        """Test bot show command with JSON output."""
        bot = test_data_factory.create_bot_config(id=1, name='Test Bot')
        mock_use_cases['bot_management'].get_bot.return_value = bot
        
        result = cli_runner.invoke(cli_runner.app, ['bot', 'show', '1', '--format', 'json'])
        
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data['id'] == 1
        assert data['name'] == 'Test Bot'


class TestBotCreateCommand:
    """Test bot create command functionality."""
    
    def test_bot_create_success(self, cli_runner, mock_use_cases):
        """Test bot create command with valid data."""
        new_bot = test_data_factory.create_bot_config(id=1, name='New Bot')
        mock_use_cases['bot_management'].create_bot.return_value = new_bot
        
        result = cli_runner.invoke(cli_runner.app, [
            'bot', 'create',
            '--name', 'New Bot',
            '--token', '123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11'
        ])
        
        assert result.exit_code == 0
        assert 'Bot created successfully' in result.output
        assert 'New Bot' in result.output
        mock_use_cases['bot_management'].create_bot.assert_called_once()
    
    def test_bot_create_missing_required_fields(self, cli_runner):
        """Test bot create command with missing required fields."""
        result = cli_runner.invoke(cli_runner.app, ['bot', 'create', '--name', 'New Bot'])
        
        assert result.exit_code == 2  # Click parameter error
        assert 'Missing option' in result.output
    
    def test_bot_create_invalid_token(self, cli_runner):
        """Test bot create command with invalid token."""
        result = cli_runner.invoke(cli_runner.app, [
            'bot', 'create',
            '--name', 'New Bot',
            '--token', 'invalid_token'
        ])
        
        assert result.exit_code == 2  # Click parameter error
        assert 'Invalid value' in result.output
    
    def test_bot_create_validation_error(self, cli_runner, mock_use_cases):
        """Test bot create command with validation error."""
        mock_use_cases['bot_management'].create_bot.side_effect = ValueError('Invalid bot name')
        
        result = cli_runner.invoke(cli_runner.app, [
            'bot', 'create',
            '--name', 'Invalid Bot Name',
            '--token', '123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11'
        ])
        
        assert result.exit_code == 1
        assert 'Error:' in result.output
        assert 'Invalid bot name' in result.output
    
    def test_bot_create_with_optional_fields(self, cli_runner, mock_use_cases):
        """Test bot create command with optional fields."""
        new_bot = test_data_factory.create_bot_config(id=1, name='New Bot')
        mock_use_cases['bot_management'].create_bot.return_value = new_bot
        
        result = cli_runner.invoke(cli_runner.app, [
            'bot', 'create',
            '--name', 'New Bot',
            '--token', '123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11',
            '--description', 'Test bot description',
            '--webhook-url', 'https://example.com/webhook'
        ])
        
        assert result.exit_code == 0
        assert 'Bot created successfully' in result.output
        mock_use_cases['bot_management'].create_bot.assert_called_once()


class TestBotUpdateCommand:
    """Test bot update command functionality."""
    
    def test_bot_update_success(self, cli_runner, mock_use_cases):
        """Test bot update command with valid data."""
        updated_bot = test_data_factory.create_bot_config(id=1, name='Updated Bot')
        mock_use_cases['bot_management'].update_bot.return_value = updated_bot
        
        result = cli_runner.invoke(cli_runner.app, [
            'bot', 'update', '1',
            '--name', 'Updated Bot',
            '--description', 'Updated description'
        ])
        
        assert result.exit_code == 0
        assert 'Bot updated successfully' in result.output
        assert 'Updated Bot' in result.output
        mock_use_cases['bot_management'].update_bot.assert_called_once()
    
    def test_bot_update_not_found(self, cli_runner, mock_use_cases):
        """Test bot update command with non-existent bot."""
        mock_use_cases['bot_management'].update_bot.return_value = None
        
        result = cli_runner.invoke(cli_runner.app, [
            'bot', 'update', '999',
            '--name', 'Updated Bot'
        ])
        
        assert result.exit_code == 1
        assert 'Bot not found' in result.output
        assert 'Error:' in result.output
    
    def test_bot_update_no_changes(self, cli_runner):
        """Test bot update command with no changes specified."""
        result = cli_runner.invoke(cli_runner.app, ['bot', 'update', '1'])
        
        assert result.exit_code == 2  # Click parameter error
        assert 'Missing option' in result.output
    
    def test_bot_update_invalid_id(self, cli_runner):
        """Test bot update command with invalid ID."""
        result = cli_runner.invoke(cli_runner.app, [
            'bot', 'update', 'invalid',
            '--name', 'Updated Bot'
        ])
        
        assert result.exit_code == 2  # Click parameter error
        assert 'Invalid value' in result.output
    
    def test_bot_update_validation_error(self, cli_runner, mock_use_cases):
        """Test bot update command with validation error."""
        mock_use_cases['bot_management'].update_bot.side_effect = ValueError('Invalid name')
        
        result = cli_runner.invoke(cli_runner.app, [
            'bot', 'update', '1',
            '--name', 'Invalid Name'
        ])
        
        assert result.exit_code == 1
        assert 'Error:' in result.output
        assert 'Invalid name' in result.output


class TestBotDeleteCommand:
    """Test bot delete command functionality."""
    
    def test_bot_delete_success(self, cli_runner, mock_use_cases):
        """Test bot delete command with confirmation."""
        mock_use_cases['bot_management'].delete_bot.return_value = True
        
        result = cli_runner.invoke(cli_runner.app, ['bot', 'delete', '1'], input='y\n')
        
        assert result.exit_code == 0
        assert 'Bot deleted successfully' in result.output
        mock_use_cases['bot_management'].delete_bot.assert_called_once_with(1)
    
    def test_bot_delete_without_confirmation(self, cli_runner, mock_use_cases):
        """Test bot delete command without confirmation."""
        result = cli_runner.invoke(cli_runner.app, ['bot', 'delete', '1'], input='n\n')
        
        assert result.exit_code == 0
        assert 'Operation cancelled' in result.output
        mock_use_cases['bot_management'].delete_bot.assert_not_called()
    
    def test_bot_delete_force_flag(self, cli_runner, mock_use_cases):
        """Test bot delete command with force flag."""
        mock_use_cases['bot_management'].delete_bot.return_value = True
        
        result = cli_runner.invoke(cli_runner.app, ['bot', 'delete', '1', '--force'])
        
        assert result.exit_code == 0
        assert 'Bot deleted successfully' in result.output
        mock_use_cases['bot_management'].delete_bot.assert_called_once_with(1)
    
    def test_bot_delete_not_found(self, cli_runner, mock_use_cases):
        """Test bot delete command with non-existent bot."""
        mock_use_cases['bot_management'].delete_bot.return_value = False
        
        result = cli_runner.invoke(cli_runner.app, ['bot', 'delete', '999', '--force'])
        
        assert result.exit_code == 1
        assert 'Bot not found' in result.output
        assert 'Error:' in result.output
    
    def test_bot_delete_invalid_id(self, cli_runner):
        """Test bot delete command with invalid ID."""
        result = cli_runner.invoke(cli_runner.app, ['bot', 'delete', 'invalid'])
        
        assert result.exit_code == 2  # Click parameter error
        assert 'Invalid value' in result.output


class TestBotStartCommand:
    """Test bot start command functionality."""
    
    def test_bot_start_success(self, cli_runner, mock_use_cases):
        """Test bot start command with valid bot."""
        mock_use_cases['bot_management'].start_bot.return_value = {
            'success': True,
            'message': 'Bot started successfully'
        }
        
        result = cli_runner.invoke(cli_runner.app, ['bot', 'start', '1'])
        
        assert result.exit_code == 0
        assert 'Bot started successfully' in result.output
        mock_use_cases['bot_management'].start_bot.assert_called_once_with(1)
    
    def test_bot_start_not_found(self, cli_runner, mock_use_cases):
        """Test bot start command with non-existent bot."""
        mock_use_cases['bot_management'].start_bot.return_value = {
            'success': False,
            'error': 'Bot not found'
        }
        
        result = cli_runner.invoke(cli_runner.app, ['bot', 'start', '999'])
        
        assert result.exit_code == 1
        assert 'Bot not found' in result.output
        assert 'Error:' in result.output
    
    def test_bot_start_already_running(self, cli_runner, mock_use_cases):
        """Test bot start command with already running bot."""
        mock_use_cases['bot_management'].start_bot.return_value = {
            'success': False,
            'error': 'Bot is already running'
        }
        
        result = cli_runner.invoke(cli_runner.app, ['bot', 'start', '1'])
        
        assert result.exit_code == 1
        assert 'Bot is already running' in result.output
        assert 'Error:' in result.output
    
    def test_bot_start_invalid_id(self, cli_runner):
        """Test bot start command with invalid ID."""
        result = cli_runner.invoke(cli_runner.app, ['bot', 'start', 'invalid'])
        
        assert result.exit_code == 2  # Click parameter error
        assert 'Invalid value' in result.output


class TestBotStopCommand:
    """Test bot stop command functionality."""
    
    def test_bot_stop_success(self, cli_runner, mock_use_cases):
        """Test bot stop command with valid bot."""
        mock_use_cases['bot_management'].stop_bot.return_value = {
            'success': True,
            'message': 'Bot stopped successfully'
        }
        
        result = cli_runner.invoke(cli_runner.app, ['bot', 'stop', '1'])
        
        assert result.exit_code == 0
        assert 'Bot stopped successfully' in result.output
        mock_use_cases['bot_management'].stop_bot.assert_called_once_with(1)
    
    def test_bot_stop_not_found(self, cli_runner, mock_use_cases):
        """Test bot stop command with non-existent bot."""
        mock_use_cases['bot_management'].stop_bot.return_value = {
            'success': False,
            'error': 'Bot not found'
        }
        
        result = cli_runner.invoke(cli_runner.app, ['bot', 'stop', '999'])
        
        assert result.exit_code == 1
        assert 'Bot not found' in result.output
        assert 'Error:' in result.output
    
    def test_bot_stop_not_running(self, cli_runner, mock_use_cases):
        """Test bot stop command with not running bot."""
        mock_use_cases['bot_management'].stop_bot.return_value = {
            'success': False,
            'error': 'Bot is not running'
        }
        
        result = cli_runner.invoke(cli_runner.app, ['bot', 'stop', '1'])
        
        assert result.exit_code == 1
        assert 'Bot is not running' in result.output
        assert 'Error:' in result.output
    
    def test_bot_stop_invalid_id(self, cli_runner):
        """Test bot stop command with invalid ID."""
        result = cli_runner.invoke(cli_runner.app, ['bot', 'stop', 'invalid'])
        
        assert result.exit_code == 2  # Click parameter error
        assert 'Invalid value' in result.output


class TestBotRestartCommand:
    """Test bot restart command functionality."""
    
    def test_bot_restart_success(self, cli_runner, mock_use_cases):
        """Test bot restart command with valid bot."""
        mock_use_cases['bot_management'].restart_bot.return_value = {
            'success': True,
            'message': 'Bot restarted successfully'
        }
        
        result = cli_runner.invoke(cli_runner.app, ['bot', 'restart', '1'])
        
        assert result.exit_code == 0
        assert 'Bot restarted successfully' in result.output
        mock_use_cases['bot_management'].restart_bot.assert_called_once_with(1)
    
    def test_bot_restart_not_found(self, cli_runner, mock_use_cases):
        """Test bot restart command with non-existent bot."""
        mock_use_cases['bot_management'].restart_bot.return_value = {
            'success': False,
            'error': 'Bot not found'
        }
        
        result = cli_runner.invoke(cli_runner.app, ['bot', 'restart', '999'])
        
        assert result.exit_code == 1
        assert 'Bot not found' in result.output
        assert 'Error:' in result.output
    
    def test_bot_restart_invalid_id(self, cli_runner):
        """Test bot restart command with invalid ID."""
        result = cli_runner.invoke(cli_runner.app, ['bot', 'restart', 'invalid'])
        
        assert result.exit_code == 2  # Click parameter error
        assert 'Invalid value' in result.output


class TestBotStatusCommand:
    """Test bot status command functionality."""
    
    def test_bot_status_success(self, cli_runner, mock_use_cases):
        """Test bot status command with valid bot."""
        status_data = {
            'bot_id': 1,
            'status': 'running',
            'uptime': '2h 30m',
            'messages_processed': 150,
            'last_activity': '2024-01-15 10:30:00'
        }
        mock_use_cases['bot_management'].get_bot_status.return_value = status_data
        
        result = cli_runner.invoke(cli_runner.app, ['bot', 'status', '1'])
        
        assert result.exit_code == 0
        assert 'running' in result.output
        assert '2h 30m' in result.output
        assert '150' in result.output
        mock_use_cases['bot_management'].get_bot_status.assert_called_once_with(1)
    
    def test_bot_status_not_found(self, cli_runner, mock_use_cases):
        """Test bot status command with non-existent bot."""
        mock_use_cases['bot_management'].get_bot_status.return_value = None
        
        result = cli_runner.invoke(cli_runner.app, ['bot', 'status', '999'])
        
        assert result.exit_code == 1
        assert 'Bot not found' in result.output
        assert 'Error:' in result.output
    
    def test_bot_status_json_format(self, cli_runner, mock_use_cases):
        """Test bot status command with JSON output."""
        status_data = {
            'bot_id': 1,
            'status': 'running',
            'uptime': '2h 30m'
        }
        mock_use_cases['bot_management'].get_bot_status.return_value = status_data
        
        result = cli_runner.invoke(cli_runner.app, ['bot', 'status', '1', '--format', 'json'])
        
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data['bot_id'] == 1
        assert data['status'] == 'running'
    
    def test_bot_status_invalid_id(self, cli_runner):
        """Test bot status command with invalid ID."""
        result = cli_runner.invoke(cli_runner.app, ['bot', 'status', 'invalid'])
        
        assert result.exit_code == 2  # Click parameter error
        assert 'Invalid value' in result.output


class TestBotStatsCommand:
    """Test bot stats command functionality."""
    
    def test_bot_stats_success(self, cli_runner, mock_use_cases):
        """Test bot stats command with valid bot."""
        stats_data = {
            'bot_id': 1,
            'total_messages': 500,
            'messages_today': 25,
            'active_users': 15,
            'response_time_avg': '1.2s',
            'error_rate': '0.5%'
        }
        mock_use_cases['bot_management'].get_bot_stats.return_value = stats_data
        
        result = cli_runner.invoke(cli_runner.app, ['bot', 'stats', '1'])
        
        assert result.exit_code == 0
        assert '500' in result.output
        assert '25' in result.output
        assert '15' in result.output
        assert '1.2s' in result.output
        assert '0.5%' in result.output
        mock_use_cases['bot_management'].get_bot_stats.assert_called_once_with(1)
    
    def test_bot_stats_not_found(self, cli_runner, mock_use_cases):
        """Test bot stats command with non-existent bot."""
        mock_use_cases['bot_management'].get_bot_stats.return_value = None
        
        result = cli_runner.invoke(cli_runner.app, ['bot', 'stats', '999'])
        
        assert result.exit_code == 1
        assert 'Bot not found' in result.output
        assert 'Error:' in result.output
    
    def test_bot_stats_with_period(self, cli_runner, mock_use_cases):
        """Test bot stats command with specific period."""
        stats_data = {'bot_id': 1, 'total_messages': 100}
        mock_use_cases['bot_management'].get_bot_stats.return_value = stats_data
        
        result = cli_runner.invoke(cli_runner.app, ['bot', 'stats', '1', '--period', '7d'])
        
        assert result.exit_code == 0
        mock_use_cases['bot_management'].get_bot_stats.assert_called_once_with(1, period='7d')
    
    def test_bot_stats_json_format(self, cli_runner, mock_use_cases):
        """Test bot stats command with JSON output."""
        stats_data = {'bot_id': 1, 'total_messages': 500}
        mock_use_cases['bot_management'].get_bot_stats.return_value = stats_data
        
        result = cli_runner.invoke(cli_runner.app, ['bot', 'stats', '1', '--format', 'json'])
        
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data['bot_id'] == 1
        assert data['total_messages'] == 500
    
    def test_bot_stats_invalid_id(self, cli_runner):
        """Test bot stats command with invalid ID."""
        result = cli_runner.invoke(cli_runner.app, ['bot', 'stats', 'invalid'])
        
        assert result.exit_code == 2  # Click parameter error
        assert 'Invalid value' in result.output


class TestBotCommandErrorHandling:
    """Test bot command error handling."""
    
    def test_bot_command_server_error(self, cli_runner, mock_use_cases):
        """Test bot command with server error."""
        mock_use_cases['bot_management'].list_bots.side_effect = Exception("Server error")
        
        result = cli_runner.invoke(cli_runner.app, ['bot', 'list'])
        
        assert result.exit_code == 1
        assert 'Error:' in result.output
        assert 'Server error' in result.output
    
    def test_bot_command_network_error(self, cli_runner, mock_use_cases):
        """Test bot command with network error."""
        mock_use_cases['bot_management'].list_bots.side_effect = ConnectionError("Network error")
        
        result = cli_runner.invoke(cli_runner.app, ['bot', 'list'])
        
        assert result.exit_code == 1
        assert 'Error:' in result.output
        assert 'Network error' in result.output
    
    def test_bot_command_timeout_error(self, cli_runner, mock_use_cases):
        """Test bot command with timeout error."""
        mock_use_cases['bot_management'].list_bots.side_effect = TimeoutError("Request timeout")
        
        result = cli_runner.invoke(cli_runner.app, ['bot', 'list'])
        
        assert result.exit_code == 1
        assert 'Error:' in result.output
        assert 'Request timeout' in result.output


class TestBotCommandHelp:
    """Test bot command help functionality."""
    
    def test_bot_command_help(self, cli_runner):
        """Test bot command help."""
        result = cli_runner.invoke(cli_runner.app, ['bot', '--help'])
        
        assert result.exit_code == 0
        assert 'Usage:' in result.output
        assert 'Commands:' in result.output
        assert 'list' in result.output
        assert 'show' in result.output
        assert 'create' in result.output
        assert 'update' in result.output
        assert 'delete' in result.output
        assert 'start' in result.output
        assert 'stop' in result.output
        assert 'restart' in result.output
        assert 'status' in result.output
        assert 'stats' in result.output
    
    def test_bot_list_help(self, cli_runner):
        """Test bot list command help."""
        result = cli_runner.invoke(cli_runner.app, ['bot', 'list', '--help'])
        
        assert result.exit_code == 0
        assert 'Usage:' in result.output
        assert 'Options:' in result.output
        assert '--format' in result.output
        assert '--status' in result.output
    
    def test_bot_create_help(self, cli_runner):
        """Test bot create command help."""
        result = cli_runner.invoke(cli_runner.app, ['bot', 'create', '--help'])
        
        assert result.exit_code == 0
        assert 'Usage:' in result.output
        assert 'Options:' in result.output
        assert '--name' in result.output
        assert '--token' in result.output
        assert '--description' in result.output







