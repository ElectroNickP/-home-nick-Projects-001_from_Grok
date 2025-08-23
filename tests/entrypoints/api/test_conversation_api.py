"""
Unit tests for conversation API endpoints (API Entry Point).

Tests cover all conversation-related API endpoints including
CRUD operations, messages, context, and stats endpoints.
"""

import pytest
import json
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from tests.entrypoints.factories import test_data_factory


class TestConversationListAPI:
    """Test conversation list API endpoint functionality."""
    
    def test_get_conversations_success(self, api_client, mock_use_cases):
        """Test successful GET /api/conversations endpoint."""
        conversations = [
            test_data_factory.create_conversation(id=1, bot_id=1, user_id=100),
            test_data_factory.create_conversation(id=2, bot_id=1, user_id=101)
        ]
        mock_use_cases['conversation'].list_conversations.return_value = conversations
        
        response = api_client.get('/api/conversations')
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]['id'] == 1
        assert data[0]['bot_id'] == 1
        assert data[0]['user_id'] == 100
        assert data[1]['id'] == 2
        assert data[1]['bot_id'] == 1
        assert data[1]['user_id'] == 101
        mock_use_cases['conversation'].list_conversations.assert_called_once()
    
    def test_get_conversations_empty(self, api_client, mock_use_cases):
        """Test GET /api/conversations endpoint with no conversations."""
        mock_use_cases['conversation'].list_conversations.return_value = []
        
        response = api_client.get('/api/conversations')
        
        assert response.status_code == 200
        data = response.json()
        assert data == []
        mock_use_cases['conversation'].list_conversations.assert_called_once()
    
    def test_get_conversations_with_filters(self, api_client, mock_use_cases):
        """Test GET /api/conversations endpoint with query parameters."""
        conversations = [test_data_factory.create_conversation(id=1, bot_id=1, user_id=100, status='active')]
        mock_use_cases['conversation'].list_conversations.return_value = conversations
        
        response = api_client.get('/api/conversations?bot_id=1&status=active&limit=10&offset=0')
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]['bot_id'] == 1
        assert data[0]['status'] == 'active'
        mock_use_cases['conversation'].list_conversations.assert_called_once_with(
            bot_id=1, status='active', limit=10, offset=0
        )
    
    def test_get_conversations_server_error(self, api_client, mock_use_cases):
        """Test GET /api/conversations endpoint with server error."""
        mock_use_cases['conversation'].list_conversations.side_effect = Exception("Server error")
        
        response = api_client.get('/api/conversations')
        
        assert response.status_code == 500
        data = response.json()
        assert 'error' in data
        assert 'Server error' in data['error']['message']
    
    def test_get_conversations_invalid_filters(self, api_client):
        """Test GET /api/conversations endpoint with invalid query parameters."""
        response = api_client.get('/api/conversations?limit=invalid&offset=-1')
        
        assert response.status_code == 422  # Validation error
        data = response.json()
        assert 'detail' in data


class TestConversationGetAPI:
    """Test conversation get API endpoint functionality."""
    
    def test_get_conversation_success(self, api_client, mock_use_cases):
        """Test successful GET /api/conversations/{conversation_id} endpoint."""
        conversation = test_data_factory.create_conversation(id=1, bot_id=1, user_id=100)
        mock_use_cases['conversation'].get_conversation.return_value = conversation
        
        response = api_client.get('/api/conversations/1')
        
        assert response.status_code == 200
        data = response.json()
        assert data['id'] == 1
        assert data['bot_id'] == 1
        assert data['user_id'] == 100
        assert 'status' in data
        assert 'created_at' in data
        mock_use_cases['conversation'].get_conversation.assert_called_once_with(1)
    
    def test_get_conversation_not_found(self, api_client, mock_use_cases):
        """Test GET /api/conversations/{conversation_id} endpoint with non-existent conversation."""
        mock_use_cases['conversation'].get_conversation.return_value = None
        
        response = api_client.get('/api/conversations/999')
        
        assert response.status_code == 404
        data = response.json()
        assert 'error' in data
        assert 'Conversation not found' in data['error']['message']
    
    def test_get_conversation_invalid_id(self, api_client):
        """Test GET /api/conversations/{conversation_id} endpoint with invalid ID."""
        response = api_client.get('/api/conversations/invalid')
        
        assert response.status_code == 422  # Validation error
        data = response.json()
        assert 'detail' in data
    
    def test_get_conversation_with_messages(self, api_client, mock_use_cases):
        """Test GET /api/conversations/{conversation_id} endpoint with messages included."""
        conversation = test_data_factory.create_conversation(id=1, bot_id=1, user_id=100)
        conversation['messages'] = [
            test_data_factory.create_message(id=1, conversation_id=1, content='Hello'),
            test_data_factory.create_message(id=2, conversation_id=1, content='Hi there')
        ]
        mock_use_cases['conversation'].get_conversation.return_value = conversation
        
        response = api_client.get('/api/conversations/1?include_messages=true')
        
        assert response.status_code == 200
        data = response.json()
        assert data['id'] == 1
        assert 'messages' in data
        assert len(data['messages']) == 2
        assert data['messages'][0]['content'] == 'Hello'
        assert data['messages'][1]['content'] == 'Hi there'
        mock_use_cases['conversation'].get_conversation.assert_called_once_with(1, include_messages=True)
    
    def test_get_conversation_server_error(self, api_client, mock_use_cases):
        """Test GET /api/conversations/{conversation_id} endpoint with server error."""
        mock_use_cases['conversation'].get_conversation.side_effect = Exception("Server error")
        
        response = api_client.get('/api/conversations/1')
        
        assert response.status_code == 500
        data = response.json()
        assert 'error' in data
        assert 'Server error' in data['error']['message']


