"""
Тесты управления ботами через API
"""

import pytest
import requests
import json
import time
from tests.utils import test_logger, test_helper, assertion_helper, performance_monitor, test_data_generator

@pytest.mark.api
@pytest.mark.integration
class TestBotManagement:
    """Тесты управления ботами"""
    
    def test_get_all_bots(self, authenticated_session):
        """Тест получения списка всех ботов"""
        test_logger.info("Тестирование получения списка всех ботов")
        
        performance_monitor.start()
        response = authenticated_session.get("/api/v2/bots")
        performance_monitor.stop()
        
        assert response.status_code == 200, f"Ожидался статус 200, получен {response.status_code}"
        assert performance_monitor.is_within_limit(5.0), f"Время ответа превышает лимит: {performance_monitor.get_duration()}s"
        
        # Проверяем структуру ответа
        data = response.json()
        assert "data" in data, "Поле 'data' отсутствует в ответе"
        assert isinstance(data["data"], list), "data должно быть списком"
        
        test_logger.success(f"Получен список ботов: {len(data['data'])} ботов")
    
    def test_create_bot(self, authenticated_session):
        """Тест создания нового бота"""
        test_logger.info("Тестирование создания нового бота")
        
        # Генерируем тестовые данные
        bot_data = test_data_generator.generate_bot_config("TestBot_Create")
        
        performance_monitor.start()
        response = authenticated_session.post("/api/v2/bots", data=bot_data)
        performance_monitor.stop()
        
        assert response.status_code == 201, f"Ожидался статус 201, получен {response.status_code}"
        assert performance_monitor.is_within_limit(10.0), f"Время ответа превышает лимит: {performance_monitor.get_duration()}s"
        
        # Проверяем структуру ответа
        data = response.json()
        required_fields = ["success", "message", "data"]
        
        for field in required_fields:
            assert field in data, f"Поле '{field}' отсутствует в ответе"
        
        assert data["success"] == True, "Создание бота должно быть успешным"
        
        # Извлекаем ID созданного бота
        bot_id = test_helper.extract_bot_id_from_response(response)
        assert bot_id is not None, "ID бота не найден в ответе"
        
        test_logger.success(f"Бот успешно создан с ID: {bot_id}")
        return bot_id
    
    def test_get_bot_by_id(self, authenticated_session):
        """Тест получения бота по ID"""
        test_logger.info("Тестирование получения бота по ID")
        
        # Сначала получаем список ботов
        response = authenticated_session.get("/api/v2/bots")
        assert response.status_code == 200
        
        data = response.json()
        if not data["data"]:
            pytest.skip("Нет ботов для тестирования")
        
        bot_id = data["data"][0]["id"]
        
        performance_monitor.start()
        response = authenticated_session.get(f"/api/v2/bots/{bot_id}")
        performance_monitor.stop()
        
        assert response.status_code == 200, f"Ожидался статус 200, получен {response.status_code}"
        assert performance_monitor.is_within_limit(3.0), f"Время ответа превышает лимит: {performance_monitor.get_duration()}s"
        
        # Проверяем структуру ответа
        data = response.json()
        assert "id" in data, "Поле 'id' отсутствует в ответе"
        assert data["id"] == bot_id, "ID бота не совпадает"
        
        test_logger.success(f"Бот с ID {bot_id} успешно получен")
    
    def test_update_bot(self, authenticated_session):
        """Тест обновления бота"""
        test_logger.info("Тестирование обновления бота")
        
        # Сначала получаем список ботов
        response = authenticated_session.get("/api/v2/bots")
        assert response.status_code == 200
        
        data = response.json()
        if not data["data"]:
            pytest.skip("Нет ботов для тестирования")
        
        bot_id = data["data"][0]["id"]
        
        # Данные для обновления
        update_data = {
            "bot_name": "Updated Test Bot",
            "group_context_limit": 20,
            "enable_voice_responses": True,
            "marketplace": {
                "enabled": True,
                "title": "Updated Test Bot",
                "description": "Updated test bot description",
                "category": "testing",
                "username": "@updatedtestbot",
                "tags": ["updated", "test"]
            }
        }
        
        performance_monitor.start()
        response = authenticated_session.put(f"/api/v2/bots/{bot_id}", data=update_data)
        performance_monitor.stop()
        
        assert response.status_code == 200, f"Ожидался статус 200, получен {response.status_code}"
        assert performance_monitor.is_within_limit(5.0), f"Время ответа превышает лимит: {performance_monitor.get_duration()}s"
        
        # Проверяем, что обновление применилось
        response = authenticated_session.get(f"/api/v2/bots/{bot_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["config"]["bot_name"] == "Updated Test Bot", "Имя бота не обновилось"
        assert data["config"]["group_context_limit"] == 20, "Лимит контекста не обновился"
        
        test_logger.success(f"Бот с ID {bot_id} успешно обновлен")
    
    def test_start_bot(self, authenticated_session):
        """Тест запуска бота"""
        test_logger.info("Тестирование запуска бота")
        
        # Сначала получаем список ботов
        response = authenticated_session.get("/api/v2/bots")
        assert response.status_code == 200
        
        data = response.json()
        if not data["data"]:
            pytest.skip("Нет ботов для тестирования")
        
        bot_id = data["data"][0]["id"]
        
        performance_monitor.start()
        response = authenticated_session.post(f"/api/v2/bots/{bot_id}/start")
        performance_monitor.stop()
        
        assert response.status_code == 200, f"Ожидался статус 200, получен {response.status_code}"
        assert performance_monitor.is_within_limit(10.0), f"Время ответа превышает лимит: {performance_monitor.get_duration()}s"
        
        # Проверяем, что бот запустился
        time.sleep(2)  # Даем время на запуск
        response = authenticated_session.get(f"/api/v2/bots/{bot_id}/status")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "running", f"Бот должен быть запущен, текущий статус: {data['status']}"
        
        test_logger.success(f"Бот с ID {bot_id} успешно запущен")
    
    def test_stop_bot(self, authenticated_session):
        """Тест остановки бота"""
        test_logger.info("Тестирование остановки бота")
        
        # Сначала получаем список ботов
        response = authenticated_session.get("/api/v2/bots")
        assert response.status_code == 200
        
        data = response.json()
        if not data["data"]:
            pytest.skip("Нет ботов для тестирования")
        
        bot_id = data["data"][0]["id"]
        
        performance_monitor.start()
        response = authenticated_session.post(f"/api/v2/bots/{bot_id}/stop")
        performance_monitor.stop()
        
        assert response.status_code == 200, f"Ожидался статус 200, получен {response.status_code}"
        assert performance_monitor.is_within_limit(10.0), f"Время ответа превышает лимит: {performance_monitor.get_duration()}s"
        
        # Проверяем, что бот остановился
        time.sleep(2)  # Даем время на остановку
        response = authenticated_session.get(f"/api/v2/bots/{bot_id}/status")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "stopped", f"Бот должен быть остановлен, текущий статус: {data['status']}"
        
        test_logger.success(f"Бот с ID {bot_id} успешно остановлен")
    
    def test_restart_bot(self, authenticated_session):
        """Тест перезапуска бота"""
        test_logger.info("Тестирование перезапуска бота")
        
        # Сначала получаем список ботов
        response = authenticated_session.get("/api/v2/bots")
        assert response.status_code == 200
        
        data = response.json()
        if not data["data"]:
            pytest.skip("Нет ботов для тестирования")
        
        bot_id = data["data"][0]["id"]
        
        performance_monitor.start()
        response = authenticated_session.post(f"/api/v2/bots/{bot_id}/restart")
        performance_monitor.stop()
        
        assert response.status_code == 200, f"Ожидался статус 200, получен {response.status_code}"
        assert performance_monitor.is_within_limit(15.0), f"Время ответа превышает лимит: {performance_monitor.get_duration()}s"
        
        # Проверяем, что бот перезапустился
        time.sleep(3)  # Даем время на перезапуск
        response = authenticated_session.get(f"/api/v2/bots/{bot_id}/status")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] in ["running", "stopped"], f"Неожиданный статус бота: {data['status']}"
        
        test_logger.success(f"Бот с ID {bot_id} успешно перезапущен")
    
    def test_get_bot_status(self, authenticated_session):
        """Тест получения статуса бота"""
        test_logger.info("Тестирование получения статуса бота")
        
        # Сначала получаем список ботов
        response = authenticated_session.get("/api/v2/bots")
        assert response.status_code == 200
        
        data = response.json()
        if not data["data"]:
            pytest.skip("Нет ботов для тестирования")
        
        bot_id = data["data"][0]["id"]
        
        performance_monitor.start()
        response = authenticated_session.get(f"/api/v2/bots/{bot_id}/status")
        performance_monitor.stop()
        
        assert response.status_code == 200, f"Ожидался статус 200, получен {response.status_code}"
        assert performance_monitor.is_within_limit(3.0), f"Время ответа превышает лимит: {performance_monitor.get_duration()}s"
        
        # Проверяем структуру ответа
        data = response.json()
        required_fields = ["id", "status", "config"]
        
        for field in required_fields:
            assert field in data, f"Поле '{field}' отсутствует в ответе"
        
        assert data["id"] == bot_id, "ID бота не совпадает"
        assert data["status"] in ["running", "stopped", "error"], f"Неожиданный статус: {data['status']}"
        
        test_logger.success(f"Статус бота с ID {bot_id} получен: {data['status']}")
    
    def test_delete_bot(self, authenticated_session):
        """Тест удаления бота"""
        test_logger.info("Тестирование удаления бота")
        
        # Сначала создаем тестового бота
        bot_data = test_data_generator.generate_bot_config("TestBot_Delete")
        response = authenticated_session.post("/api/v2/bots", data=bot_data)
        assert response.status_code == 201
        
        bot_id = test_helper.extract_bot_id_from_response(response)
        assert bot_id is not None
        
        # Удаляем бота
        performance_monitor.start()
        response = authenticated_session.delete(f"/api/v2/bots/{bot_id}")
        performance_monitor.stop()
        
        assert response.status_code == 200, f"Ожидался статус 200, получен {response.status_code}"
        assert performance_monitor.is_within_limit(5.0), f"Время ответа превышает лимит: {performance_monitor.get_duration()}s"
        
        # Проверяем, что бот удален
        response = authenticated_session.get(f"/api/v2/bots/{bot_id}")
        assert response.status_code == 404, "Бот должен быть удален"
        
        test_logger.success(f"Бот с ID {bot_id} успешно удален")
    
    def test_bot_management_error_handling(self, authenticated_session):
        """Тест обработки ошибок управления ботами"""
        test_logger.info("Тестирование обработки ошибок управления ботами")
        
        # Тестируем несуществующий бот
        non_existent_id = 99999
        
        # GET несуществующего бота
        response = authenticated_session.get(f"/api/v2/bots/{non_existent_id}")
        assert response.status_code == 404, f"Ожидался статус 404, получен {response.status_code}"
        
        # PUT несуществующего бота
        response = authenticated_session.put(f"/api/v2/bots/{non_existent_id}", data={})
        assert response.status_code == 404, f"Ожидался статус 404, получен {response.status_code}"
        
        # DELETE несуществующего бота
        response = authenticated_session.delete(f"/api/v2/bots/{non_existent_id}")
        assert response.status_code == 404, f"Ожидался статус 404, получен {response.status_code}"
        
        test_logger.success("Обработка ошибок управления ботами работает корректно")
    
    def test_bot_creation_validation(self, authenticated_session):
        """Тест валидации при создании бота"""
        test_logger.info("Тестирование валидации при создании бота")
        
        # Тестируем создание бота без обязательных полей
        invalid_data = {
            "bot_name": "Invalid Bot"
            # Отсутствуют обязательные поля
        }
        
        response = authenticated_session.post("/api/v2/bots", data=invalid_data)
        assert response.status_code == 400, f"Ожидался статус 400, получен {response.status_code}"
        
        # Проверяем сообщение об ошибке
        data = response.json()
        assert "error" in data, "Сообщение об ошибке отсутствует"
        
        test_logger.success("Валидация при создании бота работает корректно")
