"""
Pytest конфигурация и фикстуры для профессионального тестирования
"""

import pytest
import requests
import json
import time
import os
import sys
import tempfile
import shutil
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Добавляем путь к src для импорта модулей
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Конфигурация тестирования
BASE_URL = "http://localhost:5000"
TEST_CREDENTIALS = ("admin", "securepassword123")

class TestConfig:
    """Конфигурация для тестов"""
    BASE_URL = BASE_URL
    CREDENTIALS = TEST_CREDENTIALS
    TIMEOUT = 30
    RETRY_ATTEMPTS = 3
    WAIT_TIME = 2

@pytest.fixture(scope="session")
def test_config():
    """Конфигурация тестов"""
    return TestConfig()

@pytest.fixture(scope="session")
def session_manager():
    """Менеджер сессий для тестирования"""
    class SessionManager:
        def __init__(self):
            self.session = requests.Session()
            self.logged_in = False
            self.base_url = BASE_URL
        
        def login(self, username, password):
            """Вход в систему"""
            url = f"{self.base_url}/api/login"
            data = {"username": username, "password": password}
            headers = {"Content-Type": "application/json"}
            
            response = self.session.post(url, json=data, headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    self.logged_in = True
                    return True
            return False
        
        def get(self, endpoint, **kwargs):
            """GET запрос"""
            url = f"{self.base_url}{endpoint}"
            return self.session.get(url, **kwargs)
        
        def post(self, endpoint, data=None, **kwargs):
            """POST запрос"""
            url = f"{self.base_url}{endpoint}"
            headers = {"Content-Type": "application/json"}
            return self.session.post(url, json=data, headers=headers, **kwargs)
        
        def put(self, endpoint, data=None, **kwargs):
            """PUT запрос"""
            url = f"{self.base_url}{endpoint}"
            headers = {"Content-Type": "application/json"}
            return self.session.put(url, json=data, headers=headers, **kwargs)
        
        def delete(self, endpoint, **kwargs):
            """DELETE запрос"""
            url = f"{self.base_url}{endpoint}"
            return self.session.delete(url, **kwargs)
        
        def logout(self):
            """Выход из системы"""
            self.get("/logout")
            self.logged_in = False
    
    return SessionManager()

@pytest.fixture(scope="function")
def authenticated_session(session_manager):
    """Аутентифицированная сессия для тестов"""
    if not session_manager.logged_in:
        session_manager.login(*TEST_CREDENTIALS)
    yield session_manager
    # Очистка после теста не нужна, так как сессия переиспользуется

@pytest.fixture(scope="session")
def test_bot_data():
    """Тестовые данные для ботов"""
    return {
        "bot_name": "Test Bot",
        "telegram_token": "1234567890:ABCdefGHIjklMNOpqrsTUVwxyz12345678901234567890123456789012345",
        "openai_api_key": "sk-test1234567890abcdefghijklmnopqrstuvwxyz",
        "assistant_id": "asst_test1234567890abcdefghijklmnopqrstuvwxyz",
        "group_context_limit": 15,
        "enable_voice_responses": False,
        "enable_ai_responses": True,
        "marketplace": {
            "enabled": True,
            "title": "Test Bot",
            "description": "Test bot for testing",
            "category": "testing",
            "username": "@testbot",
            "tags": ["test", "demo"]
        }
    }

@pytest.fixture(scope="session")
def app_status():
    """Статус приложения"""
    def check_app():
        try:
            response = requests.get(f"{BASE_URL}/api/v2/system/health", timeout=5)
            # Приложение работает, если возвращает 401 (требует авторизацию) или 200 (авторизован)
            return response.status_code in [200, 401]
        except:
            return False
    
    return check_app

@pytest.fixture(scope="session", autouse=True)
def ensure_app_running(app_status):
    """Проверка, что приложение запущено"""
    if not app_status():
        pytest.skip("Приложение не запущено. Запустите приложение перед тестированием.")

# Новые фикстуры для профессионального тестирования

@pytest.fixture(scope="function")
def temp_config_file():
    """Временный файл конфигурации для тестов"""
    temp_dir = tempfile.mkdtemp()
    config_file = os.path.join(temp_dir, "test_bot_configs.json")
    
    # Создаем тестовую конфигурацию
    test_config = {
        "bots": {
            "1": {
                "id": 1,
                "config": {
                    "bot_name": "Test Bot 1",
                    "telegram_token": "1234567890:ABCdefGHIjklMNOpqrsTUVwxyz12345678901234567890123456789012345",
                    "openai_api_key": "sk-test1234567890abcdefghijklmnopqrstuvwxyz",
                    "assistant_id": "asst_test1234567890abcdefghijklmnopqrstuvwxyz",
                    "enable_ai_responses": True,
                    "enable_voice_responses": False,
                    "group_context_limit": 15
                },
                "status": "stopped"
            }
        }
    }
    
    with open(config_file, 'w') as f:
        json.dump(test_config, f)
    
    yield config_file
    
    # Очистка
    shutil.rmtree(temp_dir)

@pytest.fixture(scope="function")
def mock_telegram_bot():
    """Мок для Telegram бота"""
    mock_bot = Mock()
    mock_bot.get_me.return_value = Mock(username="test_bot")
    mock_bot.get_file.return_value = Mock(file_path="test_file_path")
    mock_bot.download_file.return_value = None
    return mock_bot

@pytest.fixture(scope="function")
def mock_openai_client():
    """Мок для OpenAI клиента"""
    mock_client = Mock()
    mock_client.audio.transcriptions.create.return_value = Mock(text="Test transcription")
    mock_client.audio.speech.create.return_value = Mock(content=b"test_audio_content")
    mock_client.beta.assistants.messages.create.return_value = Mock(content=[Mock(text=Mock(value="Test response"))])
    return mock_client

@pytest.fixture(scope="function")
def performance_monitor():
    """Монитор производительности для тестов"""
    class PerformanceMonitor:
        def __init__(self):
            self.start_time = None
            self.end_time = None
        
        def start(self):
            self.start_time = time.time()
        
        def stop(self):
            self.end_time = time.time()
        
        def get_duration(self):
            if self.start_time and self.end_time:
                return self.end_time - self.start_time
            return 0
        
        def is_within_limit(self, limit_seconds):
            return self.get_duration() <= limit_seconds
    
    return PerformanceMonitor()

@pytest.fixture(scope="function")
def test_logger():
    """Логгер для тестов"""
    class TestLogger:
        def __init__(self):
            self.messages = []
        
        def info(self, message):
            self.messages.append(f"INFO: {message}")
            print(f"INFO: {message}")
        
        def error(self, message):
            self.messages.append(f"ERROR: {message}")
            print(f"ERROR: {message}")
        
        def warning(self, message):
            self.messages.append(f"WARNING: {message}")
            print(f"WARNING: {message}")
        
        def success(self, message):
            self.messages.append(f"SUCCESS: {message}")
            print(f"SUCCESS: {message}")
        
        def get_messages(self):
            return self.messages
    
    return TestLogger()

@pytest.fixture(scope="function")
def test_helper():
    """Вспомогательные функции для тестов"""
    class TestHelper:
        @staticmethod
        def create_test_bot_data(bot_id=1, **kwargs):
            """Создание тестовых данных бота"""
            default_data = {
                "bot_name": f"Test Bot {bot_id}",
                "telegram_token": f"123456789{bot_id}:ABCdefGHIjklMNOpqrsTUVwxyz",
                "openai_api_key": "sk-test1234567890abcdefghijklmnopqrstuvwxyz",
                "assistant_id": f"asst_test{bot_id}",
                "enable_ai_responses": True,
                "enable_voice_responses": False,
                "group_context_limit": 15
            }
            default_data.update(kwargs)
            return default_data
        
        @staticmethod
        def assert_response_structure(response, required_fields=None):
            """Проверка структуры ответа"""
            assert response.status_code in [200, 201, 204], f"Неожиданный статус: {response.status_code}"
            
            if response.content:
                data = response.json()
                assert isinstance(data, dict), "Ответ должен быть объектом"
                
                if required_fields:
                    for field in required_fields:
                        assert field in data, f"Поле '{field}' отсутствует в ответе"
        
        @staticmethod
        def wait_for_condition(condition_func, timeout=10, interval=0.5):
            """Ожидание выполнения условия"""
            start_time = time.time()
            while time.time() - start_time < timeout:
                if condition_func():
                    return True
                time.sleep(interval)
            return False
    
    return TestHelper()

@pytest.fixture(scope="function")
def assertion_helper():
    """Помощник для проверок"""
    class AssertionHelper:
        @staticmethod
        def assert_bot_status(response, expected_status):
            """Проверка статуса бота"""
            data = response.json()
            assert data.get("status") == expected_status, f"Ожидался статус {expected_status}, получен {data.get('status')}"
        
        @staticmethod
        def assert_error_response(response, expected_status=400):
            """Проверка ответа с ошибкой"""
            assert response.status_code == expected_status, f"Ожидался статус {expected_status}, получен {response.status_code}"
            data = response.json()
            assert "error" in data, "Ответ должен содержать поле 'error'"
        
        @staticmethod
        def assert_success_response(response, expected_status=200):
            """Проверка успешного ответа"""
            assert response.status_code == expected_status, f"Ожидался статус {expected_status}, получен {response.status_code}"
            data = response.json()
            assert data.get("success", True), "Ответ должен быть успешным"
    
    return AssertionHelper()

@pytest.fixture(scope="function")
def test_data_generator():
    """Генератор тестовых данных"""
    class TestDataGenerator:
        @staticmethod
        def generate_bot_configs(count=5):
            """Генерация конфигураций ботов"""
            configs = {}
            for i in range(1, count + 1):
                configs[str(i)] = {
                    "id": i,
                    "config": {
                        "bot_name": f"Test Bot {i}",
                        "telegram_token": f"123456789{i}:ABCdefGHIjklMNOpqrsTUVwxyz",
                        "openai_api_key": f"sk-test{i}",
                        "assistant_id": f"asst_test{i}",
                        "enable_ai_responses": i % 2 == 0,
                        "enable_voice_responses": i % 3 == 0,
                        "group_context_limit": 10 + i
                    },
                    "status": "stopped" if i % 2 == 0 else "running"
                }
            return configs
        
        @staticmethod
        def generate_marketplace_data(count=10):
            """Генерация данных маркетплейса"""
            categories = ["ai", "business", "entertainment", "utility", "other"]
            data = []
            
            for i in range(count):
                data.append({
                    "id": i + 1,
                    "title": f"Test Bot {i + 1}",
                    "description": f"Description for bot {i + 1}",
                    "category": categories[i % len(categories)],
                    "username": f"@testbot{i + 1}",
                    "featured": i % 3 == 0,
                    "rating": round((i % 5) * 0.5 + 1, 1),
                    "total_users": (i + 1) * 100
                })
            
            return data
    
    return TestDataGenerator()

def pytest_configure(config):
    """Конфигурация pytest"""
    # Добавляем маркеры
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "e2e: End-to-end tests")
    config.addinivalue_line("markers", "api: API tests")
    config.addinivalue_line("markers", "ui: UI tests")
    config.addinivalue_line("markers", "performance: Performance tests")
    config.addinivalue_line("markers", "security: Security tests")
    config.addinivalue_line("markers", "smoke: Smoke tests")
    config.addinivalue_line("markers", "regression: Regression tests")
    config.addinivalue_line("markers", "slow: Slow running tests")

def pytest_collection_modifyitems(config, items):
    """Модификация коллекции тестов"""
    for item in items:
        # Автоматически добавляем маркеры на основе имени файла
        if "unit" in item.nodeid:
            item.add_marker(pytest.mark.unit)
        elif "integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)
        elif "e2e" in item.nodeid:
            item.add_marker(pytest.mark.e2e)
        elif "api" in item.nodeid:
            item.add_marker(pytest.mark.api)
        elif "ui" in item.nodeid:
            item.add_marker(pytest.mark.ui)
        elif "performance" in item.nodeid:
            item.add_marker(pytest.mark.performance)
        elif "security" in item.nodeid:
            item.add_marker(pytest.mark.security)
        elif "smoke" in item.nodeid:
            item.add_marker(pytest.mark.smoke)
        elif "regression" in item.nodeid:
            item.add_marker(pytest.mark.regression)
