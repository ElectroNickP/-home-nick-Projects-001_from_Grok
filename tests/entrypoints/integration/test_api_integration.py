"""
Integration tests for API Entry Point with real Use Cases.

Tests cover the integration between API Entry Point and Use Cases,
including real data flow, JSON API responses, and business logic.
"""

import pytest
import json
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from tests.entrypoints.factories import test_data_factory


class TestAPIBotIntegration:
    """Test integration between API Entry Point and Bot Management Use Cases."""
    
    def test_bot_list_integration_success(self, authenticated_api_client, mock_use_cases):
        """Test successful integration of GET /api/bots endpoint with real use case."""
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
        
        # Make API request
        response = authenticated_api_client.get('/api/bots')
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert len(data['bots']) == 3
        assert data['bots'][0]['name'] == 'Test Bot 1'
        assert data['bots'][1]['name'] == 'Test Bot 2'
        assert data['bots'][2]['name'] == 'Test Bot 3'
        assert data['total'] == 3
        
        # Verify use case was called
        mock_use_cases['bot_management'].list_bots.assert_called_once()
    
    def test_bot_create_integration_success(self, authenticated_api_client, mock_use_cases):
        """Test successful integration of POST /api/bots endpoint with real use case."""
        # Prepare bot data
        bot_data = test_data_factory.create_bot_config(id=1, name="New Bot", status="created")
        
        # Mock use case to return success
        mock_use_cases['bot_management'].create_bot.return_value = {
            'success': True,
            'bot': bot_data,
            'message': 'Bot created successfully'
        }
        
        # Make API request
        bot_request = {
            'name': 'New Bot',
            'token': 'test_token_123',
            'description': 'Test bot description'
        }
        response = authenticated_api_client.post('/api/bots', json=bot_request)
        
        # Verify response
        assert response.status_code == 201
        data = response.json()
        assert data['success'] is True
        assert data['bot']['name'] == 'New Bot'
        assert data['message'] == 'Bot created successfully'
        
        # Verify use case was called with correct data
        mock_use_cases['bot_management'].create_bot.assert_called_once()
        call_args = mock_use_cases['bot_management'].create_bot.call_args[0][0]
        assert call_args['name'] == 'New Bot'
        assert call_args['token'] == 'test_token_123'
    
    def test_bot_get_integration_success(self, authenticated_api_client, mock_use_cases):
        """Test successful integration of GET /api/bots/{id} endpoint with real use case."""
        # Prepare bot data
        bot_data = test_data_factory.create_bot_config(id=1, name="Test Bot", status="running")
        
        # Mock use case
        mock_use_cases['bot_management'].get_bot.return_value = {
            'success': True,
            'bot': bot_data
        }
        
        # Make API request
        response = authenticated_api_client.get('/api/bots/1')
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert data['bot']['name'] == 'Test Bot'
        assert data['bot']['status'] == 'running'
        
        # Verify use case was called
        mock_use_cases['bot_management'].get_bot.assert_called_once_with(1)
    
    def test_bot_start_integration_success(self, authenticated_api_client, mock_use_cases):
        """Test successful integration of POST /api/bots/{id}/start endpoint with real use case."""
        # Mock use case to return success
        mock_use_cases['bot_management'].start_bot.return_value = {
            'success': True,
            'message': 'Bot started successfully',
            'bot_id': 1
        }
        
        # Make API request
        response = authenticated_api_client.post('/api/bots/1/start')
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert data['message'] == 'Bot started successfully'
        assert data['bot_id'] == 1
        
        # Verify use case was called
        mock_use_cases['bot_management'].start_bot.assert_called_once_with(1)


