"""
Integration tests for Web Entry Point with real Use Cases.

Tests cover the integration between Web Entry Point and Use Cases,
including real data flow, error handling, and business logic.
"""

import pytest
import json
from unittest.mock import Mock, patch
from flask.testing import FlaskClient
from tests.entrypoints.factories import test_data_factory


class TestWebBotIntegration:
    """Test integration between Web Entry Point and Bot Management Use Cases."""
    
    def test_bot_list_integration_success(self, authenticated_web_client, mock_use_cases):
        """Test successful integration of bot listing with real use case."""
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
            'total': 3,
            'page': 1,
            'per_page': 10
        }
        
        # Make request to web endpoint
        response = authenticated_web_client.get('/bots')
        
        # Verify response
        assert response.status_code == 200
        assert b'Test Bot 1' in response.data
        assert b'Test Bot 2' in response.data
        assert b'Test Bot 3' in response.data
        assert b'running' in response.data
        assert b'stopped' in response.data
        assert b'error' in response.data
        
        # Verify use case was called correctly
        mock_use_cases['bot_management'].list_bots.assert_called_once()
    
    def test_bot_create_integration_success(self, authenticated_web_client, mock_use_cases):
        """Test successful integration of bot creation with real use case."""
        # Prepare bot data
        bot_data = test_data_factory.create_bot_config(id=1, name="New Bot", status="created")
        
        # Mock use case to return success
        mock_use_cases['bot_management'].create_bot.return_value = {
            'success': True,
            'bot': bot_data,
            'message': 'Bot created successfully'
        }
        
        # Make request to create bot
        response = authenticated_web_client.post('/bots', data={
            'name': 'New Bot',
            'token': 'test_token_123',
            'description': 'Test bot description'
        }, follow_redirects=True)
        
        # Verify response
        assert response.status_code == 200
        assert b'Bot created successfully' in response.data or b'New Bot' in response.data
        
        # Verify use case was called with correct data
        mock_use_cases['bot_management'].create_bot.assert_called_once()
        call_args = mock_use_cases['bot_management'].create_bot.call_args[0][0]
        assert call_args['name'] == 'New Bot'
        assert call_args['token'] == 'test_token_123'
    
    def test_bot_create_integration_validation_error(self, authenticated_web_client, mock_use_cases):
        """Test integration of bot creation with validation error."""
        # Mock use case to return validation error
        mock_use_cases['bot_management'].create_bot.return_value = {
            'success': False,
            'error': 'Bot name is required'
        }
        
        # Make request with invalid data
        response = authenticated_web_client.post('/bots', data={
            'name': '',  # Invalid empty name
            'token': 'test_token_123'
        }, follow_redirects=True)
        
        # Verify error handling
        assert response.status_code == 200
        assert b'Bot name is required' in response.data or b'error' in response.data.lower()
        
        # Verify use case was called
        mock_use_cases['bot_management'].create_bot.assert_called_once()
    
    def test_bot_start_integration_success(self, authenticated_web_client, mock_use_cases):
        """Test successful integration of bot start with real use case."""
        # Mock use case to return success
        mock_use_cases['bot_management'].start_bot.return_value = {
            'success': True,
            'message': 'Bot started successfully',
            'bot_id': 1
        }
        
        # Make AJAX request to start bot
        response = authenticated_web_client.post('/bots/1/start', 
                                                headers={'X-Requested-With': 'XMLHttpRequest'})
        
        # Verify JSON response
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['message'] == 'Bot started successfully'
        
        # Verify use case was called with correct bot ID
        mock_use_cases['bot_management'].start_bot.assert_called_once_with(1)
    
    def test_bot_start_integration_error(self, authenticated_web_client, mock_use_cases):
        """Test integration of bot start with error."""
        # Mock use case to return error
        mock_use_cases['bot_management'].start_bot.return_value = {
            'success': False,
            'error': 'Bot is already running'
        }
        
        # Make AJAX request
        response = authenticated_web_client.post('/bots/1/start',
                                                headers={'X-Requested-With': 'XMLHttpRequest'})
        
        # Verify error response
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'Bot is already running' in data['error']['message']
    
    def test_bot_delete_integration_success(self, authenticated_web_client, mock_use_cases):
        """Test successful integration of bot deletion with real use case."""
        # Mock use case to return success
        mock_use_cases['bot_management'].delete_bot.return_value = {
            'success': True,
            'message': 'Bot deleted successfully',
            'bot_id': 1
        }
        
        # Make request to delete bot
        response = authenticated_web_client.post('/bots/1/delete', 
                                                data={'confirm': 'yes'}, 
                                                follow_redirects=True)
        
        # Verify response
        assert response.status_code == 200
        assert b'Bot deleted successfully' in response.data or b'deleted' in response.data.lower()
        
        # Verify use case was called
        mock_use_cases['bot_management'].delete_bot.assert_called_once_with(1)
    
    def test_bot_stats_integration(self, authenticated_web_client, mock_use_cases):
        """Test integration of bot statistics with real use case."""
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
        
        # Make AJAX request
        response = authenticated_web_client.get('/bots/1/stats',
                                               headers={'X-Requested-With': 'XMLHttpRequest'})
        
        # Verify response
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['stats']['messages_sent'] == 150
        assert data['stats']['users_count'] == 25


