"""
Тесты системных API endpoints
"""


import pytest

from tests.utils import performance_monitor, test_logger


@pytest.mark.api
@pytest.mark.smoke
class TestSystemEndpoints:
    """Тесты системных endpoints"""

    def test_health_check_endpoint(self, authenticated_session):
        """Тест endpoint проверки здоровья системы"""
        test_logger.info("Тестирование endpoint проверки здоровья системы")

        performance_monitor.start()
        response = authenticated_session.get("/api/v2/system/health")
        performance_monitor.stop()

        assert response.status_code == 200, f"Ожидался статус 200, получен {response.status_code}"
        assert performance_monitor.is_within_limit(
            5.0
        ), f"Время ответа превышает лимит: {performance_monitor.get_duration()}s"

        # Проверяем структуру ответа
        data = response.json()
        required_fields = ["status", "timestamp", "version"]

        for field in required_fields:
            assert field in data, f"Поле '{field}' отсутствует в ответе"

        assert data["status"] == "healthy", "Статус системы должен быть 'healthy'"
        test_logger.success("Endpoint проверки здоровья системы работает корректно")

    def test_system_info_endpoint(self, authenticated_session):
        """Тест endpoint информации о системе"""
        test_logger.info("Тестирование endpoint информации о системе")

        performance_monitor.start()
        response = authenticated_session.get("/api/v2/system/info")
        performance_monitor.stop()

        assert response.status_code == 200, f"Ожидался статус 200, получен {response.status_code}"
        assert performance_monitor.is_within_limit(
            5.0
        ), f"Время ответа превышает лимит: {performance_monitor.get_duration()}s"

        # Проверяем структуру ответа
        data = response.json()
        required_fields = ["system_info", "bot_manager_info", "version_info"]

        for field in required_fields:
            assert field in data, f"Поле '{field}' отсутствует в ответе"

        # Проверяем подполя
        system_info = data["system_info"]
        assert "platform" in system_info, "Информация о платформе отсутствует"
        assert "python_version" in system_info, "Версия Python отсутствует"

        test_logger.success("Endpoint информации о системе работает корректно")

    def test_system_stats_endpoint(self, authenticated_session):
        """Тест endpoint статистики системы"""
        test_logger.info("Тестирование endpoint статистики системы")

        performance_monitor.start()
        response = authenticated_session.get("/api/v2/system/stats")
        performance_monitor.stop()

        assert response.status_code == 200, f"Ожидался статус 200, получен {response.status_code}"
        assert performance_monitor.is_within_limit(
            5.0
        ), f"Время ответа превышает лимит: {performance_monitor.get_duration()}s"

        # Проверяем структуру ответа
        data = response.json()
        required_fields = ["bot_stats", "system_stats", "performance_stats"]

        for field in required_fields:
            assert field in data, f"Поле '{field}' отсутствует в ответе"

        # Проверяем статистику ботов
        bot_stats = data["bot_stats"]
        assert "total_bots" in bot_stats, "Общее количество ботов отсутствует"
        assert "running_bots" in bot_stats, "Количество работающих ботов отсутствует"
        assert "stopped_bots" in bot_stats, "Количество остановленных ботов отсутствует"

        # Проверяем системную статистику
        system_stats = data["system_stats"]
        assert "cpu_usage" in system_stats, "Использование CPU отсутствует"
        assert "memory_usage" in system_stats, "Использование памяти отсутствует"

        test_logger.success("Endpoint статистики системы работает корректно")

    def test_api_docs_endpoint(self, authenticated_session):
        """Тест endpoint документации API"""
        test_logger.info("Тестирование endpoint документации API")

        performance_monitor.start()
        response = authenticated_session.get("/api/v2/docs")
        performance_monitor.stop()

        assert response.status_code == 200, f"Ожидался статус 200, получен {response.status_code}"
        assert performance_monitor.is_within_limit(
            10.0
        ), f"Время ответа превышает лимит: {performance_monitor.get_duration()}s"

        # Проверяем, что возвращается HTML страница
        content_type = response.headers.get("content-type", "")
        assert "text/html" in content_type, f"Ожидался HTML, получен {content_type}"

        # Проверяем наличие ключевых элементов документации
        content = response.text
        assert (
            "API Documentation" in content or "docs" in content.lower()
        ), "Документация API не найдена"

        test_logger.success("Endpoint документации API работает корректно")

    def test_version_endpoint(self, authenticated_session):
        """Тест endpoint версии"""
        test_logger.info("Тестирование endpoint версии")

        performance_monitor.start()
        response = authenticated_session.get("/api/version")
        performance_monitor.stop()

        assert response.status_code == 200, f"Ожидался статус 200, получен {response.status_code}"
        assert performance_monitor.is_within_limit(
            3.0
        ), f"Время ответа превышает лимит: {performance_monitor.get_duration()}s"

        # Проверяем структуру ответа
        data = response.json()
        required_fields = ["version", "build_date", "commit_hash"]

        for field in required_fields:
            assert field in data, f"Поле '{field}' отсутствует в ответе"

        assert data["version"] is not None, "Версия не должна быть пустой"
        test_logger.success("Endpoint версии работает корректно")

    def test_check_updates_endpoint(self, authenticated_session):
        """Тест endpoint проверки обновлений"""
        test_logger.info("Тестирование endpoint проверки обновлений")

        performance_monitor.start()
        response = authenticated_session.get("/api/check-updates")
        performance_monitor.stop()

        assert response.status_code == 200, f"Ожидался статус 200, получен {response.status_code}"
        assert performance_monitor.is_within_limit(
            15.0
        ), f"Время ответа превышает лимит: {performance_monitor.get_duration()}s"

        # Проверяем структуру ответа
        data = response.json()
        required_fields = ["has_updates", "current_version", "latest_version"]

        for field in required_fields:
            assert field in data, f"Поле '{field}' отсутствует в ответе"

        assert isinstance(data["has_updates"], bool), "has_updates должно быть boolean"
        test_logger.success("Endpoint проверки обновлений работает корректно")

    def test_update_backups_endpoint(self, authenticated_session):
        """Тест endpoint резервных копий"""
        test_logger.info("Тестирование endpoint резервных копий")

        performance_monitor.start()
        response = authenticated_session.get("/api/update/backups")
        performance_monitor.stop()

        assert response.status_code == 200, f"Ожидался статус 200, получен {response.status_code}"
        assert performance_monitor.is_within_limit(
            10.0
        ), f"Время ответа превышает лимит: {performance_monitor.get_duration()}s"

        # Проверяем структуру ответа
        data = response.json()
        assert "backups" in data, "Поле 'backups' отсутствует в ответе"

        # Проверяем, что backups - это список
        assert isinstance(data["backups"], list), "backups должно быть списком"

        test_logger.success("Endpoint резервных копий работает корректно")

    def test_endpoints_response_time(self, authenticated_session):
        """Тест времени ответа всех системных endpoints"""
        test_logger.info("Тестирование времени ответа системных endpoints")

        endpoints = [
            ("/api/v2/system/health", 3.0),
            ("/api/v2/system/info", 5.0),
            ("/api/v2/system/stats", 5.0),
            ("/api/version", 3.0),
            ("/api/check-updates", 15.0),
            ("/api/update/backups", 10.0),
        ]

        for endpoint, max_time in endpoints:
            performance_monitor.start()
            response = authenticated_session.get(endpoint)
            performance_monitor.stop()

            duration = performance_monitor.get_duration()
            assert (
                response.status_code == 200
            ), f"Endpoint {endpoint} вернул статус {response.status_code}"
            assert (
                duration <= max_time
            ), f"Endpoint {endpoint} превысил лимит времени: {duration}s > {max_time}s"

            test_logger.info(f"✅ {endpoint}: {duration:.2f}s")

        test_logger.success("Все системные endpoints отвечают в пределах лимитов времени")

    def test_endpoints_error_handling(self, authenticated_session):
        """Тест обработки ошибок системных endpoints"""
        test_logger.info("Тестирование обработки ошибок системных endpoints")

        # Тестируем несуществующий endpoint
        response = authenticated_session.get("/api/v2/system/nonexistent")

        assert response.status_code == 404, f"Ожидался статус 404, получен {response.status_code}"

        # Проверяем структуру ответа об ошибке
        data = response.json()
        assert "error" in data, "Поле 'error' отсутствует в ответе об ошибке"

        test_logger.success("Обработка ошибок системных endpoints работает корректно")
