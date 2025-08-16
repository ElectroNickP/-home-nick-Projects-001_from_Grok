#!/usr/bin/env python3
"""
Проверка текущего статуса системы
"""
import subprocess
import time
import requests
import os

def check_processes():
    """Проверка запущенных процессов"""
    try:
        result = subprocess.run(["pgrep", "-f", "python.*app.py"], 
                              capture_output=True, text=True, timeout=5)
        if result.stdout.strip():
            pids = result.stdout.strip().split('\n')
            print(f"🔍 Найдены процессы app.py: {pids}")
            return pids
        else:
            print("✅ Нет запущенных процессов app.py")
            return []
    except Exception as e:
        print(f"❌ Ошибка проверки процессов: {e}")
        return []

def check_app_response():
    """Проверка ответа приложения"""
    try:
        response = requests.get("http://localhost:60183/", timeout=3)
        print(f"🌐 HTTP ответ: {response.status_code}")
        return response.status_code in [200, 401]
    except Exception as e:
        print(f"❌ Приложение не отвечает: {e}")
        return False

def check_pid_file():
    """Проверка PID файла"""
    try:
        if os.path.exists("src/app.pid"):
            with open("src/app.pid", "r") as f:
                pid = f.read().strip()
            print(f"📋 PID файл: {pid}")
            return pid
        else:
            print("ℹ️ PID файл не найден")
            return None
    except Exception as e:
        print(f"❌ Ошибка чтения PID: {e}")
        return None

def main():
    print("🔍 ПРОВЕРКА СТАТУСА СИСТЕМЫ")
    print("=" * 40)
    print(f"⏰ Время: {time.strftime('%H:%M:%S')}")
    print()
    
    # Проверяем процессы
    processes = check_processes()
    
    # Проверяем PID файл
    pid_file = check_pid_file()
    
    # Проверяем ответ приложения
    app_responding = check_app_response()
    
    print()
    print("📊 СТАТУС:")
    print(f"   Процессы: {len(processes)} запущено")
    print(f"   PID файл: {'Есть' if pid_file else 'Нет'}")
    print(f"   HTTP ответ: {'✅ Да' if app_responding else '❌ Нет'}")
    
    if app_responding:
        print("✅ СИСТЕМА ГОТОВА К ТЕСТИРОВАНИЮ")
    elif processes:
        print("⚠️ ПРОЦЕССЫ ЕСТЬ, НО ПРИЛОЖЕНИЕ НЕ ОТВЕЧАЕТ")
        print("💡 Попробуйте: pkill -f 'python.*app.py' && python src/app.py &")
    else:
        print("❌ СИСТЕМА НЕ ЗАПУЩЕНА")
        print("💡 Запустите: python src/app.py &")

if __name__ == "__main__":
    main()

