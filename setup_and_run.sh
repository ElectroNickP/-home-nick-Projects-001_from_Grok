#!/bin/bash
set -e

# Цвета для вывода
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Функция для вывода шагов
step() {
    echo -e "${GREEN}>>> Шаг $1: $2${NC}"
}

# Функция для ошибок
error() {
    echo -e "${RED}✘ Ошибка: $1${NC}" >&2
    exit 1
}

# Функция для предупреждений
warn() {
    echo -e "${YELLOW}⚠ Внимание: $1${NC}"
}

# Проверка пользователя
step 1 "Проверка текущего пользователя..."
if [ "$USER" = "root" ]; then
    warn "Скрипт запущен от root. Файлы будут принадлежать root."
else
    echo "Запуск от пользователя: $USER"
fi

# Подтверждение установки
echo -e "${YELLOW}Готовимся установить Telegram GPT Bot. Продолжить? (y/n)${NC}"
read -r confirm
if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
    error "Установка отменена пользователем."
fi

# Обновление пакетов и установка зависимостей
step 2 "Обновление пакетов и установка зависимостей..."
sudo apt update || error "Не удалось обновить список пакетов."
sudo apt install -y python3 python3-pip python3-venv ffmpeg git || error "Не удалось установить зависимости."

# Установка рабочей директории
PROJECT_DIR="/opt/telegram_gpt_bot"
step 3 "Создание директории проекта: $PROJECT_DIR"
sudo mkdir -p "$PROJECT_DIR" || error "Не удалось создать директорию $PROJECT_DIR."
sudo chown "$USER:$USER" "$PROJECT_DIR" || error "Не удалось изменить владельца директории."
cd "$PROJECT_DIR" || error "Не удалось перейти в директорию $PROJECT_DIR."

# Создание виртуального окружения
step 4 "Создание виртуального окружения..."
python3 -m venv bot_env || error "Не удалось создать виртуальное окружение."
source bot_env/bin/activate || error "Не удалось активировать виртуальное окружение."

# Установка Python-зависимостей
step 5 "Установка Python-зависимостей..."
cat << 'EOF' > requirements.txt
openai
aiogram
python-dotenv
pydub
flask
flask_httpauth
EOF
pip install --upgrade pip || error "Не удалось обновить pip."
pip install -r requirements.txt || error "Не удалось установить зависимости из requirements.txt."

# Создание .gitignore
step 6 "Создание .gitignore..."
cat << 'EOF' > .gitignore
.env
__pycache__/
*.pyc
bot.log
bot_configs.json
nohup.out
EOF