class TestConversationClearAPI:
    """Test conversation clear API endpoint functionality."""
    
    def test_clear_conversation_success(self, api_client, mock_use_cases):
        """Test successful DELETE /api/conversations/{conversation_id} endpoint."""
        mock_use_cases['conversation'].clear_conversation.return_value = True
        
        response = api_client.delete('/api/conversations/1')
        
        assert response.status_code == 204  # No content
        mock_use_cases['conversation'].clear_conversation.assert_called_once_with(1)
    
    def test_clear_conversation_not_found(self, api_client, mock_use_cases):
        """Test DELETE /api/conversations/{conversation_id} endpoint with non-existent conversation."""
        mock_use_cases['conversation'].clear_conversation.return_value = False
        
        response = api_client.delete('/api/conversations/999')
        
        assert response.status_code == 404
        data = response.json()
        assert 'error' in data
        assert 'Conversation not found' in data['error']['message']
    
    def test_clear_conversation_invalid_id(self, api_client):
        """Test DELETE /api/conversations/{conversation_id} endpoint with invalid ID."""
        response = api_client.delete('/api/conversations/invalid')
        
        assert response.status_code == 422  # Validation error
        data = response.json()
        assert 'detail' in data
    
    def test_clear_all_conversations_success(self, api_client, mock_use_cases):
        """Test successful DELETE /api/conversations endpoint (clear all)."""
        mock_use_cases['conversation'].clear_all_conversations.return_value = 5
        
        response = api_client.delete('/api/conversations')
        
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert data['message'] == '5 conversations cleared'
        mock_use_cases['conversation'].clear_all_conversations.assert_called_once()
    
    def test_clear_all_conversations_with_filters(self, api_client, mock_use_cases):
        """Test DELETE /api/conversations endpoint with filters."""
        mock_use_cases['conversation'].clear_all_conversations.return_value = 3
        
        response = api_client.delete('/api/conversations?bot_id=1')
        
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert data['message'] == '3 conversations cleared'
        mock_use_cases['conversation'].clear_all_conversations.assert_called_once_with(bot_id=1)
    
    def test_clear_conversation_server_error(self, api_client, mock_use_cases):
        """Test DELETE /api/conversations/{conversation_id} endpoint with server error."""
        mock_use_cases['conversation'].clear_conversation.side_effect = Exception("Server error")
        
        response = api_client.delete('/api/conversations/1')
        
        assert response.status_code == 500
        data = response.json()
        assert 'error' in data
        assert 'Server error' in data['error']['message']


