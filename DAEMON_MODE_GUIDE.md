# 🚀 Daemon Mode Guide - Простой фоновый запуск

## Обзор

Telegram Bot Manager поддерживает **истинный Unix daemon режим**, который позволяет запускать проект в фоновом режиме с профессиональным управлением процессами.

## 🎯 В чем разница от systemd?

| Особенность | Daemon Mode (`--daemon`) | Systemd Service |
|-------------|--------------------------|-----------------|
| **Простота** | Одна команда | Требует установки |
| **Управление** | PID файлы | systemctl команды |
| **Автозапуск** | Нет | При загрузке системы |
| **Мониторинг** | Базовый | Полный (journald) |
| **Использование** | Временный запуск | Постоянная служба |

## ⚡ Быстрый старт

### Запуск в фоновом режиме:
```bash
python3 start.py --daemon
```

### Проверка статуса:
```bash
python3 start.py --status
```

### Остановка:
```bash
python3 start.py --stop
```

## 📋 Полное руководство

### 1. Запуск daemon
```bash
# Полная команда
python3 start.py --daemon

# Короткая версия
python3 start.py -d
```

**Что происходит:**
- ✅ Проверяется что daemon не запущен
- ✅ Настраивается виртуальное окружение  
- ✅ Устанавливаются зависимости
- ✅ Процесс отключается от терминала
- ✅ Создается PID файл для управления
- ✅ Настраиваются signal handlers
- ✅ Запускается Flask приложение

### 2. Проверка статуса
```bash
python3 start.py --status
```

**Показывает:**
- PID процесса
- Статус (запущен/остановлен)
- Расположение PID файла
- Дополнительная информация (если установлен psutil)

### 3. Остановка daemon
```bash
python3 start.py --stop
```

**Что происходит:**
- ✅ Отправляется SIGTERM сигнал процессу
- ✅ Ожидается graceful shutdown (до 10 секунд)
- ✅ Если не останавливается - отправляется SIGKILL
- ✅ Удаляется PID файл

## 🔧 Управление процессом

### PID файл
Daemon создает файл `telegram-bot-manager.pid` в корне проекта:
```bash
# Посмотреть PID
cat telegram-bot-manager.pid

# Проверить что процесс запущен
ps -p $(cat telegram-bot-manager.pid)
```

### Signal handling
Daemon корректно обрабатывает сигналы:
- `SIGTERM` - graceful shutdown
- `SIGINT` - graceful shutdown  
- `SIGKILL` - принудительная остановка (не рекомендуется)

### Логи
В daemon режиме логи не выводятся в терминал. Для логирования используйте:
```bash
# Перенаправление в файл при запуске
python3 start.py --daemon 2>&1 | tee daemon.log

# Или используйте systemd для продакшена
./service-install.sh
./service-manager.sh logs
```

## 🚦 Примеры использования

### Быстрое тестирование
```bash
# Запуск
python3 start.py --daemon
# ✅ Daemon started successfully! PID: 12345

# Проверка 
python3 start.py --status  
# ✅ Daemon is running (PID: 12345)

# Остановка
python3 start.py --stop
# ✅ Daemon stopped successfully
```

### Проверка работы после отключения SSH
```bash
# На сервере
python3 start.py --daemon
python3 start.py --status

# Отключаемся от SSH
exit

# Подключаемся снова
ssh user@server
cd /path/to/project

# Проверяем что daemon все еще работает
python3 start.py --status
# ✅ Daemon is running (PID: 12345)

# Веб-интерфейс доступен
curl http://localhost:5000
```

## ⚠️ Важные особенности

### 1. Daemon отключается от терминала
После запуска daemon полностью отключается от терминала:
- Нет вывода в консоль
- Не реагирует на Ctrl+C
- Работает независимо от SSH сессии

### 2. Проверка перед запуском
```bash
python3 start.py --daemon
# ⚠️ Daemon is already running (PID: 12345)
# ℹ️ Use 'python start.py --stop' to stop it first
```

### 3. Обработка портов
Daemon автоматически находит свободный порт:
```bash
python3 start.py --daemon
# ℹ️ Daemon will start in background
# 🌐 Web Interface will be available at: http://127.0.0.1:5001
# ⚠️ Port 5000 is busy, using port 5001
```

## 🔒 Безопасность

### PID файл защита
- PID файл создается с правами текущего пользователя
- Автоматическое удаление stale PID файлов  
- Проверка что процесс действительно запущен

### Signal handling
- Graceful shutdown при получении SIGTERM
- Автоматическая очистка при завершении
- Защита от zombie процессов

## 🆘 Решение проблем

### Daemon не запускается
```bash
# Проверьте что нет другого экземпляра
python3 start.py --status

# Остановите если запущен
python3 start.py --stop

# Запустите заново
python3 start.py --daemon
```

### PID файл остался после сбоя
```bash
# Проверьте что процесс не запущен
ps -p $(cat telegram-bot-manager.pid)

# Если процесса нет - удалите PID файл
rm telegram-bot-manager.pid

# Запустите заново
python3 start.py --daemon
```

### Нужны подробные логи
Для продакшена рекомендуется использовать systemd:
```bash
./service-install.sh
./service-manager.sh start
./service-manager.sh logs  # Живые логи
```

## 📊 Мониторинг

### Базовый мониторинг
```bash
# Статус каждые 10 секунд
watch -n 10 'python3 start.py --status'

# Мониторинг через htop
htop -p $(cat telegram-bot-manager.pid)
```

### Расширенный мониторинг (требует psutil)
```bash
pip install psutil
python3 start.py --status
# ✅ Daemon is running (PID: 12345)
# ℹ️ CPU: 1.2%
# ℹ️ Memory: 45.3 MB  
# ℹ️ Started: 1693123456.789
```

## 🚀 Заключение

Daemon режим идеально подходит для:
- **Быстрого тестирования** на продакшен серверах
- **Временного развертывания** без настройки systemd
- **Разработки** когда нужен фоновый режим
- **Простого управления** одной командой

Для постоянного продакшн использования рекомендуется systemd сервис с полным мониторингом и автозапуском.

**🎯 Используйте `python3 start.py --daemon` когда нужно быстро и просто запустить проект в фоне!**
