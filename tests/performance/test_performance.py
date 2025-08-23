"""
Тесты производительности
"""

import concurrent.futures
import threading
import time

import pytest
from locust import HttpUser, between, task


@pytest.mark.performance
class TestPerformance:
    """Тесты производительности"""

    def test_api_response_time(self, authenticated_session, performance_monitor):
        """Тест времени ответа API"""
        endpoints = [
            "/api/v2/system/health",
            "/api/v2/system/info",
            "/api/v2/system/stats",
            "/api/v2/bots",
        ]

        for endpoint in endpoints:
            performance_monitor.start()
            response = authenticated_session.get(endpoint)
            performance_monitor.stop()

            assert response.status_code == 200
            assert performance_monitor.is_within_limit(
                1.0
            ), f"Endpoint {endpoint} отвечает слишком медленно: {performance_monitor.get_duration():.2f}s"

    def test_concurrent_api_requests(self, authenticated_session, performance_monitor):
        """Тест одновременных запросов к API"""

        def make_request(endpoint):
            start_time = time.time()
            response = authenticated_session.get(endpoint)
            end_time = time.time()
            return {
                "endpoint": endpoint,
                "status_code": response.status_code,
                "response_time": end_time - start_time,
            }

        endpoints = [
            "/api/v2/system/health",
            "/api/v2/system/info",
            "/api/v2/system/stats",
            "/api/v2/bots",
        ]

        # Выполняем 10 одновременных запросов
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = []
            for _ in range(10):
                for endpoint in endpoints:
                    futures.append(executor.submit(make_request, endpoint))

            results = []
            for future in concurrent.futures.as_completed(futures):
                results.append(future.result())

        # Проверяем результаты
        for result in results:
            assert result["status_code"] == 200
            assert (
                result["response_time"] < 2.0
            ), f"Медленный ответ: {result['endpoint']} - {result['response_time']:.2f}s"

        # Вычисляем среднее время ответа
        avg_response_time = sum(r["response_time"] for r in results) / len(results)
        assert (
            avg_response_time < 1.0
        ), f"Среднее время ответа {avg_response_time:.2f}s превышает лимит 1.0s"

    def test_marketplace_performance(self, session_manager, performance_monitor):
        """Тест производительности маркетплейса"""
        marketplace_endpoints = [
            "/api/marketplace/bots",
            "/api/marketplace/categories",
            "/api/marketplace/bots?category=ai",
            "/api/marketplace/bots?search=test",
            "/api/marketplace/bots?featured=true",
        ]

        for endpoint in marketplace_endpoints:
            performance_monitor.start()
            response = session_manager.get(endpoint)
            performance_monitor.stop()

            assert response.status_code == 200
            assert performance_monitor.is_within_limit(
                2.0
            ), f"Маркетплейс {endpoint} отвечает слишком медленно: {performance_monitor.get_duration():.2f}s"

    def test_bot_operations_performance(
        self, authenticated_session, test_bot_data, performance_monitor
    ):
        """Тест производительности операций с ботами"""
        # Создание бота
        performance_monitor.start()
        create_response = authenticated_session.post("/api/v2/bots", data=test_bot_data)
        performance_monitor.stop()

        assert create_response.status_code == 201
        assert performance_monitor.is_within_limit(
            3.0
        ), f"Создание бота слишком медленно: {performance_monitor.get_duration():.2f}s"

        bot_id = create_response.json()["data"]["bot_id"]

        # Получение информации о боте
        performance_monitor.start()
        get_response = authenticated_session.get(f"/api/v2/bots/{bot_id}")
        performance_monitor.stop()

        assert get_response.status_code == 200
        assert performance_monitor.is_within_limit(
            1.0
        ), f"Получение информации о боте слишком медленно: {performance_monitor.get_duration():.2f}s"

        # Обновление бота
        update_data = {"bot_name": "Updated Bot"}
        performance_monitor.start()
        update_response = authenticated_session.put(f"/api/v2/bots/{bot_id}", data=update_data)
        performance_monitor.stop()

        assert update_response.status_code == 200
        assert performance_monitor.is_within_limit(
            2.0
        ), f"Обновление бота слишком медленно: {performance_monitor.get_duration():.2f}s"

        # Удаление бота
        performance_monitor.start()
        delete_response = authenticated_session.delete(f"/api/v2/bots/{bot_id}")
        performance_monitor.stop()

        assert delete_response.status_code == 200
        assert performance_monitor.is_within_limit(
            2.0
        ), f"Удаление бота слишком медленно: {performance_monitor.get_duration():.2f}s"

    def test_memory_usage(self, authenticated_session):
        """Тест использования памяти"""
        import os

        import psutil

        # Получаем PID текущего процесса
        current_pid = os.getpid()
        process = psutil.Process(current_pid)

        # Измеряем использование памяти до запросов
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Выполняем серию запросов
        for _ in range(50):
            response = authenticated_session.get("/api/v2/system/health")
            assert response.status_code == 200

        # Измеряем использование памяти после запросов
        final_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Проверяем, что утечки памяти нет (увеличение не более 50MB)
        memory_increase = final_memory - initial_memory
        assert (
            memory_increase < 50
        ), f"Подозрение на утечку памяти: увеличение на {memory_increase:.2f}MB"

    def test_cpu_usage(self, authenticated_session):
        """Тест использования CPU"""

        import psutil

        # Измеряем общее использование CPU системы
        initial_cpu = psutil.cpu_percent(interval=1)

        # Создаем нагрузку
        def make_requests():
            for _ in range(20):
                response = authenticated_session.get("/api/v2/system/health")
                assert response.status_code == 200

        # Запускаем несколько потоков
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=make_requests)
            threads.append(thread)
            thread.start()

        # Ждем завершения
        for thread in threads:
            thread.join()

        # Измеряем CPU после нагрузки
        final_cpu = psutil.cpu_percent(interval=1)

        # CPU не должен быть критически высоким (увеличиваем лимит)
        assert final_cpu < 90, f"Высокое использование CPU: {final_cpu}%"

    def test_database_performance(self, authenticated_session, test_data_generator):
        """Тест производительности базы данных"""
        # Генерируем тестовые данные
        test_configs = test_data_generator.generate_bot_configs(10)

        # Измеряем время создания множества ботов
        start_time = time.time()

        created_bots = []
        for config in test_configs.values():
            response = authenticated_session.post("/api/v2/bots", data=config["config"])
            if response.status_code == 201:
                created_bots.append(response.json()["bot_id"])

        creation_time = time.time() - start_time

        # Проверяем, что создание происходит достаточно быстро
        assert creation_time < 10.0, f"Создание ботов слишком медленно: {creation_time:.2f}s"

        # Измеряем время получения списка ботов
        start_time = time.time()
        response = authenticated_session.get("/api/v2/bots")
        list_time = time.time() - start_time

        assert response.status_code == 200
        assert list_time < 2.0, f"Получение списка ботов слишком медленно: {list_time:.2f}s"

        # Очистка - удаляем созданных ботов
        for bot_id in created_bots:
            authenticated_session.delete(f"/api/v2/bots/{bot_id}")

    def test_network_latency(self, authenticated_session):
        """Тест сетевой задержки"""
        import statistics

        latencies = []

        # Выполняем несколько запросов для измерения задержки
        for _ in range(20):
            start_time = time.time()
            response = authenticated_session.get("/api/v2/system/health")
            end_time = time.time()

            assert response.status_code == 200
            latency = (end_time - start_time) * 1000  # в миллисекундах
            latencies.append(latency)

        # Вычисляем статистику
        avg_latency = statistics.mean(latencies)
        max_latency = max(latencies)
        min_latency = min(latencies)

        # Проверяем, что задержка в разумных пределах
        assert avg_latency < 500, f"Средняя задержка слишком высока: {avg_latency:.2f}ms"
        assert max_latency < 1000, f"Максимальная задержка слишком высока: {max_latency:.2f}ms"
        assert min_latency > 0, "Задержка должна быть положительной"

    def test_scalability(self, authenticated_session):
        """Тест масштабируемости"""
        # Тестируем производительность при увеличении нагрузки
        load_levels = [1, 5, 10, 20]
        response_times = []

        for load in load_levels:
            start_time = time.time()

            with concurrent.futures.ThreadPoolExecutor(max_workers=load) as executor:
                futures = []
                for _ in range(load * 5):  # 5 запросов на поток
                    futures.append(
                        executor.submit(authenticated_session.get, "/api/v2/system/health")
                    )

                for future in concurrent.futures.as_completed(futures):
                    response = future.result()
                    assert response.status_code == 200

            end_time = time.time()
            total_time = end_time - start_time
            avg_time = total_time / (load * 5)
            response_times.append(avg_time)

        # Проверяем, что производительность не деградирует критически
        for i, response_time in enumerate(response_times):
            assert (
                response_time < 1.0
            ), f"Производительность деградирует при нагрузке {load_levels[i]}: {response_time:.2f}s"

    def test_error_recovery_performance(self, authenticated_session):
        """Тест производительности восстановления после ошибок"""
        # Создаем ситуацию с ошибками
        error_endpoints = [
            "/api/v2/bots/99999",  # Несуществующий бот
            "/api/v2/nonexistent",  # Несуществующий endpoint
        ]

        for endpoint in error_endpoints:
            start_time = time.time()
            response = authenticated_session.get(endpoint)
            end_time = time.time()

            # Проверяем, что ошибки обрабатываются быстро
            assert (
                end_time - start_time < 1.0
            ), f"Обработка ошибки слишком медленная: {end_time - start_time:.2f}s"
            assert response.status_code in [
                404,
                400,
                500,
                405,
            ], f"Неожиданный статус: {response.status_code}"