class TestWebConversationIntegration:
    """Test integration between Web Entry Point and Conversation Use Cases."""
    
    def test_conversation_list_integration_success(self, authenticated_web_client, mock_use_cases):
        """Test successful integration of conversation listing with real use case."""
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
            'total': 3,
            'page': 1,
            'per_page': 10
        }
        
        # Make request
        response = authenticated_web_client.get('/conversations')
        
        # Verify response
        assert response.status_code == 200
        # Verify conversations are displayed
        assert b'conversation' in response.data.lower()
        
        # Verify use case was called
        mock_use_cases['conversation'].list_conversations.assert_called_once()
    
    def test_conversation_show_integration_success(self, authenticated_web_client, mock_use_cases):
        """Test successful integration of conversation display with real use case."""
        # Prepare conversation with messages
        conversation = test_data_factory.create_conversation(id=1, bot_id=1, user_id=1001)
        messages = test_data_factory.create_messages(5, conversation_id=1)
        conversation['messages'] = messages
        
        # Mock use case
        mock_use_cases['conversation'].get_conversation.return_value = {
            'success': True,
            'conversation': conversation
        }
        
        # Make request
        response = authenticated_web_client.get('/conversations/1')
        
        # Verify response
        assert response.status_code == 200
        assert b'conversation' in response.data.lower()
        
        # Verify use case was called
        mock_use_cases['conversation'].get_conversation.assert_called_once_with(1)
    
    def test_conversation_clear_integration_success(self, authenticated_web_client, mock_use_cases):
        """Test successful integration of conversation clearing with real use case."""
        # Mock use case
        mock_use_cases['conversation'].clear_conversation.return_value = {
            'success': True,
            'message': 'Conversation cleared successfully',
            'conversation_id': 1
        }
        
        # Make request
        response = authenticated_web_client.post('/conversations/1/clear',
                                                data={'confirm': 'yes'},
                                                follow_redirects=True)
        
        # Verify response
        assert response.status_code == 200
        assert b'cleared' in response.data.lower() or b'success' in response.data.lower()
        
        # Verify use case was called
        mock_use_cases['conversation'].clear_conversation.assert_called_once_with(1)
    
    def test_conversation_messages_integration(self, authenticated_web_client, mock_use_cases):
        """Test integration of conversation messages with real use case."""
        # Prepare messages data
        messages = test_data_factory.create_messages(10, conversation_id=1)
        
        # Mock use case
        mock_use_cases['conversation'].get_conversation_messages.return_value = {
            'success': True,
            'messages': messages,
            'total': 10,
            'page': 1,
            'per_page': 10
        }
        
        # Make AJAX request
        response = authenticated_web_client.get('/conversations/1/messages',
                                               headers={'X-Requested-With': 'XMLHttpRequest'})
        
        # Verify response
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert len(data['messages']) == 10
        
        # Verify use case was called
        mock_use_cases['conversation'].get_conversation_messages.assert_called_once_with(1)


