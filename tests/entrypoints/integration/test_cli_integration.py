"""
Integration tests for CLI Entry Point with real Use Cases.

Tests cover the integration between CLI Entry Point and Use Cases,
including real data flow, command execution, and business logic.
"""

import pytest
import json
from unittest.mock import Mock, patch
from click.testing import CliRunner
from tests.entrypoints.factories import test_data_factory


class TestCLIBotIntegration:
    """Test integration between CLI Entry Point and Bot Management Use Cases."""
    
    def test_bot_list_integration_success(self, cli_runner, mock_use_cases):
        """Test successful integration of bot list command with real use case."""
        # Prepare real bot data
        bots_data = [
            test_data_factory.create_bot_config(id=1, name="Test Bot 1", status="running"),
            test_data_factory.create_bot_config(id=2, name="Test Bot 2", status="stopped"),
            test_data_factory.create_bot_config(id=3, name="Test Bot 3", status="error")
        ]
        
        # Mock use case to return real data
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
    
    def test_bot_list_integration_json_format(self, cli_runner, mock_use_cases):
        """Test bot list command with JSON format integration."""
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
        
        # Verify use case was called
        mock_use_cases['bot_management'].list_bots.assert_called_once()
    
    def test_bot_create_integration_success(self, cli_runner, mock_use_cases):
        """Test successful integration of bot create command with real use case."""
        # Prepare bot data
        bot_data = test_data_factory.create_bot_config(id=1, name="New Bot", status="created")
        
        # Mock use case to return success
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
        
        # Verify use case was called with correct data
        mock_use_cases['bot_management'].create_bot.assert_called_once()
        call_args = mock_use_cases['bot_management'].create_bot.call_args[0][0]
        assert call_args['name'] == 'New Bot'
        assert call_args['token'] == 'test_token_123'
    
    def test_bot_create_integration_validation_error(self, cli_runner, mock_use_cases):
        """Test bot create command with validation error integration."""
        # Mock use case to return validation error
        mock_use_cases['bot_management'].create_bot.return_value = {
            'success': False,
            'error': 'Bot name is required'
        }
        
        # Execute CLI command with invalid data
        result = cli_runner.invoke(cli_app, [
            'bot', 'create',
            '--name', '',  # Invalid empty name
            '--token', 'test_token_123'
        ])
        
        # Verify error handling
        assert result.exit_code == 1
        assert 'Bot name is required' in result.output
        
        # Verify use case was called
        mock_use_cases['bot_management'].create_bot.assert_called_once()
    
    def test_bot_start_integration_success(self, cli_runner, mock_use_cases):
        """Test successful integration of bot start command with real use case."""
        # Mock use case to return success
        mock_use_cases['bot_management'].start_bot.return_value = {
            'success': True,
            'message': 'Bot started successfully',
            'bot_id': 1
        }
        
        # Execute CLI command
        result = cli_runner.invoke(cli_app, ['bot', 'start', '1'])
        
        # Verify output
        assert result.exit_code == 0
        assert 'Bot started successfully' in result.output
        
        # Verify use case was called with correct bot ID
        mock_use_cases['bot_management'].start_bot.assert_called_once_with(1)
    
    def test_bot_start_integration_error(self, cli_runner, mock_use_cases):
        """Test bot start command with error integration."""
        # Mock use case to return error
        mock_use_cases['bot_management'].start_bot.return_value = {
            'success': False,
            'error': 'Bot is already running'
        }
        
        # Execute CLI command
        result = cli_runner.invoke(cli_app, ['bot', 'start', '1'])
        
        # Verify error handling
        assert result.exit_code == 1
        assert 'Bot is already running' in result.output
        
        # Verify use case was called
        mock_use_cases['bot_management'].start_bot.assert_called_once_with(1)
    
    def test_bot_show_integration_success(self, cli_runner, mock_use_cases):
        """Test successful integration of bot show command with real use case."""
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
        
        # Verify use case was called
        mock_use_cases['bot_management'].get_bot.assert_called_once_with(1)
    
    def test_bot_stats_integration_success(self, cli_runner, mock_use_cases):
        """Test successful integration of bot stats command with real use case."""
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


class TestCLIConversationIntegration:
    """Test integration between CLI Entry Point and Conversation Use Cases."""
    
    def test_conversation_list_integration_success(self, cli_runner, mock_use_cases):
        """Test successful integration of conversation list command with real use case."""
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
        
        # Verify use case was called
        mock_use_cases['conversation'].list_conversations.assert_called_once()
    
    def test_conversation_show_integration_success(self, cli_runner, mock_use_cases):
        """Test successful integration of conversation show command with real use case."""
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
        
        # Verify use case was called
        mock_use_cases['conversation'].get_conversation.assert_called_once_with(1)
    
    def test_conversation_clear_integration_success(self, cli_runner, mock_use_cases):
        """Test successful integration of conversation clear command with real use case."""
        # Mock use case
        mock_use_cases['conversation'].clear_conversation.return_value = {
            'success': True,
            'message': 'Conversation cleared successfully',
            'conversation_id': 1
        }
        
        # Execute CLI command with confirmation
        result = cli_runner.invoke(cli_app, ['conversation', 'clear', '1', '--force'])
        
        # Verify output
        assert result.exit_code == 0
        assert 'Conversation cleared successfully' in result.output
        
        # Verify use case was called
        mock_use_cases['conversation'].clear_conversation.assert_called_once_with(1)
    
    def test_conversation_messages_integration_success(self, cli_runner, mock_use_cases):
        """Test successful integration of conversation messages command with real use case."""
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
        
        # Verify use case was called
        mock_use_cases['conversation'].get_conversation_messages.assert_called_once_with(1)
    
    def test_conversation_stats_integration_success(self, cli_runner, mock_use_cases):
        """Test successful integration of conversation stats command with real use case."""
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


