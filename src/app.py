#!/usr/bin/env python3
import os
import logging
import json
from flask import Flask, request, jsonify, render_template
from flask_httpauth import HTTPBasicAuth

import config_manager as cm
import bot_manager as bm
import version

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    handlers=[logging.FileHandler("bot.log"), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

app = Flask(__name__, template_folder='templates')
auth = HTTPBasicAuth()

USERS = {"admin": "securepassword123"}

@auth.verify_password
def verify_password(username, password):
    if username in USERS and USERS[username] == password:
        return username
    return None

def serialize_bot_entry(bot_entry):
    return {
        "id": bot_entry["id"],
        "config": bot_entry["config"],
        "status": bot_entry.get("status", "unknown")
    }

def get_template_context():
    """Get common template context including version info"""
    version_info = version.get_version_info()
    return {
        "version": version_info.version_string,
        "full_version": version_info.full_version_string,
        "version_details": version_info.version_details
    }

@app.route("/")
@auth.login_required
def index_page():
    with cm.BOT_CONFIGS_LOCK:
        bots_list = [serialize_bot_entry(b) for b in cm.BOT_CONFIGS.values()]
    
    context = get_template_context()
    context['bots'] = bots_list
    return render_template('index.html', **context)

@app.route("/dialogs/<int:bot_id>")
@auth.login_required
def dialogs_page(bot_id):
    with cm.BOT_CONFIGS_LOCK:
        if bot_id not in cm.BOT_CONFIGS:
            return "Бот не найден", 404
        bot = cm.BOT_CONFIGS[bot_id]
        bot_name = bot["config"]["bot_name"]
        token = bot["config"]["telegram_token"]

    with cm.CONVERSATIONS_LOCK:
        bot_convs = {k: v for k, v in cm.CONVERSATIONS.items() if k.startswith(token + "_")}
        selected_key = request.args.get("conv_key")
        selected_conv = bot_convs.get(selected_key, {}).get("messages", [])

    context = get_template_context()
    context.update({
        'bot_id': bot_id,
        'bot_name': bot_name,
        'conversations': bot_convs,
        'selected_conv_key': selected_key,
        'selected_conversation': selected_conv
    })
    return render_template('dialogs.html', **context)

@app.route("/api/bots", methods=["POST"])
@auth.login_required
def create_bot():
    data = request.get_json()
    required = ["bot_name", "telegram_token", "openai_api_key", "assistant_id"]
    if not all(field in data for field in required):
        return jsonify({"error": "Отсутствуют обязательные поля"}), 400
    
    # Set default value for group_context_limit if not provided
    if "group_context_limit" not in data:
        data["group_context_limit"] = 15

    with cm.BOT_CONFIGS_LOCK:
        bot_id = cm.NEXT_BOT_ID
        cm.NEXT_BOT_ID += 1
        bot_entry = {
            "id": bot_id,
            "config": data,
            "status": "stopped", "thread": None, "loop": None, "stop_event": None
        }
        cm.BOT_CONFIGS[bot_id] = bot_entry

    cm.save_configs_async()
    return jsonify(serialize_bot_entry(bot_entry)), 201

@app.route("/api/bots/<int:bot_id>", methods=["PUT"])
@auth.login_required
def update_bot(bot_id):
    data = request.get_json()
    with cm.BOT_CONFIGS_LOCK:
        if bot_id not in cm.BOT_CONFIGS:
            return jsonify({"error": "Бот не найден"}), 404
        if cm.BOT_CONFIGS[bot_id].get("status") == "running":
            return jsonify({"error": "Остановите бота перед редактированием"}), 400
        cm.BOT_CONFIGS[bot_id]["config"].update(data)

    cm.save_configs_async()
    return jsonify(serialize_bot_entry(cm.BOT_CONFIGS[bot_id]))

@app.route("/api/bots/<int:bot_id>", methods=["DELETE"])
@auth.login_required
def delete_bot(bot_id):
    with cm.BOT_CONFIGS_LOCK:
        if bot_id not in cm.BOT_CONFIGS:
            return jsonify({"error": "Бот не найден"}), 404
        if cm.BOT_CONFIGS[bot_id].get("status") == "running":
            return jsonify({"error": "Остановите бота перед удалением"}), 400
        del cm.BOT_CONFIGS[bot_id]

    cm.save_configs_async()
    return jsonify({"success": True})

@app.route("/api/bots/<int:bot_id>/start", methods=["POST"])
@auth.login_required
def start_bot(bot_id):
    success, message = bm.start_bot_thread(bot_id)
    if success:
        return jsonify({"success": True})
    return jsonify({"error": message}), 400

@app.route("/api/bots/<int:bot_id>/stop", methods=["POST"])
@auth.login_required
def stop_bot(bot_id):
    success, message = bm.stop_bot_thread(bot_id)
    if success:
        return jsonify({"success": True})
    return jsonify({"error": message}), 400

@app.route("/api/version", methods=["GET"])
@auth.login_required
def get_version_api():
    """API endpoint for getting version information"""
    version_info = version.get_version_info()
    return jsonify(version_info.version_details)

if __name__ == '__main__':
    if not os.path.exists(cm.CONFIG_FILE):
        with open(cm.CONFIG_FILE, 'w') as f:
            json.dump({"bots": {}}, f)
    cm.load_configs()
    bm.start_all_bots()
    logger.info("Запуск Flask-сервера на http://0.0.0.0:47469")
    app.run(host="0.0.0.0", port=47469, debug=False, threaded=True)
