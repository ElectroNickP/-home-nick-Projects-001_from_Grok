"""
Unit tests for conversation commands (CLI Entry Point).

Tests cover all conversation-related CLI commands including
list, show, clear, messages.
"""

import pytest
import json
from unittest.mock import Mock, patch
from click.testing import CliRunner
from tests.entrypoints.factories import test_data_factory


class TestConversationListCommand:
    """Test conversation list command functionality."""
    
    def test_conversation_list_empty(self, cli_runner, mock_use_cases):
        """Test conversation list command with no conversations."""
        mock_use_cases['conversation'].list_conversations.return_value = []
        
        result = cli_runner.invoke(cli_runner.app, ['conversation', 'list'])
        
        assert result.exit_code == 0
        assert 'No conversations found' in result.output
        mock_use_cases['conversation'].list_conversations.assert_called_once()
    
    def test_conversation_list_populated(self, cli_runner, mock_use_cases):
        """Test conversation list command with conversations."""
        conversations = [
            test_data_factory.create_conversation(id=1, bot_id=1, user_id=100),
            test_data_factory.create_conversation(id=2, bot_id=1, user_id=101)
        ]
        mock_use_cases['conversation'].list_conversations.return_value = conversations
        
        result = cli_runner.invoke(cli_runner.app, ['conversation', 'list'])
        
        assert result.exit_code == 0
        assert 'ID' in result.output
        assert 'Bot ID' in result.output
        assert 'User ID' in result.output
        assert 'Status' in result.output
        assert 'Created' in result.output
    
    def test_conversation_list_json_format(self, cli_runner, mock_use_cases):
        """Test conversation list command with JSON output."""
        conversations = [test_data_factory.create_conversation(id=1, bot_id=1, user_id=100)]
        mock_use_cases['conversation'].list_conversations.return_value = conversations
        
        result = cli_runner.invoke(cli_runner.app, ['conversation', 'list', '--format', 'json'])
        
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]['id'] == 1
        assert data[0]['bot_id'] == 1
        assert data[0]['user_id'] == 100
    
    def test_conversation_list_csv_format(self, cli_runner, mock_use_cases):
        """Test conversation list command with CSV output."""
        conversations = [test_data_factory.create_conversation(id=1, bot_id=1, user_id=100)]
        mock_use_cases['conversation'].list_conversations.return_value = conversations
        
        result = cli_runner.invoke(cli_runner.app, ['conversation', 'list', '--format', 'csv'])
        
        assert result.exit_code == 0
        assert 'id,bot_id,user_id,status' in result.output.lower()
        assert '1,1,100' in result.output
    
    def test_conversation_list_with_filters(self, cli_runner, mock_use_cases):
        """Test conversation list command with filters."""
        conversations = [test_data_factory.create_conversation(id=1, bot_id=1, user_id=100, status='active')]
        mock_use_cases['conversation'].list_conversations.return_value = conversations
        
        result = cli_runner.invoke(cli_runner.app, ['conversation', 'list', '--bot-id', '1', '--status', 'active'])
        
        assert result.exit_code == 0
        mock_use_cases['conversation'].list_conversations.assert_called_once_with(bot_id=1, status='active')
    
    def test_conversation_list_with_limit(self, cli_runner, mock_use_cases):
        """Test conversation list command with limit."""
        conversations = [test_data_factory.create_conversation(id=1, bot_id=1, user_id=100)]
        mock_use_cases['conversation'].list_conversations.return_value = conversations
        
        result = cli_runner.invoke(cli_runner.app, ['conversation', 'list', '--limit', '10'])
        
        assert result.exit_code == 0
        mock_use_cases['conversation'].list_conversations.assert_called_once_with(limit=10)
    
    def test_conversation_list_with_offset(self, cli_runner, mock_use_cases):
        """Test conversation list command with offset."""
        conversations = [test_data_factory.create_conversation(id=1, bot_id=1, user_id=100)]
        mock_use_cases['conversation'].list_conversations.return_value = conversations
        
        result = cli_runner.invoke(cli_runner.app, ['conversation', 'list', '--offset', '20'])
        
        assert result.exit_code == 0
        mock_use_cases['conversation'].list_conversations.assert_called_once_with(offset=20)


