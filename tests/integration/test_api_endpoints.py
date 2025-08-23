"""
Интеграционные тесты для API endpoints
"""


import pytest


@pytest.mark.integration
@pytest.mark.api
class TestAPIEndpoints:
    """Тесты для API endpoints"""

    def test_health_check_endpoint(self, authenticated_session, performance_monitor):
        """Тест endpoint проверки здоровья системы"""
        performance_monitor.start()
        response = authenticated_session.get("/api/v2/system/health")
        performance_monitor.stop()

        assert response.status_code == 200
        assert performance_monitor.is_within_limit(1.0)

        data = response.json()
        assert "data" in data
        assert "status" in data["data"]
        assert "checks" in data["data"]
        assert data["data"]["status"] in ["healthy", "unhealthy", "warning"]

    def test_system_info_endpoint(self, authenticated_session, performance_monitor):
        """Тест endpoint информации о системе"""
        performance_monitor.start()
        response = authenticated_session.get("/api/v2/system/info")
        performance_monitor.stop()

        assert response.status_code == 200
        assert performance_monitor.is_within_limit(2.0)

        data = response.json()
        assert "data" in data
        required_fields = ["system", "application", "bots"]
        for field in required_fields:
            assert field in data["data"]

    def test_system_stats_endpoint(self, authenticated_session, performance_monitor):
        """Тест endpoint статистики системы"""
        performance_monitor.start()
        response = authenticated_session.get("/api/v2/system/stats")
        performance_monitor.stop()

        assert response.status_code == 200
        assert performance_monitor.is_within_limit(2.0)

        data = response.json()
        assert "data" in data
        required_fields = ["application", "bots", "system"]
        for field in required_fields:
            assert field in data["data"]

    def test_get_bots_list(self, authenticated_session, performance_monitor):
        """Тест получения списка ботов"""
        performance_monitor.start()
        response = authenticated_session.get("/api/v2/bots")
        performance_monitor.stop()

        assert response.status_code == 200
        assert performance_monitor.is_within_limit(1.0)

        data = response.json()
        assert "data" in data
        assert "bots" in data["data"]
        assert isinstance(data["data"]["bots"], list)

    def test_create_bot_success(self, authenticated_session, test_bot_data, performance_monitor):
        """Тест успешного создания бота"""
        performance_monitor.start()
        response = authenticated_session.post("/api/v2/bots", data=test_bot_data)
        performance_monitor.stop()

        assert response.status_code == 201
        assert performance_monitor.is_within_limit(2.0)

        data = response.json()
        assert "data" in data
        assert "bot_id" in data["data"]
        assert "config" in data["data"]
        assert data["data"]["status"] == "stopped"

    def test_create_bot_invalid_data(self, authenticated_session, performance_monitor):
        """Тест создания бота с невалидными данными"""
        invalid_data = {
            "bot_name": "Test Bot"
            # Отсутствуют обязательные поля
        }

        performance_monitor.start()
        response = authenticated_session.post("/api/v2/bots", data=invalid_data)
        performance_monitor.stop()

        assert response.status_code == 400
        assert performance_monitor.is_within_limit(1.0)

        data = response.json()
        assert "error" in data

    def test_get_bot_details(self, authenticated_session, test_bot_data, performance_monitor):
        """Тест получения детальной информации о боте"""
        # Сначала создаем бота
        create_response = authenticated_session.post("/api/v2/bots", data=test_bot_data)
        assert create_response.status_code == 201
        bot_id = create_response.json()["data"]["bot_id"]

        performance_monitor.start()
        response = authenticated_session.get(f"/api/v2/bots/{bot_id}")
        performance_monitor.stop()

        assert response.status_code == 200
        assert performance_monitor.is_within_limit(1.0)

        data = response.json()
        assert "data" in data
        assert data["data"]["bot_id"] == bot_id
        assert "config" in data["data"]

    def test_get_bot_details_not_found(self, authenticated_session, performance_monitor):
        """Тест получения информации о несуществующем боте"""
        performance_monitor.start()
        response = authenticated_session.get("/api/v2/bots/99999")
        performance_monitor.stop()

        assert response.status_code == 404
        assert performance_monitor.is_within_limit(1.0)

        data = response.json()
        assert "error" in data

    def test_update_bot_success(self, authenticated_session, test_bot_data, performance_monitor):
        """Тест успешного обновления бота"""
        # Сначала создаем бота
        create_response = authenticated_session.post("/api/v2/bots", data=test_bot_data)
        assert create_response.status_code == 201
        bot_id = create_response.json()["data"]["bot_id"]

        # Обновляем бота
        update_data = {"bot_name": "Updated Test Bot", "group_context_limit": 20}

        performance_monitor.start()
        response = authenticated_session.put(f"/api/v2/bots/{bot_id}", data=update_data)
        performance_monitor.stop()

        assert response.status_code == 200
        assert performance_monitor.is_within_limit(1.0)

        data = response.json()
        assert "data" in data
        assert data["data"]["config"]["bot_name"] == "Updated Test Bot"
        assert data["data"]["config"]["group_context_limit"] == 20

    def test_update_bot_not_found(self, authenticated_session, performance_monitor):
        """Тест обновления несуществующего бота"""
        update_data = {"bot_name": "Updated Bot"}

        performance_monitor.start()
        response = authenticated_session.put("/api/v2/bots/99999", data=update_data)
        performance_monitor.stop()

        assert response.status_code == 404
        assert performance_monitor.is_within_limit(1.0)

        data = response.json()
        assert "error" in data

    def test_delete_bot_success(self, authenticated_session, test_bot_data, performance_monitor):
        """Тест успешного удаления бота"""
        # Сначала создаем бота
        create_response = authenticated_session.post("/api/v2/bots", data=test_bot_data)
        assert create_response.status_code == 201
        bot_id = create_response.json()["data"]["bot_id"]

        performance_monitor.start()
        response = authenticated_session.delete(f"/api/v2/bots/{bot_id}")
        performance_monitor.stop()

        assert response.status_code == 200
        assert performance_monitor.is_within_limit(2.0)

        data = response.json()
        assert "data" in data
        assert "bot_id" in data["data"]
        assert data["data"]["bot_id"] == bot_id

    def test_delete_bot_not_found(self, authenticated_session, performance_monitor):
        """Тест удаления несуществующего бота"""
        performance_monitor.start()
        response = authenticated_session.delete("/api/v2/bots/99999")
        performance_monitor.stop()

        assert response.status_code == 404
        assert performance_monitor.is_within_limit(1.0)

        data = response.json()
        assert "error" in data

    def test_start_bot_success(self, authenticated_session, test_bot_data, performance_monitor):
        """Тест успешного запуска бота"""
        # Сначала создаем бота
        create_response = authenticated_session.post("/api/v2/bots", data=test_bot_data)
        assert create_response.status_code == 201
        bot_id = create_response.json()["data"]["bot_id"]

        performance_monitor.start()
        response = authenticated_session.post(f"/api/v2/bots/{bot_id}/start")
        performance_monitor.stop()

        # Бот может не запуститься из-за невалидного токена, но API должен ответить
        assert response.status_code in [200, 400]
        assert performance_monitor.is_within_limit(5.0)

        if response.status_code == 200:
            data = response.json()
            assert "data" in data
            assert data["data"]["status"] == "running"

    def test_start_bot_not_found(self, authenticated_session, performance_monitor):
        """Тест запуска несуществующего бота"""
        performance_monitor.start()
        response = authenticated_session.post("/api/v2/bots/99999/start")
        performance_monitor.stop()

        assert response.status_code == 404
        assert performance_monitor.is_within_limit(1.0)

        data = response.json()
        assert "error" in data

    def test_stop_bot_success(self, authenticated_session, test_bot_data, performance_monitor):
        """Тест успешной остановки бота"""
        # Сначала создаем бота
        create_response = authenticated_session.post("/api/v2/bots", data=test_bot_data)
        assert create_response.status_code == 201
        bot_id = create_response.json()["data"]["bot_id"]

        performance_monitor.start()
        response = authenticated_session.post(f"/api/v2/bots/{bot_id}/stop")
        performance_monitor.stop()

        # Бот может не быть запущен, поэтому API может вернуть 400
        assert response.status_code in [200, 400]
        assert performance_monitor.is_within_limit(2.0)

        if response.status_code == 200:
            data = response.json()
            assert "data" in data
            assert data["data"]["status"] == "stopped"
        elif response.status_code == 400:
            data = response.json()
            assert "error" in data

    def test_stop_bot_not_found(self, authenticated_session, performance_monitor):
        """Тест остановки несуществующего бота"""
        performance_monitor.start()
        response = authenticated_session.post("/api/v2/bots/99999/stop")
        performance_monitor.stop()

        assert response.status_code == 404
        assert performance_monitor.is_within_limit(1.0)

        data = response.json()
        assert "error" in data

    def test_restart_bot_success(self, authenticated_session, test_bot_data, performance_monitor):
        """Тест успешного перезапуска бота"""
        # Сначала создаем бота
        create_response = authenticated_session.post("/api/v2/bots", data=test_bot_data)
        assert create_response.status_code == 201
        bot_id = create_response.json()["data"]["bot_id"]

        performance_monitor.start()
        response = authenticated_session.post(f"/api/v2/bots/{bot_id}/restart")
        performance_monitor.stop()

        # Бот может не перезапуститься из-за невалидного токена, но API должен ответить
        assert response.status_code == 200
        assert performance_monitor.is_within_limit(5.0)

        if response.status_code == 200:
            data = response.json()
            assert "data" in data
            assert "status" in data["data"]

    def test_restart_bot_not_found(self, authenticated_session, performance_monitor):
        """Тест перезапуска несуществующего бота"""
        performance_monitor.start()
        response = authenticated_session.post("/api/v2/bots/99999/restart")
        performance_monitor.stop()

        assert response.status_code == 404
        assert performance_monitor.is_within_limit(1.0)

        data = response.json()
        assert "error" in data

    def test_get_bot_status(self, authenticated_session, test_bot_data, performance_monitor):
        """Тест получения статуса бота"""
        # Сначала создаем бота
        create_response = authenticated_session.post("/api/v2/bots", data=test_bot_data)
        assert create_response.status_code == 201
        bot_id = create_response.json()["data"]["bot_id"]

        performance_monitor.start()
        response = authenticated_session.get(f"/api/v2/bots/{bot_id}/status")
        performance_monitor.stop()

        assert response.status_code == 200
        assert performance_monitor.is_within_limit(1.0)

        data = response.json()
        assert "data" in data
        assert "status" in data["data"]
        assert data["data"]["status"] in ["running", "stopped", "error"]

    def test_get_bot_status_not_found(self, authenticated_session, performance_monitor):
        """Тест получения статуса несуществующего бота"""
        performance_monitor.start()
        response = authenticated_session.get("/api/v2/bots/99999/status")
        performance_monitor.stop()

        assert response.status_code == 404
        assert performance_monitor.is_within_limit(1.0)

        data = response.json()
        assert "error" in data

    def test_api_login_success(self, session_manager, performance_monitor):
        """Тест успешной авторизации через API"""
        performance_monitor.start()
        response = session_manager.post(
            "/api/login", data={"username": "admin", "password": "securepassword123"}
        )
        performance_monitor.stop()

        assert response.status_code == 200
        assert performance_monitor.is_within_limit(1.0)

        data = response.json()
        assert data["success"] is True

    def test_api_login_invalid_credentials(self, session_manager, performance_monitor):
        """Тест авторизации с неверными учетными данными"""
        performance_monitor.start()
        response = session_manager.post(
            "/api/login", data={"username": "admin", "password": "wrongpassword"}
        )
        performance_monitor.stop()

        assert response.status_code == 401
        assert performance_monitor.is_within_limit(1.0)

        data = response.json()
        assert data["success"] is False

    def test_api_login_missing_data(self, session_manager, performance_monitor):
        """Тест авторизации с отсутствующими данными"""
        performance_monitor.start()
        response = session_manager.post("/api/login", data={})
        performance_monitor.stop()

        assert response.status_code == 401
        assert performance_monitor.is_within_limit(1.0)

    def test_unauthorized_access(self, session_manager, performance_monitor):
        """Тест доступа к защищенным endpoints без авторизации"""
        # Убеждаемся, что сессия не авторизована
        session_manager.logout()

        endpoints = [
            "/api/v2/system/health",
            "/api/v2/system/info",
            "/api/v2/system/stats",
            "/api/v2/bots",
        ]

        for endpoint in endpoints:
            performance_monitor.start()
            response = session_manager.get(endpoint)
            performance_monitor.stop()

            assert response.status_code == 401, f"Endpoint {endpoint} не защищен авторизацией"
            assert performance_monitor.is_within_limit(1.0)

    def test_api_documentation_endpoint(self, authenticated_session, performance_monitor):
        """Тест endpoint документации API"""
        performance_monitor.start()
        response = authenticated_session.get("/api/v2/docs")
        performance_monitor.stop()

        assert response.status_code == 200
        assert performance_monitor.is_within_limit(2.0)

        # Проверяем, что это HTML страница
        content_type = response.headers.get("content-type", "")
        assert "text/html" in content_type

    def test_marketplace_bots_endpoint(self, session_manager, performance_monitor):
        """Тест публичного endpoint маркетплейса"""
        performance_monitor.start()
        response = session_manager.get("/api/marketplace/bots")
        performance_monitor.stop()

        assert response.status_code == 200
        assert performance_monitor.is_within_limit(2.0)

        data = response.json()
        assert "data" in data
        assert isinstance(data["data"], list)

    def test_marketplace_categories_endpoint(self, session_manager, performance_monitor):
        """Тест endpoint категорий маркетплейса"""
        performance_monitor.start()
        response = session_manager.get("/api/marketplace/categories")
        performance_monitor.stop()

        assert response.status_code == 200
        assert performance_monitor.is_within_limit(1.0)

        data = response.json()
        assert "data" in data
        assert isinstance(data["data"], list)
        assert len(data["data"]) > 0

    def test_marketplace_bots_filtering(self, session_manager, performance_monitor):
        """Тест фильтрации ботов в маркетплейсе"""
        categories = ["ai", "business", "entertainment", "utility", "other"]

        for category in categories:
            performance_monitor.start()
            response = session_manager.get(f"/api/marketplace/bots?category={category}")
            performance_monitor.stop()

            assert response.status_code == 200
            assert performance_monitor.is_within_limit(2.0)

            data = response.json()
            assert "data" in data

    def test_marketplace_bots_search(self, session_manager, performance_monitor):
        """Тест поиска ботов в маркетплейсе"""
        search_terms = ["test", "bot", "ai", "assistant"]

        for term in search_terms:
            performance_monitor.start()
            response = session_manager.get(f"/api/marketplace/bots?search={term}")
            performance_monitor.stop()

            assert response.status_code == 200
            assert performance_monitor.is_within_limit(2.0)

            data = response.json()
            assert "data" in data

    def test_marketplace_featured_bots(self, session_manager, performance_monitor):
        """Тест получения избранных ботов"""
        performance_monitor.start()
        response = session_manager.get("/api/marketplace/bots?featured=true")
        performance_monitor.stop()

        assert response.status_code == 200
        assert performance_monitor.is_within_limit(2.0)

        data = response.json()
        assert "data" in data

    def test_api_response_structure_consistency(self, authenticated_session):
        """Тест консистентности структуры ответов API"""
        endpoints = [
            "/api/v2/system/health",
            "/api/v2/system/info",
            "/api/v2/system/stats",
            "/api/v2/bots",
        ]

        for endpoint in endpoints:
            response = authenticated_session.get(endpoint)
            assert response.status_code == 200

            data = response.json()
            # Все ответы должны содержать поле success или data
            assert "success" in data or "data" in data or "status" in data

    def test_api_error_handling(self, authenticated_session):
        """Тест обработки ошибок API"""
        # Тестируем несуществующий endpoint
        response = authenticated_session.get("/api/v2/nonexistent")
        assert response.status_code == 404

        # Тестируем неверный метод
        response = authenticated_session.post("/api/v2/system/health")
        assert response.status_code == 405

    def test_api_performance_under_load(self, authenticated_session, performance_monitor):
        """Тест производительности API под нагрузкой"""
        # Выполняем несколько запросов подряд
        endpoints = [
            "/api/v2/system/health",
            "/api/v2/system/info",
            "/api/v2/system/stats",
            "/api/v2/bots",
        ]

        total_time = 0
        request_count = 10

        for _ in range(request_count):
            for endpoint in endpoints:
                performance_monitor.start()
                response = authenticated_session.get(endpoint)
                performance_monitor.stop()

                assert response.status_code == 200
                total_time += performance_monitor.get_duration()

        average_time = total_time / (len(endpoints) * request_count)
        assert average_time < 1.0, f"Среднее время ответа {average_time:.2f}s превышает лимит 1.0s"
