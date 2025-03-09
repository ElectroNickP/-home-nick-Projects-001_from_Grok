#!/bin/bash
set -e

# Проверка пользователя
echo ">>> Проверка пользователя..."
if [ "$USER" = "root" ]; then
    echo "Запуск от root, файлы будут принадлежать root"
else
    echo "Запуск от пользователя $USER"
fi

# Обновление пакетов и установка зависимостей
echo ">>> Обновление списка пакетов и установка системных зависимостей..."
sudo apt update
sudo apt install -y python3 python3-pip python3-venv ffmpeg git

# Установка рабочей директории
PROJECT_DIR="/opt/telegram_gpt_bot"
echo ">>> Создание директории проекта: $PROJECT_DIR"
sudo mkdir -p "$PROJECT_DIR"
sudo chown "$USER:$USER" "$PROJECT_DIR"
cd "$PROJECT_DIR"

# Создание виртуального окружения
echo ">>> Создание виртуального окружения..."
python3 -m venv bot_env
source bot_env/bin/activate

# Установка Python-зависимостей
echo ">>> Обновление pip и установка Python-зависимостей..."
cat << 'EOF' > requirements.txt
openai
aiogram
python-dotenv
pydub
flask
flask_httpauth
EOF
pip install --upgrade pip
pip install -r requirements.txt

# Создание .gitignore
echo ">>> Создание .gitignore..."
cat << 'EOF' > .gitignore
.env
__pycache__/
*.pyc
bot.log
bot_configs.json
nohup.out
EOF

# Создание server_and_bot.py
echo ">>> Создание server_and_bot.py с улучшениями..."
cat << 'EOF' > server_and_bot.py
#!/usr/bin/env python3
import os
import time
import asyncio
import threading
import logging
import json
import shutil
from flask import Flask, request, jsonify, render_template_string
from flask_httpauth import HTTPBasicAuth
from dotenv import load_dotenv
import openai
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.client.bot import DefaultBotProperties

# Глобальные блокировки
OPENAI_LOCK = threading.Lock()
BOT_CONFIGS_LOCK = threading.Lock()

# Настройка логирования
logging.basicConfig(
    level=logging.DEBUG,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
auth = HTTPBasicAuth()

# Авторизация
USERS = {
    "admin": "securepassword123"  # Измените на свои значения
}

@auth.verify_password
def verify_password(username, password):
    if username in USERS and USERS[username] == password:
        return username
    return None

# Глобальные структуры
BOT_CONFIGS = {}
NEXT_BOT_ID = 1
CONVERSATIONS = {}
CONFIG_FILE = "bot_configs.json"

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
            logger.info("Файл bot_configs.json не существует, будет создан новый")
    except Exception as e:
        logger.error(f"Ошибка загрузки конфигураций: {e}")

def save_configs_async():
    """Асинхронно сохраняет конфигурации в файл"""
    def save_task():
        try:
            # Проверка свободного места на диске
            statvfs = os.statvfs('/')
            free_space = statvfs.f_bavail * statvfs.f_frsize
            if free_space < 1024 * 1024:  # Меньше 1 МБ
                logger.error("Недостаточно места на диске для записи bot_configs.json")
                raise OSError("Недостаточно места на диске")

            if os.path.exists(CONFIG_FILE) and not os.access(CONFIG_FILE, os.W_OK):
                logger.error(f"Нет прав на запись в {CONFIG_FILE}")
                raise PermissionError(f"Нет прав на запись в {CONFIG_FILE}")

            with BOT_CONFIGS_LOCK:
                logger.debug("Запись конфигураций в файл: начата")
                data = {"bots": {str(k): v for k, v in BOT_CONFIGS.items()}}
                temp_file = CONFIG_FILE + '.tmp'
                with open(temp_file, 'w') as f:
                    json.dump(data, f, indent=2)
                os.replace(temp_file, CONFIG_FILE)
                logger.debug("Запись конфигураций в файл: завершена")
                logger.info("Конфигурации ботов сохранены в файл")
        except Exception as e:
            logger.error(f"Ошибка сохранения конфигураций: {e}")
            raise

    thread = threading.Thread(target=save_task, daemon=True)
    thread.start()
    thread.join(timeout=5)  # Ждем 5 секунд
    if thread.is_alive():
        logger.error("Таймаут записи конфигураций, процесс завис")
        raise TimeoutError("Таймаут записи конфигураций")

async def ask_openai(prompt, config, conversation_key):
    try:
        with OPENAI_LOCK:
            prev_key = openai.api_key if hasattr(openai, 'api_key') else None
            openai.api_key = config["openai_api_key"]
            if conversation_key in CONVERSATIONS:
                thread_id = CONVERSATIONS[conversation_key]
            else:
                thread_resp = openai.beta.threads.create()
                thread_id = thread_resp.id
                CONVERSATIONS[conversation_key] = thread_id
            openai.beta.threads.messages.create(thread_id=thread_id, role="user", content=prompt)
            run_resp = openai.beta.threads.runs.create(thread_id=thread_id, assistant_id=config["assistant_id"])
        start_time = time.time()
        timeout = 30
        while True:
            with OPENAI_LOCK:
                status = openai.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run_resp.id).status
            if status == "completed":
                break
            if time.time() - start_time > timeout:
                return "❌ Ошибка: Превышено время ожидания ответа от OpenAI."
            await asyncio.sleep(2)
        with OPENAI_LOCK:
            messages = openai.beta.threads.messages.list(thread_id=thread_id).data
            if prev_key is not None:
                openai.api_key = prev_key
        return messages[0].content[0].text.value
    except Exception as e:
        logger.exception("Ошибка в ask_openai:")
        return f"❌ Ошибка: {e}"

