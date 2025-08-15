#!/usr/bin/env python3
import os
import logging
import json
import subprocess
import threading
import time
import sys
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
    
    # Set default values if not provided
    if "group_context_limit" not in data:
        data["group_context_limit"] = 15
    if "enable_voice_responses" not in data:
        data["enable_voice_responses"] = False
    if "voice_model" not in data:
        data["voice_model"] = "tts-1"
    if "voice_type" not in data:
        data["voice_type"] = "alloy"

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

@app.route("/api/bots/<int:bot_id>", methods=["GET"])
@auth.login_required
def get_bot(bot_id):
    with cm.BOT_CONFIGS_LOCK:
        if bot_id not in cm.BOT_CONFIGS:
            return jsonify({"error": "Бот не найден"}), 404
        return jsonify(serialize_bot_entry(cm.BOT_CONFIGS[bot_id]))

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

def run_git_command(command, timeout=30):
    """Execute git command safely"""
    try:
        result = subprocess.run(
            ["git"] + command.split(),
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.dirname(__file__)),
            timeout=timeout
        )
        return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
    except subprocess.TimeoutExpired:
        return False, "", "Git command timed out"
    except Exception as e:
        return False, "", str(e)

def check_for_updates():
    """Check if there are new commits available in remote repository"""
    try:
        # Fetch latest changes from remote
        success, stdout, stderr = run_git_command("fetch origin")
        if not success:
            return False, f"Failed to fetch: {stderr}", None, None
        
        # Get current local commit
        success, local_commit, stderr = run_git_command("rev-parse HEAD")
        if not success:
            return False, f"Failed to get local commit: {stderr}", None, None
        
        # Get latest remote commit
        success, remote_commit, stderr = run_git_command("rev-parse origin/master")
        if not success:
            return False, f"Failed to get remote commit: {stderr}", None, None
        
        # Check if commits are different
        has_updates = local_commit.strip() != remote_commit.strip()
        
        if has_updates:
            # Get commit messages for new commits
            success, commit_log, stderr = run_git_command(f"log --oneline {local_commit[:8]}..{remote_commit[:8]}")
            return True, "Updates available", local_commit[:8], remote_commit[:8], commit_log
        else:
            return True, "No updates available", local_commit[:8], remote_commit[:8], ""
            
    except Exception as e:
        return False, f"Error checking updates: {str(e)}", None, None

def perform_update():
    """Perform git pull and return result"""
    try:
        # Save current configs before update
        cm.save_configs_async()
        time.sleep(1)  # Give save time to complete
        
        # Perform git pull
        success, stdout, stderr = run_git_command("pull origin master")
        if not success:
            return False, f"Git pull failed: {stderr}"
        
        return True, f"Update successful: {stdout}"
        
    except Exception as e:
        return False, f"Update failed: {str(e)}"

def restart_application():
    """Restart the application after a delay"""
    def delayed_restart():
        time.sleep(2)  # Give time for response to be sent
        logger.info("🔄 Restarting application after update...")
        python = sys.executable
        os.execl(python, python, *sys.argv)
    
    thread = threading.Thread(target=delayed_restart, daemon=True)
    thread.start()

@app.route("/api/check-updates", methods=["GET"])
@auth.login_required
def check_updates_api():
    """API endpoint to check for available updates"""
    try:
        success, message, local_commit, remote_commit, *commit_log = check_for_updates()
        
        if not success:
            return jsonify({"error": message}), 500
        
        response = {
            "has_updates": local_commit != remote_commit if local_commit and remote_commit else False,
            "message": message,
            "local_commit": local_commit,
            "remote_commit": remote_commit,
            "current_version": version.get_version()
        }
        
        if commit_log and commit_log[0]:
            response["new_commits"] = commit_log[0].split('\n') if commit_log[0] else []
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error in check_updates_api: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/update", methods=["POST"])
@auth.login_required
def update_application():
    """API endpoint to perform application update"""
    try:
        # Check if updates are available first
        success, message, local_commit, remote_commit, *commit_log = check_for_updates()
        
        if not success:
            return jsonify({"error": f"Update check failed: {message}"}), 500
        
        if local_commit == remote_commit:
            return jsonify({"error": "No updates available"}), 400
        
        # Stop all bots before update
        logger.info("🛑 Stopping all bots before update...")
        with cm.BOT_CONFIGS_LOCK:
            for bot_id in list(cm.BOT_CONFIGS.keys()):
                bm.stop_bot_thread(bot_id)
        
        # Perform the update
        update_success, update_message = perform_update()
        
        if not update_success:
            return jsonify({"error": update_message}), 500
        
        logger.info("✅ Update completed successfully, restarting application...")
        
        # Schedule restart
        restart_application()
        
        return jsonify({
            "success": True,
            "message": "Update completed successfully. Application is restarting...",
            "old_version": local_commit,
            "new_version": remote_commit
        })
        
    except Exception as e:
        logger.error(f"Error in update_application: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    if not os.path.exists(cm.CONFIG_FILE):
        with open(cm.CONFIG_FILE, 'w') as f:
            json.dump({"bots": {}}, f)
    cm.load_configs()
    bm.start_all_bots()
    logger.info("Запуск Flask-сервера на http://0.0.0.0:60183")
    app.run(host="0.0.0.0", port=60183, debug=False, threaded=True)
