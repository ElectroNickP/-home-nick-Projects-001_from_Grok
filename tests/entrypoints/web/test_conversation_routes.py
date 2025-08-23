"""
Unit tests for conversation routes (Web Entry Point).

Tests cover all conversation-related routes including CRUD operations,
message management, and AJAX endpoints.
"""

import pytest
import json
from unittest.mock import Mock, patch
from tests.entrypoints.factories import test_data_factory


class TestConversationRoutesAuthentication:
    """Test authentication for conversation routes."""
    
    def test_conversation_list_requires_authentication(self, web_client):
        """Test that conversation list route requires authentication."""
        response = web_client.get('/conversations')
        
        assert response.status_code == 302  # Redirect to login
        assert '/login' in response.location
    
    def test_conversation_show_requires_authentication(self, web_client):
        """Test that conversation show route requires authentication."""
        response = web_client.get('/conversations/test_key')
        
        assert response.status_code == 302  # Redirect to login
        assert '/login' in response.location
    
    def test_conversation_clear_requires_authentication(self, web_client):
        """Test that conversation clear route requires authentication."""
        response = web_client.post('/conversations/test_key/clear')
        
        assert response.status_code == 302  # Redirect to login
        assert '/login' in response.location


class TestConversationListRoute:
    """Test conversation list route functionality."""
    
    def test_conversation_list_returns_200(self, authenticated_web_client, mock_use_cases):
        """Test that conversation list route returns 200 status."""
        conversations = [
            test_data_factory.create_conversation(key="conv1", bot_id=1),
            test_data_factory.create_conversation(key="conv2", bot_id=2)
        ]
        mock_use_cases['conversation'].get_all_conversations.return_value = conversations
        
        response = authenticated_web_client.get('/conversations')
        
        assert response.status_code == 200
        assert b'conv1' in response.data
        assert b'conv2' in response.data
        mock_use_cases['conversation'].get_all_conversations.assert_called_once()
    
    def test_conversation_list_empty(self, authenticated_web_client, mock_use_cases):
        """Test conversation list with no conversations."""
        mock_use_cases['conversation'].get_all_conversations.return_value = []
        
        response = authenticated_web_client.get('/conversations')
        
        assert response.status_code == 200
        assert b'No conversations found' in response.data or b'empty' in response.data.lower()
    
    def test_conversation_list_use_case_called(self, authenticated_web_client, mock_use_cases):
        """Test that use case is called for conversation list."""
        mock_use_cases['conversation'].get_all_conversations.return_value = []
        
        authenticated_web_client.get('/conversations')
        
        mock_use_cases['conversation'].get_all_conversations.assert_called_once()
    
    def test_conversation_list_with_filter(self, authenticated_web_client, mock_use_cases):
        """Test conversation list with filter parameters."""
        conversations = [
            test_data_factory.create_conversation(key="conv1", bot_id=1)
        ]
        mock_use_cases['conversation'].get_all_conversations.return_value = conversations
        
        response = authenticated_web_client.get('/conversations?bot_id=1')
        
        assert response.status_code == 200
        mock_use_cases['conversation'].get_all_conversations.assert_called_once()


class TestConversationShowRoute:
    """Test conversation show route functionality."""
    
    def test_conversation_show_returns_200(self, authenticated_web_client, mock_use_cases):
        """Test that conversation show route returns 200 status."""
        conversation = test_data_factory.create_conversation(key="test_conv")
        mock_use_cases['conversation'].get_conversation.return_value = conversation
        
        response = authenticated_web_client.get('/conversations/test_conv')
        
        assert response.status_code == 200
        assert b'test_conv' in response.data
        mock_use_cases['conversation'].get_conversation.assert_called_once_with('test_conv')
    
    def test_conversation_show_not_found(self, authenticated_web_client, mock_use_cases):
        """Test conversation show with non-existent conversation."""
        mock_use_cases['conversation'].get_conversation.return_value = None
        
        response = authenticated_web_client.get('/conversations/nonexistent')
        
        assert response.status_code == 404
        assert b'not found' in response.data.lower()
    
    def test_conversation_show_with_messages(self, authenticated_web_client, mock_use_cases):
        """Test conversation show with messages."""
        conversation = test_data_factory.create_conversation(
            key="test_conv",
            with_messages=True,
            message_count=3
        )
        mock_use_cases['conversation'].get_conversation.return_value = conversation
        
        response = authenticated_web_client.get('/conversations/test_conv')
        
        assert response.status_code == 200
        assert b'Message 1' in response.data
        assert b'Message 2' in response.data
        assert b'Message 3' in response.data


