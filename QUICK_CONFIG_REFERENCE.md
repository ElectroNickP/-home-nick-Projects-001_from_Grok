# 🚀 Quick Configuration Reference

## 📍 **Файлы конфигурации теперь здесь:**
```
/home/nick/.telegram-bot-manager/
├── configs/bots.json      # ⚙️ Настройки ботов
├── secrets/secrets.env    # 🔐 Токены (chmod 600)
└── backups/              # 💾 Резервные копии
```

## 🤖 **Новая функция: Автоматическое имя бота**
При создании бота через веб-интерфейс имя заполняется автоматически из Telegram API!
Просто введите токен → имя появится автоматически 🎉

## ⚡ **Быстрые команды:**

### Просмотр
```bash
# Показать все боты
python scripts/config_manager_cli.py show

# Конкретный бот
python scripts/config_manager_cli.py show --bot-id 1
```

### Управление ботами
```bash
# Изменить имя бота
python scripts/config_manager_cli.py update-bot --id 1 --name "Новое имя"

# Включить/выключить AI
python scripts/config_manager_cli.py update-bot --id 1 --enable-ai true

# Изменить лимит контекста
python scripts/config_manager_cli.py update-bot --id 1 --context-limit 20
```

### Секреты
```bash
# Добавить токен
python scripts/config_manager_cli.py secret --add bot_2_token "123456:ABCD..."

# Список токенов
python scripts/config_manager_cli.py secret --list

# Удалить токен
python scripts/config_manager_cli.py secret --remove old_token
```

### Резервные копии
```bash
# Создать бэкап
python scripts/config_manager_cli.py backup --create

# Список бэкапов
python scripts/config_manager_cli.py backup --list

# Восстановить
python scripts/config_manager_cli.py restore --backup /путь/к/бэкапу --confirm
```

### Проверка
```bash
# Валидация
python scripts/config_manager_cli.py validate
```

## 🔄 **Обновление проекта:**
```bash
git pull origin main    # Конфиги остаются нетронутыми!
python src/app.py       # Просто перезапускаем
```

## 📱 **Быстрые проверки:**

### Статус системы
```python
from core.config.legacy_adapter import get_adapter
print(get_adapter().get_config_status())
```

### Текущие боты
```python
from core.config.legacy_adapter import get_adapter
configs = get_adapter().load_configs()
for bot_id, bot in configs.items():
    print(f"Bot {bot_id}: {bot['config']['bot_name']}")
```

## 🆘 **Экстренное восстановление:**
```bash
# Если что-то сломалось - восстанавливаем последний бэкап
python scripts/config_manager_cli.py backup --list
python scripts/config_manager_cli.py restore --backup [последний_бэкап] --confirm
```

---
**💡 Полная документация:** `docs/EXTERNAL_CONFIG_SYSTEM.md`