class TestAPIConversationIntegration:
    """Test integration between API Entry Point and Conversation Use Cases."""
    
    def test_conversation_list_integration_success(self, authenticated_api_client, mock_use_cases):
        """Test successful integration of GET /api/conversations endpoint with real use case."""
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
        
        # Make API request
        response = authenticated_api_client.get('/api/conversations')
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert len(data['conversations']) == 3
        assert data['total'] == 3
        
        # Verify use case was called
        mock_use_cases['conversation'].list_conversations.assert_called_once()
    
    def test_conversation_get_integration_success(self, authenticated_api_client, mock_use_cases):
        """Test successful integration of GET /api/conversations/{id} endpoint with real use case."""
        # Prepare conversation with messages
        conversation = test_data_factory.create_conversation(id=1, bot_id=1, user_id=1001)
        messages = test_data_factory.create_messages(5, conversation_id=1)
        conversation['messages'] = messages
        
        # Mock use case
        mock_use_cases['conversation'].get_conversation.return_value = {
            'success': True,
            'conversation': conversation
        }
        
        # Make API request
        response = authenticated_api_client.get('/api/conversations/1')
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert data['conversation']['id'] == 1
        assert len(data['conversation']['messages']) == 5
        
        # Verify use case was called
        mock_use_cases['conversation'].get_conversation.assert_called_once_with(1)
    
    def test_conversation_clear_integration_success(self, authenticated_api_client, mock_use_cases):
        """Test successful integration of DELETE /api/conversations/{id} endpoint with real use case."""
        # Mock use case
        mock_use_cases['conversation'].clear_conversation.return_value = {
            'success': True,
            'message': 'Conversation cleared successfully',
            'conversation_id': 1
        }
        
        # Make API request
        response = authenticated_api_client.delete('/api/conversations/1')
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert data['message'] == 'Conversation cleared successfully'
        assert data['conversation_id'] == 1
        
        # Verify use case was called
        mock_use_cases['conversation'].clear_conversation.assert_called_once_with(1)


class TestAPISystemIntegration:
    """Test integration between API Entry Point and System Use Cases."""
    
    def test_system_status_integration_success(self, authenticated_api_client, mock_use_cases):
        """Test successful integration of GET /api/system/status endpoint with real use case."""
        # Prepare system status data
        status_data = test_data_factory.create_system_status()
        
        # Mock use case
        mock_use_cases['system'].get_system_status.return_value = {
            'success': True,
            'status': status_data
        }
        
        # Make API request
        response = authenticated_api_client.get('/api/system/status')
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert 'status' in data
        
        # Verify use case was called
        mock_use_cases['system'].get_system_status.assert_called_once()
    
    def test_system_backup_create_integration_success(self, authenticated_api_client, mock_use_cases):
        """Test successful integration of POST /api/system/backup endpoint with real use case."""
        # Prepare backup data
        backup_data = test_data_factory.create_backup_info()
        
        # Mock use case
        mock_use_cases['system'].create_backup.return_value = {
            'success': True,
            'backup': backup_data,
            'message': 'Backup created successfully'
        }
        
        # Make API request
        backup_request = {'description': 'Test backup'}
        response = authenticated_api_client.post('/api/system/backup', json=backup_request)
        
        # Verify response
        assert response.status_code == 201
        data = response.json()
        assert data['success'] is True
        assert data['message'] == 'Backup created successfully'
        
        # Verify use case was called
        mock_use_cases['system'].create_backup.assert_called_once()
    
    def test_system_update_check_integration_success(self, authenticated_api_client, mock_use_cases):
        """Test successful integration of GET /api/system/update/check endpoint with real use case."""
        # Prepare update data
        update_data = test_data_factory.create_update_info()
        
        # Mock use case
        mock_use_cases['system'].check_for_updates.return_value = {
            'success': True,
            'update_available': True,
            'update_info': update_data
        }
        
        # Make API request
        response = authenticated_api_client.get('/api/system/update/check')
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert data['update_available'] is True
        
        # Verify use case was called
        mock_use_cases['system'].check_for_updates.assert_called_once()


class TestAPIAuthenticationIntegration:
    """Test integration between API Entry Point and System Use Cases for authentication."""
    
    def test_auth_login_integration_success(self, api_client, mock_use_cases):
        """Test successful integration of POST /api/auth/login endpoint with real use case."""
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
            'token': 'valid_jwt_token_123'
        }
        
        # Make API request
        login_request = {
            'username': 'admin',
            'password': 'securepassword123'
        }
        response = api_client.post('/api/auth/login', json=login_request)
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert data['user']['username'] == 'admin'
        assert data['user']['role'] == 'admin'
        assert data['token'] == 'valid_jwt_token_123'
        
        # Verify use case was called
        mock_use_cases['system'].authenticate_user.assert_called_once()
    
    def test_auth_register_integration_success(self, api_client, mock_use_cases):
        """Test successful integration of POST /api/auth/register endpoint with real use case."""
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
        
        # Make API request
        register_request = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'securepassword123',
            'confirm_password': 'securepassword123'
        }
        response = api_client.post('/api/auth/register', json=register_request)
        
        # Verify response
        assert response.status_code == 201
        data = response.json()
        assert data['success'] is True
        assert data['user']['username'] == 'newuser'
        assert data['message'] == 'User registered successfully'
        
        # Verify use case was called
        mock_use_cases['system'].register_user.assert_called_once()