class TestConversationMessagesAPI:
    """Test conversation messages API endpoint functionality."""
    
    def test_get_conversation_messages_success(self, api_client, mock_use_cases):
        """Test successful GET /api/conversations/{conversation_id}/messages endpoint."""
        messages = [
            test_data_factory.create_message(id=1, conversation_id=1, content='Hello', sender='user'),
            test_data_factory.create_message(id=2, conversation_id=1, content='Hi there', sender='bot')
        ]
        mock_use_cases['conversation'].get_conversation_messages.return_value = messages
        
        response = api_client.get('/api/conversations/1/messages')
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]['id'] == 1
        assert data[0]['content'] == 'Hello'
        assert data[0]['sender'] == 'user'
        assert data[1]['id'] == 2
        assert data[1]['content'] == 'Hi there'
        assert data[1]['sender'] == 'bot'
        mock_use_cases['conversation'].get_conversation_messages.assert_called_once_with(1)
    
    def test_get_conversation_messages_empty(self, api_client, mock_use_cases):
        """Test GET /api/conversations/{conversation_id}/messages endpoint with no messages."""
        mock_use_cases['conversation'].get_conversation_messages.return_value = []
        
        response = api_client.get('/api/conversations/1/messages')
        
        assert response.status_code == 200
        data = response.json()
        assert data == []
        mock_use_cases['conversation'].get_conversation_messages.assert_called_once_with(1)
    
    def test_get_conversation_messages_not_found(self, api_client, mock_use_cases):
        """Test GET /api/conversations/{conversation_id}/messages endpoint with non-existent conversation."""
        mock_use_cases['conversation'].get_conversation_messages.return_value = None
        
        response = api_client.get('/api/conversations/999/messages')
        
        assert response.status_code == 404
        data = response.json()
        assert 'error' in data
        assert 'Conversation not found' in data['error']['message']
    
    def test_get_conversation_messages_with_filters(self, api_client, mock_use_cases):
        """Test GET /api/conversations/{conversation_id}/messages endpoint with query parameters."""
        messages = [test_data_factory.create_message(id=1, conversation_id=1, content='Hello', sender='user')]
        mock_use_cases['conversation'].get_conversation_messages.return_value = messages
        
        response = api_client.get('/api/conversations/1/messages?limit=10&offset=0&sender=user')
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]['sender'] == 'user'
        mock_use_cases['conversation'].get_conversation_messages.assert_called_once_with(
            1, limit=10, offset=0, sender='user'
        )
    
    def test_get_conversation_messages_invalid_id(self, api_client):
        """Test GET /api/conversations/{conversation_id}/messages endpoint with invalid ID."""
        response = api_client.get('/api/conversations/invalid/messages')
        
        assert response.status_code == 422  # Validation error
        data = response.json()
        assert 'detail' in data
    
    def test_get_conversation_messages_server_error(self, api_client, mock_use_cases):
        """Test GET /api/conversations/{conversation_id}/messages endpoint with server error."""
        mock_use_cases['conversation'].get_conversation_messages.side_effect = Exception("Server error")
        
        response = api_client.get('/api/conversations/1/messages')
        
        assert response.status_code == 500
        data = response.json()
        assert 'error' in data
        assert 'Server error' in data['error']['message']


class TestConversationContextAPI:
    """Test conversation context API endpoint functionality."""
    
    def test_get_conversation_context_success(self, api_client, mock_use_cases):
        """Test successful GET /api/conversations/{conversation_id}/context endpoint."""
        context = {
            'conversation_id': 1,
            'context_data': {
                'user_preferences': {'language': 'en', 'timezone': 'UTC'},
                'session_data': {'current_state': 'menu', 'last_action': 'help'},
                'variables': {'name': 'John', 'age': 25}
            }
        }
        mock_use_cases['conversation'].get_conversation_context.return_value = context
        
        response = api_client.get('/api/conversations/1/context')
        
        assert response.status_code == 200
        data = response.json()
        assert data['conversation_id'] == 1
        assert 'context_data' in data
        assert 'user_preferences' in data['context_data']
        assert 'session_data' in data['context_data']
        assert 'variables' in data['context_data']
        assert data['context_data']['user_preferences']['language'] == 'en'
        assert data['context_data']['variables']['name'] == 'John'
        mock_use_cases['conversation'].get_conversation_context.assert_called_once_with(1)
    
    def test_get_conversation_context_not_found(self, api_client, mock_use_cases):
        """Test GET /api/conversations/{conversation_id}/context endpoint with non-existent conversation."""
        mock_use_cases['conversation'].get_conversation_context.return_value = None
        
        response = api_client.get('/api/conversations/999/context')
        
        assert response.status_code == 404
        data = response.json()
        assert 'error' in data
        assert 'Conversation not found' in data['error']['message']
    
    def test_get_conversation_context_empty(self, api_client, mock_use_cases):
        """Test GET /api/conversations/{conversation_id}/context endpoint with empty context."""
        context = {'conversation_id': 1, 'context_data': {}}
        mock_use_cases['conversation'].get_conversation_context.return_value = context
        
        response = api_client.get('/api/conversations/1/context')
        
        assert response.status_code == 200
        data = response.json()
        assert data['conversation_id'] == 1
        assert data['context_data'] == {}
    
    def test_get_conversation_context_invalid_id(self, api_client):
        """Test GET /api/conversations/{conversation_id}/context endpoint with invalid ID."""
        response = api_client.get('/api/conversations/invalid/context')
        
        assert response.status_code == 422  # Validation error
        data = response.json()
        assert 'detail' in data
    
    def test_get_conversation_context_server_error(self, api_client, mock_use_cases):
        """Test GET /api/conversations/{conversation_id}/context endpoint with server error."""
        mock_use_cases['conversation'].get_conversation_context.side_effect = Exception("Server error")
        
        response = api_client.get('/api/conversations/1/context')
        
        assert response.status_code == 500
        data = response.json()
        assert 'error' in data
        assert 'Server error' in data['error']['message']


