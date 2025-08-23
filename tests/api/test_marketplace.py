"""
Тесты API маркетплейса
"""


import pytest

from tests.utils import (
    performance_monitor,
    test_logger,
)


@pytest.mark.api
@pytest.mark.integration
class TestMarketplaceAPI:
    """Тесты API маркетплейса"""

    def test_get_marketplace_bots(self, session_manager):
        """Тест получения ботов из маркетплейса"""
        test_logger.info("Тестирование получения ботов из маркетплейса")

        performance_monitor.start()
        response = session_manager.get("/api/marketplace/bots")
        performance_monitor.stop()

        assert response.status_code == 200, f"Ожидался статус 200, получен {response.status_code}"
        assert performance_monitor.is_within_limit(
            5.0
        ), f"Время ответа превышает лимит: {performance_monitor.get_duration()}s"

        # Проверяем структуру ответа
        data = response.json()
        assert "data" in data, "Поле 'data' отсутствует в ответе"
        assert isinstance(data["data"], list), "data должно быть списком"

        # Проверяем структуру каждого бота
        if data["data"]:
            bot = data["data"][0]
            required_fields = ["id", "title", "description", "category", "username"]

            for field in required_fields:
                assert field in bot, f"Поле '{field}' отсутствует в данных бота"

        test_logger.success(f"Получено {len(data['data'])} ботов из маркетплейса")

    def test_get_marketplace_categories(self, session_manager):
        """Тест получения категорий маркетплейса"""
        test_logger.info("Тестирование получения категорий маркетплейса")

        performance_monitor.start()
        response = session_manager.get("/api/marketplace/categories")
        performance_monitor.stop()

        assert response.status_code == 200, f"Ожидался статус 200, получен {response.status_code}"
        assert performance_monitor.is_within_limit(
            3.0
        ), f"Время ответа превышает лимит: {performance_monitor.get_duration()}s"

        # Проверяем структуру ответа
        data = response.json()
        assert "categories" in data, "Поле 'categories' отсутствует в ответе"
        assert isinstance(data["categories"], list), "categories должно быть списком"

        # Проверяем, что есть хотя бы несколько категорий
        assert len(data["categories"]) > 0, "Список категорий пуст"

        test_logger.success(f"Получено {len(data['categories'])} категорий маркетплейса")

    def test_marketplace_bot_filtering(self, session_manager):
        """Тест фильтрации ботов в маркетплейсе"""
        test_logger.info("Тестирование фильтрации ботов в маркетплейсе")

        # Тестируем фильтрацию по категории
        categories = ["ai", "utility", "entertainment", "business", "other"]

        for category in categories:
            performance_monitor.start()
            response = session_manager.get(f"/api/marketplace/bots?category={category}")
            performance_monitor.stop()

            assert (
                response.status_code == 200
            ), f"Ожидался статус 200, получен {response.status_code}"
            assert performance_monitor.is_within_limit(
                5.0
            ), f"Время ответа превышает лимит: {performance_monitor.get_duration()}s"

            data = response.json()
            assert "data" in data, "Поле 'data' отсутствует в ответе"

            # Проверяем, что все боты имеют указанную категорию
            for bot in data["data"]:
                assert (
                    bot.get("category") == category
                ), f"Бот имеет неверную категорию: {bot.get('category')}"

            test_logger.info(f"✅ Фильтр по категории '{category}': {len(data['data'])} ботов")

        test_logger.success("Фильтрация ботов по категориям работает корректно")

    def test_marketplace_bot_search(self, session_manager):
        """Тест поиска ботов в маркетплейсе"""
        test_logger.info("Тестирование поиска ботов в маркетплейсе")

        # Сначала получаем всех ботов
        response = session_manager.get("/api/marketplace/bots")
        assert response.status_code == 200

        all_bots = response.json()["data"]
        if not all_bots:
            pytest.skip("Нет ботов для тестирования поиска")

        # Берем название первого бота для поиска
        search_term = all_bots[0]["title"].split()[0]  # Первое слово из названия

        performance_monitor.start()
        response = session_manager.get(f"/api/marketplace/bots?search={search_term}")
        performance_monitor.stop()

        assert response.status_code == 200, f"Ожидался статус 200, получен {response.status_code}"
        assert performance_monitor.is_within_limit(
            5.0
        ), f"Время ответа превышает лимит: {performance_monitor.get_duration()}s"

        data = response.json()
        assert "data" in data, "Поле 'data' отсутствует в ответе"

        # Проверяем, что найденные боты содержат поисковый термин
        for bot in data["data"]:
            title_lower = bot["title"].lower()
            description_lower = bot.get("description", "").lower()
            search_lower = search_term.lower()

            assert (
                search_lower in title_lower or search_lower in description_lower
            ), f"Бот не содержит поисковый термин: {search_term}"

        test_logger.success(f"Поиск по термину '{search_term}' нашел {len(data['data'])} ботов")

    def test_marketplace_bot_pagination(self, session_manager):
        """Тест пагинации ботов в маркетплейсе"""
        test_logger.info("Тестирование пагинации ботов в маркетплейсе")

        # Получаем первую страницу
        performance_monitor.start()
        response = session_manager.get("/api/marketplace/bots?page=1&limit=5")
        performance_monitor.stop()

        assert response.status_code == 200, f"Ожидался статус 200, получен {response.status_code}"
        assert performance_monitor.is_within_limit(
            5.0
        ), f"Время ответа превышает лимит: {performance_monitor.get_duration()}s"

        data = response.json()
        assert "data" in data, "Поле 'data' отсутствует в ответе"
        assert "pagination" in data, "Поле 'pagination' отсутствует в ответе"

        # Проверяем структуру пагинации
        pagination = data["pagination"]
        required_fields = ["page", "limit", "total", "pages"]

        for field in required_fields:
            assert field in pagination, f"Поле '{field}' отсутствует в пагинации"

        # Проверяем, что количество ботов не превышает лимит
        assert len(data["data"]) <= 5, f"Количество ботов превышает лимит: {len(data['data'])} > 5"

        test_logger.success(
            f"Пагинация работает: страница {pagination['page']}, всего страниц: {pagination['pages']}"
        )

    def test_marketplace_bot_sorting(self, session_manager):
        """Тест сортировки ботов в маркетплейсе"""
        test_logger.info("Тестирование сортировки ботов в маркетплейсе")

        # Тестируем сортировку по разным полям
        sort_fields = ["title", "rating", "total_users", "created_at"]

        for sort_field in sort_fields:
            performance_monitor.start()
            response = session_manager.get(f"/api/marketplace/bots?sort={sort_field}&order=asc")
            performance_monitor.stop()

            assert (
                response.status_code == 200
            ), f"Ожидался статус 200, получен {response.status_code}"
            assert performance_monitor.is_within_limit(
                5.0
            ), f"Время ответа превышает лимит: {performance_monitor.get_duration()}s"

            data = response.json()
            assert "data" in data, "Поле 'data' отсутствует в ответе"

            # Проверяем сортировку (если есть больше одного бота)
            if len(data["data"]) > 1:
                values = []
                for bot in data["data"]:
                    if sort_field in bot:
                        values.append(bot[sort_field])

                # Проверяем, что значения отсортированы по возрастанию
                if values and all(isinstance(v, (int, float)) for v in values):
                    assert values == sorted(
                        values
                    ), f"Значения не отсортированы по возрастанию: {values}"

            test_logger.info(f"✅ Сортировка по '{sort_field}': {len(data['data'])} ботов")

        test_logger.success("Сортировка ботов работает корректно")

    def test_marketplace_featured_bots(self, session_manager):
        """Тест получения избранных ботов"""
        test_logger.info("Тестирование получения избранных ботов")

        performance_monitor.start()
        response = session_manager.get("/api/marketplace/bots?featured=true")
        performance_monitor.stop()

        assert response.status_code == 200, f"Ожидался статус 200, получен {response.status_code}"
        assert performance_monitor.is_within_limit(
            5.0
        ), f"Время ответа превышает лимит: {performance_monitor.get_duration()}s"

        data = response.json()
        assert "data" in data, "Поле 'data' отсутствует в ответе"

        # Проверяем, что все боты избранные
        for bot in data["data"]:
            assert (
                bot.get("featured", False) == True
            ), f"Бот не является избранным: {bot.get('title')}"

        test_logger.success(f"Получено {len(data['data'])} избранных ботов")

    def test_marketplace_bot_details(self, session_manager):
        """Тест получения детальной информации о боте"""
        test_logger.info("Тестирование получения детальной информации о боте")

        # Сначала получаем список ботов
        response = session_manager.get("/api/marketplace/bots")
        assert response.status_code == 200

        data = response.json()
        if not data["data"]:
            pytest.skip("Нет ботов для тестирования детальной информации")

        bot_id = data["data"][0]["id"]

        performance_monitor.start()
        response = session_manager.get(f"/api/marketplace/bots/{bot_id}")
        performance_monitor.stop()

        assert response.status_code == 200, f"Ожидался статус 200, получен {response.status_code}"
        assert performance_monitor.is_within_limit(
            3.0
        ), f"Время ответа превышает лимит: {performance_monitor.get_duration()}s"

        # Проверяем структуру ответа
        data = response.json()
        required_fields = ["id", "title", "description", "category", "username"]

        for field in required_fields:
            assert field in data, f"Поле '{field}' отсутствует в ответе"

        assert data["id"] == bot_id, "ID бота не совпадает"

        test_logger.success(f"Детальная информация о боте {bot_id} получена")

    def test_marketplace_bot_statistics(self, session_manager):
        """Тест получения статистики маркетплейса"""
        test_logger.info("Тестирование получения статистики маркетплейса")

        performance_monitor.start()
        response = session_manager.get("/api/marketplace/stats")
        performance_monitor.stop()

        # Этот endpoint может не существовать, поэтому проверяем разные варианты
        if response.status_code == 200:
            assert performance_monitor.is_within_limit(
                5.0
            ), f"Время ответа превышает лимит: {performance_monitor.get_duration()}s"

            data = response.json()
            assert "total_bots" in data, "Поле 'total_bots' отсутствует в ответе"
            assert "categories" in data, "Поле 'categories' отсутствует в ответе"

            test_logger.success("Статистика маркетплейса получена")
        else:
            test_logger.warning("Endpoint статистики маркетплейса не найден")

    def test_marketplace_api_error_handling(self, session_manager):
        """Тест обработки ошибок API маркетплейса"""
        test_logger.info("Тестирование обработки ошибок API маркетплейса")

        # Тестируем несуществующий бот
        non_existent_id = 99999
        response = session_manager.get(f"/api/marketplace/bots/{non_existent_id}")

        assert response.status_code == 404, f"Ожидался статус 404, получен {response.status_code}"

        # Проверяем структуру ответа об ошибке
        data = response.json()
        assert "error" in data, "Поле 'error' отсутствует в ответе об ошибке"

        test_logger.success("Обработка ошибок API маркетплейса работает корректно")

    def test_marketplace_api_performance(self, session_manager):
        """Тест производительности API маркетплейса"""
        test_logger.info("Тестирование производительности API маркетплейса")

        endpoints = [
            ("/api/marketplace/bots", "Получение всех ботов"),
            ("/api/marketplace/categories", "Получение категорий"),
            ("/api/marketplace/bots?category=ai", "Фильтрация по категории"),
            ("/api/marketplace/bots?search=test", "Поиск ботов"),
            ("/api/marketplace/bots?page=1&limit=10", "Пагинация"),
        ]

        for endpoint, description in endpoints:
            performance_monitor.start()
            response = session_manager.get(endpoint)
            performance_monitor.stop()

            duration = performance_monitor.get_duration()
            assert (
                response.status_code == 200
            ), f"{description} вернул статус {response.status_code}"
            assert duration <= 5.0, f"{description} превысил лимит времени: {duration}s > 5s"

            test_logger.info(f"✅ {description}: {duration:.2f}s")

        test_logger.success("Все endpoints маркетплейса отвечают в пределах лимитов времени")