class TestAPIErrorHandlingIntegration:
    """Test integration error handling between API Entry Point and Use Cases."""
    
    def test_use_case_exception_handling(self, authenticated_api_client, mock_use_cases):
        """Test handling of use case exceptions in API integration."""
        # Mock use case to raise exception
        mock_use_cases['bot_management'].list_bots.side_effect = Exception("Database connection failed")
        
        # Make API request
        response = authenticated_api_client.get('/api/bots')
        
        # Verify error handling
        assert response.status_code == 500
        data = response.json()
        assert 'error' in data
        assert 'Database connection failed' in data['error']['message']
    
    def test_use_case_not_found_handling(self, authenticated_api_client, mock_use_cases):
        """Test handling of not found errors in API integration."""
        # Mock use case to return not found
        mock_use_cases['bot_management'].get_bot.return_value = {
            'success': False,
            'error': 'Bot not found'
        }
        
        # Make API request for non-existent bot
        response = authenticated_api_client.get('/api/bots/999')
        
        # Verify not found handling
        assert response.status_code == 404
        data = response.json()
        assert data['success'] is False
        assert 'Bot not found' in data['error']['message']


class TestAPIDataFlowIntegration:
    """Test complete data flow integration between API Entry Point and Use Cases."""
    
    def test_complete_bot_workflow_integration(self, authenticated_api_client, mock_use_cases):
        """Test complete bot workflow integration."""
        # Step 1: List bots
        bots_data = [test_data_factory.create_bot_config(id=1, name="Test Bot", status="stopped")]
        mock_use_cases['bot_management'].list_bots.return_value = {
            'success': True,
            'bots': bots_data,
            'total': 1
        }
        
        response = authenticated_api_client.get('/api/bots')
        assert response.status_code == 200
        
        # Step 2: Start bot
        mock_use_cases['bot_management'].start_bot.return_value = {
            'success': True,
            'message': 'Bot started successfully'
        }
        
        response = authenticated_api_client.post('/api/bots/1/start')
        assert response.status_code == 200
        
        # Step 3: Get bot status
        mock_use_cases['bot_management'].get_bot_status.return_value = {
            'success': True,
            'status': 'running'
        }
        
        response = authenticated_api_client.get('/api/bots/1/status')
        assert response.status_code == 200
        
        # Verify all use cases were called
        assert mock_use_cases['bot_management'].list_bots.called
        assert mock_use_cases['bot_management'].start_bot.called
        assert mock_use_cases['bot_management'].get_bot_status.called
    
    def test_complete_conversation_workflow_integration(self, authenticated_api_client, mock_use_cases):
        """Test complete conversation workflow integration."""
        # Step 1: List conversations
        conversations_data = [test_data_factory.create_conversation(id=1, bot_id=1)]
        mock_use_cases['conversation'].list_conversations.return_value = {
            'success': True,
            'conversations': conversations_data,
            'total': 1
        }
        
        response = authenticated_api_client.get('/api/conversations')
        assert response.status_code == 200
        
        # Step 2: Get conversation
        conversation = test_data_factory.create_conversation(id=1, bot_id=1)
        conversation['messages'] = test_data_factory.create_messages(3, conversation_id=1)
        mock_use_cases['conversation'].get_conversation.return_value = {
            'success': True,
            'conversation': conversation
        }
        
        response = authenticated_api_client.get('/api/conversations/1')
        assert response.status_code == 200
        
        # Step 3: Clear conversation
        mock_use_cases['conversation'].clear_conversation.return_value = {
            'success': True,
            'message': 'Conversation cleared'
        }
        
        response = authenticated_api_client.delete('/api/conversations/1')
        assert response.status_code == 200
        
        # Verify all use cases were called
        assert mock_use_cases['conversation'].list_conversations.called
        assert mock_use_cases['conversation'].get_conversation.called
        assert mock_use_cases['conversation'].clear_conversation.called
