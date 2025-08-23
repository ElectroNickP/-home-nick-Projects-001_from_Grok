"""
Test data factories for entry points testing.

This module provides factories for creating test data consistently
across all entry point tests.
"""

from dataclasses import dataclass
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import random
import string


@dataclass
class TestDataFactory:
    """Factory for creating test data."""
    
    def create_bot_config(self, **kwargs) -> Dict[str, Any]:
        """Create bot configuration for testing."""
        default = {
            'id': random.randint(1, 1000),
            'name': f'Test Bot {random.randint(1, 100)}',
            'telegram_token': f'test_token_{random.randint(100000, 999999)}',
            'openai_api_key': f'sk-test-{self._random_string(48)}',
            'assistant_id': f'asst_{self._random_string(20)}',
            'status': random.choice(['stopped', 'running', 'error']),
            'created_at': datetime.now().isoformat(),
            'enable_voice_responses': random.choice([True, False]),
            'voice_model': random.choice(['tts-1', 'tts-1-hd']),
            'voice_type': random.choice(['alloy', 'echo', 'fable', 'onyx', 'nova', 'shimmer']),
            'group_context_limit': random.randint(10, 50),
            'enable_ai_responses': random.choice([True, False])
        }
        default.update(kwargs)
        return default
    
    def create_conversation(self, **kwargs) -> Dict[str, Any]:
        """Create conversation for testing."""
        messages = []
        if kwargs.get('with_messages', True):
            messages = self.create_messages(kwargs.get('message_count', 5))
        
        default = {
            'key': f'conv_{self._random_string(16)}',
            'messages': messages,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'bot_id': kwargs.get('bot_id', random.randint(1, 1000)),
            'chat_id': kwargs.get('chat_id', random.randint(100000000, 999999999))
        }
        default.update(kwargs)
        return default
    
    def create_message(self, **kwargs) -> Dict[str, Any]:
        """Create message for testing."""
        default = {
            'id': random.randint(1, 10000),
            'role': random.choice(['user', 'assistant', 'system']),
            'content': f'Test message {random.randint(1, 100)}',
            'timestamp': datetime.now().isoformat(),
            'message_type': 'text',
            'voice_url': None,
            'file_url': None
        }
        default.update(kwargs)
        return default
    
    def create_messages(self, count: int = 5) -> List[Dict[str, Any]]:
        """Create multiple messages for testing."""
        messages = []
        for i in range(count):
            messages.append(self.create_message(
                id=i + 1,
                role='user' if i % 2 == 0 else 'assistant',
                content=f'Message {i + 1}'
            ))
        return messages
    
    def create_system_status(self, **kwargs) -> Dict[str, Any]:
        """Create system status for testing."""
        default = {
            'status': random.choice(['running', 'stopped', 'error']),
            'version': '3.6.0',
            'uptime': random.randint(1000, 86400),
            'memory_usage': random.randint(100, 2048),
            'cpu_usage': random.uniform(0.0, 100.0),
            'active_bots': random.randint(0, 10),
            'total_conversations': random.randint(0, 100),
            'last_backup': (datetime.now() - timedelta(hours=random.randint(1, 24))).isoformat(),
            'disk_usage': random.uniform(0.0, 100.0),
            'network_connections': random.randint(0, 50)
        }
        default.update(kwargs)
        return default
    
    def create_backup_info(self, **kwargs) -> Dict[str, Any]:
        """Create backup information for testing."""
        default = {
            'id': f'backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}',
            'created_at': datetime.now().isoformat(),
            'size': random.randint(1024, 10485760),  # 1KB to 10MB
            'status': random.choice(['completed', 'failed', 'in_progress']),
            'description': f'Backup {random.randint(1, 100)}',
            'file_path': f'/backups/backup_{random.randint(1, 100)}.tar.gz'
        }
        default.update(kwargs)
        return default
    
    def create_update_info(self, **kwargs) -> Dict[str, Any]:
        """Create update information for testing."""
        default = {
            'available': random.choice([True, False]),
            'current_version': '3.6.0',
            'latest_version': '3.6.1',
            'release_notes': 'Bug fixes and improvements',
            'download_url': 'https://github.com/example/repo/releases/latest',
            'size': random.randint(1024, 10485760),
            'requires_restart': True
        }
        default.update(kwargs)
        return default
    
    def create_error_response(self, **kwargs) -> Dict[str, Any]:
        """Create error response for testing."""
        default = {
            'success': False,
            'error': {
                'code': random.choice([400, 401, 403, 404, 500]),
                'message': 'Test error message',
                'details': 'Additional error details'
            },
            'timestamp': datetime.now().isoformat()
        }
        default.update(kwargs)
        return default
    
    def create_success_response(self, data: Any = None, **kwargs) -> Dict[str, Any]:
        """Create success response for testing."""
        default = {
            'success': True,
            'data': data or {},
            'message': 'Operation completed successfully',
            'timestamp': datetime.now().isoformat()
        }
        default.update(kwargs)
        return default
    
    def create_pagination_info(self, **kwargs) -> Dict[str, Any]:
        """Create pagination information for testing."""
        default = {
            'page': random.randint(1, 10),
            'per_page': random.choice([10, 20, 50, 100]),
            'total': random.randint(0, 1000),
            'pages': random.randint(1, 50),
            'has_next': random.choice([True, False]),
            'has_prev': random.choice([True, False])
        }
        default.update(kwargs)
        return default
    
    def create_user_session(self, **kwargs) -> Dict[str, Any]:
        """Create user session for testing."""
        default = {
            'user_id': 'admin',
            'authenticated': True,
            'login_time': datetime.now().isoformat(),
            'permissions': ['read', 'write', 'admin'],
            'session_id': f'session_{self._random_string(16)}'
        }
        default.update(kwargs)
        return default
    
    def create_api_request(self, **kwargs) -> Dict[str, Any]:
        """Create API request for testing."""
        default = {
            'method': random.choice(['GET', 'POST', 'PUT', 'DELETE']),
            'url': '/api/v1/test',
            'headers': {
                'Authorization': 'Bearer test-api-key',
                'Content-Type': 'application/json',
                'User-Agent': 'TestClient/1.0'
            },
            'params': {},
            'data': {}
        }
        default.update(kwargs)
        return default
    
    def _random_string(self, length: int) -> str:
        """Generate random string of specified length."""
        return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


# Global factory instance
test_data_factory = TestDataFactory()







