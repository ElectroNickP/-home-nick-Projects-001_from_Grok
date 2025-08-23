"""
Unit tests for bot routes (Web Entry Point).

Tests cover all bot-related routes including CRUD operations,
bot management, and AJAX endpoints.
"""

import pytest
import json
from unittest.mock import Mock, patch
from tests.entrypoints.factories import test_data_factory


class TestBotRoutesAuthentication:
    """Test authentication for bot routes."""
    
    def test_bot_list_requires_authentication(self, web_client):
        """Test that bot list route requires authentication."""
        response = web_client.get('/bots')
        
        assert response.status_code == 302  # Redirect to login
        assert '/login' in response.location
    
    def test_bot_create_requires_authentication(self, web_client):
        """Test that bot create route requires authentication."""
        response = web_client.post('/bots')
        
        assert response.status_code == 302  # Redirect to login
        assert '/login' in response.location
    
    def test_bot_edit_requires_authentication(self, web_client):
        """Test that bot edit route requires authentication."""
        response = web_client.get('/bots/1/edit')
        
        assert response.status_code == 302  # Redirect to login
        assert '/login' in response.location


class TestBotListRoute:
    """Test bot list route functionality."""
    
    def test_bot_list_returns_200(self, authenticated_web_client, mock_use_cases):
        """Test that bot list route returns 200 status."""
        # Mock the use case response
        mock_use_cases['bot_management'].get_all_bots.return_value = [
            test_data_factory.create_bot_config(id=1, name="Test Bot 1"),
            test_data_factory.create_bot_config(id=2, name="Test Bot 2")
        ]
        
        response = authenticated_web_client.get('/bots')
        
        assert response.status_code == 200
        assert b'Test Bot 1' in response.data
        assert b'Test Bot 2' in response.data
    
    def test_bot_list_empty(self, authenticated_web_client, mock_use_cases):
        """Test bot list with no bots."""
        mock_use_cases['bot_management'].get_all_bots.return_value = []
        
        response = authenticated_web_client.get('/bots')
        
        assert response.status_code == 200
        assert b'No bots found' in response.data or b'empty' in response.data.lower()
    
    def test_bot_list_use_case_called(self, authenticated_web_client, mock_use_cases):
        """Test that use case is called for bot list."""
        mock_use_cases['bot_management'].get_all_bots.return_value = []
        
        authenticated_web_client.get('/bots')
        
        mock_use_cases['bot_management'].get_all_bots.assert_called_once()