class TestCLISystemIntegration:
    """Test integration between CLI Entry Point and System Use Cases."""
    
    def test_system_status_integration_success(self, cli_runner, mock_use_cases):
        """Test successful integration of system status command with real use case."""
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
    
    def test_system_backup_integration_success(self, cli_runner, mock_use_cases):
        """Test successful integration of system backup command with real use case."""
        # Prepare backup data
        backup_data = test_data_factory.create_backup_info()
        
        # Mock use case
        mock_use_cases['system'].create_backup.return_value = {
            'success': True,
            'backup': backup_data,
            'message': 'Backup created successfully'
        }
        
        # Execute CLI command
        result = cli_runner.invoke(cli_app, ['system', 'backup', 'create', '--description', 'Test backup'])
        
        # Verify output
        assert result.exit_code == 0
        assert 'Backup created successfully' in result.output
        
        # Verify use case was called
        mock_use_cases['system'].create_backup.assert_called_once()
    
    def test_system_backup_list_integration_success(self, cli_runner, mock_use_cases):
        """Test successful integration of system backup list command with real use case."""
        # Prepare backups data
        backups_data = [
            test_data_factory.create_backup_info(id=1, name="backup_2025_08_21"),
            test_data_factory.create_backup_info(id=2, name="backup_2025_08_20"),
            test_data_factory.create_backup_info(id=3, name="backup_2025_08_19")
        ]
        
        # Mock use case
        mock_use_cases['system'].list_backups.return_value = {
            'success': True,
            'backups': backups_data,
            'total': 3
        }
        
        # Execute CLI command
        result = cli_runner.invoke(cli_app, ['system', 'backup', 'list'])
        
        # Verify output
        assert result.exit_code == 0
        assert 'backup' in result.output.lower()
        
        # Verify use case was called
        mock_use_cases['system'].list_backups.assert_called_once()
    
    def test_system_update_check_integration_success(self, cli_runner, mock_use_cases):
        """Test successful integration of system update check command with real use case."""
        # Prepare update data
        update_data = test_data_factory.create_update_info()
        
        # Mock use case
        mock_use_cases['system'].check_for_updates.return_value = {
            'success': True,
            'update_available': True,
            'update_info': update_data
        }
        
        # Execute CLI command
        result = cli_runner.invoke(cli_app, ['system', 'update', 'check'])
        
        # Verify output
        assert result.exit_code == 0
        assert 'update' in result.output.lower()
        
        # Verify use case was called
        mock_use_cases['system'].check_for_updates.assert_called_once()
    
    def test_system_config_show_integration_success(self, cli_runner, mock_use_cases):
        """Test successful integration of system config show command with real use case."""
        # Prepare config data
        config_data = {
            'database_url': 'sqlite:///test.db',
            'log_level': 'INFO',
            'max_bots': 10,
            'backup_retention_days': 30
        }
        
        # Mock use case
        mock_use_cases['system'].get_system_config.return_value = {
            'success': True,
            'config': config_data
        }
        
        # Execute CLI command
        result = cli_runner.invoke(cli_app, ['system', 'config', 'show'])
        
        # Verify output
        assert result.exit_code == 0
        assert 'sqlite' in result.output
        assert 'INFO' in result.output
        
        # Verify use case was called
        mock_use_cases['system'].get_system_config.assert_called_once()
    
    def test_system_logs_integration_success(self, cli_runner, mock_use_cases):
        """Test successful integration of system logs command with real use case."""
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