class TestConversationClearRoute:
    """Test conversation clear route functionality."""
    
    def test_conversation_clear_confirmation(self, authenticated_web_client, mock_use_cases):
        """Test conversation clear confirmation page."""
        conversation = test_data_factory.create_conversation(key="test_conv")
        mock_use_cases['conversation'].get_conversation.return_value = conversation
        
        response = authenticated_web_client.get('/conversations/test_conv/clear')
        
        assert response.status_code == 200
        assert b'test_conv' in response.data
        assert b'clear' in response.data.lower()
    
    def test_conversation_clear_success(self, authenticated_web_client, mock_use_cases):
        """Test successful conversation clearing."""
        mock_use_cases['conversation'].clear_conversation.return_value = True
        
        response = authenticated_web_client.post('/conversations/test_conv/clear', follow_redirects=True)
        
        assert response.status_code == 200
        mock_use_cases['conversation'].clear_conversation.assert_called_once_with('test_conv')
    
    def test_conversation_clear_not_found(self, authenticated_web_client, mock_use_cases):
        """Test conversation clear with non-existent conversation."""
        mock_use_cases['conversation'].get_conversation.return_value = None
        
        response = authenticated_web_client.get('/conversations/nonexistent/clear')
        
        assert response.status_code == 404
        assert b'not found' in response.data.lower()


class TestConversationMessagesRoute:
    """Test conversation messages route functionality."""
    
    def test_conversation_messages_returns_200(self, authenticated_web_client, mock_use_cases):
        """Test that conversation messages route returns 200 status."""
        messages = test_data_factory.create_messages(5)
        mock_use_cases['conversation'].get_conversation_messages.return_value = messages
        
        response = authenticated_web_client.get('/conversations/test_conv/messages')
        
        assert response.status_code == 200
        assert b'Message 1' in response.data
        assert b'Message 2' in response.data
        assert b'Message 3' in response.data
        assert b'Message 4' in response.data
        assert b'Message 5' in response.data
        mock_use_cases['conversation'].get_conversation_messages.assert_called_once_with('test_conv')
    
    def test_conversation_messages_empty(self, authenticated_web_client, mock_use_cases):
        """Test conversation messages with no messages."""
        mock_use_cases['conversation'].get_conversation_messages.return_value = []
        
        response = authenticated_web_client.get('/conversations/test_conv/messages')
        
        assert response.status_code == 200
        assert b'No messages found' in response.data or b'empty' in response.data.lower()
    
    def test_conversation_messages_with_pagination(self, authenticated_web_client, mock_use_cases):
        """Test conversation messages with pagination."""
        messages = test_data_factory.create_messages(25)
        pagination_data = test_data_factory.create_pagination_info(
            page=1, per_page=10, total=25, pages=3
        )
        
        mock_use_cases['conversation'].get_conversation_messages.return_value = {
            'messages': messages[:10],
            'pagination': pagination_data
        }
        
        response = authenticated_web_client.get('/conversations/test_conv/messages?page=1&per_page=10')
        
        assert response.status_code == 200
        assert b'page 1' in response.data.lower() or b'1 of 3' in response.data


class TestConversationContextRoute:
    """Test conversation context route functionality."""
    
    def test_conversation_context_returns_200(self, authenticated_web_client, mock_use_cases):
        """Test that conversation context route returns 200 status."""
        context_data = {
            'bot_id': 1,
            'chat_id': 123456789,
            'last_message': 'Hello, bot!',
            'message_count': 5,
            'created_at': '2025-01-01T00:00:00Z'
        }
        mock_use_cases['conversation'].get_conversation_context.return_value = context_data
        
        response = authenticated_web_client.get('/conversations/test_conv/context')
        
        assert response.status_code == 200
        assert b'Hello, bot!' in response.data
        assert b'5' in response.data
        mock_use_cases['conversation'].get_conversation_context.assert_called_once_with('test_conv')
    
    def test_conversation_context_not_found(self, authenticated_web_client, mock_use_cases):
        """Test conversation context with non-existent conversation."""
        mock_use_cases['conversation'].get_conversation_context.return_value = None
        
        response = authenticated_web_client.get('/conversations/nonexistent/context')
        
        assert response.status_code == 404
        assert b'not found' in response.data.lower()