# Locust класс для нагрузочного тестирования
class TelegramBotManagerUser(HttpUser):
    """Пользователь для нагрузочного тестирования"""

    wait_time = between(1, 3)

    def on_start(self):
        """Авторизация при старте"""
        self.client.post("/api/login", json={"username": "admin", "password": "securepassword123"})

    @task(3)
    def health_check(self):
        """Проверка здоровья системы"""
        self.client.get("/api/v2/system/health")

    @task(2)
    def get_bots(self):
        """Получение списка ботов"""
        self.client.get("/api/v2/bots")

    @task(1)
    def get_system_info(self):
        """Получение информации о системе"""
        self.client.get("/api/v2/system/info")

    @task(1)
    def get_marketplace(self):
        """Получение маркетплейса"""
        self.client.get("/api/marketplace/bots")

    @task(1)
    def create_bot(self):
        """Создание бота"""
        bot_data = {
            "bot_name": "Load Test Bot",
            "telegram_token": "1234567890:ABCdefGHIjklMNOpqrsTUVwxyz",
            "openai_api_key": "sk-test1234567890abcdefghijklmnopqrstuvwxyz",
            "assistant_id": "asst_test1234567890abcdefghijklmnopqrstuvwxyz",
            "enable_ai_responses": True,
            "enable_voice_responses": False,
            "group_context_limit": 15,
        }
        response = self.client.post("/api/v2/bots", json=bot_data)

        # Если бот создан, удаляем его
        if response.status_code == 201:
            bot_id = response.json().get("bot_id")
            if bot_id:
                self.client.delete(f"/api/v2/bots/{bot_id}")