class TestConversationShowCommand:
    """Test conversation show command functionality."""
    
    def test_conversation_show_success(self, cli_runner, mock_use_cases):
        """Test conversation show command with valid conversation ID."""
        conversation = test_data_factory.create_conversation(id=1, bot_id=1, user_id=100)
        mock_use_cases['conversation'].get_conversation.return_value = conversation
        
        result = cli_runner.invoke(cli_runner.app, ['conversation', 'show', '1'])
        
        assert result.exit_code == 0
        assert 'ID: 1' in result.output
        assert 'Bot ID: 1' in result.output
        assert 'User ID: 100' in result.output
        assert 'Status:' in result.output
        assert 'Created:' in result.output
        mock_use_cases['conversation'].get_conversation.assert_called_once_with(1)
    
    def test_conversation_show_not_found(self, cli_runner, mock_use_cases):
        """Test conversation show command with non-existent conversation."""
        mock_use_cases['conversation'].get_conversation.return_value = None
        
        result = cli_runner.invoke(cli_runner.app, ['conversation', 'show', '999'])
        
        assert result.exit_code == 1
        assert 'Conversation not found' in result.output
        assert 'Error:' in result.output
    
    def test_conversation_show_invalid_id(self, cli_runner):
        """Test conversation show command with invalid ID."""
        result = cli_runner.invoke(cli_runner.app, ['conversation', 'show', 'invalid'])
        
        assert result.exit_code == 2  # Click parameter error
        assert 'Invalid value' in result.output
    
    def test_conversation_show_json_format(self, cli_runner, mock_use_cases):
        """Test conversation show command with JSON output."""
        conversation = test_data_factory.create_conversation(id=1, bot_id=1, user_id=100)
        mock_use_cases['conversation'].get_conversation.return_value = conversation
        
        result = cli_runner.invoke(cli_runner.app, ['conversation', 'show', '1', '--format', 'json'])
        
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data['id'] == 1
        assert data['bot_id'] == 1
        assert data['user_id'] == 100
    
    def test_conversation_show_with_messages(self, cli_runner, mock_use_cases):
        """Test conversation show command with messages included."""
        conversation = test_data_factory.create_conversation(id=1, bot_id=1, user_id=100)
        conversation['messages'] = [
            test_data_factory.create_message(id=1, conversation_id=1, content='Hello'),
            test_data_factory.create_message(id=2, conversation_id=1, content='Hi there')
        ]
        mock_use_cases['conversation'].get_conversation.return_value = conversation
        
        result = cli_runner.invoke(cli_runner.app, ['conversation', 'show', '1', '--include-messages'])
        
        assert result.exit_code == 0
        assert 'Messages:' in result.output
        assert 'Hello' in result.output
        assert 'Hi there' in result.output
        mock_use_cases['conversation'].get_conversation.assert_called_once_with(1, include_messages=True)