async def aiogram_bot(config, stop_event):
    bot = Bot(token=config["telegram_token"], default=DefaultBotProperties(parse_mode="HTML"))
    dp = Dispatcher()

    @dp.message(Command(commands=["start"]))
    async def cmd_start(message: types.Message):
        text = f"👋 Привет! Я бот {config.get('bot_name', '')}. Напиши сообщение, и я передам его в OpenAI."
        await message.answer(text)
        logger.info(f"User({message.from_user.id}) -> /start: {text} (бот: {config.get('bot_name', '')})")

    @dp.message()
    async def handle_message(message: types.Message):
        user_text = message.text
        conversation_key = f"{config['telegram_token']}_{message.from_user.id}"
        logger.info(f"User({message.from_user.id}) ({config.get('bot_name', '')}): {user_text}")
        response = await ask_openai(user_text, config, conversation_key)
        await message.answer(response)
        logger.info(f"Бот ({config.get('bot_name', '')}): {response}")

    logger.info(f"Запуск Telegram-бота {config.get('bot_name', '')}...")
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        stop_wait_task = asyncio.create_task(stop_event.wait())
        polling_task = asyncio.create_task(dp.start_polling(bot, handle_signals=False))
        done, pending = await asyncio.wait([polling_task, stop_wait_task], return_when=asyncio.FIRST_COMPLETED)
        if stop_wait_task in done:
            polling_task.cancel()
            logger.info(f"Остановка бота {config.get('bot_name', '')} по запросу.")
    except Exception as e:
        logger.exception(f"Ошибка в боте {config.get('bot_name', '')}:")
    finally:
        await bot.session.close()

def run_bot(bot_entry):
    loop = asyncio.new_event_loop()
    bot_entry["loop"] = loop
    bot_entry["status"] = "running"
    stop_event = asyncio.Event()
    bot_entry["stop_event"] = stop_event
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(aiogram_bot(bot_entry["config"], stop_event))
    except Exception as e:
        logger.exception(f"Ошибка в фоновом потоке для бота {bot_entry['config'].get('bot_name', '')}:")
    finally:
        bot_entry["status"] = "stopped"
        loop.close()
        bot_entry["loop"] = None
        bot_entry["thread"] = None
        bot_entry["stop_event"] = None

def serialize_bot_entry(bot_entry):
    return {
        "id": bot_entry["id"],
        "config": bot_entry["config"],
        "status": bot_entry["status"]
    }

MAIN_PAGE_TEMPLATE = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <title>Управление Telegram ботами</title>
    <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.0/css/bootstrap.min.css">