class TestConversationStatsRoute:
    """Test conversation stats route functionality."""
    
    def test_conversation_stats_returns_200(self, authenticated_web_client, mock_use_cases):
        """Test that conversation stats route returns 200 status."""
        stats_data = {
            'message_count': 15,
            'user_messages': 8,
            'bot_messages': 7,
            'avg_response_time': 2.5,
            'last_activity': '2025-01-01T12:00:00Z'
        }
        mock_use_cases['conversation'].get_conversation_stats.return_value = stats_data
        
        response = authenticated_web_client.get('/conversations/test_conv/stats')
        
        assert response.status_code == 200
        assert b'15' in response.data
        assert b'8' in response.data
        assert b'7' in response.data
        assert b'2.5' in response.data
        mock_use_cases['conversation'].get_conversation_stats.assert_called_once_with('test_conv')


class TestConversationAJAXRoutes:
    """Test AJAX routes for conversation operations."""
    
    def test_conversation_list_ajax(self, authenticated_web_client, mock_use_cases):
        """Test conversation list AJAX endpoint."""
        conversations = [
            test_data_factory.create_conversation(key="conv1"),
            test_data_factory.create_conversation(key="conv2")
        ]
        mock_use_cases['conversation'].get_all_conversations.return_value = conversations
        
        response = authenticated_web_client.get('/api/conversations')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert len(data['data']) == 2
    
    def test_conversation_show_ajax(self, authenticated_web_client, mock_use_cases):
        """Test conversation show AJAX endpoint."""
        conversation = test_data_factory.create_conversation(key="test_conv")
        mock_use_cases['conversation'].get_conversation.return_value = conversation
        
        response = authenticated_web_client.get('/api/conversations/test_conv')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['data']['key'] == 'test_conv'
    
    def test_conversation_messages_ajax(self, authenticated_web_client, mock_use_cases):
        """Test conversation messages AJAX endpoint."""
        messages = test_data_factory.create_messages(3)
        mock_use_cases['conversation'].get_conversation_messages.return_value = messages
        
        response = authenticated_web_client.get('/api/conversations/test_conv/messages')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert len(data['data']) == 3
    
    def test_conversation_context_ajax(self, authenticated_web_client, mock_use_cases):
        """Test conversation context AJAX endpoint."""
        context_data = {
            'bot_id': 1,
            'chat_id': 123456789,
            'last_message': 'Hello, bot!'
        }
        mock_use_cases['conversation'].get_conversation_context.return_value = context_data
        
        response = authenticated_web_client.get('/api/conversations/test_conv/context')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['data']['last_message'] == 'Hello, bot!'
    
    def test_conversation_stats_ajax(self, authenticated_web_client, mock_use_cases):
        """Test conversation stats AJAX endpoint."""
        stats_data = {
            'message_count': 15,
            'user_messages': 8,
            'bot_messages': 7
        }
        mock_use_cases['conversation'].get_conversation_stats.return_value = stats_data
        
        response = authenticated_web_client.get('/api/conversations/test_conv/stats')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['data']['message_count'] == 15
    
    def test_conversation_clear_ajax(self, authenticated_web_client, mock_use_cases):
        """Test conversation clear AJAX endpoint."""
        mock_use_cases['conversation'].clear_conversation.return_value = True
        
        response = authenticated_web_client.delete('/api/conversations/test_conv')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        mock_use_cases['conversation'].clear_conversation.assert_called_once_with('test_conv')
    
    def test_conversation_last_message_ajax(self, authenticated_web_client, mock_use_cases):
        """Test conversation last message AJAX endpoint."""
        last_message = test_data_factory.create_message(
            id=10,
            role='user',
            content='Last message from user'
        )
        mock_use_cases['conversation'].get_last_message.return_value = last_message
        
        response = authenticated_web_client.get('/api/conversations/test_conv/last-message')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['data']['content'] == 'Last message from user'


class TestConversationRoutesErrorHandling:
    """Test error handling in conversation routes."""
    
    def test_conversation_not_found_ajax(self, authenticated_web_client, mock_use_cases):
        """Test AJAX endpoint with non-existent conversation."""
        mock_use_cases['conversation'].get_conversation.return_value = None
        
        response = authenticated_web_client.get('/api/conversations/nonexistent')
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'not found' in data['error']['message'].lower()
    
    def test_conversation_clear_error_ajax(self, authenticated_web_client, mock_use_cases):
        """Test AJAX endpoint with conversation clear error."""
        mock_use_cases['conversation'].clear_conversation.side_effect = Exception("Clear error")
        
        response = authenticated_web_client.delete('/api/conversations/test_conv')
        
        assert response.status_code == 500
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'error' in data['error']['message'].lower()
    
    def test_conversation_server_error_ajax(self, authenticated_web_client, mock_use_cases):
        """Test AJAX endpoint with server error."""
        mock_use_cases['conversation'].get_all_conversations.side_effect = Exception("Database error")
        
        response = authenticated_web_client.get('/api/conversations')
        
        assert response.status_code == 500
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'error' in data['error']['message'].lower()


