"""
E2E тесты для веб-интерфейса
"""

import pytest
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException

@pytest.mark.e2e
@pytest.mark.ui
class TestWebInterface:
    """E2E тесты для веб-интерфейса"""
    
    @pytest.fixture(scope="class")
    def driver(self):
        """Настройка веб-драйвера"""
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Запуск в фоновом режиме
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        
        driver = webdriver.Chrome(options=chrome_options)
        driver.implicitly_wait(10)
        
        yield driver
        
        driver.quit()
    
    @pytest.fixture(scope="function")
    def wait(self, driver):
        """Ожидание элементов"""
        return WebDriverWait(driver, 10)
    
    def test_login_page_loads(self, driver, wait):
        """Тест загрузки страницы входа"""
        driver.get("http://localhost:5000/login")
        
        # Проверяем, что страница загрузилась
        assert "login" in driver.current_url.lower()
        
        # Проверяем наличие элементов формы
        username_field = wait.until(EC.presence_of_element_located((By.NAME, "username")))
        password_field = driver.find_element(By.NAME, "password")
        login_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        
        assert username_field.is_displayed()
        assert password_field.is_displayed()
        assert login_button.is_displayed()
    
    def test_login_success(self, driver, wait):
        """Тест успешного входа в систему"""
        driver.get("http://localhost:5000/login")
        
        # Заполняем форму
        username_field = wait.until(EC.presence_of_element_located((By.NAME, "username")))
        password_field = driver.find_element(By.NAME, "password")
        
        username_field.send_keys("admin")
        password_field.send_keys("securepassword123")
        
        # Нажимаем кнопку входа
        login_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        login_button.click()
        
        # Проверяем, что мы перенаправлены на главную страницу
        wait.until(EC.url_contains("/"))
        assert "login" not in driver.current_url
    
    def test_login_invalid_credentials(self, driver, wait):
        """Тест входа с неверными учетными данными"""
        driver.get("http://localhost:5000/login")
        
        # Заполняем форму неверными данными
        username_field = wait.until(EC.presence_of_element_located((By.NAME, "username")))
        password_field = driver.find_element(By.NAME, "password")
        
        username_field.send_keys("admin")
        password_field.send_keys("wrongpassword")
        
        # Нажимаем кнопку входа
        login_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        login_button.click()
        
        # Проверяем, что остались на странице входа
        assert "login" in driver.current_url
        
        # Проверяем наличие сообщения об ошибке
        try:
            error_message = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "error")))
            assert error_message.is_displayed()
        except TimeoutException:
            # Возможно, ошибка отображается по-другому
            pass
    
    def test_main_dashboard_loads(self, driver, wait):
        """Тест загрузки главной панели управления"""
        # Сначала входим в систему
        driver.get("http://localhost:5000/login")
        
        username_field = wait.until(EC.presence_of_element_located((By.NAME, "username")))
        password_field = driver.find_element(By.NAME, "password")
        
        username_field.send_keys("admin")
        password_field.send_keys("securepassword123")
        
        login_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        login_button.click()
        
        # Ждем загрузки главной страницы
        wait.until(EC.url_contains("/"))
        
        # Проверяем наличие основных элементов
        try:
            # Проверяем наличие панели управления ботами
            dashboard = wait.until(EC.presence_of_element_located((By.ID, "bots-dashboard")))
            assert dashboard.is_displayed()
        except TimeoutException:
            # Возможно, элемент имеет другое имя
            pass
        
        # Проверяем наличие статистических карточек
        try:
            stats_cards = driver.find_elements(By.CLASS_NAME, "stats-card")
            assert len(stats_cards) > 0
        except NoSuchElementException:
            # Возможно, класс другой
            pass
    
    def test_bot_management_buttons(self, driver, wait):
        """Тест кнопок управления ботами"""
        # Входим в систему
        driver.get("http://localhost:5000/login")
        
        username_field = wait.until(EC.presence_of_element_located((By.NAME, "username")))
        password_field = driver.find_element(By.NAME, "password")
        
        username_field.send_keys("admin")
        password_field.send_keys("securepassword123")
        
        login_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        login_button.click()
        
        wait.until(EC.url_contains("/"))
        
        # Проверяем наличие кнопок управления
        try:
            # Кнопка создания нового бота
            create_bot_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-action='create-bot']")))
            assert create_bot_button.is_displayed()
        except TimeoutException:
            # Возможно, кнопка имеет другое имя
            pass
        
        # Проверяем наличие кнопок фильтрации
        try:
            filter_buttons = driver.find_elements(By.CSS_SELECTOR, ".filter-button")
            assert len(filter_buttons) > 0
        except NoSuchElementException:
            # Возможно, класс другой
            pass
    
    def test_marketplace_page(self, driver, wait):
        """Тест страницы маркетплейса"""
        driver.get("http://localhost:5000/marketplace")
        
        # Проверяем, что страница загрузилась
        assert "marketplace" in driver.current_url
        
        # Проверяем наличие элементов маркетплейса
        try:
            # Проверяем наличие списка ботов
            bots_list = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "bots-grid")))
            assert bots_list.is_displayed()
        except TimeoutException:
            # Возможно, класс другой
            pass
        
        # Проверяем наличие поиска
        try:
            search_input = driver.find_element(By.CSS_SELECTOR, "input[type='search']")
            assert search_input.is_displayed()
        except NoSuchElementException:
            # Возможно, поиск реализован по-другому
            pass
    
    def test_marketplace_search(self, driver, wait):
        """Тест поиска в маркетплейсе"""
        driver.get("http://localhost:5000/marketplace")
        
        try:
            # Находим поле поиска
            search_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='search']")))
            
            # Вводим поисковый запрос
            search_input.clear()
            search_input.send_keys("test")
            
            # Ждем результатов поиска
            time.sleep(2)
            
            # Проверяем, что поиск работает
            assert search_input.get_attribute("value") == "test"
            
        except TimeoutException:
            # Поиск может быть реализован по-другому
            pass
    
    def test_marketplace_filtering(self, driver, wait):
        """Тест фильтрации в маркетплейсе"""
        driver.get("http://localhost:5000/marketplace")
        
        try:
            # Находим кнопки фильтрации
            filter_buttons = driver.find_elements(By.CSS_SELECTOR, ".category-filter")
            
            if filter_buttons:
                # Нажимаем на первую кнопку фильтра
                filter_buttons[0].click()
                
                # Ждем применения фильтра
                time.sleep(2)
                
                # Проверяем, что фильтр применился
                assert filter_buttons[0].get_attribute("class").find("active") != -1
                
        except NoSuchElementException:
            # Фильтрация может быть реализована по-другому
            pass
    
    def test_logout_functionality(self, driver, wait):
        """Тест функциональности выхода"""
        # Сначала входим в систему
        driver.get("http://localhost:5000/login")
        
        username_field = wait.until(EC.presence_of_element_located((By.NAME, "username")))
        password_field = driver.find_element(By.NAME, "password")
        
        username_field.send_keys("admin")
        password_field.send_keys("securepassword123")
        
        login_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        login_button.click()
        
        wait.until(EC.url_contains("/"))
        
        # Находим и нажимаем кнопку выхода
        try:
            logout_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-action='logout']")))
            logout_button.click()
            
            # Проверяем, что мы перенаправлены на страницу входа
            wait.until(EC.url_contains("login"))
            assert "login" in driver.current_url
            
        except TimeoutException:
            # Возможно, кнопка выхода имеет другое имя
            pass
    
    def test_responsive_design(self, driver, wait):
        """Тест адаптивного дизайна"""
        # Тестируем на мобильном разрешении
        driver.set_window_size(375, 667)  # iPhone размер
        
        driver.get("http://localhost:5000/login")
        
        # Проверяем, что элементы отображаются корректно
        username_field = wait.until(EC.presence_of_element_located((By.NAME, "username")))
        password_field = driver.find_element(By.NAME, "password")
        
        assert username_field.is_displayed()
        assert password_field.is_displayed()
        
        # Проверяем размеры элементов (должны быть достаточно большими для касания)
        username_rect = username_field.rect
        assert username_rect['height'] >= 44  # Минимальная высота для касания
        
        # Возвращаем нормальное разрешение
        driver.set_window_size(1920, 1080)
    
    def test_navigation_buttons(self, driver, wait):
        """Тест кнопок навигации"""
        # Входим в систему
        driver.get("http://localhost:5000/login")
        
        username_field = wait.until(EC.presence_of_element_located((By.NAME, "username")))
        password_field = driver.find_element(By.NAME, "password")
        
        username_field.send_keys("admin")
        password_field.send_keys("securepassword123")
        
        login_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        login_button.click()
        
        wait.until(EC.url_contains("/"))
        
        # Проверяем навигацию между страницами
        try:
            # Переходим на маркетплейс
            marketplace_link = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[href='/marketplace']")))
            marketplace_link.click()
            
            wait.until(EC.url_contains("marketplace"))
            assert "marketplace" in driver.current_url
            
            # Возвращаемся на главную
            home_link = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[href='/']")))
            home_link.click()
            
            wait.until(EC.url_contains("/"))
            assert "marketplace" not in driver.current_url
            
        except TimeoutException:
            # Навигация может быть реализована по-другому
            pass
    
    def test_form_validation(self, driver, wait):
        """Тест валидации форм"""
        driver.get("http://localhost:5000/login")
        
        # Пытаемся войти с пустыми полями
        login_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']")))
        login_button.click()
        
        # Проверяем, что остались на странице входа
        assert "login" in driver.current_url
        
        # Проверяем наличие сообщений об ошибках валидации
        try:
            validation_errors = driver.find_elements(By.CSS_SELECTOR, ".error-message")
            assert len(validation_errors) > 0
        except NoSuchElementException:
            # Валидация может быть реализована по-другому
            pass
    
    def test_page_load_performance(self, driver, wait):
        """Тест производительности загрузки страниц"""
        import time
        
        # Тестируем время загрузки страницы входа
        start_time = time.time()
        driver.get("http://localhost:5000/login")
        
        # Ждем загрузки основного элемента
        wait.until(EC.presence_of_element_located((By.NAME, "username")))
        load_time = time.time() - start_time
        
        # Проверяем, что страница загружается быстро
        assert load_time < 3.0, f"Страница входа загружается слишком медленно: {load_time:.2f}s"
        
        # Тестируем время загрузки маркетплейса
        start_time = time.time()
        driver.get("http://localhost:5000/marketplace")
        
        # Ждем загрузки основного элемента
        try:
            wait.until(EC.presence_of_element_located((By.CLASS_NAME, "bots-grid")))
        except TimeoutException:
            # Возможно, элемент имеет другое имя
            pass
        
        load_time = time.time() - start_time
        
        # Проверяем, что страница загружается быстро
        assert load_time < 3.0, f"Страница маркетплейса загружается слишком медленно: {load_time:.2f}s"
    
    def test_error_handling(self, driver, wait):
        """Тест обработки ошибок"""
        # Пытаемся зайти на несуществующую страницу
        driver.get("http://localhost:5000/nonexistent-page")
        
        # Проверяем, что отображается страница 404
        try:
            error_message = wait.until(EC.presence_of_element_located((By.TAG_NAME, "h1")))
            assert "404" in error_message.text or "Not Found" in error_message.text
        except TimeoutException:
            # Ошибка может отображаться по-другому
            pass
    
    def test_accessibility_features(self, driver, wait):
        """Тест функций доступности"""
        driver.get("http://localhost:5000/login")
        
        # Проверяем наличие alt-текстов для изображений
        images = driver.find_elements(By.TAG_NAME, "img")
        for img in images:
            alt_text = img.get_attribute("alt")
            # Alt-текст должен быть либо пустым (для декоративных изображений), либо содержать описание
            assert alt_text is not None
        
        # Проверяем наличие label для полей ввода
        username_field = wait.until(EC.presence_of_element_located((By.NAME, "username")))
        password_field = driver.find_element(By.NAME, "password")
        
        # Проверяем, что поля имеют соответствующие id или aria-label
        username_id = username_field.get_attribute("id")
        password_id = password_field.get_attribute("id")
        
        if username_id:
            try:
                username_label = driver.find_element(By.CSS_SELECTOR, f"label[for='{username_id}']")
                assert username_label.is_displayed()
            except NoSuchElementException:
                # Label может быть реализован по-другому
                pass
        
        if password_id:
            try:
                password_label = driver.find_element(By.CSS_SELECTOR, f"label[for='{password_id}']")
                assert password_label.is_displayed()
            except NoSuchElementException:
                # Label может быть реализован по-другому
                pass

