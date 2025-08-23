"""
Unit tests for bot API endpoints (API Entry Point).

Tests cover all bot-related API endpoints including
CRUD operations, management, and status endpoints.
"""

import pytest
import json
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from tests.entrypoints.factories import test_data_factory


class TestBotListAPI:
    """Test bot list API endpoint functionality."""
    
    def test_get_bots_success(self, api_client, mock_use_cases):
        """Test successful GET /api/bots endpoint."""
        bots = [
            test_data_factory.create_bot_config(id=1, name='Test Bot 1'),
            test_data_factory.create_bot_config(id=2, name='Test Bot 2')
        ]
        mock_use_cases['bot_management'].list_bots.return_value = bots
        
        response = api_client.get('/api/bots')
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]['id'] == 1
        assert data[0]['name'] == 'Test Bot 1'
        assert data[1]['id'] == 2
        assert data[1]['name'] == 'Test Bot 2'
        mock_use_cases['bot_management'].list_bots.assert_called_once()
    
    def test_get_bots_empty(self, api_client, mock_use_cases):
        """Test GET /api/bots endpoint with no bots."""
        mock_use_cases['bot_management'].list_bots.return_value = []
        
        response = api_client.get('/api/bots')
        
        assert response.status_code == 200
        data = response.json()
        assert data == []
        mock_use_cases['bot_management'].list_bots.assert_called_once()
    
    def test_get_bots_with_filters(self, api_client, mock_use_cases):
        """Test GET /api/bots endpoint with query parameters."""
        bots = [test_data_factory.create_bot_config(id=1, name='Active Bot', status='active')]
        mock_use_cases['bot_management'].list_bots.return_value = bots
        
        response = api_client.get('/api/bots?status=active&limit=10&offset=0')
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]['status'] == 'active'
        mock_use_cases['bot_management'].list_bots.assert_called_once_with(
            status='active', limit=10, offset=0
        )
    
    def test_get_bots_server_error(self, api_client, mock_use_cases):
        """Test GET /api/bots endpoint with server error."""
        mock_use_cases['bot_management'].list_bots.side_effect = Exception("Server error")
        
        response = api_client.get('/api/bots')
        
        assert response.status_code == 500
        data = response.json()
        assert 'error' in data
        assert 'Server error' in data['error']['message']
    
    def test_get_bots_invalid_filters(self, api_client):
        """Test GET /api/bots endpoint with invalid query parameters."""
        response = api_client.get('/api/bots?limit=invalid&offset=-1')
        
        assert response.status_code == 422  # Validation error
        data = response.json()
        assert 'detail' in data