# Создание server_and_bot.py
step 7 "Создание основного скрипта server_and_bot.py..."
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
    thread.join(timeout=5)
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
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Управление Telegram ботами</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css">
    <style>
        body { background-color: #f8f9fa; }
        .status-running { color: green; font-weight: bold; }
        .status-stopped { color: red; font-weight: bold; }
        .spinner { display: none; }
        .table-responsive { max-height: 60vh; overflow-y: auto; }
    </style>
</head>
<body>
<div class="container py-4">
    <h1 class="mb-4">Управление Telegram ботами</h1>
    <div class="alert alert-warning" role="alert">
        ⚠ Внимание: Измените логин и пароль в server_and_bot.py (раздел USERS) для безопасности!
    </div>

    <div class="card mb-4">
        <div class="card-header">Добавить нового бота</div>
        <div class="card-body">
            <form id="createBotForm">
                <div class="row g-3">
                    <div class="col-md-6">
                        <label for="bot_name" class="form-label">Название бота</label>
                        <input type="text" class="form-control" id="bot_name" required>
                    </div>
                    <div class="col-md-6">
                        <label for="telegram_token" class="form-label">Telegram Token</label>
                        <input type="text" class="form-control" id="telegram_token" required>
                    </div>
                    <div class="col-md-6">
                        <label for="openai_api_key" class="form-label">OpenAI API Key</label>
                        <input type="text" class="form-control" id="openai_api_key" required>
                    </div>
                    <div class="col-md-6">
                        <label for="assistant_id" class="form-label">Assistant ID</label>
                        <input type="text" class="form-control" id="assistant_id" required>
                    </div>
                    <div class="col-12">
                        <button type="submit" class="btn btn-primary" id="createBtn">
                            <span class="spinner-border spinner-border-sm spinner" role="status" aria-hidden="true"></span>
                            Создать бота
                        </button>
                    </div>
                </div>
            </form>
        </div>
    </div>

    <div class="mb-3">
        <input type="text" class="form-control" id="searchBots" placeholder="Поиск по названию бота...">
    </div>

    <h2 class="mb-3">Список ботов</h2>
    <div class="table-responsive">
        <table class="table table-hover align-middle" id="botsTable">
            <thead class="table-dark">
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
                    <td class="bot-name">{{ bot.config.bot_name }}</td>
                    <td class="bot-token text-break">{{ bot.config.telegram_token }}</td>
                    <td class="bot-openai text-break">{{ bot.config.openai_api_key }}</td>
                    <td class="bot-assistant">{{ bot.config.assistant_id }}</td>
                    <td class="bot-status {% if bot.status == 'running' %}status-running{% else %}status-stopped{% endif %}">
                        {{ bot.status }}
                    </td>
                    <td>
                        <button class="btn btn-sm btn-success start-btn" {% if bot.status == 'running' %}disabled{% endif %}>
                            <span class="spinner-border spinner-border-sm spinner" role="status" aria-hidden="true"></span>
                            Старт
                        </button>
                        <button class="btn btn-sm btn-warning stop-btn" {% if bot.status != 'running' %}disabled{% endif %}>
                            <span class="spinner-border spinner-border-sm spinner" role="status" aria-hidden="true"></span>
                            Стоп
                        </button>
                        <button class="btn btn-sm btn-info edit-btn">Редактировать</button>
                        <button class="btn btn-sm btn-danger delete-btn">Удалить</button>
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
</div>

<div class="modal fade" id="editModal" tabindex="-1" aria-labelledby="editModalLabel" aria-hidden="true">
    <div class="modal-dialog">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title" id="editModalLabel">Редактировать бота</h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
            </div>
            <div class="modal-body">
                <form id="editBotForm">
                    <input type="hidden" id="edit_bot_id">
                    <div class="mb-3">
                        <label for="edit_bot_name" class="form-label">Название бота</label>
                        <input type="text" class="form-control" id="edit_bot_name" required>
                    </div>
                    <div class="mb-3">
                        <label for="edit_telegram_token" class="form-label">Telegram Token</label>
                        <input type="text" class="form-control" id="edit_telegram_token" required>
                    </div>
                    <div class="mb-3">
                        <label for="edit_openai_api_key" class="form-label">OpenAI API Key</label>
                        <input type="text" class="form-control" id="edit_openai_api_key" required>
                    </div>
                    <div class="mb-3">
                        <label for="edit_assistant_id" class="form-label">Assistant ID</label>
                        <input type="text" class="form-control" id="edit_assistant_id" required>
                    </div>
                    <button type="submit" class="btn btn-primary" id="saveEditBtn">
                        <span class="spinner-border spinner-border-sm spinner" role="status" aria-hidden="true"></span>
                        Сохранить
                    </button>
                </form>
            </div>
        </div>
    </div>
</div>

<script src="https://code.jquery.com/jquery-3.7.1.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>
<script>
$(document).ready(function() {
    function showSpinner(btn) { $(btn).find('.spinner').show(); $(btn).prop('disabled', true); }
    function hideSpinner(btn) { $(btn).find('.spinner').hide(); $(btn).prop('disabled', false); }

    $("#createBotForm").submit(function(e) {
        e.preventDefault();
        showSpinner('#createBtn');
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
                hideSpinner('#createBtn');
                alert("Бот успешно создан!");
                location.reload();
            },
            error: function(xhr) {
                hideSpinner('#createBtn');
                var errorMsg = xhr.responseJSON?.error || "Неизвестная ошибка";
                alert("Ошибка: " + errorMsg);
            }
        });
    });

    $(".edit-btn").click(function() {
        var row = $(this).closest("tr");
        $("#edit_bot_id").val(row.data("bot-id"));
        $("#edit_bot_name").val(row.find(".bot-name").text());
        $("#edit_telegram_token").val(row.find(".bot-token").text());
        $("#edit_openai_api_key").val(row.find(".bot-openai").text());
        $("#edit_assistant_id").val(row.find(".bot-assistant").text());
        $("#editModal").modal("show");
    });

    $("#editBotForm").submit(function(e) {
        e.preventDefault();
        showSpinner('#saveEditBtn');
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
                hideSpinner('#saveEditBtn');
                $("#editModal").modal("hide");
                alert("Бот успешно обновлен!");
                location.reload();
            },
            error: function(xhr) {
                hideSpinner('#saveEditBtn');
                var errorMsg = xhr.responseJSON?.error || "Неизвестная ошибка";
                alert("Ошибка: " + errorMsg);
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
            success: function() {
                alert("Бот успешно удален!");
                location.reload();
            },
            error: function(xhr) {
                var errorMsg = xhr.responseJSON?.error || "Неизвестная ошибка";
                alert("Ошибка: " + errorMsg);
            }
        });
    });

    $(".start-btn").click(function() {
        var btn = this;
        showSpinner(btn);
        var row = $(this).closest("tr");
        var botId = row.data("bot-id");
        $.ajax({
            url: "/api/bots/" + botId + "/start",
            method: "POST",
            success: function() {
                hideSpinner(btn);
                alert("Бот успешно запущен!");
                location.reload();
            },
            error: function(xhr) {
                hideSpinner(btn);
                var errorMsg = xhr.responseJSON?.error || "Неизвестная ошибка";
                alert("Ошибка: " + errorMsg);
            }
        });
    });

    $(".stop-btn").click(function() {
        var btn = this;
        showSpinner(btn);
        var row = $(this).closest("tr");
        var botId = row.data("bot-id");
        $.ajax({
            url: "/api/bots/" + botId + "/stop",
            method: "POST",
            success: function() {
                hideSpinner(btn);
                alert("Бот успешно остановлен!");
                location.reload();
            },
            error: function(xhr) {
                hideSpinner(btn);
                var errorMsg = xhr.responseJSON?.error || "Неизвестная ошибка";
                alert("Ошибка: " + errorMsg);
            }
        });
    });

    $("#searchBots").on("keyup", function() {
        var value = $(this).val().toLowerCase();
        $("#botsTable tbody tr").filter(function() {
            $(this).toggle($(this).find(".bot-name").text().toLowerCase().indexOf(value) > -1);
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
        save_configs_async()
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

# Создание systemd-сервиса
step 8 "Создание systemd-сервиса..."
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
EOF" || error "Не удалось создать systemd-сервис."

# Активация и запуск сервиса
step 9 "Активация и запуск сервиса..."
sudo systemctl daemon-reload || error "Не удалось перезагрузить конфигурацию systemd."
sudo systemctl enable telegram-gpt-bot.service || error "Не удалось включить сервис."
sudo systemctl start telegram-gpt-bot.service || error "Не удалось запустить сервис."

# Проверка статуса
step 10 "Проверка статуса сервиса..."
sudo systemctl status telegram-gpt-bot.service --no-pager -l

# Финальное сообщение
echo -e "${GREEN}✔ Установка завершена успешно!${NC}"
echo "Сервер доступен по адресу: http://<ваш_IP>:5000"
echo "Логин: admin | Пароль: securepassword123"
echo -e "${YELLOW}Рекомендация: Измените логин и пароль в server_and_bot.py в разделе USERS для безопасности.${NC}"