</head>
<body>
<div class="container">
    <h1 class="mt-4">Управление Telegram ботами</h1>
    <div class="card mt-4">
        <div class="card-header">Добавить нового бота</div>
        <div class="card-body">
            <form id="createBotForm">
                <div class="form-group">
                    <label for="bot_name">Название бота</label>
                    <input type="text" class="form-control" id="bot_name" required>
                </div>
                <div class="form-group">
                    <label for="telegram_token">Telegram Token</label>
                    <input type="text" class="form-control" id="telegram_token" required>
                </div>
                <div class="form-group">
                    <label for="openai_api_key">OpenAI API Key</label>
                    <input type="text" class="form-control" id="openai_api_key" required>
                </div>
                <div class="form-group">
                    <label for="assistant_id">Assistant ID</label>
                    <input type="text" class="form-control" id="assistant_id" required>
                </div>
                <button type="submit" class="btn btn-primary">Создать бота</button>
            </form>
        </div>
    </div>
    <h2 class="mt-4">Список ботов</h2>
    <table class="table table-bordered" id="botsTable">
        <thead>
            <tr>
                <th>ID</th>
                <th>Название</th>
                <th>Telegram Token</th>
                <th>OpenAI API Key</th>
                <th>Assistant ID</th>
                <th>Статус</th>
                <th>Действия</th>
            </tr>
        </thead>
        <tbody>
            {% for bot in bots %}
            <tr data-bot-id="{{ bot.id }}">
                <td>{{ bot.id }}</td>
                <td><span class="bot-name">{{ bot.config.bot_name }}</span></td>
                <td><span class="bot-token">{{ bot.config.telegram_token }}</span></td>
                <td><span class="bot-openai">{{ bot.config.openai_api_key }}</span></td>
                <td><span class="bot-assistant">{{ bot.config.assistant_id }}</span></td>
                <td class="bot-status">{{ bot.status }}</td>
                <td>
                    <button class="btn btn-sm btn-success start-btn">Старт</button>
                    <button class="btn btn-sm btn-warning stop-btn">Стоп</button>
                    <button class="btn btn-sm btn-info edit-btn">Редактировать</button>
                    <button class="btn btn-sm btn-danger delete-btn">Удалить</button>
                </td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</div>

<div class="modal fade" id="editModal" tabindex="-1" role="dialog" aria-labelledby="editModalLabel" aria-hidden="true">
  <div class="modal-dialog" role="document">
    <div class="modal-content">
      <div class="modal-header">
        <h5 class="modal-title" id="editModalLabel">Редактировать бота</h5>
        <button type="button" class="close" data-dismiss="modal" aria-label="Закрыть">
          <span aria-hidden="true">×</span>
        </button>
      </div>
      <div class="modal-body">
        <form id="editBotForm">
            <input type="hidden" id="edit_bot_id">
            <div class="form-group">
                <label for="edit_bot_name">Название бота</label>
                <input type="text" class="form-control" id="edit_bot_name" required>
            </div>
            <div class="form-group">
                <label for="edit_telegram_token">Telegram Token</label>
                <input type="text" class="form-control" id="edit_telegram_token" required>
            </div>
            <div class="form-group">
                <label for="edit_openai_api_key">OpenAI API Key</label>
                <input type="text" class="form-control" id="edit_openai_api_key" required>
            </div>
            <div class="form-group">
                <label for="edit_assistant_id">Assistant ID</label>
                <input type="text" class="form-control" id="edit_assistant_id" required>
            </div>
            <button type="submit" class="btn btn-primary">Сохранить изменения</button>
        </form>
      </div>
    </div>
  </div>
</div>

