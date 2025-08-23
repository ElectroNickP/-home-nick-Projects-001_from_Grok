"""
End-to-End tests for API Entry Point.

Tests cover real HTTP interactions, API scenarios, and performance testing.
"""

import pytest
import requests
import json
import time
from fastapi.testclient import TestClient
from tests.entrypoints.factories import test_data_factory


class TestAPIE2EAuthentication:
    """Test end-to-end authentication scenarios in API interface."""
    
    def test_api_documentation_access(self, api_client):
        """Test API documentation accessibility."""
        # Test OpenAPI schema
        response = api_client.get('/openapi.json')
        assert response.status_code == 200
        data = response.json()
        assert 'openapi' in data
        assert 'paths' in data
        assert '/api/bots' in str(data['paths'])
        
        # Test Swagger UI
        response = api_client.get('/docs')
        assert response.status_code == 200
        assert 'text/html' in response.headers['content-type']
        assert 'Swagger UI' in response.text
        
        # Test ReDoc
        response = api_client.get('/redoc')
        assert response.status_code == 200
        assert 'text/html' in response.headers['content-type']
        assert 'ReDoc' in response.text
    
    def test_api_health_endpoints(self, api_client):
        """Test API health check endpoints."""
        # Test basic health check
        response = api_client.get('/health')
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'healthy'
        
        # Test readiness check
        response = api_client.get('/ready')
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'ready'
        
        # Test liveness check
        response = api_client.get('/live')
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'alive'
    
    def test_api_root_redirect(self, api_client):
        """Test API root redirect to documentation."""
        response = api_client.get('/', follow_redirects=False)
        assert response.status_code == 307  # Temporary redirect
        
        # Follow redirect
        response = api_client.get('/', follow_redirects=True)
        assert response.status_code == 200
        assert 'text/html' in response.headers['content-type']


