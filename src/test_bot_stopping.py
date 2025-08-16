#!/usr/bin/env python3
"""
Тест профессиональной остановки ботов
"""
import logging
import time
import sys
import os

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_bot_stopping():
    """Тест новой системы остановки ботов"""
    print("🧪 ТЕСТ ПРОФЕССИОНАЛЬНОЙ ОСТАНОВКИ БОТОВ")
    print("=" * 50)
    
    try:
        # Импортируем модули
        from bot_manager import stop_all_bots_for_update
        from config_manager import BOT_CONFIGS
        
        print("✅ Модули импортированы успешно")
        
        # Проверяем текущее состояние
        with open("bot_configs.json", "r", encoding='utf-8') as f:
            import json
            configs = json.load(f)
            
        print(f"📋 Найдено {len(configs)} ботов в конфигурации")
        
        # Показываем текущий статус ботов
        running_count = 0
        for bot_id, bot_data in BOT_CONFIGS.items():
            status = bot_data.get("status", "unknown")
            print(f"   Бот {bot_id}: {status}")
            if status == "running":
                running_count += 1
                
        print(f"🏃 Активных ботов: {running_count}")
        
        if running_count == 0:
            print("ℹ️ Нет активных ботов для тестирования остановки")
            print("💡 Запустите сначала приложение: python app.py")
            return
        
        # Тестируем профессиональную остановку
        print(f"\n🛑 Тестирую профессиональную остановку {running_count} ботов...")
        start_time = time.time()
        
        success, message = stop_all_bots_for_update(total_timeout=30)
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"⏱️ Остановка заняла: {duration:.2f} секунд")
        print(f"📊 Результат: {'✅ УСПЕХ' if success else '❌ ОШИБКА'}")
        print(f"📝 Сообщение: {message}")
        
        # Проверяем финальное состояние
        print(f"\n📋 Финальное состояние ботов:")
        stopped_count = 0
        for bot_id, bot_data in BOT_CONFIGS.items():
            status = bot_data.get("status", "unknown")
            print(f"   Бот {bot_id}: {status}")
            if status == "stopped":
                stopped_count += 1
        
        print(f"🛑 Остановлено ботов: {stopped_count}")
        
        if success and stopped_count == running_count:
            print("🎉 ТЕСТ ПРОШЕЛ УСПЕШНО!")
            return True
        else:
            print("❌ ТЕСТ НЕ ПРОШЕЛ!")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка теста: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_bot_stopping()
    sys.exit(0 if success else 1)

