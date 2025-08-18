"""
Тесты веб-интерфейса
"""

import pytest
import requests
from tests.utils import test_logger, test_helper, performance_monitor

@pytest.mark.ui
@pytest.mark.e2e
class TestWebInterface:
    """Тесты веб-интерфейса"""
    
    def test_login_page_accessibility(self, session_manager):
        """Тест доступности страницы авторизации"""
        test_logger.info("Тестирование доступности страницы авторизации")
        
        performance_monitor.start()
        response = session_manager.get("/login")
        performance_monitor.stop()
        
        assert response.status_code == 200, f"Ожидался статус 200, получен {response.status_code}"
        assert performance_monitor.is_within_limit(3.0), f"Время ответа превышает лимит: {performance_monitor.get_duration()}s"
        
        # Проверяем, что это HTML страница
        content_type = response.headers.get('content-type', '')
        assert 'text/html' in content_type, f"Ожидался HTML, получен {content_type}"
        
        # Проверяем наличие ключевых элементов
        content = response.text
        assert "login" in content.lower(), "Страница авторизации не найдена"
        assert "username" in content.lower() or "логин" in content.lower(), "Поле логина не найдено"
        assert "password" in content.lower() or "пароль" in content.lower(), "Поле пароля не найдено"
        
        test_logger.success("Страница авторизации доступна и корректна")
    
    def test_main_page_with_authentication(self, authenticated_session):
        """Тест главной страницы с авторизацией"""
        test_logger.info("Тестирование главной страницы с авторизацией")
        
        performance_monitor.start()
        response = authenticated_session.get("/")
        performance_monitor.stop()
        
        assert response.status_code == 200, f"Ожидался статус 200, получен {response.status_code}"
        assert performance_monitor.is_within_limit(5.0), f"Время ответа превышает лимит: {performance_monitor.get_duration()}s"
        
        # Проверяем, что это HTML страница
        content_type = response.headers.get('content-type', '')
        assert 'text/html' in content_type, f"Ожидался HTML, получен {content_type}"
        
        # Проверяем наличие новых элементов интерфейса
        content = response.text
        new_elements = [
            "bots-dashboard",
            "stats-cards",
            "filter-buttons",
            "bots-grid",
            "bot-card",
            "feature-badges",
            "action-buttons"
        ]
        
        missing_elements = []
        for element in new_elements:
            if element not in content:
                missing_elements.append(element)
        
        assert not missing_elements, f"Отсутствуют элементы интерфейса: {missing_elements}"
        
        # Проверяем CSS стили
        css_elements = [
            "linear-gradient",
            "backdrop-filter",
            "grid-template-columns",
            "animation: fadeInUp"
        ]
        
        missing_css = []
        for css in css_elements:
            if css not in content:
                missing_css.append(css)
        
        if missing_css:
            test_logger.warning(f"Отсутствуют CSS стили: {missing_css}")
        else:
            test_logger.success("Все CSS стили присутствуют")
        
        test_logger.success("Главная страница с авторизацией работает корректно")
    
    def test_main_page_without_authentication(self, session_manager):
        """Тест главной страницы без авторизации"""
        test_logger.info("Тестирование главной страницы без авторизации")
        
        performance_monitor.start()
        response = session_manager.get("/")
        performance_monitor.stop()
        
        # Должен быть редирект на страницу авторизации
        assert response.status_code in [302, 401], f"Ожидался статус 302 или 401, получен {response.status_code}"
        assert performance_monitor.is_within_limit(3.0), f"Время ответа превышает лимит: {performance_monitor.get_duration()}s"
        
        test_logger.success("Главная страница правильно защищена авторизацией")
    
    def test_marketplace_page_accessibility(self, session_manager):
        """Тест доступности страницы маркетплейса"""
        test_logger.info("Тестирование доступности страницы маркетплейса")
        
        performance_monitor.start()
        response = session_manager.get("/marketplace")
        performance_monitor.stop()
        
        assert response.status_code == 200, f"Ожидался статус 200, получен {response.status_code}"
        assert performance_monitor.is_within_limit(5.0), f"Время ответа превышает лимит: {performance_monitor.get_duration()}s"
        
        # Проверяем, что это HTML страница
        content_type = response.headers.get('content-type', '')
        assert 'text/html' in content_type, f"Ожидался HTML, получен {content_type}"
        
        # Проверяем наличие ключевых элементов маркетплейса
        content = response.text
        assert "marketplace" in content.lower() or "маркетплейс" in content.lower(), "Страница маркетплейса не найдена"
        
        test_logger.success("Страница маркетплейса доступна")
    
    def test_logout_page_accessibility(self, authenticated_session):
        """Тест доступности страницы выхода"""
        test_logger.info("Тестирование доступности страницы выхода")
        
        performance_monitor.start()
        response = authenticated_session.get("/logout")
        performance_monitor.stop()
        
        assert response.status_code == 200, f"Ожидался статус 200, получен {response.status_code}"
        assert performance_monitor.is_within_limit(3.0), f"Время ответа превышает лимит: {performance_monitor.get_duration()}s"
        
        # Проверяем, что это HTML страница
        content_type = response.headers.get('content-type', '')
        assert 'text/html' in content_type, f"Ожидался HTML, получен {content_type}"
        
        # Проверяем наличие элементов страницы выхода
        content = response.text
        assert "logout" in content.lower() or "выход" in content.lower(), "Страница выхода не найдена"
        
        test_logger.success("Страница выхода доступна")
    
    def test_dialogs_page_accessibility(self, authenticated_session):
        """Тест доступности страницы диалогов"""
        test_logger.info("Тестирование доступности страницы диалогов")
        
        # Сначала получаем список ботов
        response = authenticated_session.get("/api/v2/bots")
        assert response.status_code == 200
        
        data = response.json()
        if not data["data"]:
            pytest.skip("Нет ботов для тестирования страницы диалогов")
        
        bot_id = data["data"][0]["id"]
        
        performance_monitor.start()
        response = authenticated_session.get(f"/dialogs/{bot_id}")
        performance_monitor.stop()
        
        assert response.status_code == 200, f"Ожидался статус 200, получен {response.status_code}"
        assert performance_monitor.is_within_limit(5.0), f"Время ответа превышает лимит: {performance_monitor.get_duration()}s"
        
        # Проверяем, что это HTML страница
        content_type = response.headers.get('content-type', '')
        assert 'text/html' in content_type, f"Ожидался HTML, получен {content_type}"
        
        # Проверяем наличие элементов страницы диалогов
        content = response.text
        assert "dialogs" in content.lower() or "диалоги" in content.lower(), "Страница диалогов не найдена"
        
        test_logger.success(f"Страница диалогов для бота {bot_id} доступна")
    
    def test_marketplace_bot_page_accessibility(self, session_manager):
        """Тест доступности страницы бота в маркетплейсе"""
        test_logger.info("Тестирование доступности страницы бота в маркетплейсе")
        
        # Сначала получаем список ботов из маркетплейса
        response = session_manager.get("/api/marketplace/bots")
        assert response.status_code == 200
        
        data = response.json()
        if not data["data"]:
            pytest.skip("Нет ботов в маркетплейсе для тестирования")
        
        bot_id = data["data"][0]["id"]
        
        performance_monitor.start()
        response = session_manager.get(f"/marketplace/{bot_id}")
        performance_monitor.stop()
        
        assert response.status_code == 200, f"Ожидался статус 200, получен {response.status_code}"
        assert performance_monitor.is_within_limit(5.0), f"Время ответа превышает лимит: {performance_monitor.get_duration()}s"
        
        # Проверяем, что это HTML страница
        content_type = response.headers.get('content-type', '')
        assert 'text/html' in content_type, f"Ожидался HTML, получен {content_type}"
        
        test_logger.success(f"Страница бота {bot_id} в маркетплейсе доступна")
    
    def test_page_responsive_design(self, authenticated_session):
        """Тест адаптивного дизайна страниц"""
        test_logger.info("Тестирование адаптивного дизайна страниц")
        
        # Проверяем главную страницу
        response = authenticated_session.get("/")
        assert response.status_code == 200
        
        content = response.text
        
        # Проверяем наличие адаптивных элементов
        responsive_elements = [
            "media query",
            "responsive",
            "mobile",
            "tablet",
            "viewport"
        ]
        
        found_responsive = []
        for element in responsive_elements:
            if element in content.lower():
                found_responsive.append(element)
        
        if found_responsive:
            test_logger.success(f"Найдены элементы адаптивного дизайна: {found_responsive}")
        else:
            test_logger.warning("Элементы адаптивного дизайна не найдены")
        
        test_logger.success("Проверка адаптивного дизайна завершена")
    
    def test_page_load_performance(self, authenticated_session):
        """Тест производительности загрузки страниц"""
        test_logger.info("Тестирование производительности загрузки страниц")
        
        pages = [
            ("/", "Главная страница"),
            ("/login", "Страница авторизации"),
            ("/marketplace", "Страница маркетплейса"),
            ("/logout", "Страница выхода")
        ]
        
        for endpoint, name in pages:
            performance_monitor.start()
            response = authenticated_session.get(endpoint)
            performance_monitor.stop()
            
            duration = performance_monitor.get_duration()
            assert response.status_code == 200, f"{name} вернула статус {response.status_code}"
            assert duration <= 10.0, f"{name} превысила лимит времени: {duration}s > 10s"
            
            test_logger.info(f"✅ {name}: {duration:.2f}s")
        
        test_logger.success("Все страницы загружаются в пределах лимитов времени")
    
    def test_page_content_integrity(self, authenticated_session):
        """Тест целостности содержимого страниц"""
        test_logger.info("Тестирование целостности содержимого страниц")
        
        # Проверяем главную страницу
        response = authenticated_session.get("/")
        assert response.status_code == 200
        
        content = response.text
        
        # Проверяем наличие обязательных элементов
        required_elements = [
            "<html",
            "<head",
            "<body",
            "</html>"
        ]
        
        missing_elements = []
        for element in required_elements:
            if element not in content:
                missing_elements.append(element)
        
        assert not missing_elements, f"Отсутствуют обязательные HTML элементы: {missing_elements}"
        
        # Проверяем, что нет очевидных ошибок
        error_indicators = [
            "error",
            "exception",
            "traceback",
            "undefined",
            "null reference"
        ]
        
        found_errors = []
        for indicator in error_indicators:
            if indicator in content.lower():
                found_errors.append(indicator)
        
        if found_errors:
            test_logger.warning(f"Найдены возможные ошибки: {found_errors}")
        else:
            test_logger.success("Очевидных ошибок не найдено")
        
        test_logger.success("Целостность содержимого страниц проверена")
    
    def test_page_security_headers(self, authenticated_session):
        """Тест заголовков безопасности страниц"""
        test_logger.info("Тестирование заголовков безопасности страниц")
        
        response = authenticated_session.get("/")
        assert response.status_code == 200
        
        headers = response.headers
        
        # Проверяем наличие важных заголовков безопасности
        security_headers = [
            "X-Content-Type-Options",
            "X-Frame-Options",
            "X-XSS-Protection",
            "Content-Security-Policy"
        ]
        
        found_headers = []
        for header in security_headers:
            if header in headers:
                found_headers.append(header)
        
        if found_headers:
            test_logger.success(f"Найдены заголовки безопасности: {found_headers}")
        else:
            test_logger.warning("Заголовки безопасности не найдены")
        
        test_logger.success("Проверка заголовков безопасности завершена")
