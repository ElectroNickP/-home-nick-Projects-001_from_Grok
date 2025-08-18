"""
Тесты системы авторизации
"""

import pytest
import requests
from tests.utils import test_logger, test_helper, assertion_helper

@pytest.mark.api
@pytest.mark.smoke
class TestAuthentication:
    """Тесты авторизации"""
    
    def test_login_with_valid_credentials(self, authenticated_session):
        """Тест входа с валидными учетными данными"""
        test_logger.info("Тестирование входа с валидными учетными данными")
        
        # Проверяем, что сессия аутентифицирована
        response = authenticated_session.get("/api/v2/system/health")
        
        assert response.status_code == 200, f"Ожидался статус 200, получен {response.status_code}"
        test_logger.success("Вход с валидными учетными данными прошел успешно")
    
    def test_login_with_invalid_credentials(self, session_manager):
        """Тест входа с невалидными учетными данными"""
        test_logger.info("Тестирование входа с невалидными учетными данными")
        
        # Пытаемся войти с неверными данными
        login_data = {"username": "invalid", "password": "wrong"}
        response = session_manager.post("/api/login", data=login_data)
        
        assert response.status_code == 401, f"Ожидался статус 401, получен {response.status_code}"
        test_logger.success("Вход с невалидными учетными данными правильно отклонен")
    
    def test_access_protected_endpoint_without_auth(self, session_manager):
        """Тест доступа к защищенному endpoint без авторизации"""
        test_logger.info("Тестирование доступа к защищенному endpoint без авторизации")
        
        # Пытаемся получить доступ к защищенному endpoint
        response = session_manager.get("/api/v2/system/health")
        
        assert response.status_code == 401, f"Ожидался статус 401, получен {response.status_code}"
        test_logger.success("Доступ к защищенному endpoint без авторизации правильно отклонен")
    
    def test_access_public_endpoint_without_auth(self, session_manager):
        """Тест доступа к публичному endpoint без авторизации"""
        test_logger.info("Тестирование доступа к публичному endpoint без авторизации")
        
        # Пытаемся получить доступ к публичному endpoint
        response = session_manager.get("/api/marketplace/bots")
        
        assert response.status_code == 200, f"Ожидался статус 200, получен {response.status_code}"
        test_logger.success("Доступ к публичному endpoint без авторизации разрешен")
    
    def test_logout_functionality(self, authenticated_session):
        """Тест функциональности выхода"""
        test_logger.info("Тестирование функциональности выхода")
        
        # Выходим из системы
        response = authenticated_session.get("/logout")
        
        assert response.status_code == 200, f"Ожидался статус 200, получен {response.status_code}"
        
        # Проверяем, что после выхода доступ к защищенным endpoint закрыт
        response = authenticated_session.get("/api/v2/system/health")
        
        assert response.status_code == 401, f"После выхода ожидался статус 401, получен {response.status_code}"
        test_logger.success("Функциональность выхода работает корректно")
    
    def test_session_persistence(self, authenticated_session):
        """Тест сохранения сессии"""
        test_logger.info("Тестирование сохранения сессии")
        
        # Делаем несколько запросов подряд
        endpoints = [
            "/api/v2/system/health",
            "/api/v2/system/info",
            "/api/v2/system/stats"
        ]
        
        for endpoint in endpoints:
            response = authenticated_session.get(endpoint)
            assert response.status_code == 200, f"Endpoint {endpoint} вернул статус {response.status_code}"
        
        test_logger.success("Сессия сохраняется между запросами")
    
    def test_login_api_response_structure(self, session_manager):
        """Тест структуры ответа API авторизации"""
        test_logger.info("Тестирование структуры ответа API авторизации")
        
        # Входим в систему
        login_data = {"username": "admin", "password": "securepassword123"}
        response = session_manager.post("/api/login", data=login_data)
        
        assert response.status_code == 200, f"Ожидался статус 200, получен {response.status_code}"
        
        # Проверяем структуру ответа
        data = response.json()
        required_fields = ["success", "message"]
        
        for field in required_fields:
            assert field in data, f"Поле '{field}' отсутствует в ответе"
        
        assert data["success"] == True, "Поле success должно быть True"
        test_logger.success("Структура ответа API авторизации корректна")
    
    def test_unauthorized_api_response_structure(self, session_manager):
        """Тест структуры ответа при неавторизованном доступе"""
        test_logger.info("Тестирование структуры ответа при неавторизованном доступе")
        
        # Пытаемся получить доступ к защищенному endpoint
        response = session_manager.get("/api/v2/system/health")
        
        assert response.status_code == 401, f"Ожидался статус 401, получен {response.status_code}"
        
        # Проверяем структуру ответа об ошибке
        data = response.json()
        required_fields = ["error", "message"]
        
        for field in required_fields:
            assert field in data, f"Поле '{field}' отсутствует в ответе об ошибке"
        
        assert data["error"] == "Unauthorized", "Тип ошибки должен быть 'Unauthorized'"
        test_logger.success("Структура ответа при неавторизованном доступе корректна")
