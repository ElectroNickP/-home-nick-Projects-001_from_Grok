#!/usr/bin/env python3
"""
Запуск приложения для тестирования новой системы остановки ботов
БЕЗ ЗАВИСАЮЩИХ КОМАНД!
"""
import subprocess
import time
import os
import sys
import signal

def kill_existing_processes():
    """Убиваем существующие процессы приложения"""
    try:
        result = subprocess.run(["pkill", "-f", "python.*app.py"], 
                              capture_output=True, timeout=5)
        print("🛑 Существующие процессы остановлены")
        time.sleep(2)
    except:
        print("ℹ️ Нет существующих процессов для остановки")

def start_app():
    """Запускаем приложение в фоне"""
    try:
        os.chdir("src")
        
        # Запускаем приложение
        process = subprocess.Popen([
            sys.executable, "app.py"
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        print(f"🚀 Приложение запущено с PID: {process.pid}")
        
        # Сохраняем PID для дальнейшего использования
        with open("app.pid", "w") as f:
            f.write(str(process.pid))
        
        return process.pid
        
    except Exception as e:
        print(f"❌ Ошибка запуска приложения: {e}")
        return None

def wait_for_app():
    """Ждем, пока приложение не станет готово"""
    print("⏳ Ожидание готовности приложения...")
    
    for attempt in range(15):  # 15 попыток по 2 секунды = 30 секунд
        try:
            import requests
            response = requests.get("http://localhost:60183/", timeout=2)
            if response.status_code in [200, 401]:  # 401 = нужна аутентификация (это норма)
                print("✅ Приложение готово к работе!")
                return True
        except:
            pass
        
        time.sleep(2)
        print(f"   Попытка {attempt + 1}/15...")
    
    print("❌ Приложение не отвечает")
    return False

def create_test_commit():
    """Создаем тестовый коммит для автообновления"""
    try:
        os.chdir("..")  # Возвращаемся в корень проекта
        
        # Добавляем строку в README для создания изменений
        with open("README.md", "a", encoding='utf-8') as f:
            f.write(f"\n# Test auto-update at {time.strftime('%H:%M:%S')}\n")
        
        # Коммитим изменения
        subprocess.run(["git", "add", "README.md"], timeout=10, check=True)
        subprocess.run(["git", "commit", "-m", "test: trigger auto-update"], timeout=10, check=True)
        
        print("✅ Тестовый коммит создан")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка создания коммита: {e}")
        return False

def main():
    print("🔧 ТЕСТ ПРОФЕССИОНАЛЬНОЙ ОСТАНОВКИ БОТОВ")
    print("=" * 60)
    print("✅ Новая функция: stop_all_bots_for_update()")
    print("✅ Таймауты для каждого бота")
    print("✅ Ожидание завершения потоков")
    print("✅ Принудительная очистка состояния")
    print("✅ НЕТ DEADLOCK'ов!")
    print("=" * 60)
    
    # Шаг 1: Остановка существующих процессов
    kill_existing_processes()
    
    # Шаг 2: Запуск приложения
    pid = start_app()
    if not pid:
        print("❌ Не удалось запустить приложение")
        return 1
    
    # Шаг 3: Ожидание готовности
    if not wait_for_app():
        print("❌ Приложение не готово")
        return 1
    
    # Шаг 4: Создание тестового коммита
    if not create_test_commit():
        print("❌ Не удалось создать тестовый коммит")
        return 1
    
    print("\n🎯 ГОТОВ К ТЕСТИРОВАНИЮ!")
    print("🌐 Веб-интерфейс: http://localhost:60183/")
    print("🔑 Логин: admin / Пароль: securepassword123")
    print("🧪 Тест остановки ботов: python src/test_bot_stopping.py")
    print("🔄 Тест автообновления: нажмите 'Update Application' в веб-интерфейсе")
    print(f"🛑 Остановка приложения: kill {pid}")
    
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n🛑 Прервано пользователем")
        sys.exit(1)

