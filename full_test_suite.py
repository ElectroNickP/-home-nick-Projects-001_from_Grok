#!/usr/bin/env python3
"""
🧪 ПОЛНОЕ ТЕСТИРОВАНИЕ АВТООБНОВЛЕНИЯ
Все этапы без зависающих команд!
"""
import subprocess
import time
import os
import sys
import signal
import json
import requests
from requests.auth import HTTPBasicAuth

class AutoUpdateTester:
    def __init__(self):
        self.app_pid = None
        self.test_results = {}
        
    def log(self, message):
        print(f"[{time.strftime('%H:%M:%S')}] {message}")
        
    def step(self, step_name):
        print(f"\n🔸 ЭТАП: {step_name}")
        print("=" * 60)
        
    def kill_existing_processes(self):
        """Убиваем существующие процессы"""
        try:
            result = subprocess.run(["pkill", "-f", "python.*app.py"], 
                                  capture_output=True, timeout=5)
            self.log("🛑 Существующие процессы остановлены")
            time.sleep(3)
            return True
        except Exception as e:
            self.log(f"ℹ️ Нет существующих процессов: {e}")
            return True
            
    def start_app(self):
        """Запуск приложения"""
        try:
            os.chdir("src")
            
            # Запускаем приложение
            process = subprocess.Popen([
                sys.executable, "app.py"
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            self.app_pid = process.pid
            self.log(f"🚀 Приложение запущено с PID: {self.app_pid}")
            
            # Сохраняем PID
            with open("app.pid", "w") as f:
                f.write(str(self.app_pid))
                
            return True
            
        except Exception as e:
            self.log(f"❌ Ошибка запуска приложения: {e}")
            return False
            
    def wait_for_app_ready(self, max_attempts=20):
        """Ожидание готовности приложения"""
        self.log("⏳ Ожидание готовности приложения...")
        
        for attempt in range(max_attempts):
            try:
                response = requests.get("http://localhost:60183/", timeout=2)
                if response.status_code in [200, 401]:
                    self.log("✅ Приложение готово к работе!")
                    return True
            except:
                pass
            
            time.sleep(2)
            self.log(f"   Попытка {attempt + 1}/{max_attempts}...")
        
        self.log("❌ Приложение не отвечает")
        return False
        
    def test_bot_stopping(self):
        """Тест системы остановки ботов"""
        try:
            self.log("🧪 Тестирую систему остановки ботов...")
            
            # Импортируем модули (они должны быть доступны)
            sys.path.append('.')
            from bot_manager import stop_all_bots_for_update
            from config_manager import BOT_CONFIGS
            
            # Проверяем активные боты
            running_count = 0
            for bot_id, bot_data in BOT_CONFIGS.items():
                if bot_data.get("status") == "running":
                    running_count += 1
                    
            self.log(f"📋 Найдено {running_count} активных ботов")
            
            if running_count == 0:
                self.log("ℹ️ Нет активных ботов для тестирования")
                return True
            
            # Тестируем остановку
            start_time = time.time()
            success, message = stop_all_bots_for_update(total_timeout=30)
            duration = time.time() - start_time
            
            self.log(f"⏱️ Остановка заняла: {duration:.2f} сек")
            self.log(f"📊 Результат: {'✅ УСПЕХ' if success else '❌ ОШИБКА'}")
            self.log(f"📝 Сообщение: {message}")
            
            self.test_results['bot_stopping'] = {
                'success': success,
                'duration': duration,
                'message': message
            }
            
            return success
            
        except Exception as e:
            self.log(f"❌ Ошибка теста остановки: {e}")
            self.test_results['bot_stopping'] = {'success': False, 'error': str(e)}
            return False
            
    def create_test_commit(self):
        """Создание тестового коммита"""
        try:
            os.chdir("..")  # Возвращаемся в корень
            
            # Добавляем изменение в README
            timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
            with open("README.md", "a", encoding='utf-8') as f:
                f.write(f"\n# Full test auto-update at {timestamp}\n")
            
            # Коммитим
            subprocess.run(["git", "add", "README.md"], timeout=10, check=True)
            subprocess.run(["git", "commit", "-m", f"test: full auto-update test {timestamp}"], 
                          timeout=10, check=True)
            
            self.log("✅ Тестовый коммит создан")
            return True
            
        except Exception as e:
            self.log(f"❌ Ошибка создания коммита: {e}")
            return False
            
    def test_auto_update(self):
        """Тест полного автообновления"""
        try:
            self.log("🔄 Запуск автообновления через API...")
            
            # Запускаем автообновление
            start_time = time.time()
            response = requests.post(
                "http://localhost:60183/api/update",
                auth=HTTPBasicAuth('admin', 'securepassword123'),
                timeout=120  # 2 минуты на весь процесс
            )
            
            duration = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                self.log(f"✅ Автообновление завершено за {duration:.1f} сек")
                self.log(f"📊 Результат: {result}")
                
                self.test_results['auto_update'] = {
                    'success': True,
                    'duration': duration,
                    'result': result
                }
                return True
            else:
                self.log(f"❌ Автообновление провалилось: HTTP {response.status_code}")
                self.log(f"📄 Ответ: {response.text}")
                
                self.test_results['auto_update'] = {
                    'success': False,
                    'http_code': response.status_code,
                    'response': response.text
                }
                return False
                
        except Exception as e:
            self.log(f"❌ Ошибка автообновления: {e}")
            self.test_results['auto_update'] = {'success': False, 'error': str(e)}
            return False
            
    def check_app_after_update(self):
        """Проверка приложения после обновления"""
        try:
            self.log("🔍 Проверка приложения после обновления...")
            
            # Ждем немного для restart
            time.sleep(10)
            
            # Проверяем HTTP ответ
            for attempt in range(15):
                try:
                    response = requests.get("http://localhost:60183/", timeout=3)
                    if response.status_code in [200, 401]:
                        self.log("✅ Приложение отвечает после обновления!")
                        
                        # Проверяем API статус
                        status_response = requests.get(
                            "http://localhost:60183/api/update/status",
                            auth=HTTPBasicAuth('admin', 'securepassword123'),
                            timeout=5
                        )
                        
                        if status_response.status_code == 200:
                            status_data = status_response.json()
                            self.log(f"📊 Статус обновления: {status_data}")
                            
                            self.test_results['post_update_check'] = {
                                'success': True,
                                'status': status_data
                            }
                            return True
                        
                except:
                    pass
                
                time.sleep(2)
                self.log(f"   Попытка {attempt + 1}/15...")
            
            self.log("❌ Приложение не отвечает после обновления")
            self.test_results['post_update_check'] = {'success': False}
            return False
            
        except Exception as e:
            self.log(f"❌ Ошибка проверки после обновления: {e}")
            self.test_results['post_update_check'] = {'success': False, 'error': str(e)}
            return False
            
    def generate_report(self):
        """Генерация отчета о тестировании"""
        report = f"""
🧪 ОТЧЕТ О ПОЛНОМ ТЕСТИРОВАНИИ АВТООБНОВЛЕНИЯ
=====================================================
Время тестирования: {time.strftime('%Y-%m-%d %H:%M:%S')}

📊 РЕЗУЛЬТАТЫ:
"""
        
        for test_name, result in self.test_results.items():
            status = "✅ УСПЕХ" if result.get('success') else "❌ ОШИБКА"
            report += f"\n{test_name}: {status}"
            if 'duration' in result:
                report += f" ({result['duration']:.1f}с)"
            if 'error' in result:
                report += f" - {result['error']}"
                
        report += f"\n\n🎯 ОБЩИЙ РЕЗУЛЬТАТ: "
        all_success = all(r.get('success', False) for r in self.test_results.values())
        report += "✅ ВСЕ ТЕСТЫ ПРОШЛИ!" if all_success else "❌ ЕСТЬ ПРОБЛЕМЫ!"
        
        return report
        
    def run_full_test(self):
        """Запуск полного теста"""
        print("🧪 ПОЛНОЕ ТЕСТИРОВАНИЕ АВТООБНОВЛЕНИЯ")
        print("=" * 80)
        
        # Этап 1: Подготовка
        self.step("ПОДГОТОВКА")
        if not self.kill_existing_processes():
            return False
            
        # Этап 2: Запуск приложения
        self.step("ЗАПУСК ПРИЛОЖЕНИЯ")
        if not self.start_app():
            return False
            
        if not self.wait_for_app_ready():
            return False
            
        # Этап 3: Тест остановки ботов
        self.step("ТЕСТ ОСТАНОВКИ БОТОВ")
        self.test_bot_stopping()
        
        # Этап 4: Создание тестового коммита
        self.step("СОЗДАНИЕ ТЕСТОВОГО КОММИТА")
        if not self.create_test_commit():
            return False
            
        # Этап 5: Тест автообновления
        self.step("ТЕСТ АВТООБНОВЛЕНИЯ")
        if not self.test_auto_update():
            return False
            
        # Этап 6: Проверка после обновления
        self.step("ПРОВЕРКА ПОСЛЕ ОБНОВЛЕНИЯ")
        self.check_app_after_update()
        
        # Этап 7: Отчет
        self.step("ФИНАЛЬНЫЙ ОТЧЕТ")
        report = self.generate_report()
        print(report)
        
        # Сохраняем отчет
        with open("test_report.txt", "w", encoding='utf-8') as f:
            f.write(report)
            
        return True

def main():
    tester = AutoUpdateTester()
    try:
        success = tester.run_full_test()
        return 0 if success else 1
    except KeyboardInterrupt:
        print("\n🛑 Тестирование прервано пользователем")
        return 1
    except Exception as e:
        print(f"\n❌ Критическая ошибка тестирования: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())

