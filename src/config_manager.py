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
                BOT_CONFIGS.update({int(k): v for k, v in data["bots"].items()})
                NEXT_BOT_ID = max([int(k) for k in data["bots"].keys()] + [0]) + 1
                logger.info("Конфигурации ботов загружены из файла")
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
                data = {"bots": {str(k): v for k, v in BOT_CONFIGS.items()}}
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
