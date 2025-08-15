import asyncio
import threading
import logging
from telegram_bot import aiogram_bot
from config_manager import BOT_CONFIGS, BOT_CONFIGS_LOCK

logger = logging.getLogger(__name__)

def run_bot(bot_entry):
    """Запускает бота в новом цикле событий asyncio."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    bot_entry["loop"] = loop
    bot_entry["status"] = "running"
    stop_event = asyncio.Event()
    bot_entry["stop_event"] = stop_event

    try:
        loop.run_until_complete(aiogram_bot(bot_entry["config"], stop_event))
    except Exception as e:
        logger.exception(f"Ошибка в потоке бота {bot_entry['config'].get('bot_name', '')}:")
    finally:
        bot_entry["status"] = "stopped"
        bot_entry["loop"] = None
        bot_entry["thread"] = None
        bot_entry["stop_event"] = None
        loop.close()

def start_bot_thread(bot_id):
    """Запускает поток для указанного бота."""
    with BOT_CONFIGS_LOCK:
        if bot_id not in BOT_CONFIGS:
            logger.error(f"Бот с ID {bot_id} не найден.")
            return False, "Бот не найден"

        bot_entry = BOT_CONFIGS[bot_id]
        if bot_entry.get("status") == "running":
            logger.warning(f"Бот {bot_id} уже запущен.")
            return False, "Бот уже запущен"

        thread = threading.Thread(target=run_bot, args=(bot_entry,), daemon=True)
        bot_entry["thread"] = thread
        thread.start()
        logger.info(f"Бот {bot_id} успешно запущен.")
        return True, "Бот запущен"

def stop_bot_thread(bot_id):
    """Останавливает поток для указанного бота."""
    with BOT_CONFIGS_LOCK:
        if bot_id not in BOT_CONFIGS:
            logger.error(f"Бот с ID {bot_id} не найден.")
            return False, "Бот не найден"

        bot_entry = BOT_CONFIGS[bot_id]
        if bot_entry.get("status") != "running":
            logger.warning(f"Бот {bot_id} не запущен.")
            return False, "Бот не запущен"

        if bot_entry.get("loop") and bot_entry.get("stop_event"):
            bot_entry["loop"].call_soon_threadsafe(bot_entry["stop_event"].set)
            logger.info(f"Запрос на остановку бота {bot_id} отправлен.")
            return True, "Бот останавливается"
        else:
            logger.error(f"Не удалось найти loop или stop_event для бота {bot_id}.")
            return False, "Внутренняя ошибка"

def start_all_bots():
    """Запускает всех ботов со статусом 'stopped'."""
    with BOT_CONFIGS_LOCK:
        bot_ids = list(BOT_CONFIGS.keys())
    for bot_id in bot_ids:
        start_bot_thread(bot_id)