class TestConversationRoutesPagination:
    """Test pagination in conversation routes."""
    
    def test_conversation_list_pagination(self, authenticated_web_client, mock_use_cases):
        """Test conversation list with pagination."""
        conversations = [test_data_factory.create_conversation(key=f"conv{i}") for i in range(1, 26)]
        pagination_data = test_data_factory.create_pagination_info(
            page=1, per_page=10, total=25, pages=3
        )
        
        mock_use_cases['conversation'].get_all_conversations.return_value = {
            'conversations': conversations[:10],
            'pagination': pagination_data
        }
        
        response = authenticated_web_client.get('/conversations?page=1&per_page=10')
        
        assert response.status_code == 200
        assert b'page 1' in response.data.lower() or b'1 of 3' in response.data
    
    def test_conversation_list_ajax_pagination(self, authenticated_web_client, mock_use_cases):
        """Test conversation list AJAX with pagination."""
        conversations = [test_data_factory.create_conversation(key=f"conv{i}") for i in range(1, 26)]
        pagination_data = test_data_factory.create_pagination_info(
            page=1, per_page=10, total=25, pages=3
        )
        
        mock_use_cases['conversation'].get_all_conversations.return_value = {
            'conversations': conversations[:10],
            'pagination': pagination_data
        }
        
        response = authenticated_web_client.get('/api/conversations?page=1&per_page=10')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'pagination' in data['data']
        assert data['data']['pagination']['page'] == 1


class TestConversationRoutesSearch:
    """Test search functionality in conversation routes."""
    
    def test_conversation_search(self, authenticated_web_client, mock_use_cases):
        """Test conversation search functionality."""
        conversations = [
            test_data_factory.create_conversation(key="conv1"),
            test_data_factory.create_conversation(key="conv2")
        ]
        mock_use_cases['conversation'].search_conversations.return_value = conversations
        
        response = authenticated_web_client.get('/conversations?search=test')
        
        assert response.status_code == 200
        mock_use_cases['conversation'].search_conversations.assert_called_once_with('test')
    
    def test_conversation_search_ajax(self, authenticated_web_client, mock_use_cases):
        """Test conversation search AJAX endpoint."""
        conversations = [
            test_data_factory.create_conversation(key="conv1"),
            test_data_factory.create_conversation(key="conv2")
        ]
        mock_use_cases['conversation'].search_conversations.return_value = conversations
        
        response = authenticated_web_client.get('/api/conversations?search=test')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert len(data['data']) == 2
        mock_use_cases['conversation'].search_conversations.assert_called_once_with('test')


class TestConversationRoutesFiltering:
    """Test filtering functionality in conversation routes."""
    
    def test_conversation_filter_by_bot(self, authenticated_web_client, mock_use_cases):
        """Test conversation filtering by bot ID."""
        conversations = [test_data_factory.create_conversation(key="conv1", bot_id=1)]
        mock_use_cases['conversation'].get_conversations_by_bot.return_value = conversations
        
        response = authenticated_web_client.get('/conversations?bot_id=1')
        
        assert response.status_code == 200
        mock_use_cases['conversation'].get_conversations_by_bot.assert_called_once_with(1)
    
    def test_conversation_filter_by_date(self, authenticated_web_client, mock_use_cases):
        """Test conversation filtering by date."""
        conversations = [test_data_factory.create_conversation(key="conv1")]
        mock_use_cases['conversation'].get_conversations_by_date.return_value = conversations
        
        response = authenticated_web_client.get('/conversations?date=2025-01-01')
        
        assert response.status_code == 200
        mock_use_cases['conversation'].get_conversations_by_date.assert_called_once_with('2025-01-01')
    
    def test_conversation_filter_ajax(self, authenticated_web_client, mock_use_cases):
        """Test conversation filtering AJAX endpoint."""
        conversations = [test_data_factory.create_conversation(key="conv1", bot_id=1)]
        mock_use_cases['conversation'].get_conversations_by_bot.return_value = conversations
        
        response = authenticated_web_client.get('/api/conversations?bot_id=1')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert len(data['data']) == 1
        mock_use_cases['conversation'].get_conversations_by_bot.assert_called_once_with(1)