class TestWebSystemIntegration:
    """Test integration between Web Entry Point and System Use Cases."""
    
    def test_system_status_integration_success(self, authenticated_web_client, mock_use_cases):
        """Test successful integration of system status with real use case."""
        # Prepare system status data
        status_data = test_data_factory.create_system_status()
        
        # Mock use case
        mock_use_cases['system'].get_system_status.return_value = {
            'success': True,
            'status': status_data
        }
        
        # Make request
        response = authenticated_web_client.get('/system/status')
        
        # Verify response
        assert response.status_code == 200
        assert b'system' in response.data.lower()
        assert b'status' in response.data.lower()
        
        # Verify use case was called
        mock_use_cases['system'].get_system_status.assert_called_once()
    
    def test_system_backup_integration_success(self, authenticated_web_client, mock_use_cases):
        """Test successful integration of system backup with real use case."""
        # Prepare backup data
        backup_data = test_data_factory.create_backup_info()
        
        # Mock use case
        mock_use_cases['system'].create_backup.return_value = {
            'success': True,
            'backup': backup_data,
            'message': 'Backup created successfully'
        }
        
        # Make request
        response = authenticated_web_client.post('/system/backup',
                                                data={'description': 'Test backup'},
                                                follow_redirects=True)
        
        # Verify response
        assert response.status_code == 200
        assert b'backup' in response.data.lower() or b'success' in response.data.lower()
        
        # Verify use case was called
        mock_use_cases['system'].create_backup.assert_called_once()
    
    def test_system_backup_list_integration(self, authenticated_web_client, mock_use_cases):
        """Test integration of system backup listing with real use case."""
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
        
        # Make request
        response = authenticated_web_client.get('/system/backups')
        
        # Verify response
        assert response.status_code == 200
        assert b'backup' in response.data.lower()
        
        # Verify use case was called
        mock_use_cases['system'].list_backups.assert_called_once()
    
    def test_system_update_check_integration(self, authenticated_web_client, mock_use_cases):
        """Test integration of system update check with real use case."""
        # Prepare update data
        update_data = test_data_factory.create_update_info()
        
        # Mock use case
        mock_use_cases['system'].check_for_updates.return_value = {
            'success': True,
            'update_available': True,
            'update_info': update_data
        }
        
        # Make AJAX request
        response = authenticated_web_client.get('/system/update/check',
                                               headers={'X-Requested-With': 'XMLHttpRequest'})
        
        # Verify response
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['update_available'] is True
        
        # Verify use case was called
        mock_use_cases['system'].check_for_updates.assert_called_once()


class TestWebAuthenticationIntegration:
    """Test integration between Web Entry Point and System Use Cases for authentication."""
    
    def test_login_integration_success(self, web_client, mock_use_cases):
        """Test successful integration of login with real use case."""
        # Prepare user data
        user_data = {
            'id': 1,
            'username': 'admin',
            'role': 'admin',
            'permissions': ['read', 'write', 'admin']
        }
        
        # Mock use case
        mock_use_cases['system'].authenticate_user.return_value = {
            'success': True,
            'user': user_data,
            'session_id': 'session_123'
        }
        
        # Make login request
        response = web_client.post('/auth/login', data={
            'username': 'admin',
            'password': 'securepassword123'
        }, follow_redirects=True)
        
        # Verify response
        assert response.status_code == 200
        # Should redirect to dashboard or show success message
        assert b'admin' in response.data.lower() or b'dashboard' in response.data.lower()
        
        # Verify use case was called
        mock_use_cases['system'].authenticate_user.assert_called_once()
    
    def test_login_integration_failure(self, web_client, mock_use_cases):
        """Test integration of login failure with real use case."""
        # Mock use case to return failure
        mock_use_cases['system'].authenticate_user.return_value = {
            'success': False,
            'error': 'Invalid username or password'
        }
        
        # Make login request
        response = web_client.post('/auth/login', data={
            'username': 'admin',
            'password': 'wrongpassword'
        }, follow_redirects=True)
        
        # Verify error handling
        assert response.status_code == 200
        assert b'error' in response.data.lower() or b'invalid' in response.data.lower()
        
        # Verify use case was called
        mock_use_cases['system'].authenticate_user.assert_called_once()
    
    def test_logout_integration_success(self, authenticated_web_client, mock_use_cases):
        """Test successful integration of logout with real use case."""
        # Mock use case
        mock_use_cases['system'].logout_user.return_value = {
            'success': True,
            'message': 'Logged out successfully'
        }
        
        # Make logout request
        response = authenticated_web_client.get('/auth/logout', follow_redirects=True)
        
        # Verify response
        assert response.status_code == 200
        # Should redirect to login page or show logout message
        assert b'login' in response.data.lower() or b'logout' in response.data.lower()
        
        # Verify use case was called
        mock_use_cases['system'].logout_user.assert_called_once()
    
    def test_register_integration_success(self, web_client, mock_use_cases):
        """Test successful integration of registration with real use case."""
        # Prepare user data
        user_data = {
            'id': 2,
            'username': 'newuser',
            'role': 'user'
        }
        
        # Mock use case
        mock_use_cases['system'].register_user.return_value = {
            'success': True,
            'user': user_data,
            'message': 'User registered successfully'
        }
        
        # Make registration request
        response = web_client.post('/auth/register', data={
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'securepassword123',
            'confirm_password': 'securepassword123'
        }, follow_redirects=True)
        
        # Verify response
        assert response.status_code == 200
        assert b'registered' in response.data.lower() or b'success' in response.data.lower()
        
        # Verify use case was called
        mock_use_cases['system'].register_user.assert_called_once()


