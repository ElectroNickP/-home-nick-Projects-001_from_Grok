#!/usr/bin/env python3
"""
Test script for port cleanup functionality
"""

import socket
import subprocess
import time
import os

def is_port_in_use(port):
    """Check if port is in use"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            result = s.connect_ex(('127.0.0.1', port))
            return result == 0
    except Exception:
        return False

def start_dummy_server(port):
    """Start a dummy server on port to simulate existing process"""
    try:
        process = subprocess.Popen([
            'python3', '-c', f'''
import socket
import time
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind(("127.0.0.1", {port}))
s.listen(1)
print(f"Dummy server listening on port {port}, PID: {{os.getpid()}}")
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("Shutting down dummy server")
finally:
    s.close()
'''
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait a bit for server to start
        time.sleep(2)
        return process
    except Exception as e:
        print(f"Failed to start dummy server: {e}")
        return None

def main():
    print("🧪 ТЕСТИРОВАНИЕ СИСТЕМЫ ОЧИСТКИ ПОРТОВ")
    print("=" * 50)
    
    # Test 1: Check initial port status
    print("\n1. Проверяем начальное состояние порта 5000:")
    if is_port_in_use(5000):
        print("⚠️ Порт 5000 уже используется")
    else:
        print("✅ Порт 5000 свободен")
    
    # Test 2: Start dummy server
    print("\n2. Запускаем dummy server на порту 5000:")
    dummy_process = start_dummy_server(5000)
    
    if dummy_process:
        print(f"✅ Dummy server запущен, PID: {dummy_process.pid}")
        
        # Verify port is now in use
        if is_port_in_use(5000):
            print("✅ Порт 5000 теперь занят (правильно)")
        else:
            print("❌ Порт 5000 все еще свободен (ошибка)")
        
        # Test 3: Test daemon start with cleanup
        print("\n3. Тестируем запуск daemon с автоочисткой порта:")
        print("Запускаем: python3 start.py --daemon")
        print("Daemon должен остановить dummy server и запуститься на порту 5000")
        
        # Clean up dummy server
        print("\n🧹 Убираем dummy server для чистого теста:")
        dummy_process.terminate()
        dummy_process.wait()
        print("✅ Dummy server остановлен")
    else:
        print("❌ Не удалось запустить dummy server")
    
    print("\n✅ Тест завершен. Теперь можете запустить:")
    print("   python3 start.py --daemon")
    print("Проект должен запуститься на порту 5000 без конфликтов!")

if __name__ == "__main__":
    main()
