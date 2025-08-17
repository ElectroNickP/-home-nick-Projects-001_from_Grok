#!/usr/bin/env python3
"""
Комплексный тест нового интерфейса с правильной работой сессий
"""

import requests
import json
import time
import sys
from datetime import datetime

# Конфигурация
BASE_URL = "http://localhost:60183"
CREDENTIALS = ("admin", "securepassword123")

def log(message, level="INFO"):
    """Логирование с временными метками"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {level}: {message}")

class SessionManager:
    """Менеджер сессий для работы с Flask"""
    
    def __init__(self, base_url):
        self.base_url = base_url
        self.session = requests.Session()
        self.logged_in = False
    
    def login(self, username, password):
        """Вход в систему через API"""
        url = f"{self.base_url}/api/login"
        data = {"username": username, "password": password}
        headers = {"Content-Type": "application/json"}
        
        response = self.session.post(url, json=data, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                self.logged_in = True
                log("✅ Успешная авторизация через API")
                return True
        
        log(f"❌ Ошибка авторизации: {response.status_code}", "ERROR")
        return False
    
    def get(self, endpoint):
        """GET запрос с сессией"""
        url = f"{self.base_url}{endpoint}"
        return self.session.get(url)
    
    def post(self, endpoint, data=None):
        """POST запрос с сессией"""
        url = f"{self.base_url}{endpoint}"
        headers = {"Content-Type": "application/json"}
        return self.session.post(url, json=data, headers=headers)
    
    def logout(self):
        """Выход из системы"""
        self.get("/logout")
        self.logged_in = False
        log("✅ Выход из системы")

def test_authentication(session_mgr):
    """Тест системы авторизации"""
    log("🔐 Тестирование системы авторизации...")
    
    # Тест без авторизации
    response = session_mgr.get("/api/v2/system/health")
    if response.status_code == 401:
        log("✅ API требует авторизацию (безопасность)")
    else:
        log("❌ API не требует авторизацию (небезопасно)", "ERROR")
        return False
    
    # Тест с авторизацией
    if session_mgr.login(*CREDENTIALS):
        response = session_mgr.get("/api/v2/system/health")
        if response.status_code == 200:
            log("✅ Авторизация работает корректно")
            return True
        else:
            log(f"❌ Ошибка после авторизации: {response.status_code}", "ERROR")
            return False
    else:
        return False

def test_system_endpoints(session_mgr):
    """Тест системных API endpoints"""
    log("🔧 Тестирование системных endpoints...")
    
    endpoints = [
        ("GET", "/api/v2/system/health", "Health Check"),
        ("GET", "/api/v2/system/info", "System Info"),
        ("GET", "/api/v2/system/stats", "System Stats"),
    ]
    
    for method, endpoint, name in endpoints:
        if method == "GET":
            response = session_mgr.get(endpoint)
        else:
            response = session_mgr.post(endpoint)
            
        if response.status_code == 200:
            log(f"✅ {name}: {endpoint}")
        else:
            log(f"❌ {name}: {endpoint} - {response.status_code}", "ERROR")
            return False
    
    return True

def test_bots_endpoints(session_mgr):
    """Тест API endpoints для управления ботами"""
    log("🤖 Тестирование API управления ботами...")
    
    # Получение списка ботов
    response = session_mgr.get("/api/v2/bots")
    if response.status_code == 200:
        bots_data = response.json()
        log(f"✅ Получен список ботов: {len(bots_data.get('data', []))} ботов")
        
        bots_list = bots_data.get('data', [])
        if isinstance(bots_list, list) and len(bots_list) > 0:
            bot_id = bots_list[0]['id']
            
            # Тест получения статуса конкретного бота
            status_response = session_mgr.get(f"/api/v2/bots/{bot_id}/status")
            if status_response.status_code == 200:
                log(f"✅ Статус бота {bot_id} получен")
            else:
                log(f"❌ Ошибка получения статуса бота {bot_id}", "ERROR")
                return False
        else:
            log("⚠️ Нет ботов для тестирования")
            return True
    else:
        log(f"❌ Ошибка получения списка ботов: {response.status_code}", "ERROR")
        return False
    
    return True

def test_marketplace_api():
    """Тест API маркетплейса (публичный)"""
    log("🏪 Тестирование API маркетплейса...")
    
    # Публичный endpoint маркетплейса
    response = requests.get(f"{BASE_URL}/api/marketplace/bots")
    if response.status_code == 200:
        marketplace_data = response.json()
        log(f"✅ Маркетплейс API работает: {len(marketplace_data.get('data', []))} ботов")
        return True
    else:
        log(f"❌ Ошибка маркетплейса API: {response.status_code}", "ERROR")
        return False

def test_web_interface():
    """Тест веб-интерфейса"""
    log("🌐 Тестирование веб-интерфейса...")
    
    # Тест главной страницы (должна требовать авторизацию)
    response = requests.get(f"{BASE_URL}/")
    if response.status_code in [401, 302]:
        log("✅ Главная страница защищена авторизацией")
    else:
        log(f"⚠️ Главная страница не защищена: {response.status_code}")
    
    # Тест страницы авторизации
    response = requests.get(f"{BASE_URL}/login")
    if response.status_code == 200:
        log("✅ Страница авторизации доступна")
    else:
        log(f"❌ Ошибка страницы авторизации: {response.status_code}", "ERROR")
        return False
    
    # Тест маркетплейса (публичная страница)
    response = requests.get(f"{BASE_URL}/marketplace")
    if response.status_code == 200:
        log("✅ Публичная страница маркетплейса доступна")
    else:
        log(f"❌ Ошибка страницы маркетплейса: {response.status_code}", "ERROR")
        return False
    
    return True

def test_new_interface_features(session_mgr):
    """Тест новых функций интерфейса"""
    log("🎨 Тестирование новых функций интерфейса...")
    
    # Получение главной страницы с авторизацией
    response = session_mgr.get("/")
    if response.status_code == 200:
        content = response.text
        
        # Проверка наличия новых элементов интерфейса
        new_features = [
            "bots-dashboard",
            "stats-cards", 
            "filter-buttons",
            "bots-grid",
            "bot-card",
            "feature-badges",
            "action-buttons"
        ]
        
        missing_features = []
        for feature in new_features:
            if feature not in content:
                missing_features.append(feature)
        
        if missing_features:
            log(f"❌ Отсутствуют элементы интерфейса: {missing_features}", "ERROR")
            return False
        else:
            log("✅ Все новые элементы интерфейса присутствуют")
        
        # Проверка CSS стилей
        css_features = [
            "linear-gradient",
            "backdrop-filter",
            "grid-template-columns",
            "animation: fadeInUp"
        ]
        
        missing_css = []
        for css in css_features:
            if css not in content:
                missing_css.append(css)
        
        if missing_css:
            log(f"⚠️ Отсутствуют CSS стили: {missing_css}", "WARNING")
        else:
            log("✅ Все CSS стили присутствуют")
        
        return True
    else:
        log(f"❌ Ошибка доступа к главной странице: {response.status_code}", "ERROR")
        return False

def test_bot_management(session_mgr):
    """Тест управления ботами через API"""
    log("⚙️ Тестирование управления ботами...")
    
    # Получение списка ботов
    response = session_mgr.get("/api/v2/bots")
    if response.status_code != 200:
        log("❌ Не удалось получить список ботов", "ERROR")
        return False
    
    bots_data = response.json()
    bots = bots_data.get('data', [])
    
    if not isinstance(bots, list) or not bots:
        log("⚠️ Нет ботов для тестирования управления")
        return True
    
    bot_id = bots[0]['id']
    log(f"🔧 Тестирование управления ботом {bot_id}")
    
    # Тест получения информации о боте
    response = session_mgr.get(f"/api/v2/bots/{bot_id}")
    if response.status_code == 200:
        log("✅ Информация о боте получена")
    else:
        log(f"❌ Ошибка получения информации о боте: {response.status_code}", "ERROR")
        return False
    
    return True

def test_update_system(session_mgr):
    """Тест системы обновлений"""
    log("🔄 Тестирование системы обновлений...")
    
    # Проверка обновлений
    response = session_mgr.get("/api/check-updates")
    if response.status_code == 200:
        update_data = response.json()
        log(f"✅ Система обновлений работает: {update_data.get('has_updates', False)}")
        return True
    else:
        log(f"❌ Ошибка системы обновлений: {response.status_code}", "ERROR")
        return False

def main():
    """Основная функция тестирования"""
    log("🚀 Начало комплексного тестирования нового интерфейса")
    log("=" * 60)
    
    # Создаем менеджер сессий
    session_mgr = SessionManager(BASE_URL)
    
    tests = [
        ("Авторизация", lambda: test_authentication(session_mgr)),
        ("Системные endpoints", lambda: test_system_endpoints(session_mgr)),
        ("API ботов", lambda: test_bots_endpoints(session_mgr)),
        ("API маркетплейса", test_marketplace_api),
        ("Веб-интерфейс", test_web_interface),
        ("Новые функции интерфейса", lambda: test_new_interface_features(session_mgr)),
        ("Управление ботами", lambda: test_bot_management(session_mgr)),
        ("Система обновлений", lambda: test_update_system(session_mgr)),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        log(f"\n📋 Тест: {test_name}")
        try:
            if test_func():
                passed += 1
                log(f"✅ {test_name}: ПРОЙДЕН")
            else:
                log(f"❌ {test_name}: ПРОВАЛЕН", "ERROR")
        except Exception as e:
            import traceback
            log(f"❌ {test_name}: ОШИБКА - {str(e)}", "ERROR")
            log(f"📋 Детали ошибки: {traceback.format_exc()}", "ERROR")
    
    # Выход из системы
    session_mgr.logout()
    
    log("=" * 60)
    log(f"📊 РЕЗУЛЬТАТ: {passed}/{total} тестов пройдено")
    
    if passed == total:
        log("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ! Новый интерфейс работает корректно!")
        return True
    else:
        log(f"⚠️ {total - passed} тестов провалено. Требуется доработка.", "WARNING")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