class TestWebErrorHandlingIntegration:
    """Test integration error handling between Web Entry Point and Use Cases."""
    
    def test_use_case_exception_handling(self, authenticated_web_client, mock_use_cases):
        """Test handling of use case exceptions in web integration."""
        # Mock use case to raise exception
        mock_use_cases['bot_management'].list_bots.side_effect = Exception("Database connection failed")
        
        # Make request
        response = authenticated_web_client.get('/bots')
        
        # Verify error handling
        assert response.status_code == 500
        assert b'error' in response.data.lower() or b'failed' in response.data.lower()
    
    def test_use_case_validation_error_handling(self, authenticated_web_client, mock_use_cases):
        """Test handling of validation errors in web integration."""
        # Mock use case to return validation error
        mock_use_cases['bot_management'].create_bot.return_value = {
            'success': False,
            'error': 'Validation failed',
            'details': {
                'name': ['Name is required'],
                'token': ['Token is invalid']
            }
        }
        
        # Make request with invalid data
        response = authenticated_web_client.post('/bots', data={
            'name': '',
            'token': 'invalid'
        }, follow_redirects=True)
        
        # Verify validation error handling
        assert response.status_code == 200
        assert b'validation' in response.data.lower() or b'error' in response.data.lower()
    
    def test_use_case_not_found_handling(self, authenticated_web_client, mock_use_cases):
        """Test handling of not found errors in web integration."""
        # Mock use case to return not found
        mock_use_cases['bot_management'].get_bot.return_value = {
            'success': False,
            'error': 'Bot not found'
        }
        
        # Make request for non-existent bot
        response = authenticated_web_client.get('/bots/999')
        
        # Verify not found handling
        assert response.status_code == 404
        assert b'not found' in response.data.lower() or b'404' in response.data


class TestWebDataFlowIntegration:
    """Test complete data flow integration between Web Entry Point and Use Cases."""
    
    def test_complete_bot_workflow_integration(self, authenticated_web_client, mock_use_cases):
        """Test complete bot workflow integration."""
        # Step 1: List bots
        bots_data = [test_data_factory.create_bot_config(id=1, name="Test Bot", status="stopped")]
        mock_use_cases['bot_management'].list_bots.return_value = {
            'success': True,
            'bots': bots_data,
            'total': 1
        }
        
        response = authenticated_web_client.get('/bots')
        assert response.status_code == 200
        
        # Step 2: Start bot
        mock_use_cases['bot_management'].start_bot.return_value = {
            'success': True,
            'message': 'Bot started successfully'
        }
        
        response = authenticated_web_client.post('/bots/1/start',
                                                headers={'X-Requested-With': 'XMLHttpRequest'})
        assert response.status_code == 200
        
        # Step 3: Get bot status
        mock_use_cases['bot_management'].get_bot_status.return_value = {
            'success': True,
            'status': 'running'
        }
        
        response = authenticated_web_client.get('/bots/1/status',
                                               headers={'X-Requested-With': 'XMLHttpRequest'})
        assert response.status_code == 200
        
        # Verify all use cases were called
        assert mock_use_cases['bot_management'].list_bots.called
        assert mock_use_cases['bot_management'].start_bot.called
        assert mock_use_cases['bot_management'].get_bot_status.called
    
    def test_complete_conversation_workflow_integration(self, authenticated_web_client, mock_use_cases):
        """Test complete conversation workflow integration."""
        # Step 1: List conversations
        conversations_data = [test_data_factory.create_conversation(id=1, bot_id=1)]
        mock_use_cases['conversation'].list_conversations.return_value = {
            'success': True,
            'conversations': conversations_data,
            'total': 1
        }
        
        response = authenticated_web_client.get('/conversations')
        assert response.status_code == 200
        
        # Step 2: Show conversation
        conversation = test_data_factory.create_conversation(id=1, bot_id=1)
        conversation['messages'] = test_data_factory.create_messages(3, conversation_id=1)
        mock_use_cases['conversation'].get_conversation.return_value = {
            'success': True,
            'conversation': conversation
        }
        
        response = authenticated_web_client.get('/conversations/1')
        assert response.status_code == 200
        
        # Step 3: Clear conversation
        mock_use_cases['conversation'].clear_conversation.return_value = {
            'success': True,
            'message': 'Conversation cleared'
        }
        
        response = authenticated_web_client.post('/conversations/1/clear',
                                                data={'confirm': 'yes'},
                                                follow_redirects=True)
        assert response.status_code == 200
        
        # Verify all use cases were called
        assert mock_use_cases['conversation'].list_conversations.called
        assert mock_use_cases['conversation'].get_conversation.called
        assert mock_use_cases['conversation'].clear_conversation.called