class TestConversationClearCommand:
    """Test conversation clear command functionality."""
    
    def test_conversation_clear_success(self, cli_runner, mock_use_cases):
        """Test conversation clear command with confirmation."""
        mock_use_cases['conversation'].clear_conversation.return_value = True
        
        result = cli_runner.invoke(cli_runner.app, ['conversation', 'clear', '1'], input='y\n')
        
        assert result.exit_code == 0
        assert 'Conversation cleared successfully' in result.output
        mock_use_cases['conversation'].clear_conversation.assert_called_once_with(1)
    
    def test_conversation_clear_without_confirmation(self, cli_runner, mock_use_cases):
        """Test conversation clear command without confirmation."""
        result = cli_runner.invoke(cli_runner.app, ['conversation', 'clear', '1'], input='n\n')
        
        assert result.exit_code == 0
        assert 'Operation cancelled' in result.output
        mock_use_cases['conversation'].clear_conversation.assert_not_called()
    
    def test_conversation_clear_force_flag(self, cli_runner, mock_use_cases):
        """Test conversation clear command with force flag."""
        mock_use_cases['conversation'].clear_conversation.return_value = True
        
        result = cli_runner.invoke(cli_runner.app, ['conversation', 'clear', '1', '--force'])
        
        assert result.exit_code == 0
        assert 'Conversation cleared successfully' in result.output
        mock_use_cases['conversation'].clear_conversation.assert_called_once_with(1)
    
    def test_conversation_clear_not_found(self, cli_runner, mock_use_cases):
        """Test conversation clear command with non-existent conversation."""
        mock_use_cases['conversation'].clear_conversation.return_value = False
        
        result = cli_runner.invoke(cli_runner.app, ['conversation', 'clear', '999', '--force'])
        
        assert result.exit_code == 1
        assert 'Conversation not found' in result.output
        assert 'Error:' in result.output
    
    def test_conversation_clear_invalid_id(self, cli_runner):
        """Test conversation clear command with invalid ID."""
        result = cli_runner.invoke(cli_runner.app, ['conversation', 'clear', 'invalid'])
        
        assert result.exit_code == 2  # Click parameter error
        assert 'Invalid value' in result.output
    
    def test_conversation_clear_all(self, cli_runner, mock_use_cases):
        """Test conversation clear all command."""
        mock_use_cases['conversation'].clear_all_conversations.return_value = 5
        
        result = cli_runner.invoke(cli_runner.app, ['conversation', 'clear', '--all'], input='y\n')
        
        assert result.exit_code == 0
        assert '5 conversations cleared' in result.output
        mock_use_cases['conversation'].clear_all_conversations.assert_called_once()
    
    def test_conversation_clear_all_with_bot_filter(self, cli_runner, mock_use_cases):
        """Test conversation clear all command with bot filter."""
        mock_use_cases['conversation'].clear_all_conversations.return_value = 3
        
        result = cli_runner.invoke(cli_runner.app, [
            'conversation', 'clear', '--all', '--bot-id', '1'
        ], input='y\n')
        
        assert result.exit_code == 0
        assert '3 conversations cleared' in result.output
        mock_use_cases['conversation'].clear_all_conversations.assert_called_once_with(bot_id=1)


