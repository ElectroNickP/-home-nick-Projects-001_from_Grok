import os
import json
import logging
import threading

logger = logging.getLogger(__name__)

BOT_CONFIGS = {}
NEXT_BOT_ID = 1
CONVERSATIONS = {}
CONFIG_FILE = "bot_configs.json"

BOT_CONFIGS_LOCK = threading.Lock()
CONVERSATIONS_LOCK = threading.Lock()
OPENAI_LOCK = threading.Lock()

def load_configs():
    """Загружает конфигурации ботов из файла"""
    global NEXT_BOT_ID
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                data = json.load(f)
                BOT_CONFIGS.clear()
                for k, v in data["bots"].items():
                    # Восстанавливаем полную структуру бота с runtime полями
                    # При загрузке все боты останавливаются (runtime объекты не сохраняются)
                    bot_entry = {
                        "id": v["id"],
                        "config": v["config"],
                        "status": "stopped",  # Принудительно останавливаем все боты при перезапуске
                        "thread": None,
                        "loop": None,
                        "stop_event": None
                    }
                    BOT_CONFIGS[int(k)] = bot_entry
                
                NEXT_BOT_ID = max([int(k) for k in data["bots"].keys()] + [0]) + 1
                logger.info(f"Конфигурации ботов загружены из файла: {len(BOT_CONFIGS)} ботов")
        else:
            logger.info(f"Файл {CONFIG_FILE} не существует, будет создан новый")
    except Exception as e:
        logger.error(f"Ошибка загрузки конфигураций: {e}")

def save_configs_async():
    """Асинхронно сохраняет конфигурации в файл"""
    def save_task():
        try:
            if os.path.exists(CONFIG_FILE) and not os.access(CONFIG_FILE, os.W_OK):
                raise PermissionError(f"Нет прав на запись в {CONFIG_FILE}")

            with BOT_CONFIGS_LOCK:
                # Очищаем конфигурацию от несериализуемых объектов
                clean_configs = {}
                for k, v in BOT_CONFIGS.items():
                    clean_bot = {
                        "id": v["id"],
                        "config": v["config"],
                        "status": v.get("status", "stopped")
                        # Исключаем thread, loop, stop_event - они не сериализуются в JSON
                    }
                    clean_configs[str(k)] = clean_bot
                
                data = {"bots": clean_configs}
                temp_file = CONFIG_FILE + '.tmp'
                with open(temp_file, 'w') as f:
                    json.dump(data, f, indent=2)
                os.replace(temp_file, CONFIG_FILE)
                logger.info("Конфигурации ботов сохранены в файл")
        except Exception as e:
            logger.error(f"Ошибка сохранения конфигураций: {e}")
            raise

    thread = threading.Thread(target=save_task, daemon=True)
    thread.start()
