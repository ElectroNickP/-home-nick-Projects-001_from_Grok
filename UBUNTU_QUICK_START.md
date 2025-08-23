# 🚀 Ubuntu Quick Start

## Проблема решена! 

Проект теперь корректно развертывается на чистом Ubuntu.

### Единственная команда для запуска:

```bash
git clone https://github.com/ElectroNickP/Telegram-Bot-Manager.git
cd Telegram-Bot-Manager
git checkout prod-test
python3 start.py
```

### Что делает start.py автоматически:

✅ Проверяет версию Python (нужна 3.11+)  
✅ Создает виртуальное окружение (решает проблему externally-managed-environment)  
✅ Устанавливает зависимости  
✅ Находит свободный порт (если 5000 занят)  
✅ Запускает веб-сервер  

### Если Python < 3.11:

```bash
sudo apt update
sudo apt install software-properties-common  
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt install python3.11 python3.11-venv
```

### Результат:

- 🌐 Web Interface: http://localhost:5000
- 🔐 Login: admin / securepassword123
- 🏪 Marketplace: http://localhost:5000/marketplace

### Проверка:
```bash
curl http://localhost:5000/
```

## ✅ Готово к продакшену!

Проект полностью готов к развертыванию на любом Ubuntu сервере.