class TestBotCreateRoute:
    """Test bot create route functionality."""
    
    def test_bot_create_form_returns_200(self, authenticated_web_client):
        """Test that bot create form returns 200 status."""
        response = authenticated_web_client.get('/bots/create')
        
        assert response.status_code == 200
        assert b'Create Bot' in response.data or b'New Bot' in response.data
    
    def test_bot_create_success(self, authenticated_web_client, mock_use_cases):
        """Test successful bot creation."""
        bot_data = test_data_factory.create_bot_config(id=1, name="New Bot")
        mock_use_cases['bot_management'].create_bot.return_value = bot_data
        
        response = authenticated_web_client.post('/bots/create', data={
            'name': 'New Bot',
            'telegram_token': 'test_token',
            'openai_api_key': 'test_key',
            'assistant_id': 'test_assistant'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        mock_use_cases['bot_management'].create_bot.assert_called_once()
    
    def test_bot_create_validation_error(self, authenticated_web_client, mock_use_cases):
        """Test bot creation with validation error."""
        mock_use_cases['bot_management'].create_bot.side_effect = ValueError("Invalid token")
        
        response = authenticated_web_client.post('/bots/create', data={
            'name': 'New Bot',
            'telegram_token': 'invalid_token',
            'openai_api_key': 'test_key',
            'assistant_id': 'test_assistant'
        })
        
        assert response.status_code == 200  # Form should be re-rendered with errors
        assert b'Invalid token' in response.data or b'error' in response.data.lower()


class TestBotEditRoute:
    """Test bot edit route functionality."""
    
    def test_bot_edit_form_returns_200(self, authenticated_web_client, mock_use_cases):
        """Test that bot edit form returns 200 status."""
        bot_data = test_data_factory.create_bot_config(id=1, name="Test Bot")
        mock_use_cases['bot_management'].get_bot.return_value = bot_data
        
        response = authenticated_web_client.get('/bots/1/edit')
        
        assert response.status_code == 200
        assert b'Test Bot' in response.data
        mock_use_cases['bot_management'].get_bot.assert_called_once_with(1)
    
    def test_bot_edit_not_found(self, authenticated_web_client, mock_use_cases):
        """Test bot edit with non-existent bot."""
        mock_use_cases['bot_management'].get_bot.return_value = None
        
        response = authenticated_web_client.get('/bots/999/edit')
        
        assert response.status_code == 404
        assert b'not found' in response.data.lower()
    
    def test_bot_update_success(self, authenticated_web_client, mock_use_cases):
        """Test successful bot update."""
        bot_data = test_data_factory.create_bot_config(id=1, name="Updated Bot")
        mock_use_cases['bot_management'].update_bot.return_value = bot_data
        
        response = authenticated_web_client.post('/bots/1/edit', data={
            'name': 'Updated Bot',
            'telegram_token': 'test_token',
            'openai_api_key': 'test_key',
            'assistant_id': 'test_assistant'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        mock_use_cases['bot_management'].update_bot.assert_called_once()


class TestBotDeleteRoute:
    """Test bot delete route functionality."""
    
    def test_bot_delete_confirmation(self, authenticated_web_client, mock_use_cases):
        """Test bot delete confirmation page."""
        bot_data = test_data_factory.create_bot_config(id=1, name="Test Bot")
        mock_use_cases['bot_management'].get_bot.return_value = bot_data
        
        response = authenticated_web_client.get('/bots/1/delete')
        
        assert response.status_code == 200
        assert b'Test Bot' in response.data
        assert b'delete' in response.data.lower()
    
    def test_bot_delete_success(self, authenticated_web_client, mock_use_cases):
        """Test successful bot deletion."""
        mock_use_cases['bot_management'].delete_bot.return_value = True
        
        response = authenticated_web_client.post('/bots/1/delete', follow_redirects=True)
        
        assert response.status_code == 200
        mock_use_cases['bot_management'].delete_bot.assert_called_once_with(1)


class TestBotManagementRoutes:
    """Test bot management routes (start, stop, restart)."""
    
    def test_bot_start_success(self, authenticated_web_client, mock_use_cases):
        """Test successful bot start."""
        mock_use_cases['bot_management'].start_bot.return_value = True
        
        response = authenticated_web_client.post('/bots/1/start', follow_redirects=True)
        
        assert response.status_code == 200
        mock_use_cases['bot_management'].start_bot.assert_called_once_with(1)
    
    def test_bot_stop_success(self, authenticated_web_client, mock_use_cases):
        """Test successful bot stop."""
        mock_use_cases['bot_management'].stop_bot.return_value = True
        
        response = authenticated_web_client.post('/bots/1/stop', follow_redirects=True)
        
        assert response.status_code == 200
        mock_use_cases['bot_management'].stop_bot.assert_called_once_with(1)
    
    def test_bot_restart_success(self, authenticated_web_client, mock_use_cases):
        """Test successful bot restart."""
        mock_use_cases['bot_management'].restart_bot.return_value = True
        
        response = authenticated_web_client.post('/bots/1/restart', follow_redirects=True)
        
        assert response.status_code == 200
        mock_use_cases['bot_management'].restart_bot.assert_called_once_with(1)
    
    def test_bot_management_error(self, authenticated_web_client, mock_use_cases):
        """Test bot management with error."""
        mock_use_cases['bot_management'].start_bot.side_effect = Exception("Bot error")
        
        response = authenticated_web_client.post('/bots/1/start', follow_redirects=True)
        
        assert response.status_code == 200
        assert b'error' in response.data.lower() or b'failed' in response.data.lower()


class TestBotAJAXRoutes:
    """Test AJAX routes for bot operations."""
    
    def test_bot_status_ajax(self, authenticated_web_client, mock_use_cases):
        """Test bot status AJAX endpoint."""
        bot_data = test_data_factory.create_bot_config(id=1, status="running")
        mock_use_cases['bot_management'].get_bot.return_value = bot_data
        
        response = authenticated_web_client.get('/api/bots/1/status')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'running'
        assert data['success'] is True
    
    def test_bot_stats_ajax(self, authenticated_web_client, mock_use_cases):
        """Test bot stats AJAX endpoint."""
        stats_data = {
            'messages_processed': 100,
            'users_count': 50,
            'uptime': 3600
        }
        mock_use_cases['bot_management'].get_bot_stats.return_value = stats_data
        
        response = authenticated_web_client.get('/api/bots/1/stats')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['data']['messages_processed'] == 100
    
    def test_bot_list_ajax(self, authenticated_web_client, mock_use_cases):
        """Test bot list AJAX endpoint."""
        bots_data = [
            test_data_factory.create_bot_config(id=1, name="Bot 1"),
            test_data_factory.create_bot_config(id=2, name="Bot 2")
        ]
        mock_use_cases['bot_management'].get_all_bots.return_value = bots_data
        
        response = authenticated_web_client.get('/api/bots')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert len(data['data']) == 2
    
    def test_bot_create_ajax(self, authenticated_web_client, mock_use_cases):
        """Test bot create AJAX endpoint."""
        bot_data = test_data_factory.create_bot_config(id=1, name="New Bot")
        mock_use_cases['bot_management'].create_bot.return_value = bot_data
        
        response = authenticated_web_client.post('/api/bots', 
            data=json.dumps({
                'name': 'New Bot',
                'telegram_token': 'test_token',
                'openai_api_key': 'test_key',
                'assistant_id': 'test_assistant'
            }),
            content_type='application/json'
        )
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['data']['name'] == 'New Bot'
    
    def test_bot_update_ajax(self, authenticated_web_client, mock_use_cases):
        """Test bot update AJAX endpoint."""
        bot_data = test_data_factory.create_bot_config(id=1, name="Updated Bot")
        mock_use_cases['bot_management'].update_bot.return_value = bot_data
        
        response = authenticated_web_client.put('/api/bots/1',
            data=json.dumps({
                'name': 'Updated Bot',
                'telegram_token': 'test_token'
            }),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['data']['name'] == 'Updated Bot'
    
    def test_bot_delete_ajax(self, authenticated_web_client, mock_use_cases):
        """Test bot delete AJAX endpoint."""
        mock_use_cases['bot_management'].delete_bot.return_value = True
        
        response = authenticated_web_client.delete('/api/bots/1')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        mock_use_cases['bot_management'].delete_bot.assert_called_once_with(1)


class TestBotRoutesErrorHandling:
    """Test error handling in bot routes."""
    
    def test_bot_not_found_ajax(self, authenticated_web_client, mock_use_cases):
        """Test AJAX endpoint with non-existent bot."""
        mock_use_cases['bot_management'].get_bot.return_value = None
        
        response = authenticated_web_client.get('/api/bots/999/status')
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'not found' in data['error']['message'].lower()
    
    def test_bot_validation_error_ajax(self, authenticated_web_client, mock_use_cases):
        """Test AJAX endpoint with validation error."""
        mock_use_cases['bot_management'].create_bot.side_effect = ValueError("Invalid token")
        
        response = authenticated_web_client.post('/api/bots',
            data=json.dumps({
                'name': 'Test Bot',
                'telegram_token': 'invalid_token'
            }),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'Invalid token' in data['error']['message']
    
    def test_bot_server_error_ajax(self, authenticated_web_client, mock_use_cases):
        """Test AJAX endpoint with server error."""
        mock_use_cases['bot_management'].get_all_bots.side_effect = Exception("Database error")
        
        response = authenticated_web_client.get('/api/bots')
        
        assert response.status_code == 500
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'error' in data['error']['message'].lower()


class TestBotRoutesPagination:
    """Test pagination in bot routes."""
    
    def test_bot_list_pagination(self, authenticated_web_client, mock_use_cases):
        """Test bot list with pagination."""
        bots_data = [test_data_factory.create_bot_config(id=i) for i in range(1, 26)]
        pagination_data = test_data_factory.create_pagination_info(
            page=1, per_page=10, total=25, pages=3
        )
        
        mock_use_cases['bot_management'].get_all_bots.return_value = {
            'bots': bots_data[:10],
            'pagination': pagination_data
        }
        
        response = authenticated_web_client.get('/bots?page=1&per_page=10')
        
        assert response.status_code == 200
        assert b'page 1' in response.data.lower() or b'1 of 3' in response.data
    
    def test_bot_list_ajax_pagination(self, authenticated_web_client, mock_use_cases):
        """Test bot list AJAX with pagination."""
        bots_data = [test_data_factory.create_bot_config(id=i) for i in range(1, 26)]
        pagination_data = test_data_factory.create_pagination_info(
            page=1, per_page=10, total=25, pages=3
        )
        
        mock_use_cases['bot_management'].get_all_bots.return_value = {
            'bots': bots_data[:10],
            'pagination': pagination_data
        }
        
        response = authenticated_web_client.get('/api/bots?page=1&per_page=10')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'pagination' in data['data']
        assert data['data']['pagination']['page'] == 1