class TestCLIErrorHandlingIntegration:
    """Test integration error handling between CLI Entry Point and Use Cases."""
    
    def test_use_case_exception_handling(self, cli_runner, mock_use_cases):
        """Test handling of use case exceptions in CLI integration."""
        # Mock use case to raise exception
        mock_use_cases['bot_management'].list_bots.side_effect = Exception("Database connection failed")
        
        # Execute CLI command
        result = cli_runner.invoke(cli_app, ['bot', 'list'])
        
        # Verify error handling
        assert result.exit_code == 1
        assert 'Database connection failed' in result.output or 'error' in result.output.lower()
    
    def test_use_case_validation_error_handling(self, cli_runner, mock_use_cases):
        """Test handling of validation errors in CLI integration."""
        # Mock use case to return validation error
        mock_use_cases['bot_management'].create_bot.return_value = {
            'success': False,
            'error': 'Validation failed',
            'details': {
                'name': ['Name is required'],
                'token': ['Token is invalid']
            }
        }
        
        # Execute CLI command with invalid data
        result = cli_runner.invoke(cli_app, [
            'bot', 'create',
            '--name', '',
            '--token', 'invalid'
        ])
        
        # Verify validation error handling
        assert result.exit_code == 1
        assert 'Validation failed' in result.output or 'error' in result.output.lower()
    
    def test_use_case_not_found_handling(self, cli_runner, mock_use_cases):
        """Test handling of not found errors in CLI integration."""
        # Mock use case to return not found
        mock_use_cases['bot_management'].get_bot.return_value = {
            'success': False,
            'error': 'Bot not found'
        }
        
        # Execute CLI command for non-existent bot
        result = cli_runner.invoke(cli_app, ['bot', 'show', '999'])
        
        # Verify not found handling
        assert result.exit_code == 1
        assert 'Bot not found' in result.output


class TestCLIDataFlowIntegration:
    """Test complete data flow integration between CLI Entry Point and Use Cases."""
    
    def test_complete_bot_workflow_integration(self, cli_runner, mock_use_cases):
        """Test complete bot workflow integration."""
        # Step 1: List bots
        bots_data = [test_data_factory.create_bot_config(id=1, name="Test Bot", status="stopped")]
        mock_use_cases['bot_management'].list_bots.return_value = {
            'success': True,
            'bots': bots_data,
            'total': 1
        }
        
        result = cli_runner.invoke(cli_app, ['bot', 'list'])
        assert result.exit_code == 0
        
        # Step 2: Start bot
        mock_use_cases['bot_management'].start_bot.return_value = {
            'success': True,
            'message': 'Bot started successfully'
        }
        
        result = cli_runner.invoke(cli_app, ['bot', 'start', '1'])
        assert result.exit_code == 0
        
        # Step 3: Get bot status
        mock_use_cases['bot_management'].get_bot_status.return_value = {
            'success': True,
            'status': 'running'
        }
        
        result = cli_runner.invoke(cli_app, ['bot', 'status', '1'])
        assert result.exit_code == 0
        
        # Verify all use cases were called
        assert mock_use_cases['bot_management'].list_bots.called
        assert mock_use_cases['bot_management'].start_bot.called
        assert mock_use_cases['bot_management'].get_bot_status.called
    
    def test_complete_conversation_workflow_integration(self, cli_runner, mock_use_cases):
        """Test complete conversation workflow integration."""
        # Step 1: List conversations
        conversations_data = [test_data_factory.create_conversation(id=1, bot_id=1)]
        mock_use_cases['conversation'].list_conversations.return_value = {
            'success': True,
            'conversations': conversations_data,
            'total': 1
        }
        
        result = cli_runner.invoke(cli_app, ['conversation', 'list'])
        assert result.exit_code == 0
        
        # Step 2: Show conversation
        conversation = test_data_factory.create_conversation(id=1, bot_id=1)
        conversation['messages'] = test_data_factory.create_messages(3, conversation_id=1)
        mock_use_cases['conversation'].get_conversation.return_value = {
            'success': True,
            'conversation': conversation
        }
        
        result = cli_runner.invoke(cli_app, ['conversation', 'show', '1'])
        assert result.exit_code == 0
        
        # Step 3: Clear conversation
        mock_use_cases['conversation'].clear_conversation.return_value = {
            'success': True,
            'message': 'Conversation cleared'
        }
        
        result = cli_runner.invoke(cli_app, ['conversation', 'clear', '1', '--force'])
        assert result.exit_code == 0
        
        # Verify all use cases were called
        assert mock_use_cases['conversation'].list_conversations.called
        assert mock_use_cases['conversation'].get_conversation.called
        assert mock_use_cases['conversation'].clear_conversation.called
    
    def test_complete_system_workflow_integration(self, cli_runner, mock_use_cases):
        """Test complete system workflow integration."""
        # Step 1: Check system status
        status_data = test_data_factory.create_system_status()
        mock_use_cases['system'].get_system_status.return_value = {
            'success': True,
            'status': status_data
        }
        
        result = cli_runner.invoke(cli_app, ['system', 'status'])
        assert result.exit_code == 0
        
        # Step 2: Create backup
        backup_data = test_data_factory.create_backup_info()
        mock_use_cases['system'].create_backup.return_value = {
            'success': True,
            'backup': backup_data,
            'message': 'Backup created'
        }
        
        result = cli_runner.invoke(cli_app, ['system', 'backup', 'create'])
        assert result.exit_code == 0
        
        # Step 3: Check for updates
        update_data = test_data_factory.create_update_info()
        mock_use_cases['system'].check_for_updates.return_value = {
            'success': True,
            'update_available': False,
            'update_info': update_data
        }
        
        result = cli_runner.invoke(cli_app, ['system', 'update', 'check'])
        assert result.exit_code == 0
        
        # Verify all use cases were called
        assert mock_use_cases['system'].get_system_status.called
        assert mock_use_cases['system'].create_backup.called
        assert mock_use_cases['system'].check_for_updates.called