class TestConversationStatsAPI:
    """Test conversation stats API endpoint functionality."""
    
    def test_get_conversation_stats_success(self, api_client, mock_use_cases):
        """Test successful GET /api/conversations/{conversation_id}/stats endpoint."""
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
        
        response = api_client.get('/api/conversations/1/stats')
        
        assert response.status_code == 200
        data = response.json()
        assert data['conversation_id'] == 1
        assert data['total_messages'] == 50
        assert data['user_messages'] == 25
        assert data['bot_messages'] == 25
        assert data['avg_response_time'] == '1.5s'
        assert data['last_activity'] == '2024-01-15 10:30:00'
        assert data['duration'] == '2h 15m'
        mock_use_cases['conversation'].get_conversation_stats.assert_called_once_with(1)
    
    def test_get_conversation_stats_not_found(self, api_client, mock_use_cases):
        """Test GET /api/conversations/{conversation_id}/stats endpoint with non-existent conversation."""
        mock_use_cases['conversation'].get_conversation_stats.return_value = None
        
        response = api_client.get('/api/conversations/999/stats')
        
        assert response.status_code == 404
        data = response.json()
        assert 'error' in data
        assert 'Conversation not found' in data['error']['message']
    
    def test_get_conversation_stats_invalid_id(self, api_client):
        """Test GET /api/conversations/{conversation_id}/stats endpoint with invalid ID."""
        response = api_client.get('/api/conversations/invalid/stats')
        
        assert response.status_code == 422  # Validation error
        data = response.json()
        assert 'detail' in data
    
    def test_get_conversation_stats_server_error(self, api_client, mock_use_cases):
        """Test GET /api/conversations/{conversation_id}/stats endpoint with server error."""
        mock_use_cases['conversation'].get_conversation_stats.side_effect = Exception("Server error")
        
        response = api_client.get('/api/conversations/1/stats')
        
        assert response.status_code == 500
        data = response.json()
        assert 'error' in data
        assert 'Server error' in data['error']['message']


class TestConversationLastMessageAPI:
    """Test conversation last message API endpoint functionality."""
    
    def test_get_conversation_last_message_success(self, api_client, mock_use_cases):
        """Test successful GET /api/conversations/{conversation_id}/last-message endpoint."""
        last_message = test_data_factory.create_message(
            id=1, conversation_id=1, content='Last message', sender='user'
        )
        mock_use_cases['conversation'].get_conversation_last_message.return_value = last_message
        
        response = api_client.get('/api/conversations/1/last-message')
        
        assert response.status_code == 200
        data = response.json()
        assert data['id'] == 1
        assert data['conversation_id'] == 1
        assert data['content'] == 'Last message'
        assert data['sender'] == 'user'
        mock_use_cases['conversation'].get_conversation_last_message.assert_called_once_with(1)
    
    def test_get_conversation_last_message_not_found(self, api_client, mock_use_cases):
        """Test GET /api/conversations/{conversation_id}/last-message endpoint with non-existent conversation."""
        mock_use_cases['conversation'].get_conversation_last_message.return_value = None
        
        response = api_client.get('/api/conversations/999/last-message')
        
        assert response.status_code == 404
        data = response.json()
        assert 'error' in data
        assert 'Conversation not found' in data['error']['message']
    
    def test_get_conversation_last_message_no_messages(self, api_client, mock_use_cases):
        """Test GET /api/conversations/{conversation_id}/last-message endpoint with no messages."""
        mock_use_cases['conversation'].get_conversation_last_message.return_value = None
        
        response = api_client.get('/api/conversations/1/last-message')
        
        assert response.status_code == 404
        data = response.json()
        assert 'error' in data
        assert 'No messages found' in data['error']['message']
    
    def test_get_conversation_last_message_invalid_id(self, api_client):
        """Test GET /api/conversations/{conversation_id}/last-message endpoint with invalid ID."""
        response = api_client.get('/api/conversations/invalid/last-message')
        
        assert response.status_code == 422  # Validation error
        data = response.json()
        assert 'detail' in data