class TestConversationMessagesCommand:
    """Test conversation messages command functionality."""
    
    def test_conversation_messages_success(self, cli_runner, mock_use_cases):
        """Test conversation messages command with valid conversation ID."""
        messages = [
            test_data_factory.create_message(id=1, conversation_id=1, content='Hello', sender='user'),
            test_data_factory.create_message(id=2, conversation_id=1, content='Hi there', sender='bot')
        ]
        mock_use_cases['conversation'].get_conversation_messages.return_value = messages
        
        result = cli_runner.invoke(cli_runner.app, ['conversation', 'messages', '1'])
        
        assert result.exit_code == 0
        assert 'Hello' in result.output
        assert 'Hi there' in result.output
        assert 'user' in result.output
        assert 'bot' in result.output
        mock_use_cases['conversation'].get_conversation_messages.assert_called_once_with(1)
    
    def test_conversation_messages_empty(self, cli_runner, mock_use_cases):
        """Test conversation messages command with no messages."""
        mock_use_cases['conversation'].get_conversation_messages.return_value = []
        
        result = cli_runner.invoke(cli_runner.app, ['conversation', 'messages', '1'])
        
        assert result.exit_code == 0
        assert 'No messages found' in result.output
        mock_use_cases['conversation'].get_conversation_messages.assert_called_once_with(1)
    
    def test_conversation_messages_not_found(self, cli_runner, mock_use_cases):
        """Test conversation messages command with non-existent conversation."""
        mock_use_cases['conversation'].get_conversation_messages.return_value = None
        
        result = cli_runner.invoke(cli_runner.app, ['conversation', 'messages', '999'])
        
        assert result.exit_code == 1
        assert 'Conversation not found' in result.output
        assert 'Error:' in result.output
    
    def test_conversation_messages_invalid_id(self, cli_runner):
        """Test conversation messages command with invalid ID."""
        result = cli_runner.invoke(cli_runner.app, ['conversation', 'messages', 'invalid'])
        
        assert result.exit_code == 2  # Click parameter error
        assert 'Invalid value' in result.output
    
    def test_conversation_messages_json_format(self, cli_runner, mock_use_cases):
        """Test conversation messages command with JSON output."""
        messages = [test_data_factory.create_message(id=1, conversation_id=1, content='Hello', sender='user')]
        mock_use_cases['conversation'].get_conversation_messages.return_value = messages
        
        result = cli_runner.invoke(cli_runner.app, ['conversation', 'messages', '1', '--format', 'json'])
        
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]['id'] == 1
        assert data[0]['content'] == 'Hello'
        assert data[0]['sender'] == 'user'
    
    def test_conversation_messages_csv_format(self, cli_runner, mock_use_cases):
        """Test conversation messages command with CSV output."""
        messages = [test_data_factory.create_message(id=1, conversation_id=1, content='Hello', sender='user')]
        mock_use_cases['conversation'].get_conversation_messages.return_value = messages
        
        result = cli_runner.invoke(cli_runner.app, ['conversation', 'messages', '1', '--format', 'csv'])
        
        assert result.exit_code == 0
        assert 'id,conversation_id,content,sender' in result.output.lower()
        assert '1,1,hello,user' in result.output.lower()
    
    def test_conversation_messages_with_limit(self, cli_runner, mock_use_cases):
        """Test conversation messages command with limit."""
        messages = [test_data_factory.create_message(id=1, conversation_id=1, content='Hello')]
        mock_use_cases['conversation'].get_conversation_messages.return_value = messages
        
        result = cli_runner.invoke(cli_runner.app, ['conversation', 'messages', '1', '--limit', '10'])
        
        assert result.exit_code == 0
        mock_use_cases['conversation'].get_conversation_messages.assert_called_once_with(1, limit=10)
    
    def test_conversation_messages_with_offset(self, cli_runner, mock_use_cases):
        """Test conversation messages command with offset."""
        messages = [test_data_factory.create_message(id=1, conversation_id=1, content='Hello')]
        mock_use_cases['conversation'].get_conversation_messages.return_value = messages
        
        result = cli_runner.invoke(cli_runner.app, ['conversation', 'messages', '1', '--offset', '20'])
        
        assert result.exit_code == 0
        mock_use_cases['conversation'].get_conversation_messages.assert_called_once_with(1, offset=20)
    
    def test_conversation_messages_with_sender_filter(self, cli_runner, mock_use_cases):
        """Test conversation messages command with sender filter."""
        messages = [test_data_factory.create_message(id=1, conversation_id=1, content='Hello', sender='user')]
        mock_use_cases['conversation'].get_conversation_messages.return_value = messages
        
        result = cli_runner.invoke(cli_runner.app, ['conversation', 'messages', '1', '--sender', 'user'])
        
        assert result.exit_code == 0
        mock_use_cases['conversation'].get_conversation_messages.assert_called_once_with(1, sender='user')


