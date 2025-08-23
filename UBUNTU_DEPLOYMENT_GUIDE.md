# Ubuntu Server Deployment Guide

## Быстрое развертывание на чистом Ubuntu сервере

### Требования
- Ubuntu 22.04+ 
- Python 3.11+
- Git

### Установка Python 3.11 (если не установлен)
```bash
sudo apt update
sudo apt install software-properties-common
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt install python3.11 python3.11-venv python3.11-pip
```

### Развертывание проекта

1. **Клонировать репозиторий:**
```bash
git clone https://github.com/ElectroNickP/Telegram-Bot-Manager.git
cd Telegram-Bot-Manager
git checkout prod-test
```

2. **Запустить проект:**

**Вариант A (Рекомендуемый):** Полная настройка с виртуальным окружением
```bash
python3 start.py
```

**Вариант B:** Быстрый запуск для продакшена
```bash
python3 start-prod.py
```

### Доступ к приложению

После запуска будет доступно:
- **Web Interface:** http://localhost:5000
- **Login:** admin / securepassword123  
- **Marketplace:** http://localhost:5000/marketplace

### Решение проблем

1. **Порт занят:** Скрипт автоматически найдет свободный порт
2. **Python < 3.11:** Установите Python 3.11 по инструкции выше
3. **Нет интернета:** Убедитесь что есть доступ к PyPI для установки зависимостей

### Проверка работы
```bash
curl http://localhost:5000/
```

Должен вернуть HTML страницу (код 200).
