# 🔧 Background Service Setup Guide

## Запуск Telegram Bot Manager в фоновом режиме

Этот гайд покажет как настроить проект для работы в фоновом режиме на Ubuntu сервере через systemd.

### 🚀 Быстрая установка

1. **Клонируйте и настройте проект:**
```bash
git clone https://github.com/ElectroNickP/Telegram-Bot-Manager.git
cd Telegram-Bot-Manager
git checkout prod-test
```

2. **Установите сервис:**
```bash
./service-install.sh
```

3. **Запустите сервис:**
```bash
sudo systemctl start telegram-bot-manager
```

### 📋 Команды управления

#### Основные команды:
```bash
# Запуск сервиса
sudo systemctl start telegram-bot-manager

# Остановка сервиса  
sudo systemctl stop telegram-bot-manager

# Перезапуск сервиса
sudo systemctl restart telegram-bot-manager

# Статус сервиса
sudo systemctl status telegram-bot-manager

# Просмотр логов
sudo journalctl -u telegram-bot-manager -f
```

#### Удобный менеджер (рекомендуется):
```bash
# Используйте service-manager.sh для удобства
./service-manager.sh start     # Запустить
./service-manager.sh stop      # Остановить  
./service-manager.sh restart   # Перезапустить
./service-manager.sh status    # Статус
./service-manager.sh logs      # Живые логи
./service-manager.sh enable    # Автозапуск при загрузке
./service-manager.sh disable   # Отключить автозапуск
```

### ⚙️ Режимы запуска

#### Интерактивный режим (для разработки):
```bash
python3 start.py
```
- Показывает вывод в терминале
- Останавливается при закрытии SSH
- Подходит для тестирования

#### Фоновый режим через start.py:
```bash  
python3 start.py --daemon
# или
python3 start.py -d
```
- Запускается в фоне
- Но лучше использовать systemd сервис

#### Systemd сервис (рекомендуется для продакшена):
```bash
./service-manager.sh start
```
- Автоматический перезапуск при сбоях
- Логирование через journald
- Автозапуск при перезагрузке сервера
- Профессиональное управление

### 🔍 Мониторинг и логи

#### Просмотр статуса:
```bash
./service-manager.sh status
```

#### Просмотр логов в реальном времени:
```bash  
./service-manager.sh logs
```

#### Просмотр последних логов:
```bash
sudo journalctl -u telegram-bot-manager --since "1 hour ago"
```

### 🔧 Настройка автозапуска

#### Включить автозапуск при загрузке сервера:
```bash
./service-manager.sh enable
```

#### Отключить автозапуск:
```bash
./service-manager.sh disable
```

### 📁 Файлы сервиса

- `telegram-bot-manager.service` - конфигурация systemd сервиса
- `service-install.sh` - скрипт установки сервиса
- `service-manager.sh` - удобный менеджер сервиса

### 🔒 Безопасность

Сервис настроен с базовыми мерами безопасности:
- `NoNewPrivileges=true` - запрет повышения привилегий
- `PrivateTmp=true` - изолированный /tmp
- `ProtectSystem=strict` - защита системных директорий
- Ограничения памяти и задач

### ❌ Удаление сервиса

Если нужно полностью удалить сервис:
```bash
./service-manager.sh uninstall
```

### 🌐 Доступ к веб-интерфейсу

После запуска сервиса:
- **URL:** http://your-server-ip:5000
- **Логин:** admin  
- **Пароль:** securepassword123
- **Marketplace:** http://your-server-ip:5000/marketplace

### 🔄 Обновление проекта

При обновлении проекта:
```bash
git pull origin prod-test
./service-manager.sh restart
```

### 🆘 Решение проблем

#### Сервис не запускается:
```bash
sudo systemctl status telegram-bot-manager
sudo journalctl -u telegram-bot-manager
```

#### Порт занят:
Сервис автоматически найдет свободный порт (5001, 5002, etc.)

#### Права доступа:
Убедитесь что файлы принадлежат правильному пользователю:
```bash
sudo chown -R $USER:$USER /path/to/Telegram-Bot-Manager
```

### 📞 Поддержка

Если возникли проблемы:
1. Проверьте статус: `./service-manager.sh status`
2. Посмотрите логи: `./service-manager.sh logs`  
3. Перезапустите: `./service-manager.sh restart`

**🚀 Готово! Теперь ваш Telegram Bot Manager работает в фоновом режиме и будет автоматически запускаться при перезагрузке сервера.**