<script src="https://code.jquery.com/jquery-3.5.1.min.js" crossorigin="anonymous"></script>
<script src="https://stackpath.bootstrapcdn.com/bootstrap/4.5.0/js/bootstrap.bundle.min.js"></script>
<script>
$(document).ready(function() {
    $("#createBotForm").submit(function(e) {
        e.preventDefault();
        var data = {
            bot_name: $("#bot_name").val(),
            telegram_token: $("#telegram_token").val(),
            openai_api_key: $("#openai_api_key").val(),
            assistant_id: $("#assistant_id").val()
        };
        $.ajax({
            url: "/api/bots",
            method: "POST",
            contentType: "application/json",
            data: JSON.stringify(data),
            success: function(response) {
                alert("Бот успешно создан!");
                location.reload();
            },
            error: function(xhr) {
                var errorMsg = xhr.responseJSON && xhr.responseJSON.error ? xhr.responseJSON.error : "Неизвестная ошибка";
                alert("Ошибка при создании бота: " + errorMsg);
            }
        });
    });

    $(".edit-btn").click(function() {
        var row = $(this).closest("tr");
        var botId = row.data("bot-id");
        $("#edit_bot_id").val(botId);
        $("#edit_bot_name").val(row.find(".bot-name").text());
        $("#edit_telegram_token").val(row.find(".bot-token").text());
        $("#edit_openai_api_key").val(row.find(".bot-openai").text());
        $("#edit_assistant_id").val(row.find(".bot-assistant").text());
        $("#editModal").modal("show");
    });

    $("#editBotForm").submit(function(e) {
        e.preventDefault();
        var botId = $("#edit_bot_id").val();
        var data = {
            bot_name: $("#edit_bot_name").val(),
            telegram_token: $("#edit_telegram_token").val(),
            openai_api_key: $("#edit_openai_api_key").val(),
            assistant_id: $("#edit_assistant_id").val()
        };
        $.ajax({
            url: "/api/bots/" + botId,
            method: "PUT",
            contentType: "application/json",
            data: JSON.stringify(data),
            success: function(response) {
                $("#editModal").modal("hide");
                alert("Бот успешно обновлен!");
                location.reload();
            },
            error: function(xhr) {
                var errorMsg = xhr.responseJSON && xhr.responseJSON.error ? xhr.responseJSON.error : "Неизвестная ошибка";
                alert("Ошибка при редактировании бота: " + errorMsg);
            }
        });
    });

    $(".delete-btn").click(function() {
        if (!confirm("Удалить бота?")) return;
        var row = $(this).closest("tr");
        var botId = row.data("bot-id");
        $.ajax({
            url: "/api/bots/" + botId,
            method: "DELETE",
            success: function(response) {
                alert("Бот успешно удален!");
                location.reload();
            },
            error: function(xhr) {
                var errorMsg = xhr.responseJSON && xhr.responseJSON.error ? xhr.responseJSON.error : "Неизвестная ошибка";
                alert("Ошибка при удалении бота: " + errorMsg);
            }
        });
    });

    $(".start-btn").click(function() {
        var row = $(this).closest("tr");
        var botId = row.data("bot-id");
        $.ajax({
            url: "/api/bots/" + botId + "/start",
            method: "POST",
            success: function(response) {
                alert("Бот успешно запущен!");
                location.reload();
            },
            error: function(xhr) {
                var errorMsg = xhr.responseJSON && xhr.responseJSON.error ? xhr.responseJSON.error : "Неизвестная ошибка";
                alert("Ошибка при запуске бота: " + errorMsg);
            }
        });
    });

    $(".stop-btn").click(function() {
        var row = $(this).closest("tr");
        var botId = row.data("bot-id");
        $.ajax({
            url: "/api/bots/" + botId + "/stop",
            method: "POST",
            success: function(response) {
                alert("Бот успешно остановлен!");
                location.reload();
            },
            error: function(xhr) {
                var errorMsg = xhr.responseJSON && xhr.responseJSON.error ? xhr.responseJSON.error : "Неизвестная ошибка";
                alert("Ошибка при остановке бота: " + errorMsg);
            }
        });
    });
});
</script>
</body>
</html>
"""

@app.route("/")
@auth.login_required
def index_page():
    with BOT_CONFIGS_LOCK:
        bots_list = list(BOT_CONFIGS.values())
    return render_template_string(MAIN_PAGE_TEMPLATE, bots=bots_list)

@app.route("/api/bots", methods=["GET"])
@auth.login_required
def get_bots():
    with BOT_CONFIGS_LOCK:
        return jsonify([serialize_bot_entry(bot) for bot in BOT_CONFIGS.values()])

@app.route("/api/bots", methods=["POST"])
@auth.login_required
def create_bot():
    global NEXT_BOT_ID
    data = request.get_json()
    logger.info(f"Получен запрос на создание бота: {data}")
    required_fields = ["bot_name", "telegram_token", "openai_api_key", "assistant_id"]
    for field in required_fields:
        if field not in data or not data[field]:
            logger.error(f"Отсутствует обязательное поле: {field}")
            return jsonify({"error": f"Поле {field} обязательно"}), 400
    try:
        with BOT_CONFIGS_LOCK:
            logger.debug("Блокировка BOT_CONFIGS_LOCK получена")
            bot_id = NEXT_BOT_ID
            NEXT_BOT_ID += 1
            bot_entry = {
                "id": bot_id,
                "config": {
                    "bot_name": data["bot_name"],
                    "telegram_token": data["telegram_token"],
                    "openai_api_key": data["openai_api_key"],
                    "assistant_id": data["assistant_id"],
                },
                "status": "stopped",
                "thread": None,
                "loop": None,
                "stop_event": None,
            }
            BOT_CONFIGS[bot_id] = bot_entry
            logger.debug(f"Бот {bot_id} добавлен в BOT_CONFIGS")
        save_configs_async()  # Асинхронное сохранение
        logger.info(f"Бот {bot_id} успешно создан")
        logger.debug("Блокировка BOT_CONFIGS_LOCK освобождена после добавления")
        return jsonify(serialize_bot_entry(bot_entry)), 201
    except Exception as e:
        logger.error(f"Ошибка при создании бота: {e}")
        return jsonify({"error": f"Внутренняя ошибка сервера: {str(e)}"}), 500

@app.route("/api/bots/<int:bot_id>", methods=["PUT"])
@auth.login_required
def update_bot(bot_id):
    data = request.get_json()
    try:
        with BOT_CONFIGS_LOCK:
            if bot_id not in BOT_CONFIGS:
                logger.error(f"Бот с ID {bot_id} не найден")
                return jsonify({"error": "Бот не найден"}), 404
            bot_entry = BOT_CONFIGS[bot_id]
            if bot_entry["status"] == "running":
                logger.error(f"Попытка редактировать запущенный бот {bot_id}")
                return jsonify({"error": "Остановите бота перед редактированием"}), 400
            for field in ["bot_name", "telegram_token", "openai_api_key", "assistant_id"]:
                if field in data:
                    bot_entry["config"][field] = data[field]
        save_configs_async()
        logger.info(f"Бот {bot_id} успешно обновлен")
        return jsonify(serialize_bot_entry(bot_entry))
    except Exception as e:
        logger.error(f"Ошибка при обновлении бота {bot_id}: {e}")
        return jsonify({"error": f"Внутренняя ошибка сервера: {str(e)}"}), 500

@app.route("/api/bots/<int:bot_id>", methods=["DELETE"])
@auth.login_required
def delete_bot(bot_id):
    try:
        with BOT_CONFIGS_LOCK:
            if bot_id not in BOT_CONFIGS:
                logger.error(f"Бот с ID {bot_id} не найден")
                return jsonify({"error": "Бот не найден"}), 404
            bot_entry = BOT_CONFIGS[bot_id]
            if bot_entry["status"] == "running":
                logger.error(f"Попытка удалить запущенный бот {bot_id}")
                return jsonify({"error": "Остановите бота перед удалением"}), 400
            del BOT_CONFIGS[bot_id]
        save_configs_async()
        logger.info(f"Бот {bot_id} успешно удален")
        return jsonify({"success": True})
    except Exception as e:
        logger.error(f"Ошибка при удалении бота {bot_id}: {e}")
        return jsonify({"error": f"Внутренняя ошибка сервера: {str(e)}"}), 500

@app.route("/api/bots/<int:bot_id>/start", methods=["POST"])
@auth.login_required
def start_bot(bot_id):
    try:
        with BOT_CONFIGS_LOCK:
            if bot_id not in BOT_CONFIGS:
                logger.error(f"Бот с ID {bot_id} не найден")
                return jsonify({"error": "Бот не найден"}), 404
            bot_entry = BOT_CONFIGS[bot_id]
            if bot_entry["status"] == "running":
                logger.error(f"Бот {bot_id} уже запущен")
                return jsonify({"error": "Бот уже запущен"}), 400
            t = threading.Thread(target=run_bot, args=(bot_entry,), daemon=True)
            bot_entry["thread"] = t
            t.start()
            logger.info(f"Бот {bot_id} успешно запущен")
        return jsonify({"success": True, "bot": serialize_bot_entry(bot_entry)})
    except Exception as e:
        logger.error(f"Ошибка при запуске бота {bot_id}: {e}")
        return jsonify({"error": f"Внутренняя ошибка сервера: {str(e)}"}), 500

@app.route("/api/bots/<int:bot_id>/stop", methods=["POST"])
@auth.login_required
def stop_bot(bot_id):
    try:
        with BOT_CONFIGS_LOCK:
            if bot_id not in BOT_CONFIGS:
                logger.error(f"Бот с ID {bot_id} не найден")
                return jsonify({"error": "Бот не найден"}), 404
            bot_entry = BOT_CONFIGS[bot_id]
            if bot_entry["status"] != "running":
                logger.error(f"Бот {bot_id} не запущен")
                return jsonify({"error": "Бот не запущен"}), 400
            if bot_entry["loop"] and bot_entry["stop_event"]:
                bot_entry["loop"].call_soon_threadsafe(bot_entry["stop_event"].set)
                logger.info(f"Бот {bot_id} успешно остановлен")
        return jsonify({"success": True, "bot": serialize_bot_entry(bot_entry)})
    except Exception as e:
        logger.error(f"Ошибка при остановке бота {bot_id}: {e}")
        return jsonify({"error": f"Внутренняя ошибка сервера: {str(e)}"}), 500

def start_all_bots():
    with BOT_CONFIGS_LOCK:
        for bot_id, bot_entry in BOT_CONFIGS.items():
            if bot_entry["status"] == "stopped":
                t = threading.Thread(target=run_bot, args=(bot_entry,), daemon=True)
                bot_entry["thread"] = t
                t.start()
                logger.info(f"Автозапуск бота {bot_entry['config'].get('bot_name', '')}")

if __name__ == '__main__':
    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'w') as f:
            json.dump({"bots": {}}, f)
        os.chmod(CONFIG_FILE, 0o664)
        logger.info("Создан новый пустой файл bot_configs.json")
    elif not os.access(CONFIG_FILE, os.W_OK):
        logger.error(f"Нет прав на запись в {CONFIG_FILE}, исправляем...")
        os.chmod(CONFIG_FILE, 0o664)
        logger.info(f"Права на {CONFIG_FILE} исправлены")

    load_configs()
    start_all_bots()
    logger.info("Запуск Flask-сервера на http://0.0.0.0:5000 с внешним доступом")
    app.run(host="0.0.0.0", port=5000, debug=False, threaded=True)
EOF

chmod +x server_and_bot.py

echo ">>> Создание systemd-сервиса..."
sudo bash -c "cat <<EOF > /etc/systemd/system/telegram-gpt-bot.service
[Unit]
Description=Telegram GPT Bot Service
After=network.target

[Service]
ExecStart=$PROJECT_DIR/bot_env/bin/python3 $PROJECT_DIR/server_and_bot.py
WorkingDirectory=$PROJECT_DIR
Restart=always
User=$USER
Environment=PATH=$PROJECT_DIR/bot_env/bin:/usr/local/bin:/usr/bin:/bin

[Install]
WantedBy=multi-user.target
EOF"

echo ">>> Активация и запуск сервиса..."
sudo systemctl daemon-reload
sudo systemctl enable telegram-gpt-bot.service
sudo systemctl start telegram-gpt-bot.service

echo ">>> Проверка статуса сервиса..."
sudo systemctl status telegram-gpt-bot.service

echo ">>> Готово! Сервер доступен на http://<ваш_IP>:5000 с авторизацией (логин: admin, пароль: securepassword123)."
echo ">>> Измените логин и пароль в server_and_bot.py в разделе USERS."