class TestConversationSearchAPI:
    """Test conversation search API endpoint functionality."""
    
    def test_search_conversations_success(self, api_client, mock_use_cases):
        """Test successful GET /api/conversations/search endpoint."""
        conversations = [
            test_data_factory.create_conversation(id=1, bot_id=1, user_id=100),
            test_data_factory.create_conversation(id=2, bot_id=1, user_id=101)
        ]
        mock_use_cases['conversation'].search_conversations.return_value = conversations
        
        response = api_client.get('/api/conversations/search?q=test&bot_id=1')
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]['id'] == 1
        assert data[1]['id'] == 2
        mock_use_cases['conversation'].search_conversations.assert_called_once_with(
            q='test', bot_id=1
        )
    
    def test_search_conversations_empty(self, api_client, mock_use_cases):
        """Test GET /api/conversations/search endpoint with no results."""
        mock_use_cases['conversation'].search_conversations.return_value = []
        
        response = api_client.get('/api/conversations/search?q=nonexistent')
        
        assert response.status_code == 200
        data = response.json()
        assert data == []
        mock_use_cases['conversation'].search_conversations.assert_called_once_with(q='nonexistent')
    
    def test_search_conversations_missing_query(self, api_client):
        """Test GET /api/conversations/search endpoint with missing query parameter."""
        response = api_client.get('/api/conversations/search')
        
        assert response.status_code == 422  # Validation error
        data = response.json()
        assert 'detail' in data
    
    def test_search_conversations_server_error(self, api_client, mock_use_cases):
        """Test GET /api/conversations/search endpoint with server error."""
        mock_use_cases['conversation'].search_conversations.side_effect = Exception("Server error")
        
        response = api_client.get('/api/conversations/search?q=test')
        
        assert response.status_code == 500
        data = response.json()
        assert 'error' in data
        assert 'Server error' in data['error']['message']


class TestConversationAPIErrorHandling:
    """Test conversation API error handling."""
    
    def test_api_server_error(self, api_client, mock_use_cases):
        """Test API endpoint with server error."""
        mock_use_cases['conversation'].list_conversations.side_effect = Exception("Server error")
        
        response = api_client.get('/api/conversations')
        
        assert response.status_code == 500
        data = response.json()
        assert 'error' in data
        assert 'Server error' in data['error']['message']
    
    def test_api_network_error(self, api_client, mock_use_cases):
        """Test API endpoint with network error."""
        mock_use_cases['conversation'].list_conversations.side_effect = ConnectionError("Network error")
        
        response = api_client.get('/api/conversations')
        
        assert response.status_code == 500
        data = response.json()
        assert 'error' in data
        assert 'Network error' in data['error']['message']
    
    def test_api_timeout_error(self, api_client, mock_use_cases):
        """Test API endpoint with timeout error."""
        mock_use_cases['conversation'].list_conversations.side_effect = TimeoutError("Request timeout")
        
        response = api_client.get('/api/conversations')
        
        assert response.status_code == 500
        data = response.json()
        assert 'error' in data
        assert 'Request timeout' in data['error']['message']
    
    def test_api_validation_error(self, api_client):
        """Test API endpoint with validation error."""
        response = api_client.get('/api/conversations?limit=invalid')
        
        assert response.status_code == 422  # Validation error
        data = response.json()
        assert 'detail' in data


class TestConversationAPIPerformance:
    """Test conversation API performance."""
    
    def test_api_response_time(self, api_client, mock_use_cases):
        """Test API response time."""
        conversations = [test_data_factory.create_conversation(id=1, bot_id=1, user_id=100)]
        mock_use_cases['conversation'].list_conversations.return_value = conversations
        
        import time
        start_time = time.time()
        response = api_client.get('/api/conversations')
        end_time = time.time()
        
        assert response.status_code == 200
        assert (end_time - start_time) < 1.0  # Response time should be under 1 second
    
    def test_api_concurrent_requests(self, api_client, mock_use_cases):
        """Test API with concurrent requests."""
        conversations = [test_data_factory.create_conversation(id=1, bot_id=1, user_id=100)]
        mock_use_cases['conversation'].list_conversations.return_value = conversations
        
        import threading
        import time
        
        results = []
        errors = []
        
        def make_request():
            try:
                response = api_client.get('/api/conversations')
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


class TestConversationAPIDocumentation:
    """Test conversation API documentation."""
    
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
        assert '/api/conversations' in data['paths']
    
    def test_api_redoc_accessible(self, api_client):
        """Test that ReDoc documentation is accessible."""
        response = api_client.get('/redoc')
        
        assert response.status_code == 200
        assert 'text/html' in response.headers['content-type']
        assert 'ReDoc' in response.text