class TestBotCreateAPI:
    """Test bot create API endpoint functionality."""
    
    def test_create_bot_success(self, api_client, mock_use_cases):
        """Test successful POST /api/bots endpoint."""
        new_bot = test_data_factory.create_bot_config(id=1, name='New Bot')
        mock_use_cases['bot_management'].create_bot.return_value = new_bot
        
        bot_data = {
            'name': 'New Bot',
            'token': '123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11',
            'description': 'Test bot description'
        }
        
        response = api_client.post('/api/bots', json=bot_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data['id'] == 1
        assert data['name'] == 'New Bot'
        assert data['description'] == 'Test bot description'
        mock_use_cases['bot_management'].create_bot.assert_called_once()
    
    def test_create_bot_missing_required_fields(self, api_client):
        """Test POST /api/bots endpoint with missing required fields."""
        bot_data = {'name': 'New Bot'}  # Missing token
        
        response = api_client.post('/api/bots', json=bot_data)
        
        assert response.status_code == 422  # Validation error
        data = response.json()
        assert 'detail' in data
    
    def test_create_bot_invalid_token(self, api_client):
        """Test POST /api/bots endpoint with invalid token."""
        bot_data = {
            'name': 'New Bot',
            'token': 'invalid_token'
        }
        
        response = api_client.post('/api/bots', json=bot_data)
        
        assert response.status_code == 422  # Validation error
        data = response.json()
        assert 'detail' in data
    
    def test_create_bot_validation_error(self, api_client, mock_use_cases):
        """Test POST /api/bots endpoint with validation error."""
        mock_use_cases['bot_management'].create_bot.side_effect = ValueError('Invalid bot name')
        
        bot_data = {
            'name': 'Invalid Bot Name',
            'token': '123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11'
        }
        
        response = api_client.post('/api/bots', json=bot_data)
        
        assert response.status_code == 400
        data = response.json()
        assert 'error' in data
        assert 'Invalid bot name' in data['error']['message']
    
    def test_create_bot_duplicate_name(self, api_client, mock_use_cases):
        """Test POST /api/bots endpoint with duplicate name."""
        mock_use_cases['bot_management'].create_bot.side_effect = ValueError('Bot name already exists')
        
        bot_data = {
            'name': 'Existing Bot',
            'token': '123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11'
        }
        
        response = api_client.post('/api/bots', json=bot_data)
        
        assert response.status_code == 409  # Conflict
        data = response.json()
        assert 'error' in data
        assert 'Bot name already exists' in data['error']['message']


class TestBotGetAPI:
    """Test bot get API endpoint functionality."""
    
    def test_get_bot_success(self, api_client, mock_use_cases):
        """Test successful GET /api/bots/{bot_id} endpoint."""
        bot = test_data_factory.create_bot_config(id=1, name='Test Bot')
        mock_use_cases['bot_management'].get_bot.return_value = bot
        
        response = api_client.get('/api/bots/1')
        
        assert response.status_code == 200
        data = response.json()
        assert data['id'] == 1
        assert data['name'] == 'Test Bot'
        assert 'token' in data
        assert 'status' in data
        mock_use_cases['bot_management'].get_bot.assert_called_once_with(1)
    
    def test_get_bot_not_found(self, api_client, mock_use_cases):
        """Test GET /api/bots/{bot_id} endpoint with non-existent bot."""
        mock_use_cases['bot_management'].get_bot.return_value = None
        
        response = api_client.get('/api/bots/999')
        
        assert response.status_code == 404
        data = response.json()
        assert 'error' in data
        assert 'Bot not found' in data['error']['message']
    
    def test_get_bot_invalid_id(self, api_client):
        """Test GET /api/bots/{bot_id} endpoint with invalid ID."""
        response = api_client.get('/api/bots/invalid')
        
        assert response.status_code == 422  # Validation error
        data = response.json()
        assert 'detail' in data
    
    def test_get_bot_server_error(self, api_client, mock_use_cases):
        """Test GET /api/bots/{bot_id} endpoint with server error."""
        mock_use_cases['bot_management'].get_bot.side_effect = Exception("Server error")
        
        response = api_client.get('/api/bots/1')
        
        assert response.status_code == 500
        data = response.json()
        assert 'error' in data
        assert 'Server error' in data['error']['message']


class TestBotUpdateAPI:
    """Test bot update API endpoint functionality."""
    
    def test_update_bot_success(self, api_client, mock_use_cases):
        """Test successful PUT /api/bots/{bot_id} endpoint."""
        updated_bot = test_data_factory.create_bot_config(id=1, name='Updated Bot')
        mock_use_cases['bot_management'].update_bot.return_value = updated_bot
        
        update_data = {
            'name': 'Updated Bot',
            'description': 'Updated description'
        }
        
        response = api_client.put('/api/bots/1', json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data['id'] == 1
        assert data['name'] == 'Updated Bot'
        assert data['description'] == 'Updated description'
        mock_use_cases['bot_management'].update_bot.assert_called_once()
    
    def test_update_bot_not_found(self, api_client, mock_use_cases):
        """Test PUT /api/bots/{bot_id} endpoint with non-existent bot."""
        mock_use_cases['bot_management'].update_bot.return_value = None
        
        update_data = {'name': 'Updated Bot'}
        
        response = api_client.put('/api/bots/999', json=update_data)
        
        assert response.status_code == 404
        data = response.json()
        assert 'error' in data
        assert 'Bot not found' in data['error']['message']
    
    def test_update_bot_invalid_id(self, api_client):
        """Test PUT /api/bots/{bot_id} endpoint with invalid ID."""
        update_data = {'name': 'Updated Bot'}
        
        response = api_client.put('/api/bots/invalid', json=update_data)
        
        assert response.status_code == 422  # Validation error
        data = response.json()
        assert 'detail' in data
    
    def test_update_bot_validation_error(self, api_client, mock_use_cases):
        """Test PUT /api/bots/{bot_id} endpoint with validation error."""
        mock_use_cases['bot_management'].update_bot.side_effect = ValueError('Invalid name')
        
        update_data = {'name': 'Invalid Name'}
        
        response = api_client.put('/api/bots/1', json=update_data)
        
        assert response.status_code == 400
        data = response.json()
        assert 'error' in data
        assert 'Invalid name' in data['error']['message']
    
    def test_update_bot_empty_data(self, api_client):
        """Test PUT /api/bots/{bot_id} endpoint with empty data."""
        response = api_client.put('/api/bots/1', json={})
        
        assert response.status_code == 422  # Validation error
        data = response.json()
        assert 'detail' in data


class TestBotDeleteAPI:
    """Test bot delete API endpoint functionality."""
    
    def test_delete_bot_success(self, api_client, mock_use_cases):
        """Test successful DELETE /api/bots/{bot_id} endpoint."""
        mock_use_cases['bot_management'].delete_bot.return_value = True
        
        response = api_client.delete('/api/bots/1')
        
        assert response.status_code == 204  # No content
        mock_use_cases['bot_management'].delete_bot.assert_called_once_with(1)
    
    def test_delete_bot_not_found(self, api_client, mock_use_cases):
        """Test DELETE /api/bots/{bot_id} endpoint with non-existent bot."""
        mock_use_cases['bot_management'].delete_bot.return_value = False
        
        response = api_client.delete('/api/bots/999')
        
        assert response.status_code == 404
        data = response.json()
        assert 'error' in data
        assert 'Bot not found' in data['error']['message']
    
    def test_delete_bot_invalid_id(self, api_client):
        """Test DELETE /api/bots/{bot_id} endpoint with invalid ID."""
        response = api_client.delete('/api/bots/invalid')
        
        assert response.status_code == 422  # Validation error
        data = response.json()
        assert 'detail' in data
    
    def test_delete_bot_server_error(self, api_client, mock_use_cases):
        """Test DELETE /api/bots/{bot_id} endpoint with server error."""
        mock_use_cases['bot_management'].delete_bot.side_effect = Exception("Server error")
        
        response = api_client.delete('/api/bots/1')
        
        assert response.status_code == 500
        data = response.json()
        assert 'error' in data
        assert 'Server error' in data['error']['message']


class TestBotStartAPI:
    """Test bot start API endpoint functionality."""
    
    def test_start_bot_success(self, api_client, mock_use_cases):
        """Test successful POST /api/bots/{bot_id}/start endpoint."""
        mock_use_cases['bot_management'].start_bot.return_value = {
            'success': True,
            'message': 'Bot started successfully'
        }
        
        response = api_client.post('/api/bots/1/start')
        
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert data['message'] == 'Bot started successfully'
        mock_use_cases['bot_management'].start_bot.assert_called_once_with(1)
    
    def test_start_bot_not_found(self, api_client, mock_use_cases):
        """Test POST /api/bots/{bot_id}/start endpoint with non-existent bot."""
        mock_use_cases['bot_management'].start_bot.return_value = {
            'success': False,
            'error': 'Bot not found'
        }
        
        response = api_client.post('/api/bots/999/start')
        
        assert response.status_code == 404
        data = response.json()
        assert 'error' in data
        assert 'Bot not found' in data['error']['message']
    
    def test_start_bot_already_running(self, api_client, mock_use_cases):
        """Test POST /api/bots/{bot_id}/start endpoint with already running bot."""
        mock_use_cases['bot_management'].start_bot.return_value = {
            'success': False,
            'error': 'Bot is already running'
        }
        
        response = api_client.post('/api/bots/1/start')
        
        assert response.status_code == 400
        data = response.json()
        assert 'error' in data
        assert 'Bot is already running' in data['error']['message']
    
    def test_start_bot_invalid_id(self, api_client):
        """Test POST /api/bots/{bot_id}/start endpoint with invalid ID."""
        response = api_client.post('/api/bots/invalid/start')
        
        assert response.status_code == 422  # Validation error
        data = response.json()
        assert 'detail' in data


class TestBotStopAPI:
    """Test bot stop API endpoint functionality."""
    
    def test_stop_bot_success(self, api_client, mock_use_cases):
        """Test successful POST /api/bots/{bot_id}/stop endpoint."""
        mock_use_cases['bot_management'].stop_bot.return_value = {
            'success': True,
            'message': 'Bot stopped successfully'
        }
        
        response = api_client.post('/api/bots/1/stop')
        
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert data['message'] == 'Bot stopped successfully'
        mock_use_cases['bot_management'].stop_bot.assert_called_once_with(1)
    
    def test_stop_bot_not_found(self, api_client, mock_use_cases):
        """Test POST /api/bots/{bot_id}/stop endpoint with non-existent bot."""
        mock_use_cases['bot_management'].stop_bot.return_value = {
            'success': False,
            'error': 'Bot not found'
        }
        
        response = api_client.post('/api/bots/999/stop')
        
        assert response.status_code == 404
        data = response.json()
        assert 'error' in data
        assert 'Bot not found' in data['error']['message']
    
    def test_stop_bot_not_running(self, api_client, mock_use_cases):
        """Test POST /api/bots/{bot_id}/stop endpoint with not running bot."""
        mock_use_cases['bot_management'].stop_bot.return_value = {
            'success': False,
            'error': 'Bot is not running'
        }
        
        response = api_client.post('/api/bots/1/stop')
        
        assert response.status_code == 400
        data = response.json()
        assert 'error' in data
        assert 'Bot is not running' in data['error']['message']
    
    def test_stop_bot_invalid_id(self, api_client):
        """Test POST /api/bots/{bot_id}/stop endpoint with invalid ID."""
        response = api_client.post('/api/bots/invalid/stop')
        
        assert response.status_code == 422  # Validation error
        data = response.json()
        assert 'detail' in data


class TestBotRestartAPI:
    """Test bot restart API endpoint functionality."""
    
    def test_restart_bot_success(self, api_client, mock_use_cases):
        """Test successful POST /api/bots/{bot_id}/restart endpoint."""
        mock_use_cases['bot_management'].restart_bot.return_value = {
            'success': True,
            'message': 'Bot restarted successfully'
        }
        
        response = api_client.post('/api/bots/1/restart')
        
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert data['message'] == 'Bot restarted successfully'
        mock_use_cases['bot_management'].restart_bot.assert_called_once_with(1)
    
    def test_restart_bot_not_found(self, api_client, mock_use_cases):
        """Test POST /api/bots/{bot_id}/restart endpoint with non-existent bot."""
        mock_use_cases['bot_management'].restart_bot.return_value = {
            'success': False,
            'error': 'Bot not found'
        }
        
        response = api_client.post('/api/bots/999/restart')
        
        assert response.status_code == 404
        data = response.json()
        assert 'error' in data
        assert 'Bot not found' in data['error']['message']
    
    def test_restart_bot_invalid_id(self, api_client):
        """Test POST /api/bots/{bot_id}/restart endpoint with invalid ID."""
        response = api_client.post('/api/bots/invalid/restart')
        
        assert response.status_code == 422  # Validation error
        data = response.json()
        assert 'detail' in data


class TestBotStatusAPI:
    """Test bot status API endpoint functionality."""
    
    def test_get_bot_status_success(self, api_client, mock_use_cases):
        """Test successful GET /api/bots/{bot_id}/status endpoint."""
        status_data = {
            'bot_id': 1,
            'status': 'running',
            'uptime': '2h 30m',
            'messages_processed': 150,
            'last_activity': '2024-01-15 10:30:00'
        }
        mock_use_cases['bot_management'].get_bot_status.return_value = status_data
        
        response = api_client.get('/api/bots/1/status')
        
        assert response.status_code == 200
        data = response.json()
        assert data['bot_id'] == 1
        assert data['status'] == 'running'
        assert data['uptime'] == '2h 30m'
        assert data['messages_processed'] == 150
        mock_use_cases['bot_management'].get_bot_status.assert_called_once_with(1)
    
    def test_get_bot_status_not_found(self, api_client, mock_use_cases):
        """Test GET /api/bots/{bot_id}/status endpoint with non-existent bot."""
        mock_use_cases['bot_management'].get_bot_status.return_value = None
        
        response = api_client.get('/api/bots/999/status')
        
        assert response.status_code == 404
        data = response.json()
        assert 'error' in data
        assert 'Bot not found' in data['error']['message']
    
    def test_get_bot_status_invalid_id(self, api_client):
        """Test GET /api/bots/{bot_id}/status endpoint with invalid ID."""
        response = api_client.get('/api/bots/invalid/status')
        
        assert response.status_code == 422  # Validation error
        data = response.json()
        assert 'detail' in data


class TestBotStatsAPI:
    """Test bot stats API endpoint functionality."""
    
    def test_get_bot_stats_success(self, api_client, mock_use_cases):
        """Test successful GET /api/bots/{bot_id}/stats endpoint."""
        stats_data = {
            'bot_id': 1,
            'total_messages': 500,
            'messages_today': 25,
            'active_users': 15,
            'response_time_avg': '1.2s',
            'error_rate': '0.5%'
        }
        mock_use_cases['bot_management'].get_bot_stats.return_value = stats_data
        
        response = api_client.get('/api/bots/1/stats')
        
        assert response.status_code == 200
        data = response.json()
        assert data['bot_id'] == 1
        assert data['total_messages'] == 500
        assert data['messages_today'] == 25
        assert data['active_users'] == 15
        assert data['response_time_avg'] == '1.2s'
        assert data['error_rate'] == '0.5%'
        mock_use_cases['bot_management'].get_bot_stats.assert_called_once_with(1)
    
    def test_get_bot_stats_with_period(self, api_client, mock_use_cases):
        """Test GET /api/bots/{bot_id}/stats endpoint with period parameter."""
        stats_data = {'bot_id': 1, 'total_messages': 100}
        mock_use_cases['bot_management'].get_bot_stats.return_value = stats_data
        
        response = api_client.get('/api/bots/1/stats?period=7d')
        
        assert response.status_code == 200
        data = response.json()
        assert data['bot_id'] == 1
        mock_use_cases['bot_management'].get_bot_stats.assert_called_once_with(1, period='7d')
    
    def test_get_bot_stats_not_found(self, api_client, mock_use_cases):
        """Test GET /api/bots/{bot_id}/stats endpoint with non-existent bot."""
        mock_use_cases['bot_management'].get_bot_stats.return_value = None
        
        response = api_client.get('/api/bots/999/stats')
        
        assert response.status_code == 404
        data = response.json()
        assert 'error' in data
        assert 'Bot not found' in data['error']['message']
    
    def test_get_bot_stats_invalid_id(self, api_client):
        """Test GET /api/bots/{bot_id}/stats endpoint with invalid ID."""
        response = api_client.get('/api/bots/invalid/stats')
        
        assert response.status_code == 422  # Validation error
        data = response.json()
        assert 'detail' in data


class TestBotAPIErrorHandling:
    """Test bot API error handling."""
    
    def test_api_server_error(self, api_client, mock_use_cases):
        """Test API endpoint with server error."""
        mock_use_cases['bot_management'].list_bots.side_effect = Exception("Server error")
        
        response = api_client.get('/api/bots')
        
        assert response.status_code == 500
        data = response.json()
        assert 'error' in data
        assert 'Server error' in data['error']['message']
    
    def test_api_network_error(self, api_client, mock_use_cases):
        """Test API endpoint with network error."""
        mock_use_cases['bot_management'].list_bots.side_effect = ConnectionError("Network error")
        
        response = api_client.get('/api/bots')
        
        assert response.status_code == 500
        data = response.json()
        assert 'error' in data
        assert 'Network error' in data['error']['message']
    
    def test_api_timeout_error(self, api_client, mock_use_cases):
        """Test API endpoint with timeout error."""
        mock_use_cases['bot_management'].list_bots.side_effect = TimeoutError("Request timeout")
        
        response = api_client.get('/api/bots')
        
        assert response.status_code == 500
        data = response.json()
        assert 'error' in data
        assert 'Request timeout' in data['error']['message']
    
    def test_api_validation_error(self, api_client):
        """Test API endpoint with validation error."""
        response = api_client.post('/api/bots', json={'invalid': 'data'})
        
        assert response.status_code == 422  # Validation error
        data = response.json()
        assert 'detail' in data


class TestBotAPIPerformance:
    """Test bot API performance."""
    
    def test_api_response_time(self, api_client, mock_use_cases):
        """Test API response time."""
        bots = [test_data_factory.create_bot_config(id=1, name='Test Bot')]
        mock_use_cases['bot_management'].list_bots.return_value = bots
        
        import time
        start_time = time.time()
        response = api_client.get('/api/bots')
        end_time = time.time()
        
        assert response.status_code == 200
        assert (end_time - start_time) < 1.0  # Response time should be under 1 second
    
    def test_api_concurrent_requests(self, api_client, mock_use_cases):
        """Test API with concurrent requests."""
        bots = [test_data_factory.create_bot_config(id=1, name='Test Bot')]
        mock_use_cases['bot_management'].list_bots.return_value = bots
        
        import threading
        import time
        
        results = []
        errors = []
        
        def make_request():
            try:
                response = api_client.get('/api/bots')
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


class TestBotAPIDocumentation:
    """Test bot API documentation."""
    
    def test_api_docs_accessible(self, api_client):
        """Test that API documentation is accessible."""
        response = api_client.get('/docs')
        
        assert response.status_code == 200
        assert 'text/html' in response.headers['content-type']
        assert 'Swagger UI' in response.text
    
    def test_api_openapi_schema(self, api_client):
        """Test that OpenAPI schema is accessible."""
        response = api_client.get('/openapi.json')
        
        assert response.status_code == 200
        data = response.json()
        assert 'openapi' in data
        assert 'paths' in data
        assert '/api/bots' in data['paths']
    
    def test_api_redoc_accessible(self, api_client):
        """Test that ReDoc documentation is accessible."""
        response = api_client.get('/redoc')
        
        assert response.status_code == 200
        assert 'text/html' in response.headers['content-type']
        assert 'ReDoc' in response.text






