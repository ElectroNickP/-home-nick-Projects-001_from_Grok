#!/usr/bin/env python3
"""
Простой тест автообновления по частям
"""
import subprocess
import time
import os
import sys

def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}")

def test_step_1():
    """Шаг 1: Убить существующие процессы и запустить приложение"""
    log("🔸 ШАГ 1: Запуск приложения")
    
    # Убиваем процессы
    try:
        subprocess.run(["pkill", "-f", "python.*app.py"], timeout=5, capture_output=True)
        log("🛑 Процессы остановлены")
        time.sleep(2)
    except:
        log("ℹ️ Нет процессов для остановки")
    
    # Запускаем приложение
    try:
        os.chdir("src")
        process = subprocess.Popen([sys.executable, "app.py"], 
                                 stdout=subprocess.DEVNULL, 
                                 stderr=subprocess.DEVNULL)
        
        with open("app.pid", "w") as f:
            f.write(str(process.pid))
            
        log(f"🚀 Приложение запущено с PID: {process.pid}")
        
        # Ждем запуска
        log("⏳ Ожидание готовности...")
        time.sleep(10)
        
        return True
    except Exception as e:
        log(f"❌ Ошибка: {e}")
        return False

def test_step_2():
    """Шаг 2: Проверить готовность приложения"""
    log("🔸 ШАГ 2: Проверка готовности")
    
    try:
        import requests
        
        for i in range(10):
            try:
                response = requests.get("http://localhost:60183/", timeout=2)
                if response.status_code in [200, 401]:
                    log("✅ Приложение готово!")
                    return True
            except:
                pass
            time.sleep(2)
            log(f"   Попытка {i+1}/10...")
            
        log("❌ Приложение не отвечает")
        return False
        
    except Exception as e:
        log(f"❌ Ошибка: {e}")
        return False

def test_step_3():
    """Шаг 3: Создать тестовый коммит"""
    log("🔸 ШАГ 3: Создание тестового коммита")
    
    try:
        os.chdir("..")
        
        # Добавляем строку в README
        with open("README.md", "a") as f:
            f.write(f"\n# Test at {time.strftime('%H:%M:%S')}\n")
        
        # Коммитим
        subprocess.run(["git", "add", "README.md"], timeout=10)
        subprocess.run(["git", "commit", "-m", "test: auto-update trigger"], timeout=10)
        
        log("✅ Коммит создан")
        return True
        
    except Exception as e:
        log(f"❌ Ошибка: {e}")
        return False

def test_step_4():
    """Шаг 4: Тест автообновления"""
    log("🔸 ШАГ 4: Тест автообновления")
    
    try:
        import requests
        from requests.auth import HTTPBasicAuth
        
        # Запускаем автообновление
        response = requests.post(
            "http://localhost:60183/api/update",
            auth=HTTPBasicAuth('admin', 'securepassword123'),
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            log(f"✅ Автообновление: {result.get('message', 'Выполнено')}")
            return True
        else:
            log(f"❌ HTTP {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        log(f"❌ Ошибка: {e}")
        return False

if __name__ == "__main__":
    print("🧪 ПРОСТОЙ ТЕСТ АВТООБНОВЛЕНИЯ")
    print("=" * 50)
    
    steps = [test_step_1, test_step_2, test_step_3, test_step_4]
    
    for i, step in enumerate(steps, 1):
        if not step():
            print(f"\n❌ ТЕСТ ПРОВАЛИЛСЯ НА ШАГЕ {i}")
            sys.exit(1)
        time.sleep(2)  # Небольшая пауза между шагами
    
    print(f"\n🎉 ВСЕ ШАГИ ПРОШЛИ УСПЕШНО!")
    print("🔍 Проверьте веб-интерфейс: http://localhost:60183/")