class TestConversationContextCommand:
    """Test conversation context command functionality."""
    
    def test_conversation_context_success(self, cli_runner, mock_use_cases):
        """Test conversation context command with valid conversation ID."""
        context = {
            'conversation_id': 1,
            'context_data': {
                'user_preferences': {'language': 'en', 'timezone': 'UTC'},
                'session_data': {'current_state': 'menu', 'last_action': 'help'},
                'variables': {'name': 'John', 'age': 25}
            }
        }
        mock_use_cases['conversation'].get_conversation_context.return_value = context
        
        result = cli_runner.invoke(cli_runner.app, ['conversation', 'context', '1'])
        
        assert result.exit_code == 0
        assert 'Context Data:' in result.output
        assert 'user_preferences' in result.output
        assert 'session_data' in result.output
        assert 'variables' in result.output
        mock_use_cases['conversation'].get_conversation_context.assert_called_once_with(1)
    
    def test_conversation_context_not_found(self, cli_runner, mock_use_cases):
        """Test conversation context command with non-existent conversation."""
        mock_use_cases['conversation'].get_conversation_context.return_value = None
        
        result = cli_runner.invoke(cli_runner.app, ['conversation', 'context', '999'])
        
        assert result.exit_code == 1
        assert 'Conversation not found' in result.output
        assert 'Error:' in result.output
    
    def test_conversation_context_empty(self, cli_runner, mock_use_cases):
        """Test conversation context command with empty context."""
        context = {'conversation_id': 1, 'context_data': {}}
        mock_use_cases['conversation'].get_conversation_context.return_value = context
        
        result = cli_runner.invoke(cli_runner.app, ['conversation', 'context', '1'])
        
        assert result.exit_code == 0
        assert 'No context data' in result.output
    
    def test_conversation_context_json_format(self, cli_runner, mock_use_cases):
        """Test conversation context command with JSON output."""
        context = {
            'conversation_id': 1,
            'context_data': {'user_preferences': {'language': 'en'}}
        }
        mock_use_cases['conversation'].get_conversation_context.return_value = context
        
        result = cli_runner.invoke(cli_runner.app, ['conversation', 'context', '1', '--format', 'json'])
        
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data['conversation_id'] == 1
        assert data['context_data']['user_preferences']['language'] == 'en'
    
    def test_conversation_context_invalid_id(self, cli_runner):
        """Test conversation context command with invalid ID."""
        result = cli_runner.invoke(cli_runner.app, ['conversation', 'context', 'invalid'])
        
        assert result.exit_code == 2  # Click parameter error
        assert 'Invalid value' in result.output


class TestConversationStatsCommand:
    """Test conversation stats command functionality."""
    
    def test_conversation_stats_success(self, cli_runner, mock_use_cases):
        """Test conversation stats command with valid conversation ID."""
        stats = {
            'conversation_id': 1,
            'total_messages': 50,
            'user_messages': 25,
            'bot_messages': 25,
            'avg_response_time': '1.5s',
            'last_activity': '2024-01-15 10:30:00',
            'duration': '2h 15m'
        }
        mock_use_cases['conversation'].get_conversation_stats.return_value = stats
        
        result = cli_runner.invoke(cli_runner.app, ['conversation', 'stats', '1'])
        
        assert result.exit_code == 0
        assert '50' in result.output
        assert '25' in result.output
        assert '1.5s' in result.output
        assert '2h 15m' in result.output
        mock_use_cases['conversation'].get_conversation_stats.assert_called_once_with(1)
    
    def test_conversation_stats_not_found(self, cli_runner, mock_use_cases):
        """Test conversation stats command with non-existent conversation."""
        mock_use_cases['conversation'].get_conversation_stats.return_value = None
        
        result = cli_runner.invoke(cli_runner.app, ['conversation', 'stats', '999'])
        
        assert result.exit_code == 1
        assert 'Conversation not found' in result.output
        assert 'Error:' in result.output
    
    def test_conversation_stats_json_format(self, cli_runner, mock_use_cases):
        """Test conversation stats command with JSON output."""
        stats = {
            'conversation_id': 1,
            'total_messages': 50,
            'user_messages': 25,
            'bot_messages': 25
        }
        mock_use_cases['conversation'].get_conversation_stats.return_value = stats
        
        result = cli_runner.invoke(cli_runner.app, ['conversation', 'stats', '1', '--format', 'json'])
        
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data['conversation_id'] == 1
        assert data['total_messages'] == 50
        assert data['user_messages'] == 25
        assert data['bot_messages'] == 25
    
    def test_conversation_stats_invalid_id(self, cli_runner):
        """Test conversation stats command with invalid ID."""
        result = cli_runner.invoke(cli_runner.app, ['conversation', 'stats', 'invalid'])
        
        assert result.exit_code == 2  # Click parameter error
        assert 'Invalid value' in result.output


