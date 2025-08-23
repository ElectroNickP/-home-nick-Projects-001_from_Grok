"""
Common fixtures for entry points testing.

This module provides shared fixtures and utilities for testing
all entry points (Web, CLI, API) with proper isolation and
test data management.
"""

import pytest
from unittest.mock import Mock, MagicMock
from typing import Dict, Any, Generator
import tempfile
import os
import json

from core.entrypoints.factories import UseCaseFactory, EntryPointFactory
from core.entrypoints.config import EntryPointConfig


@pytest.fixture
def mock_use_cases() -> Dict[str, Mock]:
    """Mock use cases for testing."""
    return {
        'bot_management': Mock(),
        'conversation': Mock(),
        'system': Mock()
    }


@pytest.fixture
def use_case_factory(mock_use_cases: Dict[str, Mock]) -> UseCaseFactory:
    """Factory with mocked use cases."""
    factory = UseCaseFactory()
    
    # Mock the creation methods
    factory._create_bot_management_use_case = lambda: mock_use_cases['bot_management']
    factory._create_conversation_use_case = lambda: mock_use_cases['conversation']
    factory._create_system_use_case = lambda: mock_use_cases['system']
    
    return factory


@pytest.fixture
def entry_point_factory(use_case_factory: UseCaseFactory) -> EntryPointFactory:
    """Factory with mocked dependencies."""
    return EntryPointFactory(use_case_factory)


@pytest.fixture
def test_config() -> EntryPointConfig:
    """Test configuration."""
    return EntryPointConfig(
        web_host="127.0.0.1",
        web_port=0,  # Use random port for testing
        api_host="127.0.0.1", 
        api_port=0,  # Use random port for testing
        debug=True,
        secret_key="test-secret-key",
        api_key="test-api-key"
    )


@pytest.fixture
def temp_config_file() -> Generator[str, None, None]:
    """Temporary configuration file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump({
            'bots': {},
            'conversations': {},
            'system': {
                'version': '3.6.0',
                'debug': True
            }
        }, f)
        temp_file = f.name
    
    yield temp_file
    
    # Cleanup
    if os.path.exists(temp_file):
        os.unlink(temp_file)


@pytest.fixture
def sample_bot_config() -> Dict[str, Any]:
    """Sample bot configuration for testing."""
    return {
        'id': 1,
        'name': 'Test Bot',
        'telegram_token': 'test_telegram_token',
        'openai_api_key': 'test_openai_key',
        'assistant_id': 'test_assistant_id',
        'status': 'stopped',
        'created_at': '2025-01-01T00:00:00Z',
        'enable_voice_responses': True,
        'voice_model': 'tts-1',
        'voice_type': 'nova',
        'group_context_limit': 15
    }


@pytest.fixture
def sample_conversation() -> Dict[str, Any]:
    """Sample conversation for testing."""
    return {
        'key': 'test_conversation_key',
        'messages': [
            {
                'id': 1,
                'role': 'user',
                'content': 'Hello, bot!',
                'timestamp': '2025-01-01T00:00:00Z'
            },
            {
                'id': 2,
                'role': 'assistant',
                'content': 'Hello! How can I help you?',
                'timestamp': '2025-01-01T00:00:01Z'
            }
        ],
        'created_at': '2025-01-01T00:00:00Z',
        'updated_at': '2025-01-01T00:00:01Z'
    }


@pytest.fixture
def sample_system_status() -> Dict[str, Any]:
    """Sample system status for testing."""
    return {
        'status': 'running',
        'version': '3.6.0',
        'uptime': 3600,
        'memory_usage': 512,
        'cpu_usage': 25.5,
        'active_bots': 2,
        'total_conversations': 10,
        'last_backup': '2025-01-01T00:00:00Z'
    }


@pytest.fixture
def mock_telegram_adapter() -> Mock:
    """Mock Telegram adapter."""
    adapter = Mock()
    adapter.send_message.return_value = "test_message_id"
    adapter.send_voice.return_value = "test_voice_id"
    adapter.get_me.return_value = {
        'id': 123456789,
        'username': 'test_bot',
        'first_name': 'Test Bot'
    }
    adapter.validate_token.return_value = True
    return adapter


@pytest.fixture
def mock_storage_adapter() -> Mock:
    """Mock storage adapter."""
    adapter = Mock()
    adapter.read_config.return_value = {}
    adapter.write_config.return_value = None
    adapter.get_bot_config.return_value = None
    adapter.update_bot_config.return_value = None
    adapter.delete_bot_config.return_value = None
    return adapter


@pytest.fixture
def mock_updater_adapter() -> Mock:
    """Mock updater adapter."""
    adapter = Mock()
    adapter.check_updates.return_value = {
        'available': False,
        'current_version': '3.6.0',
        'latest_version': '3.6.0'
    }
    adapter.apply_update.return_value = True
    adapter.create_backup.return_value = 'backup_20250101_000000'
    adapter.restore_backup.return_value = True
    return adapter


@pytest.fixture
def web_client(test_config: EntryPointConfig, entry_point_factory: EntryPointFactory):
    """Flask test client for web entry point."""
    from core.entrypoints.web.flask_app import create_app
    
    app = create_app(test_config, entry_point_factory)
    app.config['TESTING'] = True
    
    with app.test_client() as client:
        yield client


@pytest.fixture
def api_client(test_config: EntryPointConfig, entry_point_factory: EntryPointFactory):
    """FastAPI test client for API entry point."""
    from core.entrypoints.api.api_app import create_app
    from fastapi.testclient import TestClient
    
    app = create_app(test_config, entry_point_factory)
    
    with TestClient(app) as client:
        yield client


@pytest.fixture
def cli_runner():
    """Click test runner for CLI entry point."""
    from click.testing import CliRunner
    
    runner = CliRunner()
    return runner


@pytest.fixture
def authenticated_web_client(web_client):
    """Authenticated web client with session."""
    with web_client.session_transaction() as sess:
        sess['authenticated'] = True
        sess['user'] = 'admin'
    
    return web_client


@pytest.fixture
def authenticated_api_client(api_client):
    """Authenticated API client with headers."""
    api_client.headers.update({
        'Authorization': 'Bearer test-api-key'
    })
    return api_client