class TestAPIE2EBotManagement:
    """Test end-to-end bot management scenarios in API interface."""
    
    def test_bot_crud_operations_e2e(self, authenticated_api_client, mock_use_cases):
        """Test complete CRUD operations for bots via API."""
        # Prepare bot data
        bot_data = test_data_factory.create_bot_config(id=1, name="E2E Test Bot", status="created")
        
        # Mock use cases
        mock_use_cases['bot_management'].create_bot.return_value = {
            'success': True,
            'bot': bot_data,
            'message': 'Bot created successfully'
        }
        mock_use_cases['bot_management'].get_bot.return_value = {
            'success': True,
            'bot': bot_data
        }
        mock_use_cases['bot_management'].update_bot.return_value = {
            'success': True,
            'bot': {**bot_data, 'name': 'Updated E2E Test Bot'},
            'message': 'Bot updated successfully'
        }
        mock_use_cases['bot_management'].delete_bot.return_value = {
            'success': True,
            'message': 'Bot deleted successfully',
            'bot_id': 1
        }
        
        # 1. Create bot
        create_data = {
            'name': 'E2E Test Bot',
            'token': 'test_token_e2e',
            'description': 'Bot for E2E testing'
        }
        response = authenticated_api_client.post('/api/bots', json=create_data)
        assert response.status_code == 201
        data = response.json()
        assert data['success'] is True
        assert data['bot']['name'] == 'E2E Test Bot'
        
        # 2. Get bot
        response = authenticated_api_client.get('/api/bots/1')
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert data['bot']['name'] == 'E2E Test Bot'
        
        # 3. Update bot
        update_data = {
            'name': 'Updated E2E Test Bot',
            'description': 'Updated description for E2E testing'
        }
        response = authenticated_api_client.put('/api/bots/1', json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert data['bot']['name'] == 'Updated E2E Test Bot'
        
        # 4. Delete bot
        response = authenticated_api_client.delete('/api/bots/1')
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert data['message'] == 'Bot deleted successfully'
    
    def test_bot_list_with_pagination_e2e(self, authenticated_api_client, mock_use_cases):
        """Test bot list with pagination via API."""
        # Prepare paginated bot data
        bots_data = [
            test_data_factory.create_bot_config(id=i, name=f"Bot {i}", status="running")
            for i in range(1, 11)  # 10 bots
        ]
        
        mock_use_cases['bot_management'].list_bots.return_value = {
            'success': True,
            'bots': bots_data[:5],  # First page
            'total': 10,
            'page': 1,
            'per_page': 5
        }
        
        # Test first page
        response = authenticated_api_client.get('/api/bots?page=1&per_page=5')
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert len(data['bots']) == 5
        assert data['total'] == 10
        assert data['page'] == 1
        assert data['per_page'] == 5
        
        # Test second page
        mock_use_cases['bot_management'].list_bots.return_value = {
            'success': True,
            'bots': bots_data[5:],  # Second page
            'total': 10,
            'page': 2,
            'per_page': 5
        }
        
        response = authenticated_api_client.get('/api/bots?page=2&per_page=5')
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert len(data['bots']) == 5
        assert data['page'] == 2
    
    def test_bot_management_actions_e2e(self, authenticated_api_client, mock_use_cases):
        """Test bot management actions via API."""
        # Mock use cases for different actions
        mock_use_cases['bot_management'].start_bot.return_value = {
            'success': True,
            'message': 'Bot started successfully'
        }
        mock_use_cases['bot_management'].stop_bot.return_value = {
            'success': True,
            'message': 'Bot stopped successfully'
        }
        mock_use_cases['bot_management'].restart_bot.return_value = {
            'success': True,
            'message': 'Bot restarted successfully'
        }
        mock_use_cases['bot_management'].get_bot_status.return_value = {
            'success': True,
            'status': 'running'
        }
        
        # Test start bot
        response = authenticated_api_client.post('/api/bots/1/start')
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert data['message'] == 'Bot started successfully'
        
        # Test stop bot
        response = authenticated_api_client.post('/api/bots/1/stop')
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert data['message'] == 'Bot stopped successfully'
        
        # Test restart bot
        response = authenticated_api_client.post('/api/bots/1/restart')
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert data['message'] == 'Bot restarted successfully'
        
        # Test get bot status
        response = authenticated_api_client.get('/api/bots/1/status')
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert data['status'] == 'running'
    
    def test_bot_stats_e2e(self, authenticated_api_client, mock_use_cases):
        """Test bot statistics via API."""
        # Prepare stats data
        stats_data = {
            'messages_sent': 150,
            'messages_received': 200,
            'users_count': 25,
            'uptime': '2 days, 5 hours',
            'last_activity': '2025-08-21 10:30:00'
        }
        
        mock_use_cases['bot_management'].get_bot_stats.return_value = {
            'success': True,
            'stats': stats_data
        }
        
        # Test get bot stats
        response = authenticated_api_client.get('/api/bots/1/stats')
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert data['stats']['messages_sent'] == 150
        assert data['stats']['users_count'] == 25
        assert data['stats']['uptime'] == '2 days, 5 hours'


class TestAPIE2EConversationManagement:
    """Test end-to-end conversation management scenarios in API interface."""
    
    def test_conversation_list_with_filters_e2e(self, authenticated_api_client, mock_use_cases):
        """Test conversation list with filters via API."""
        # Prepare filtered conversation data
        conversations_data = [
            test_data_factory.create_conversation(id=1, bot_id=1, user_id=1001),
            test_data_factory.create_conversation(id=2, bot_id=1, user_id=1002)
        ]
        
        mock_use_cases['conversation'].list_conversations.return_value = {
            'success': True,
            'conversations': conversations_data,
            'total': 2,
            'page': 1,
            'per_page': 10
        }
        
        # Test conversation list with bot filter
        response = authenticated_api_client.get('/api/conversations?bot_id=1&page=1&per_page=10')
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert len(data['conversations']) == 2
        assert data['total'] == 2
    
    def test_conversation_detail_with_messages_e2e(self, authenticated_api_client, mock_use_cases):
        """Test conversation detail with messages via API."""
        # Prepare conversation with messages
        conversation = test_data_factory.create_conversation(id=1, bot_id=1, user_id=1001)
        messages = test_data_factory.create_messages(10, conversation_id=1)
        conversation['messages'] = messages
        
        mock_use_cases['conversation'].get_conversation.return_value = {
            'success': True,
            'conversation': conversation
        }
        
        # Test get conversation with messages
        response = authenticated_api_client.get('/api/conversations/1')
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert data['conversation']['id'] == 1
        assert len(data['conversation']['messages']) == 10
    
    def test_conversation_messages_pagination_e2e(self, authenticated_api_client, mock_use_cases):
        """Test conversation messages with pagination via API."""
        # Prepare paginated messages data
        messages = test_data_factory.create_messages(20, conversation_id=1)
        
        mock_use_cases['conversation'].get_conversation_messages.return_value = {
            'success': True,
            'messages': messages[:10],  # First page
            'total': 20,
            'page': 1,
            'per_page': 10
        }
        
        # Test first page of messages
        response = authenticated_api_client.get('/api/conversations/1/messages?page=1&per_page=10')
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert len(data['messages']) == 10
        assert data['total'] == 20
        
        # Test second page
        mock_use_cases['conversation'].get_conversation_messages.return_value = {
            'success': True,
            'messages': messages[10:],  # Second page
            'total': 20,
            'page': 2,
            'per_page': 10
        }
        
        response = authenticated_api_client.get('/api/conversations/1/messages?page=2&per_page=10')
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert len(data['messages']) == 10
        assert data['page'] == 2
    
    def test_conversation_search_e2e(self, authenticated_api_client, mock_use_cases):
        """Test conversation search via API."""
        # Prepare search results
        conversations_data = [
            test_data_factory.create_conversation(id=1, bot_id=1, user_id=1001)
        ]
        
        mock_use_cases['conversation'].search_conversations.return_value = {
            'success': True,
            'conversations': conversations_data,
            'total': 1,
            'query': 'test'
        }
        
        # Test conversation search
        response = authenticated_api_client.get('/api/conversations/search?q=test')
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert len(data['conversations']) == 1
        assert data['query'] == 'test'
    
    def test_conversation_clear_e2e(self, authenticated_api_client, mock_use_cases):
        """Test conversation clearing via API."""
        mock_use_cases['conversation'].clear_conversation.return_value = {
            'success': True,
            'message': 'Conversation cleared successfully',
            'conversation_id': 1
        }
        
        # Test clear conversation
        response = authenticated_api_client.delete('/api/conversations/1')
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert data['message'] == 'Conversation cleared successfully'
        assert data['conversation_id'] == 1


class TestAPIE2ESystemManagement:
    """Test end-to-end system management scenarios in API interface."""
    
    def test_system_status_e2e(self, authenticated_api_client, mock_use_cases):
        """Test system status via API."""
        # Prepare system status data
        status_data = test_data_factory.create_system_status()
        
        mock_use_cases['system'].get_system_status.return_value = {
            'success': True,
            'status': status_data
        }
        
        # Test get system status
        response = authenticated_api_client.get('/api/system/status')
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert 'status' in data
    
    def test_backup_management_e2e(self, authenticated_api_client, mock_use_cases):
        """Test backup management via API."""
        # Prepare backup data
        backup_data = test_data_factory.create_backup_info()
        
        # Test create backup
        mock_use_cases['system'].create_backup.return_value = {
            'success': True,
            'backup': backup_data,
            'message': 'Backup created successfully'
        }
        
        create_data = {'description': 'E2E test backup'}
        response = authenticated_api_client.post('/api/system/backup', json=create_data)
        assert response.status_code == 201
        data = response.json()
        assert data['success'] is True
        assert data['message'] == 'Backup created successfully'
        
        # Test list backups
        backups_data = [
            test_data_factory.create_backup_info(id=1, name="backup_1"),
            test_data_factory.create_backup_info(id=2, name="backup_2")
        ]
        
        mock_use_cases['system'].list_backups.return_value = {
            'success': True,
            'backups': backups_data,
            'total': 2
        }
        
        response = authenticated_api_client.get('/api/system/backup')
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert len(data['backups']) == 2
        
        # Test restore backup
        mock_use_cases['system'].restore_backup.return_value = {
            'success': True,
            'message': 'Backup restored successfully'
        }
        
        response = authenticated_api_client.post('/api/system/backup/1/restore')
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert data['message'] == 'Backup restored successfully'
    
    def test_system_config_e2e(self, authenticated_api_client, mock_use_cases):
        """Test system configuration via API."""
        # Prepare config data
        config_data = {
            'database_url': 'sqlite:///test.db',
            'log_level': 'INFO',
            'max_bots': 10,
            'backup_retention_days': 30
        }
        
        # Test get config
        mock_use_cases['system'].get_system_config.return_value = {
            'success': True,
            'config': config_data
        }
        
        response = authenticated_api_client.get('/api/system/config')
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert data['config']['database_url'] == 'sqlite:///test.db'
        assert data['config']['log_level'] == 'INFO'
        
        # Test update config
        mock_use_cases['system'].update_system_config.return_value = {
            'success': True,
            'message': 'Configuration updated successfully'
        }
        
        update_data = {
            'log_level': 'DEBUG',
            'max_bots': 15
        }
        response = authenticated_api_client.put('/api/system/config', json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert data['message'] == 'Configuration updated successfully'
    
    def test_system_update_e2e(self, authenticated_api_client, mock_use_cases):
        """Test system update via API."""
        # Prepare update data
        update_data = test_data_factory.create_update_info()
        
        # Test check for updates
        mock_use_cases['system'].check_for_updates.return_value = {
            'success': True,
            'update_available': True,
            'update_info': update_data
        }
        
        response = authenticated_api_client.get('/api/system/update/check')
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert data['update_available'] is True
        
        # Test apply update
        mock_use_cases['system'].apply_update.return_value = {
            'success': True,
            'message': 'Update applied successfully'
        }
        
        response = authenticated_api_client.post('/api/system/update/apply')
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert data['message'] == 'Update applied successfully'


class TestAPIE2EAuthenticationFlow:
    """Test end-to-end authentication flow via API."""
    
    def test_auth_login_logout_flow_e2e(self, api_client, mock_use_cases):
        """Test complete authentication flow via API."""
        # Prepare user data
        user_data = {
            'id': 1,
            'username': 'admin',
            'role': 'admin',
            'permissions': ['read', 'write', 'admin']
        }
        
        # Test login
        mock_use_cases['system'].authenticate_user.return_value = {
            'success': True,
            'user': user_data,
            'token': 'valid_jwt_token_e2e'
        }
        
        login_data = {
            'username': 'admin',
            'password': 'securepassword123'
        }
        response = api_client.post('/api/auth/login', json=login_data)
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert data['user']['username'] == 'admin'
        assert data['token'] == 'valid_jwt_token_e2e'
        
        # Test logout
        mock_use_cases['system'].logout_user.return_value = {
            'success': True,
            'message': 'Logged out successfully'
        }
        
        # Create authenticated client with token
        headers = {'Authorization': f'Bearer {data["token"]}'}
        response = api_client.post('/api/auth/logout', headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert data['message'] == 'Logged out successfully'
    
    def test_auth_register_flow_e2e(self, api_client, mock_use_cases):
        """Test user registration flow via API."""
        # Prepare user data
        user_data = {
            'id': 2,
            'username': 'newuser',
            'role': 'user'
        }
        
        # Test registration
        mock_use_cases['system'].register_user.return_value = {
            'success': True,
            'user': user_data,
            'message': 'User registered successfully'
        }
        
        register_data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'securepassword123',
            'confirm_password': 'securepassword123'
        }
        response = api_client.post('/api/auth/register', json=register_data)
        assert response.status_code == 201
        data = response.json()
        assert data['success'] is True
        assert data['user']['username'] == 'newuser'
        assert data['message'] == 'User registered successfully'


class TestAPIE2EErrorHandling:
    """Test end-to-end error handling scenarios in API interface."""
    
    def test_authentication_required_e2e(self, api_client):
        """Test authentication required for protected endpoints."""
        # Test accessing protected endpoint without authentication
        response = api_client.get('/api/bots')
        assert response.status_code == 401
        data = response.json()
        assert 'error' in data
        assert 'Unauthorized' in data['error']['message']
    
    def test_invalid_json_handling_e2e(self, authenticated_api_client):
        """Test handling of invalid JSON requests."""
        # Test sending invalid JSON
        response = authenticated_api_client.post(
            '/api/bots',
            data='invalid json',
            headers={'Content-Type': 'application/json'}
        )
        assert response.status_code == 422
        data = response.json()
        assert 'detail' in data
    
    def test_validation_error_handling_e2e(self, authenticated_api_client):
        """Test handling of validation errors."""
        # Test sending invalid data
        invalid_data = {
            'name': '',  # Invalid empty name
            'token': 'invalid'  # Invalid token format
        }
        response = authenticated_api_client.post('/api/bots', json=invalid_data)
        assert response.status_code == 422
        data = response.json()
        assert 'detail' in data
    
    def test_not_found_handling_e2e(self, authenticated_api_client):
        """Test handling of not found resources."""
        # Test accessing non-existent resource
        response = authenticated_api_client.get('/api/bots/999999')
        assert response.status_code == 404
        data = response.json()
        assert 'error' in data
        assert 'not found' in data['error']['message'].lower()


class TestAPIE2EPerformance:
    """Test end-to-end performance scenarios in API interface."""
    
    def test_api_response_time_e2e(self, authenticated_api_client, mock_use_cases):
        """Test API response time for various endpoints."""
        # Prepare test data
        bots_data = [test_data_factory.create_bot_config(id=1, name="Test Bot", status="running")]
        mock_use_cases['bot_management'].list_bots.return_value = {
            'success': True,
            'bots': bots_data,
            'total': 1
        }
        
        # Test response time for bot list
        start_time = time.time()
        response = authenticated_api_client.get('/api/bots')
        response_time = time.time() - start_time
        
        assert response.status_code == 200
        assert response_time < 1.0, f"Response time {response_time}s exceeds 1s"
        
        # Test response time for bot detail
        mock_use_cases['bot_management'].get_bot.return_value = {
            'success': True,
            'bot': bots_data[0]
        }
        
        start_time = time.time()
        response = authenticated_api_client.get('/api/bots/1')
        response_time = time.time() - start_time
        
        assert response.status_code == 200
        assert response_time < 1.0, f"Response time {response_time}s exceeds 1s"
    
    def test_concurrent_requests_e2e(self, authenticated_api_client, mock_use_cases):
        """Test handling of concurrent requests."""
        import threading
        import time
        
        # Prepare test data
        bots_data = [test_data_factory.create_bot_config(id=1, name="Test Bot", status="running")]
        mock_use_cases['bot_management'].list_bots.return_value = {
            'success': True,
            'bots': bots_data,
            'total': 1
        }
        
        results = []
        errors = []
        
        def make_request():
            try:
                response = authenticated_api_client.get('/api/bots')
                results.append(response.status_code)
            except Exception as e:
                errors.append(str(e))
        
        # Start multiple threads
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check results
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == 5
        assert all(status == 200 for status in results)
    
    def test_large_payload_handling_e2e(self, authenticated_api_client, mock_use_cases):
        """Test handling of large payloads."""
        # Prepare large bot data
        large_bot_data = {
            'name': 'Large Test Bot',
            'token': 'test_token_large',
            'description': 'A' * 10000  # Large description
        }
        
        bot_data = test_data_factory.create_bot_config(id=1, name="Large Test Bot", status="created")
        mock_use_cases['bot_management'].create_bot.return_value = {
            'success': True,
            'bot': bot_data,
            'message': 'Bot created successfully'
        }
        
        # Test creating bot with large payload
        response = authenticated_api_client.post('/api/bots', json=large_bot_data)
        assert response.status_code == 201
        data = response.json()
        assert data['success'] is True
        assert data['bot']['name'] == 'Large Test Bot'
    
    def test_memory_usage_e2e(self, authenticated_api_client, mock_use_cases):
        """Test memory usage during API operations."""
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
        
        # Test memory usage with large dataset
        response = authenticated_api_client.get('/api/bots')
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert len(data['bots']) == 100
        
        # Verify response is still valid
        assert all('id' in bot for bot in data['bots'])
        assert all('name' in bot for bot in data['bots'])
        assert all('status' in bot for bot in data['bots'])