class TestConversationCommandErrorHandling:
    """Test conversation command error handling."""
    
    def test_conversation_command_server_error(self, cli_runner, mock_use_cases):
        """Test conversation command with server error."""
        mock_use_cases['conversation'].list_conversations.side_effect = Exception("Server error")
        
        result = cli_runner.invoke(cli_runner.app, ['conversation', 'list'])
        
        assert result.exit_code == 1
        assert 'Error:' in result.output
        assert 'Server error' in result.output
    
    def test_conversation_command_network_error(self, cli_runner, mock_use_cases):
        """Test conversation command with network error."""
        mock_use_cases['conversation'].list_conversations.side_effect = ConnectionError("Network error")
        
        result = cli_runner.invoke(cli_runner.app, ['conversation', 'list'])
        
        assert result.exit_code == 1
        assert 'Error:' in result.output
        assert 'Network error' in result.output
    
    def test_conversation_command_timeout_error(self, cli_runner, mock_use_cases):
        """Test conversation command with timeout error."""
        mock_use_cases['conversation'].list_conversations.side_effect = TimeoutError("Request timeout")
        
        result = cli_runner.invoke(cli_runner.app, ['conversation', 'list'])
        
        assert result.exit_code == 1
        assert 'Error:' in result.output
        assert 'Request timeout' in result.output


class TestConversationCommandHelp:
    """Test conversation command help functionality."""
    
    def test_conversation_command_help(self, cli_runner):
        """Test conversation command help."""
        result = cli_runner.invoke(cli_runner.app, ['conversation', '--help'])
        
        assert result.exit_code == 0
        assert 'Usage:' in result.output
        assert 'Commands:' in result.output
        assert 'list' in result.output
        assert 'show' in result.output
        assert 'clear' in result.output
        assert 'messages' in result.output
        assert 'context' in result.output
        assert 'stats' in result.output
    
    def test_conversation_list_help(self, cli_runner):
        """Test conversation list command help."""
        result = cli_runner.invoke(cli_runner.app, ['conversation', 'list', '--help'])
        
        assert result.exit_code == 0
        assert 'Usage:' in result.output
        assert 'Options:' in result.output
        assert '--format' in result.output
        assert '--bot-id' in result.output
        assert '--status' in result.output
        assert '--limit' in result.output
        assert '--offset' in result.output
    
    def test_conversation_show_help(self, cli_runner):
        """Test conversation show command help."""
        result = cli_runner.invoke(cli_runner.app, ['conversation', 'show', '--help'])
        
        assert result.exit_code == 0
        assert 'Usage:' in result.output
        assert 'Options:' in result.output
        assert '--format' in result.output
        assert '--include-messages' in result.output
    
    def test_conversation_clear_help(self, cli_runner):
        """Test conversation clear command help."""
        result = cli_runner.invoke(cli_runner.app, ['conversation', 'clear', '--help'])
        
        assert result.exit_code == 0
        assert 'Usage:' in result.output
        assert 'Options:' in result.output
        assert '--force' in result.output
        assert '--all' in result.output
        assert '--bot-id' in result.output
    
    def test_conversation_messages_help(self, cli_runner):
        """Test conversation messages command help."""
        result = cli_runner.invoke(cli_runner.app, ['conversation', 'messages', '--help'])
        
        assert result.exit_code == 0
        assert 'Usage:' in result.output
        assert 'Options:' in result.output
        assert '--format' in result.output
        assert '--limit' in result.output
        assert '--offset' in result.output
        assert '--sender' in result.output








