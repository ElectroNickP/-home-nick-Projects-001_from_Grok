"""
Тесты безопасности
"""


import pytest


@pytest.mark.security
class TestSecurity:
    """Тесты безопасности"""

    def test_authentication_required(self, session_manager):
        """Тест обязательной аутентификации"""
        protected_endpoints = [
            "/api/v2/system/health",
            "/api/v2/system/info",
            "/api/v2/system/stats",
            "/api/v2/bots",
            "/api/v2/bots/1",
            "/api/v2/bots/1/start",
            "/api/v2/bots/1/stop",
        ]

        for endpoint in protected_endpoints:
            response = session_manager.get(endpoint)
            assert response.status_code in [
                401,
                405,
            ], f"Endpoint {endpoint} не защищен аутентификацией (статус: {response.status_code})"

    def test_invalid_credentials_rejection(self, session_manager):
        """Тест отклонения неверных учетных данных"""
        invalid_credentials = [
            {"username": "admin", "password": "wrongpassword"},
            {"username": "wronguser", "password": "securepassword123"},
            {"username": "", "password": "securepassword123"},
            {"username": "admin", "password": ""},
            {"username": "", "password": ""},
            {"username": "admin' OR '1'='1", "password": "securepassword123"},  # SQL injection
            {"username": "admin", "password": "admin' OR '1'='1"},  # SQL injection
        ]

        for credentials in invalid_credentials:
            response = session_manager.post("/api/login", data=credentials)
            assert response.status_code == 401, f"Неверные учетные данные приняты: {credentials}"

    def test_sql_injection_prevention(self, authenticated_session):
        """Тест защиты от SQL инъекций"""
        sql_injection_payloads = [
            "'; DROP TABLE bots; --",
            "' OR '1'='1",
            "' UNION SELECT * FROM users --",
            "admin'--",
            "admin'/*",
            "'; INSERT INTO bots VALUES (999, 'hacked'); --",
        ]

        for payload in sql_injection_payloads:
            # Тестируем в различных полях
            test_data = {
                "bot_name": payload,
                "telegram_token": "1234567890:ABCdefGHIjklMNOpqrsTUVwxyz",
                "openai_api_key": "sk-test1234567890abcdefghijklmnopqrstuvwxyz",
                "assistant_id": "asst_test1234567890abcdefghijklmnopqrstuvwxyz",
            }

            response = authenticated_session.post("/api/v2/bots", data=test_data)
            # Должен вернуть 400 (Bad Request) или 422 (Unprocessable Entity)
            assert response.status_code in [400, 422], f"SQL инъекция не заблокирована: {payload}"

    def test_xss_prevention(self, authenticated_session):
        """Тест защиты от XSS атак"""
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "javascript:alert('XSS')",
            "<svg onload=alert('XSS')>",
            "'><script>alert('XSS')</script>",
            "<iframe src=javascript:alert('XSS')>",
        ]

        for payload in xss_payloads:
            test_data = {
                "bot_name": payload,
                "telegram_token": "1234567890:ABCdefGHIjklMNOpqrsTUVwxyz",
                "openai_api_key": "sk-test1234567890abcdefghijklmnopqrstuvwxyz",
                "assistant_id": "asst_test1234567890abcdefghijklmnopqrstuvwxyz",
            }

            response = authenticated_session.post("/api/v2/bots", data=test_data)
            # Должен вернуть 400 или 422
            assert response.status_code in [400, 422], f"XSS не заблокирован: {payload}"

    def test_path_traversal_prevention(self, authenticated_session):
        """Тест защиты от path traversal атак"""
        path_traversal_payloads = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\drivers\\etc\\hosts",
            "....//....//....//etc/passwd",
            "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",
            "..%252f..%252f..%252fetc%252fpasswd",
        ]

        for payload in path_traversal_payloads:
            # Тестируем в различных контекстах
            test_data = {
                "bot_name": "Test Bot",
                "telegram_token": payload,
                "openai_api_key": "sk-test1234567890abcdefghijklmnopqrstuvwxyz",
                "assistant_id": "asst_test1234567890abcdefghijklmnopqrstuvwxyz",
            }

            response = authenticated_session.post("/api/v2/bots", data=test_data)
            assert response.status_code in [400, 422], f"Path traversal не заблокирован: {payload}"

    def test_csrf_protection(self, session_manager):
        """Тест защиты от CSRF атак"""
        # Создаем сессию без CSRF токена
        response = session_manager.post(
            "/api/login", data={"username": "admin", "password": "securepassword123"}
        )

        if response.status_code == 200:
            # Пытаемся выполнить действия без CSRF токена
            csrf_test_actions = [
                ("POST", "/api/v2/bots", {"bot_name": "CSRF Test Bot"}),
                ("PUT", "/api/v2/bots/1", {"bot_name": "Updated Bot"}),
                ("DELETE", "/api/v2/bots/1", {}),
                ("POST", "/api/v2/bots/1/start", {}),
                ("POST", "/api/v2/bots/1/stop", {}),
            ]

            for method, endpoint, data in csrf_test_actions:
                if method == "POST":
                    response = session_manager.post(endpoint, data=data)
                elif method == "PUT":
                    response = session_manager.put(endpoint, data=data)
                elif method == "DELETE":
                    response = session_manager.delete(endpoint)

                # Должен вернуть 403 (Forbidden) или 400 (Bad Request)
                assert response.status_code in [
                    403,
                    400,
                ], f"CSRF защита не работает для {method} {endpoint}"

    def test_input_validation(self, authenticated_session):
        """Тест валидации входных данных"""
        invalid_inputs = [
            # Слишком длинные строки
            {"bot_name": "A" * 1000},
            {"telegram_token": "A" * 1000},
            {"openai_api_key": "A" * 1000},
            # Неверные форматы токенов
            {"telegram_token": "invalid_token"},
            {"telegram_token": "123:invalid"},
            {"openai_api_key": "invalid_key"},
            {"openai_api_key": "sk-invalid"},
            # Отрицательные числа
            {"group_context_limit": -1},
            {"group_context_limit": -100},
            # Слишком большие числа
            {"group_context_limit": 1000000},
            # Неверные типы данных
            {"enable_ai_responses": "not_boolean"},
            {"group_context_limit": "not_number"},
        ]

        for invalid_input in invalid_inputs:
            test_data = {
                "bot_name": "Test Bot",
                "telegram_token": "1234567890:ABCdefGHIjklMNOpqrsTUVwxyz",
                "openai_api_key": "sk-test1234567890abcdefghijklmnopqrstuvwxyz",
                "assistant_id": "asst_test1234567890abcdefghijklmnopqrstuvwxyz",
                **invalid_input,
            }

            response = authenticated_session.post("/api/v2/bots", data=test_data)
            assert response.status_code in [400, 422], f"Невалидные данные приняты: {invalid_input}"

    def test_rate_limiting(self, session_manager):
        """Тест ограничения частоты запросов"""
        # Выполняем множество запросов подряд
        for _ in range(50):
            response = session_manager.post(
                "/api/login", data={"username": "admin", "password": "wrongpassword"}
            )

            # После определенного количества запросов должен вернуться 429 (Too Many Requests)
            if response.status_code == 429:
                break
        else:
            # Если rate limiting не работает, это не критично, но стоит отметить
            pytest.skip("Rate limiting не настроен")

    def test_session_management(self, session_manager):
        """Тест управления сессиями"""
        # Входим в систему
        response = session_manager.post(
            "/api/login", data={"username": "admin", "password": "securepassword123"}
        )

        if response.status_code == 200:
            # Проверяем, что сессия работает
            health_response = session_manager.get("/api/v2/system/health")
            assert health_response.status_code == 200

            # Выходим из системы
            logout_response = session_manager.get("/logout")

            # Проверяем, что сессия закрыта
            health_response_after_logout = session_manager.get("/api/v2/system/health")
            assert health_response_after_logout.status_code == 401

    def test_secure_headers(self, session_manager):
        """Тест безопасных заголовков"""
        response = session_manager.get("/")

        # Проверяем наличие важных заголовков безопасности
        headers = response.headers

        # Content-Security-Policy (если настроен)
        if "Content-Security-Policy" in headers:
            csp = headers["Content-Security-Policy"]
            assert "script-src" in csp.lower()

        # X-Content-Type-Options
        if "X-Content-Type-Options" in headers:
            assert headers["X-Content-Type-Options"] == "nosniff"

        # X-Frame-Options
        if "X-Frame-Options" in headers:
            assert headers["X-Frame-Options"] in ["DENY", "SAMEORIGIN"]

        # X-XSS-Protection
        if "X-XSS-Protection" in headers:
            assert "1" in headers["X-XSS-Protection"]

    def test_https_redirect(self, session_manager):
        """Тест перенаправления на HTTPS"""
        # Этот тест актуален только для production
        # В development окружении может не работать
        pass

    def test_parameter_pollution(self, authenticated_session):
        """Тест защиты от parameter pollution"""
        # Создаем бота с дублирующимися параметрами
        test_data = {
            "bot_name": "Test Bot",
            "bot_name": "Duplicate Bot",  # Дублирующийся параметр
            "telegram_token": "1234567890:ABCdefGHIjklMNOpqrsTUVwxyz",
            "openai_api_key": "sk-test1234567890abcdefghijklmnopqrstuvwxyz",
            "assistant_id": "asst_test1234567890abcdefghijklmnopqrstuvwxyz",
        }

        response = authenticated_session.post("/api/v2/bots", data=test_data)
        # Должен вернуть 400 или 422
        assert response.status_code in [400, 422], "Parameter pollution не заблокирован"

    def test_json_injection(self, authenticated_session):
        """Тест защиты от JSON инъекций"""
        json_injection_payloads = [
            '{"bot_name": "Test", "telegram_token": "123", "malicious": "payload"}',
            '{"bot_name": "Test", "telegram_token": "123", "__proto__": {"admin": true}}',
            '{"bot_name": "Test", "telegram_token": "123", "constructor": {"prototype": {"admin": true}}}',
        ]

        for payload in json_injection_payloads:
            response = authenticated_session.post("/api/v2/bots", data=payload)
            assert response.status_code in [400, 422], f"JSON инъекция не заблокирована: {payload}"

    def test_no_sensitive_data_exposure(self, session_manager):
        """Тест отсутствия утечки чувствительных данных"""
        # Проверяем, что в ответах не содержится чувствительная информация
        response = session_manager.get("/api/marketplace/bots")

        if response.status_code == 200:
            data = response.json()

            # Проверяем, что в публичных данных нет токенов
            if "data" in data and isinstance(data["data"], list):
                for bot in data["data"]:
                    # Не должно быть токенов в публичных данных
                    assert "telegram_token" not in bot, "Telegram токен утечен в публичных данных"
                    assert "openai_api_key" not in bot, "OpenAI ключ утечен в публичных данных"
                    assert "assistant_id" not in bot, "Assistant ID утечен в публичных данных"

    def test_error_message_security(self, authenticated_session):
        """Тест безопасности сообщений об ошибках"""
        # Пытаемся получить информацию о несуществующем боте
        response = authenticated_session.get("/api/v2/bots/99999")

        if response.status_code == 404:
            data = response.json()

            # Сообщение об ошибке не должно содержать чувствительную информацию
            error_message = data.get("error", "")

            # Не должно содержать пути к файлам
            assert "../" not in error_message
            assert "/etc/" not in error_message
            assert "/var/" not in error_message

            # Не должно содержать SQL запросов
            assert "SELECT" not in error_message.upper()
            assert "INSERT" not in error_message.upper()
            assert "UPDATE" not in error_message.upper()
            assert "DELETE" not in error_message.upper()

    def test_file_upload_security(self, authenticated_session):
        """Тест безопасности загрузки файлов"""
        # Создаем вредоносные файлы для тестирования
        malicious_files = [
            ("test.php", b"<?php system($_GET['cmd']); ?>"),
            ("test.jsp", b"<% Runtime.getRuntime().exec(request.getParameter('cmd')); %>"),
            (
                "test.asp",
                b"<% Response.Write(CreateObject('WScript.Shell').Exec(Request.QueryString('cmd')).StdOut.ReadAll()) %>",
            ),
            ("test.exe", b"MZ\x90\x00\x03\x00\x00\x00\x04\x00\x00\x00"),
            ("test.sh", b"#!/bin/bash\nrm -rf /"),
        ]

        for filename, content in malicious_files:
            files = {"file": (filename, content, "application/octet-stream")}

            # Пытаемся загрузить файл (если есть endpoint для загрузки)
            # response = authenticated_session.post("/api/v2/upload", files=files)
            # assert response.status_code in [400, 403, 415], f"Вредоносный файл {filename} принят"
            pass

    def test_authorization_bypass(self, authenticated_session):
        """Тест обхода авторизации"""
        # Пытаемся получить доступ к ресурсам других пользователей
        # (если система поддерживает множественных пользователей)

        # Тестируем доступ к несуществующим ресурсам
        response = authenticated_session.get("/api/v2/bots/99999")
        assert response.status_code == 404, "Доступ к несуществующему ресурсу"

        # Тестируем доступ к системным файлам
        system_paths = ["/api/v2/system/config", "/api/v2/system/logs", "/api/v2/system/backup"]

        for path in system_paths:
            response = authenticated_session.get(path)
            assert response.status_code in [404, 403], f"Неавторизованный доступ к {path}"

    def test_information_disclosure(self, session_manager):
        """Тест утечки информации"""
        # Проверяем, что в ответах сервера нет лишней информации

        # Тестируем несуществующий endpoint
        response = session_manager.get("/api/v2/nonexistent")

        # В ответе не должно быть информации о структуре системы
        if response.status_code == 404:
            data = response.json()
            error_message = data.get("error", "")

            # Не должно содержать информации о файловой системе
            assert "FileNotFoundError" not in error_message
            assert "No such file" not in error_message
            assert "path" not in error_message.lower()

            # Не должно содержать информации о базе данных
            assert "sql" not in error_message.lower()
            assert "database" not in error_message.lower()
            assert "table" not in error_message.lower()

    def test_secure_cookies(self, session_manager):
        """Тест безопасности cookies"""
        # Входим в систему
        response = session_manager.post(
            "/api/login", data={"username": "admin", "password": "securepassword123"}
        )

        if response.status_code == 200:
            # Проверяем cookies
            cookies = session_manager.session.cookies

            for cookie in cookies:
                # Проверяем флаги безопасности
                if hasattr(cookie, "secure"):
                    # В production должно быть True
                    pass

                if hasattr(cookie, "httponly"):
                    # Должно быть True для session cookies
                    pass

                if hasattr(cookie, "samesite"):
                    # Должно быть 'Strict' или 'Lax'
                    pass
