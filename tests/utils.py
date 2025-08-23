"""
Утилиты для тестирования
"""

import json
import logging
import time
from typing import Any

import requests

# Настройка логирования для тестов
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
    handlers=[logging.FileHandler("tests/test.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


class TestLogger:
    """Логгер для тестов"""

    @staticmethod
    def info(message: str):
        """Информационное сообщение"""
        logger.info(f"ℹ️ {message}")

    @staticmethod
    def success(message: str):
        """Успешное выполнение"""
        logger.info(f"✅ {message}")

    @staticmethod
    def error(message: str):
        """Ошибка"""
        logger.error(f"❌ {message}")

    @staticmethod
    def warning(message: str):
        """Предупреждение"""
        logger.warning(f"⚠️ {message}")

    @staticmethod
    def debug(message: str):
        """Отладочная информация"""
        logger.debug(f"🔍 {message}")


class TestHelper:
    """Помощник для тестирования"""

    @staticmethod
    def wait_for_element(condition_func, timeout: int = 10, interval: float = 0.5):
        """Ожидание выполнения условия"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            if condition_func():
                return True
            time.sleep(interval)
        return False

    @staticmethod
    def retry_request(request_func, max_attempts: int = 3, delay: float = 1.0):
        """Повторные попытки запроса"""
        for attempt in range(max_attempts):
            try:
                response = request_func()
                if response.status_code < 500:  # Не повторяем для клиентских ошибок
                    return response
            except Exception as e:
                TestLogger.warning(f"Попытка {attempt + 1} не удалась: {e}")

            if attempt < max_attempts - 1:
                time.sleep(delay)

        return None

    @staticmethod
    def validate_response(response: requests.Response, expected_status: int = 200):
        """Валидация ответа"""
        if response.status_code != expected_status:
            TestLogger.error(
                f"Неожиданный статус: {response.status_code}, ожидался: {expected_status}"
            )
            return False

        try:
            response.json()  # Проверяем, что ответ - валидный JSON
            return True
        except json.JSONDecodeError:
            TestLogger.error("Ответ не является валидным JSON")
            return False

    @staticmethod
    def extract_bot_id_from_response(response: requests.Response) -> int | None:
        """Извлечение ID бота из ответа"""
        try:
            data = response.json()
            if isinstance(data, dict):
                # Пробуем разные варианты структуры ответа
                bot_id = data.get("bot_id") or data.get("data", {}).get("bot_id") or data.get("id")
                return int(bot_id) if bot_id else None
        except (json.JSONDecodeError, ValueError, TypeError):
            pass
        return None


class PerformanceMonitor:
    """Мониторинг производительности"""

    def __init__(self):
        self.start_time = None
        self.end_time = None

    def start(self):
        """Начало измерения"""
        self.start_time = time.time()

    def stop(self):
        """Окончание измерения"""
        self.end_time = time.time()

    def get_duration(self) -> float:
        """Получение длительности в секундах"""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return 0.0

    def is_within_limit(self, limit: float) -> bool:
        """Проверка, что время выполнения в пределах лимита"""
        duration = self.get_duration()
        return duration <= limit


class TestDataGenerator:
    """Генератор тестовых данных"""

    @staticmethod
    def generate_bot_config(bot_name: str = None) -> dict[str, Any]:
        """Генерация конфигурации бота"""
        if not bot_name:
            bot_name = f"TestBot_{int(time.time())}"

        return {
            "bot_name": bot_name,
            "telegram_token": f"1234567890:ABCdefGHIjklMNOpqrsTUVwxyz_{int(time.time())}",
            "openai_api_key": f"sk-test1234567890abcdefghijklmnopqrstuvwxyz_{int(time.time())}",
            "assistant_id": f"asst_test1234567890abcdefghijklmnopqrstuvwxyz_{int(time.time())}",
            "group_context_limit": 15,
            "enable_voice_responses": False,
            "enable_ai_responses": True,
            "marketplace": {
                "enabled": True,
                "title": bot_name,
                "description": f"Test bot {bot_name} for testing",
                "category": "testing",
                "username": f"@{bot_name.lower()}",
                "tags": ["test", "demo", "automated"],
            },
        }

    @staticmethod
    def generate_marketplace_data() -> dict[str, Any]:
        """Генерация данных для маркетплейса"""
        timestamp = int(time.time())
        return {
            "enabled": True,
            "title": f"Test Bot {timestamp}",
            "description": f"Automated test bot {timestamp}",
            "category": "testing",
            "username": f"@testbot{timestamp}",
            "website": f"https://test{timestamp}.com",
            "image_url": f"https://example.com/bot{timestamp}.jpg",
            "tags": ["test", "automated", "demo"],
            "featured": False,
            "rating": 4.5,
            "total_users": 100,
        }


class AssertionHelper:
    """Помощник для проверок"""

    @staticmethod
    def assert_response_structure(response: requests.Response, required_fields: list):
        """Проверка структуры ответа"""
        try:
            data = response.json()
            for field in required_fields:
                assert field in data, f"Поле '{field}' отсутствует в ответе"
        except json.JSONDecodeError:
            assert False, "Ответ не является валидным JSON"

    @staticmethod
    def assert_bot_status(response: requests.Response, expected_status: str):
        """Проверка статуса бота"""
        try:
            data = response.json()
            actual_status = data.get("status", data.get("data", {}).get("status"))
            assert (
                actual_status == expected_status
            ), f"Статус бота: {actual_status}, ожидался: {expected_status}"
        except json.JSONDecodeError:
            assert False, "Ответ не является валидным JSON"

    @staticmethod
    def assert_marketplace_bot(response: requests.Response, expected_enabled: bool = True):
        """Проверка бота в маркетплейсе"""
        try:
            data = response.json()
            marketplace_data = data.get("marketplace", {})
            actual_enabled = marketplace_data.get("enabled", False)
            assert (
                actual_enabled == expected_enabled
            ), f"Маркетплейс: {actual_enabled}, ожидался: {expected_enabled}"
        except json.JSONDecodeError:
            assert False, "Ответ не является валидным JSON"


# Глобальные экземпляры для использования в тестах
test_logger = TestLogger()
test_helper = TestHelper()
performance_monitor = PerformanceMonitor()
test_data_generator = TestDataGenerator()
assertion_helper = AssertionHelper()
