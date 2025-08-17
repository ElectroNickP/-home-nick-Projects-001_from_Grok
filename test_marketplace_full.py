#!/usr/bin/env python3
"""
Полное тестирование маркетплейса ботов v3.2.0
"""
import requests
import json
import time
from datetime import datetime

BASE_URL = "http://localhost:60183"
AUTH = ("admin", "securepassword123")

def test_endpoint(method, url, auth=None, json_data=None, description=""):
    """Тестирует API endpoint"""
    print(f"\n🧪 {description}")
    print(f"   {method} {url}")
    
    try:
        if method == "GET":
            response = requests.get(url, auth=auth, timeout=10)
        elif method == "POST":
            response = requests.post(url, auth=auth, json=json_data, timeout=10)
        elif method == "PUT":
            response = requests.put(url, auth=auth, json=json_data, timeout=10)
        elif method == "DELETE":
            response = requests.delete(url, auth=auth, timeout=10)
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code < 400:
            if 'application/json' in response.headers.get('content-type', ''):
                data = response.json()
                if isinstance(data, dict) and 'data' in data:
                    print(f"   ✅ SUCCESS - Data items: {len(data.get('data', []))}")
                elif isinstance(data, dict) and 'success' in data:
                    print(f"   ✅ SUCCESS - {data.get('message', 'OK')}")
                else:
                    print(f"   ✅ SUCCESS - Response: {str(data)[:100]}...")
            else:
                print(f"   ✅ SUCCESS - HTML content: {len(response.text)} chars")
        else:
            print(f"   ❌ ERROR - {response.text[:200]}")
            
        return response
        
    except Exception as e:
        print(f"   💥 EXCEPTION - {str(e)}")
        return None

def main():
    print("🚀 Полное тестирование Telegram Bot Manager v3.2.0 с маркетплейсом")
    print("=" * 70)
    
    # 1. Проверяем основные страницы
    print("\n📄 ТЕСТИРОВАНИЕ СТРАНИЦ:")
    test_endpoint("GET", f"{BASE_URL}/", AUTH, description="Админ-панель")
    test_endpoint("GET", f"{BASE_URL}/marketplace", description="Маркетплейс (публичный)")
    
    # 2. Проверяем API v2 документацию
    print("\n📚 ТЕСТИРОВАНИЕ ДОКУМЕНТАЦИИ:")
    test_endpoint("GET", f"{BASE_URL}/api/v2/docs", AUTH, description="API v2 документация")
    
    # 3. Тестируем Marketplace API
    print("\n🏪 ТЕСТИРОВАНИЕ MARKETPLACE API:")
    test_endpoint("GET", f"{BASE_URL}/api/marketplace/categories", description="Категории маркетплейса")
    test_endpoint("GET", f"{BASE_URL}/api/marketplace/bots", description="Боты маркетплейса")
    test_endpoint("GET", f"{BASE_URL}/api/marketplace/bots?category=assistant", description="Фильтр по категории")
    test_endpoint("GET", f"{BASE_URL}/api/marketplace/bots?search=AI", description="Поиск ботов")
    test_endpoint("GET", f"{BASE_URL}/api/marketplace/bots?featured=true", description="Featured боты")
    
    # 4. Тестируем API v2
    print("\n🔧 ТЕСТИРОВАНИЕ API v2:")
    test_endpoint("GET", f"{BASE_URL}/api/v2/system/health", AUTH, description="System health")
    test_endpoint("GET", f"{BASE_URL}/api/v2/system/info", AUTH, description="System info")
    test_endpoint("GET", f"{BASE_URL}/api/v2/bots", AUTH, description="Список ботов v2")
    
    # 5. Проверяем существующих ботов
    print("\n🤖 ТЕСТИРОВАНИЕ БОТОВ:")
    response = test_endpoint("GET", f"{BASE_URL}/api/bots", AUTH, description="Список ботов v1")
    if response and response.status_code == 200:
        bots = response.json()
        print(f"   📊 Найдено ботов: {len(bots)}")
        
        for bot in bots:
            bot_id = bot['id']
            marketplace = bot['config'].get('marketplace', {})
            enabled = marketplace.get('enabled', False)
            print(f"   🤖 Bot {bot_id}: {bot['config']['bot_name']} - marketplace: {enabled}")
            
            # Тестируем детальную страницу если в маркетплейсе
            if enabled:
                test_endpoint("GET", f"{BASE_URL}/marketplace/{bot_id}", description=f"Детальная страница бота {bot_id}")
    
    # 6. Создаем тестового бота если нужно
    print("\n🔨 СОЗДАНИЕ ТЕСТОВОГО БОТА:")
    test_bot_data = {
        "bot_name": "Test Marketplace Bot",
        "telegram_token": "123456789:AABBccDDeeFFggHHiiJJkkLLmmNNooP_TEST",
        "openai_api_key": "sk-test1234567890abcdefghijklmnopqrstuvwxyz",
        "assistant_id": "asst_test123456789",
        "group_context_limit": 15,
        "enable_ai_responses": True,
        "enable_voice_responses": False,
        "marketplace": {
            "enabled": True,
            "title": "Test Bot for Marketplace",
            "description": "Тестовый бот для проверки функций маркетплейса",
            "category": "productivity",
            "username": "test_marketplace_bot",
            "website": "https://test.example.com",
            "image_url": "https://via.placeholder.com/300x300/28a745/ffffff?text=TEST+BOT",
            "tags": ["тест", "маркетплейс", "productivity"],
            "featured": False,
            "rating": 3.5,
            "total_users": 42,
            "last_updated": datetime.now().strftime("%Y-%m-%d")
        }
    }
    
    create_response = test_endpoint("POST", f"{BASE_URL}/api/bots", AUTH, test_bot_data, 
                                  description="Создание тестового бота")
    
    if create_response and create_response.status_code == 201:
        new_bot = create_response.json()
        new_bot_id = new_bot['id']
        print(f"   ✅ Создан тестовый бот ID: {new_bot_id}")
        
        # Проверяем что он появился в маркетплейсе
        time.sleep(1)
        marketplace_response = test_endpoint("GET", f"{BASE_URL}/api/marketplace/bots", 
                                           description="Проверка нового бота в маркетплейсе")
        
        if marketplace_response and marketplace_response.status_code == 200:
            marketplace_bots = marketplace_response.json()
            bot_found = any(bot['id'] == new_bot_id for bot in marketplace_bots.get('data', []))
            print(f"   {'✅' if bot_found else '❌'} Бот {'найден' if bot_found else 'НЕ найден'} в маркетплейсе")
    
    print("\n" + "=" * 70)
    print("✅ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО!")
    print(f"🕐 Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("📊 Результаты показаны выше")

if __name__ == "__main__":
    main()
