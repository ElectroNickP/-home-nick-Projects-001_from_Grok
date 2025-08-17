#!/usr/bin/env python3
import os
import logging
import json
import subprocess
import threading
import time
import sys
import psutil
from datetime import datetime
from flask import Flask, request, jsonify, render_template
from flask_httpauth import HTTPBasicAuth

import config_manager as cm
import bot_manager as bm
import version
from auto_updater import auto_updater

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
    """Serialize bot entry for API v1 compatibility"""
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

@app.route("/api/bots", methods=["GET"])
@auth.login_required  
def get_all_bots():
    """Get all bots (API v1 compatibility)"""
    try:
        with cm.BOT_CONFIGS_LOCK:
            bots = []
            for bot_id, bot_data in cm.BOT_CONFIGS.items():
                if bot_data is not None:
                    # Extract actual config from bot_data, avoiding double nesting
                    if 'config' in bot_data and isinstance(bot_data['config'], dict):
                        actual_config = bot_data['config']
                    else:
                        # Fallback: use bot_data directly as config (excluding system fields)
                        actual_config = {k: v for k, v in bot_data.items() 
                                       if k not in ['thread', 'loop', 'stop_event', 'status', 'id']}
                    
                    bot_entry = {
                        "id": bot_id,
                        "config": actual_config,
                        "status": bot_data.get("status", "stopped")
                    }
                    bots.append(serialize_bot_entry(bot_entry))
            return jsonify(bots)
    except Exception as e:
        logger.error(f"Error in get_all_bots: {e}")
        return jsonify({"error": str(e)}), 500

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
    if "enable_ai_responses" not in data:
        data["enable_ai_responses"] = True  # По умолчанию включены для обратной совместимости
    
    # Marketplace settings with default values
    if "marketplace" not in data:
        data["marketplace"] = {
            "enabled": False,
            "title": "",
            "description": "",
            "category": "other",
            "username": "",
            "website": "",
            "image_url": "",
            "tags": [],
            "featured": False,
            "rating": 0.0,
            "total_users": 0,
            "last_updated": None
        }

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
    """Legacy function - redirects to auto_updater"""
    return auto_updater._run_git_command(command)

def check_for_updates():
    """Legacy function - redirects to auto_updater with compatibility format"""
    result = auto_updater.check_for_updates()
    if result["success"]:
        return (
            True, 
            result["message"],
            result.get("local_commit", "unknown"),
            result.get("remote_commit", "unknown"),
            result.get("commit_log", [])
        )
    else:
        return False, result["error"], None, None

def perform_update():
    """Legacy function - redirects to auto_updater"""
    result = auto_updater.perform_update()
    if result["success"]:
        return True, result["message"]
    else:
        return False, result["error"]

def restart_application():
    """Legacy function - no longer used, handled by auto_updater"""
    logger.warning("⚠️ Legacy restart_application called - using auto_updater instead")
    pass

@app.route("/api/check-updates", methods=["GET"])
@auth.login_required
def check_updates_api():
    """API endpoint to check for available updates"""
    try:
        result = check_for_updates()
        if not isinstance(result, tuple) or len(result) < 4:
            return jsonify({"error": "Invalid update check result"}), 500
        
        success, message, local_commit, remote_commit, *commit_log = result
        
        if not success:
            return jsonify({"error": message}), 500
        
        response = {
            "has_updates": local_commit != remote_commit if local_commit and remote_commit else False,
            "message": message,
            "local_commit": local_commit,
            "remote_commit": remote_commit,
            "current_version": version.get_version()
        }
        
        if commit_log:
            # commit_log is already a list of commit lines
            response["new_commits"] = commit_log if isinstance(commit_log, list) else []
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error in check_updates_api: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/update", methods=["POST"])
@auth.login_required
def update_application():
    """API endpoint to perform professional application update"""
    try:
        if auto_updater.is_update_in_progress():
            return jsonify({
                "error": "Update already in progress",
                "status": auto_updater.get_update_status()
            }), 409
        
        # Perform professional update with backup and rollback
        result = auto_updater.perform_update()
        
        if result["success"]:
            return jsonify({
                "success": True,
                "message": result["message"],
                "backup_id": result.get("backup_id"),
                "new_version": result.get("new_version")
            })
        else:
            return jsonify({
                "error": result["error"],
                "backup_id": result.get("backup_id")
            }), 500
        
    except Exception as e:
        logger.error(f"Error in update_application: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/update/status", methods=["GET"])
@auth.login_required
def get_update_status():
    """Get current update status with progress information"""
    try:
        status = auto_updater.get_update_status()
        return jsonify({
            "success": True,
            "data": status
        })
    except Exception as e:
        logger.error(f"Error getting update status: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/update/backups", methods=["GET"])
@auth.login_required
def list_backups():
    """List all available backups"""
    try:
        backups = auto_updater.list_backups()
        return jsonify({
            "success": True,
            "data": backups,
            "count": len(backups)
        })
    except Exception as e:
        logger.error(f"Error listing backups: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/update/backups/cleanup", methods=["POST"])
@auth.login_required
def cleanup_backups():
    """Clean up old backups, keeping only the most recent ones"""
    try:
        data = request.get_json() or {}
        keep_count = data.get("keep_count", 5)
        
        result = auto_updater.cleanup_old_backups(keep_count)
        
        if result["success"]:
            return jsonify({
                "success": True,
                "message": result["message"],
                "removed_count": result.get("removed_count", 0)
            })
        else:
            return jsonify({"error": result["error"]}), 500
            
    except Exception as e:
        logger.error(f"Error cleaning up backups: {e}")
        return jsonify({"error": str(e)}), 500

# ============== PROFESSIONAL API ENDPOINTS ==============

def api_response(data=None, message="Success", status_code=200, error=None):
    """Standard API response format"""
    if error:
        response = {
            "success": False,
            "error": error,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    else:
        response = {
            "success": True,
            "data": data,
            "message": message,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    return jsonify(response), status_code

@app.route("/api/v2/system/health", methods=["GET"])
@auth.login_required
def health_check():
    """System health check endpoint"""
    try:
        health_status = {
            "status": "healthy",
            "checks": {
                "database": "healthy",
                "memory": "healthy", 
                "disk": "healthy",
                "bots": "healthy"
            }
        }
        
        # Check config file access
        try:
            if os.path.exists(cm.CONFIG_FILE):
                with open(cm.CONFIG_FILE, 'r') as f:
                    f.read(1)
        except Exception:
            health_status["checks"]["database"] = "unhealthy"
            health_status["status"] = "unhealthy"
        
        # Check memory usage
        try:
            memory = psutil.virtual_memory()
            if memory.percent > 95:
                health_status["checks"]["memory"] = "unhealthy"
                health_status["status"] = "unhealthy"
            elif memory.percent > 90:
                health_status["checks"]["memory"] = "warning"
        except Exception:
            health_status["checks"]["memory"] = "unknown"
        
        # Check disk usage
        try:
            disk = psutil.disk_usage('/')
            if disk.percent > 95:
                health_status["checks"]["disk"] = "unhealthy"
                health_status["status"] = "unhealthy"
            elif disk.percent > 90:
                health_status["checks"]["disk"] = "warning"
        except Exception:
            health_status["checks"]["disk"] = "unknown"
        
        # Check bots status
        try:
            with cm.BOT_CONFIGS_LOCK:
                total_bots = len(cm.BOT_CONFIGS)
                running_bots = sum(1 for bot in cm.BOT_CONFIGS.values() if bot.get("status") == "running")
            
            if total_bots > 0 and running_bots == 0:
                health_status["checks"]["bots"] = "warning"
        except Exception:
            health_status["checks"]["bots"] = "unknown"
        
        status_code = 200 if health_status["status"] == "healthy" else 503
        return api_response(health_status, f"System is {health_status['status']}", status_code)
        
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return api_response(error="Health check failed", status_code=500)

@app.route("/api/v2/system/info", methods=["GET"])
@auth.login_required
def system_info():
    """Get detailed system information"""
    try:
        # System metrics
        cpu_count = psutil.cpu_count()
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        boot_time = datetime.fromtimestamp(psutil.boot_time())
        
        # Process info
        process = psutil.Process()
        process_memory = process.memory_info()
        
        # Bot statistics
        with cm.BOT_CONFIGS_LOCK:
            total_bots = len(cm.BOT_CONFIGS)
            running_bots = sum(1 for bot in cm.BOT_CONFIGS.values() if bot.get("status") == "running")
            voice_bots = sum(1 for bot in cm.BOT_CONFIGS.values() if bot["config"].get("enable_voice_responses", False))
        
        # Version info
        version_info = version.get_version_info()
        
        system_data = {
            "application": {
                "name": "Telegram Bot Manager",
                "version": version_info.version_string,
                "full_version": version_info.full_version_string,
                "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
                "process_memory_mb": round(process_memory.rss / (1024**2), 2),
                "uptime_seconds": round(time.time() - process.create_time(), 1)
            },
            "system": {
                "platform": sys.platform,
                "cpu_cores": cpu_count,
                "cpu_percent": psutil.cpu_percent(interval=0.1),
                "memory": {
                    "total_gb": round(memory.total / (1024**3), 2),
                    "available_gb": round(memory.available / (1024**3), 2),
                    "used_percent": memory.percent
                },
                "disk": {
                    "total_gb": round(disk.total / (1024**3), 2),
                    "free_gb": round(disk.free / (1024**3), 2),
                    "used_percent": round((disk.used / disk.total) * 100, 1)
                },
                "boot_time": boot_time.isoformat(),
                "uptime_hours": round((datetime.now() - boot_time).total_seconds() / 3600, 1)
            },
            "bots": {
                "total": total_bots,
                "running": running_bots,
                "stopped": total_bots - running_bots,
                "voice_enabled": voice_bots
            }
        }
        
        return api_response(system_data, "System information retrieved")
        
    except Exception as e:
        logger.error(f"Error getting system info: {e}")
        return api_response(error="Failed to retrieve system information", status_code=500)

@app.route("/api/v2/bots", methods=["GET"])
@auth.login_required
def get_all_bots_v2():
    """Get all bots with filtering and pagination"""
    try:
        # Query parameters
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 50, type=int), 100)
        status_filter = request.args.get('status')
        search = request.args.get('search', '').strip()
        
        with cm.BOT_CONFIGS_LOCK:
            all_bots = list(cm.BOT_CONFIGS.values())
        
        # Apply filters
        filtered_bots = all_bots
        
        if status_filter:
            filtered_bots = [bot for bot in filtered_bots if bot.get("status") == status_filter]
        
        if search:
            filtered_bots = [
                bot for bot in filtered_bots 
                if search.lower() in bot["config"]["bot_name"].lower()
            ]
        
        # Sort by ID
        filtered_bots.sort(key=lambda x: x["id"])
        
        # Pagination
        total = len(filtered_bots)
        start_index = (page - 1) * per_page
        end_index = start_index + per_page
        bots_page = filtered_bots[start_index:end_index]
        
        # Enhanced serialization
        def serialize_bot_enhanced(bot_entry):
            return {
                "id": bot_entry["id"],
                "config": bot_entry["config"],
                "status": bot_entry.get("status", "stopped"),
                "has_runtime": all([
                    bot_entry.get("thread") is not None,
                    bot_entry.get("loop") is not None,
                    bot_entry.get("stop_event") is not None
                ]),
                "features": {
                    "voice_responses": bot_entry["config"].get("enable_voice_responses", False),
                    "voice_model": bot_entry["config"].get("voice_model", "tts-1"),
                    "voice_type": bot_entry["config"].get("voice_type", "alloy"),
                    "context_limit": bot_entry["config"].get("group_context_limit", 15)
                }
            }
        
        serialized_bots = [serialize_bot_enhanced(bot) for bot in bots_page]
        
        response_data = {
            "bots": serialized_bots,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": total,
                "pages": (total + per_page - 1) // per_page,
                "has_next": end_index < total,
                "has_prev": page > 1
            }
        }
        
        return api_response(response_data, f"Retrieved {len(serialized_bots)} bots")
        
    except Exception as e:
        logger.error(f"Error getting bots: {e}")
        return api_response(error="Failed to retrieve bots", status_code=500)

@app.route("/api/v2/bots/<int:bot_id>/status", methods=["GET"])
@auth.login_required
def get_bot_status_v2(bot_id):
    """Get detailed bot status"""
    try:
        with cm.BOT_CONFIGS_LOCK:
            if bot_id not in cm.BOT_CONFIGS:
                return api_response(error="Bot not found", status_code=404)
            
            bot_entry = cm.BOT_CONFIGS[bot_id]
        
        status_info = {
            "bot_id": bot_id,
            "status": bot_entry.get("status", "stopped"),
            "bot_name": bot_entry["config"]["bot_name"],
            "runtime": {
                "has_thread": bot_entry.get("thread") is not None,
                "has_loop": bot_entry.get("loop") is not None,
                "has_stop_event": bot_entry.get("stop_event") is not None
            },
            "config": {
                "voice_enabled": bot_entry["config"].get("enable_voice_responses", False),
                "voice_model": bot_entry["config"].get("voice_model", "tts-1"),
                "voice_type": bot_entry["config"].get("voice_type", "alloy"),
                "context_limit": bot_entry["config"].get("group_context_limit", 15)
            }
        }
        
        return api_response(status_info, "Bot status retrieved")
        
    except Exception as e:
        logger.error(f"Error getting bot status {bot_id}: {e}")
        return api_response(error="Failed to get bot status", status_code=500)

@app.route("/api/v2/bots/<int:bot_id>/restart", methods=["POST"])
@auth.login_required
def restart_bot_v2(bot_id):
    """Restart a bot"""
    try:
        with cm.BOT_CONFIGS_LOCK:
            if bot_id not in cm.BOT_CONFIGS:
                return api_response(error="Bot not found", status_code=404)
        
        # Stop if running
        if cm.BOT_CONFIGS[bot_id].get("status") == "running":
            stop_success, stop_message = bm.stop_bot_thread(bot_id)
            if not stop_success:
                return api_response(error=f"Failed to stop bot: {stop_message}", status_code=400)
        
        # Wait a moment
        time.sleep(1)
        
        # Start again
        start_success, start_message = bm.start_bot_thread(bot_id)
        
        if start_success:
            return api_response(
                {"bot_id": bot_id, "status": "restarting"},
                "Bot restarted successfully"
            )
        else:
            return api_response(error=f"Failed to start bot: {start_message}", status_code=400)
            
    except Exception as e:
        logger.error(f"Error restarting bot {bot_id}: {e}")
        return api_response(error="Failed to restart bot", status_code=500)

@app.route("/api/v2/bots", methods=["POST"])
@auth.login_required
def create_bot_v2():
    """Create a new bot via API v2"""
    try:
        data = request.get_json()
        if not data:
            return api_response(error="JSON data required", status_code=400)
        
        required = ["bot_name", "telegram_token", "openai_api_key", "assistant_id"]
        missing = [field for field in required if field not in data]
        if missing:
            return api_response(error=f"Missing required fields: {', '.join(missing)}", status_code=400)
        
        # Set default values if not provided
        defaults = {
            "group_context_limit": 15,
            "enable_voice_responses": False,
            "voice_model": "tts-1",
            "voice_type": "alloy",
            "enable_ai_responses": True,  # По умолчанию включены для обратной совместимости
            "marketplace": {
                "enabled": False,
                "title": "",
                "description": "",
                "category": "other",
                "username": "",
                "website": "",
                "image_url": "",
                "tags": [],
                "featured": False,
                "rating": 0.0,
                "total_users": 0,
                "last_updated": None
            }
        }
        for key, default_value in defaults.items():
            if key not in data:
                data[key] = default_value

        with cm.BOT_CONFIGS_LOCK:
            bot_id = cm.NEXT_BOT_ID
            cm.NEXT_BOT_ID += 1
            
            bot_entry = {
                "id": bot_id,
                "config": data,
                "status": "stopped",
                "thread": None,
                "loop": None,
                "stop_event": None,
                "created_at": datetime.utcnow().isoformat() + "Z",
                "last_updated": datetime.utcnow().isoformat() + "Z"
            }
            cm.BOT_CONFIGS[bot_id] = bot_entry

        cm.save_configs_async()
        
        response_data = {
            "bot_id": bot_id,
            "config": data,
            "status": "stopped",
            "created_at": bot_entry["created_at"]
        }
        
        return api_response(response_data, "Bot created successfully", status_code=201)
        
    except Exception as e:
        logger.error(f"Error creating bot: {e}")
        return api_response(error="Failed to create bot", status_code=500)

@app.route("/api/v2/bots/<int:bot_id>", methods=["PUT"])
@auth.login_required
def update_bot_v2(bot_id):
    """Update bot configuration via API v2"""
    try:
        with cm.BOT_CONFIGS_LOCK:
            if bot_id not in cm.BOT_CONFIGS:
                return api_response(error="Bot not found", status_code=404)
        
        data = request.get_json()
        if not data:
            return api_response(error="JSON data required", status_code=400)
        
        with cm.BOT_CONFIGS_LOCK:
            bot_entry = cm.BOT_CONFIGS[bot_id]
            
            # Update configuration
            bot_entry["config"].update(data)
            bot_entry["last_updated"] = datetime.utcnow().isoformat() + "Z"
            
            cm.BOT_CONFIGS[bot_id] = bot_entry

        cm.save_configs_async()
        
        response_data = {
            "bot_id": bot_id,
            "config": bot_entry["config"],
            "status": bot_entry.get("status", "stopped"),
            "last_updated": bot_entry["last_updated"]
        }
        
        return api_response(response_data, "Bot updated successfully")
        
    except Exception as e:
        logger.error(f"Error updating bot {bot_id}: {e}")
        return api_response(error="Failed to update bot", status_code=500)

@app.route("/api/v2/bots/<int:bot_id>", methods=["DELETE"])
@auth.login_required
def delete_bot_v2(bot_id):
    """Delete a bot via API v2"""
    try:
        with cm.BOT_CONFIGS_LOCK:
            if bot_id not in cm.BOT_CONFIGS:
                return api_response(error="Bot not found", status_code=404)
            
            # Stop bot if running
            bot_entry = cm.BOT_CONFIGS[bot_id]
            if bot_entry.get("status") == "running":
                stop_success, stop_message = bm.stop_bot_thread(bot_id)
                if not stop_success:
                    return api_response(error=f"Failed to stop bot before deletion: {stop_message}", status_code=400)
            
            # Delete bot
            deleted_bot = cm.BOT_CONFIGS.pop(bot_id)

        cm.save_configs_async()
        
        response_data = {
            "bot_id": bot_id,
            "bot_name": deleted_bot["config"]["bot_name"],
            "deleted_at": datetime.utcnow().isoformat() + "Z"
        }
        
        return api_response(response_data, "Bot deleted successfully")
        
    except Exception as e:
        logger.error(f"Error deleting bot {bot_id}: {e}")
        return api_response(error="Failed to delete bot", status_code=500)

@app.route("/api/v2/bots/<int:bot_id>/start", methods=["POST"])
@auth.login_required
def start_bot_v2(bot_id):
    """Start a bot via API v2"""
    try:
        with cm.BOT_CONFIGS_LOCK:
            if bot_id not in cm.BOT_CONFIGS:
                return api_response(error="Bot not found", status_code=404)
        
        if cm.BOT_CONFIGS[bot_id].get("status") == "running":
            return api_response(error="Bot is already running", status_code=400)
        
        success, message = bm.start_bot_thread(bot_id)
        
        if success:
            response_data = {
                "bot_id": bot_id,
                "status": "running",
                "started_at": datetime.utcnow().isoformat() + "Z"
            }
            return api_response(response_data, "Bot started successfully")
        else:
            return api_response(error=f"Failed to start bot: {message}", status_code=400)
            
    except Exception as e:
        logger.error(f"Error starting bot {bot_id}: {e}")
        return api_response(error="Failed to start bot", status_code=500)

@app.route("/api/v2/bots/<int:bot_id>/stop", methods=["POST"])
@auth.login_required
def stop_bot_v2(bot_id):
    """Stop a bot via API v2"""
    try:
        with cm.BOT_CONFIGS_LOCK:
            if bot_id not in cm.BOT_CONFIGS:
                return api_response(error="Bot not found", status_code=404)
        
        if cm.BOT_CONFIGS[bot_id].get("status") != "running":
            return api_response(error="Bot is not running", status_code=400)
        
        success, message = bm.stop_bot_thread(bot_id)
        
        if success:
            response_data = {
                "bot_id": bot_id,
                "status": "stopped",
                "stopped_at": datetime.utcnow().isoformat() + "Z"
            }
            return api_response(response_data, "Bot stopped successfully")
        else:
            return api_response(error=f"Failed to stop bot: {message}", status_code=400)
            
    except Exception as e:
        logger.error(f"Error stopping bot {bot_id}: {e}")
        return api_response(error="Failed to stop bot", status_code=500)

@app.route("/api/v2/system/stats", methods=["GET"])
@auth.login_required
def get_stats_v2():
    """Get system statistics"""
    try:
        # Process stats
        process = psutil.Process()
        process_memory = process.memory_info()
        
        # File sizes
        log_size = os.path.getsize("bot.log") if os.path.exists("bot.log") else 0
        config_size = os.path.getsize(cm.CONFIG_FILE) if os.path.exists(cm.CONFIG_FILE) else 0
        
        # Bot statistics
        with cm.BOT_CONFIGS_LOCK:
            bots = list(cm.BOT_CONFIGS.values())
        
        voice_enabled = sum(1 for bot in bots if bot["config"].get("enable_voice_responses", False))
        running_bots = sum(1 for bot in bots if bot.get("status") == "running")
        
        stats_data = {
            "application": {
                "process_memory_mb": round(process_memory.rss / (1024**2), 2),
                "process_cpu_percent": process.cpu_percent(),
                "uptime_seconds": round(time.time() - process.create_time(), 1),
                "files": {
                    "log_size_kb": round(log_size / 1024, 2),
                    "config_size_kb": round(config_size / 1024, 2)
                }
            },
            "bots": {
                "total": len(bots),
                "running": running_bots,
                "stopped": len(bots) - running_bots,
                "voice_enabled": voice_enabled,
                "voice_disabled": len(bots) - voice_enabled
            },
            "system": {
                "cpu_percent": psutil.cpu_percent(interval=0.1),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_percent": round((psutil.disk_usage('/').used / psutil.disk_usage('/').total) * 100, 1)
            }
        }
        
        return api_response(stats_data, "Statistics retrieved")
        
    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        return api_response(error="Failed to retrieve statistics", status_code=500)

# API Documentation endpoint
@app.route("/api/v2/docs", methods=["GET"])
@auth.login_required
def api_docs():
    """API Documentation"""
    docs_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Telegram Bot Manager API v2.0 Documentation</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
            .container { max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            h1 { color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }
            h2 { color: #34495e; margin-top: 30px; }
            .endpoint { background: #ecf0f1; padding: 15px; margin: 10px 0; border-radius: 5px; }
            .method { font-weight: bold; color: white; padding: 4px 8px; border-radius: 3px; font-size: 12px; }
            .get { background: #27ae60; }
            .post { background: #e74c3c; }
            .put { background: #f39c12; }
            .delete { background: #c0392b; }
            code { background: #2c3e50; color: #ecf0f1; padding: 2px 6px; border-radius: 3px; }
            .description { margin: 10px 0; color: #7f8c8d; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🤖 Telegram Bot Manager API v2.0</h1>
            <p><strong>Base URL:</strong> <code>http://localhost:60183/api/v2</code></p>
            
            <h2>🔐 Authentication</h2>
            <p>Все API endpoints требуют <strong>HTTP Basic Authentication</strong></p>
            <p><strong>⚠️ Default Credentials:</strong> <code>admin:securepassword123</code> (смените в продакшене!)</p>
            
            <h3>📋 Примеры авторизации:</h3>
            
            <div class="endpoint">
                <strong>curl (рекомендуется):</strong><br>
                <code>curl -u username:password http://localhost:60183/api/v2/system/health</code>
            </div>
            
            <div class="endpoint">
                <strong>Base64 заголовок:</strong><br>
                <code>Authorization: Basic dXNlcm5hbWU6cGFzc3dvcmQ=</code><br>
                <small>💡 Где base64(username:password)</small>
            </div>
            
            <div class="endpoint">
                <strong>JavaScript/fetch:</strong><br>
                <code>
                fetch('http://localhost:60183/api/v2/bots', {<br>
                &nbsp;&nbsp;headers: { 'Authorization': 'Basic ' + btoa('username:password') }<br>
                })
                </code>
            </div>
            
            <div class="endpoint">
                <strong>Python requests:</strong><br>
                <code>
                import requests<br>
                response = requests.get('http://localhost:60183/api/v2/bots', <br>
                &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;auth=('username', 'password'))
                </code>
            </div>
            
            <h2>🏥 System Endpoints</h2>
            
            <div class="endpoint">
                <span class="method get">GET</span> <code>/system/health</code>
                <div class="description">System health check with component status</div>
            </div>
            
            <div class="endpoint">
                <span class="method get">GET</span> <code>/system/info</code>
                <div class="description">Detailed system information (CPU, memory, disk, etc.)</div>
            </div>
            
            <div class="endpoint">
                <span class="method get">GET</span> <code>/system/stats</code>
                <div class="description">Real-time system statistics and metrics</div>
            </div>
            
            <h2>🤖 Bot Management</h2>
            
            <div class="endpoint">
                <span class="method get">GET</span> <code>/bots</code>
                <div class="description">Get all bots with filtering and pagination<br>
                <strong>Parameters:</strong> page, per_page, status, search</div>
            </div>
            
            <div class="endpoint">
                <span class="method post">POST</span> <code>/bots</code>
                <div class="description">Create a new bot<br>
                <strong>Required:</strong> bot_name, telegram_token, openai_api_key, assistant_id<br>
                <strong>Optional:</strong> group_context_limit, enable_voice_responses, voice_model, voice_type</div>
            </div>
            
            <div class="endpoint">
                <span class="method get">GET</span> <code>/bots/{id}/status</code>
                <div class="description">Get detailed status for specific bot</div>
            </div>
            
            <div class="endpoint">
                <span class="method put">PUT</span> <code>/bots/{id}</code>
                <div class="description">Update bot configuration<br>
                <strong>Body:</strong> JSON with fields to update</div>
            </div>
            
            <div class="endpoint">
                <span class="method delete">DELETE</span> <code>/bots/{id}</code>
                <div class="description">Delete a bot (automatically stops if running)</div>
            </div>
            
            <div class="endpoint">
                <span class="method post">POST</span> <code>/bots/{id}/start</code>
                <div class="description">Start a bot</div>
            </div>
            
            <div class="endpoint">
                <span class="method post">POST</span> <code>/bots/{id}/stop</code>
                <div class="description">Stop a bot</div>
            </div>
            
            <div class="endpoint">
                <span class="method post">POST</span> <code>/bots/{id}/restart</code>
                <div class="description">Restart a bot (stop + start)</div>
            </div>
            
            <h2>📊 Response Format</h2>
            <p>All API v2 endpoints return standardized JSON responses:</p>
            <pre><code>{
    "success": true/false,
    "data": {...},
    "message": "Response message",
    "timestamp": "2025-08-15T20:00:00Z"
}</code></pre>
            
            <h2>💡 Практические примеры</h2>
            
            <h3>🤖 Создание бота:</h3>
            <pre><code>curl -u username:password -X POST \\
  http://localhost:60183/api/v2/bots \\
  -H "Content-Type: application/json" \\
  -d '{
    "bot_name": "MyBot",
    "telegram_token": "123456789:AABBccDDeeFFggHHiiJJkkLLmmNNooP",
    "openai_api_key": "sk-example1234567890abcdefghij",
    "assistant_id": "asst_example1234567890",
    "enable_voice_responses": true,
    "voice_model": "tts-1-hd",
    "voice_type": "nova",
    "group_context_limit": 20
  }'</code></pre>
            
            <h3>✏️ Обновление конфигурации:</h3>
            <pre><code>curl -u username:password -X PUT \\
  http://localhost:60183/api/v2/bots/4 \\
  -H "Content-Type: application/json" \\
  -d '{
    "bot_name": "UpdatedBotName",
    "group_context_limit": 30,
    "enable_voice_responses": false
  }'</code></pre>
            
            <h3>▶️ Управление состоянием:</h3>
            <pre><code># Запуск бота
curl -u username:password -X POST \\
  http://localhost:60183/api/v2/bots/4/start

# Остановка бота  
curl -u username:password -X POST \\
  http://localhost:60183/api/v2/bots/4/stop

# Перезапуск бота
curl -u username:password -X POST \\
  http://localhost:60183/api/v2/bots/4/restart</code></pre>
            
            <h3>📊 Получение информации:</h3>
            <pre><code># Статус бота
curl -u username:password \\
  http://localhost:60183/api/v2/bots/4/status

# Список всех ботов
curl -u username:password \\
  http://localhost:60183/api/v2/bots

# Системная информация
curl -u username:password \\
  http://localhost:60183/api/v2/system/health</code></pre>
            
            <h3>🗑️ Удаление бота:</h3>
            <pre><code>curl -u username:password -X DELETE \\
  http://localhost:60183/api/v2/bots/4</code></pre>
            
            <h2>⚠️ Коды ошибок и обработка</h2>
            <div class="endpoint">
                <strong>200</strong> - Успешный запрос<br>
                <strong>201</strong> - Ресурс создан (для POST /bots)<br>
                <strong>400</strong> - Неверный запрос (отсутствуют параметры)<br>
                <strong>401</strong> - Неавторизован (неверные credentials)<br>
                <strong>404</strong> - Ресурс не найден (бот не существует)<br>
                <strong>405</strong> - Метод не поддерживается<br>
                <strong>500</strong> - Внутренняя ошибка сервера
            </div>
            
            <h3>Пример ошибки:</h3>
            <pre><code>{
    "success": false,
    "error": "Bot not found",
    "timestamp": "2025-08-15T20:00:00Z"
}</code></pre>
            
            <h2>📋 Обязательные поля для создания бота</h2>
            <div class="endpoint">
                <strong>bot_name</strong> - Имя бота (строка)<br>
                <strong>telegram_token</strong> - Токен Telegram бота<br>
                <strong>openai_api_key</strong> - API ключ OpenAI<br>
                <strong>assistant_id</strong> - ID OpenAI Assistant
            </div>
            
            <h2>⚙️ Опциональные параметры</h2>
            <div class="endpoint">
                <strong>group_context_limit</strong> - Лимит контекста (по умолчанию: 15)<br>
                <strong>enable_voice_responses</strong> - Голосовые ответы (по умолчанию: false)<br>
                <strong>voice_model</strong> - Модель TTS: "tts-1" или "tts-1-hd" (по умолчанию: "tts-1")<br>
                <strong>voice_type</strong> - Тип голоса: "alloy", "echo", "fable", "onyx", "nova", "shimmer" (по умолчанию: "alloy")
            </div>
            
            <h2>🏪 Marketplace API</h2>
            <p><strong>📋 Public Endpoints (No Authentication Required):</strong></p>
            
            <div class="endpoint">
                <span class="method get">GET</span> <code>/marketplace</code>
                <div class="description">Public marketplace page with bot catalog</div>
            </div>
            
            <div class="endpoint">
                <span class="method get">GET</span> <code>/marketplace/{id}</code>
                <div class="description">Individual bot details page</div>
            </div>
            
            <div class="endpoint">
                <span class="method get">GET</span> <code>/api/marketplace/bots</code>
                <div class="description">Get marketplace bots (JSON API)<br>
                <strong>Parameters:</strong> category, search, featured</div>
            </div>
            
            <div class="endpoint">
                <span class="method get">GET</span> <code>/api/marketplace/categories</code>
                <div class="description">Get available bot categories</div>
            </div>
            
            <h3>📋 Marketplace Examples:</h3>
            
            <div class="endpoint">
                <strong>Get all marketplace bots:</strong><br>
                <code>curl http://localhost:60183/api/marketplace/bots</code>
            </div>
            
            <div class="endpoint">
                <strong>Filter by category:</strong><br>
                <code>curl "http://localhost:60183/api/marketplace/bots?category=assistant"</code>
            </div>
            
            <div class="endpoint">
                <strong>Search bots:</strong><br>
                <code>curl "http://localhost:60183/api/marketplace/bots?search=AI"</code>
            </div>
            
            <div class="endpoint">
                <strong>Get featured bots only:</strong><br>
                <code>curl "http://localhost:60183/api/marketplace/bots?featured=true"</code>
            </div>
            
            <div class="endpoint">
                <strong>Get categories:</strong><br>
                <code>curl http://localhost:60183/api/marketplace/categories</code>
            </div>
            
            <h3>🤖 Bot Marketplace Data Structure:</h3>
            <pre><code>{
  "marketplace": {
    "enabled": true,
    "title": "Custom Bot Title",
    "description": "Detailed bot description",
    "category": "assistant|business|education|entertainment|productivity|support|social|news|finance|health|travel|food|other",
    "username": "bot_username",
    "website": "https://example.com",
    "image_url": "https://example.com/bot-avatar.jpg",
    "tags": ["tag1", "tag2", "tag3"],
    "featured": false,
    "rating": 4.5,
    "total_users": 1000,
    "last_updated": "2025-08-17"
  }
}</code></pre>
            
            <h3>📱 Mobile Optimization:</h3>
            <ul class="list-unstyled small">
                <li><i class="fas fa-check text-success"></i> Responsive design for all devices</li>
                <li><i class="fas fa-check text-success"></i> Touch-friendly interface</li>
                <li><i class="fas fa-check text-success"></i> Direct Telegram app integration</li>
                <li><i class="fas fa-check text-success"></i> Fast loading and smooth animations</li>
            </ul>
            
            <h2>🔗 Legacy API</h2>
            <p>Original endpoints are still available at <code>/api/*</code> for web interface compatibility.</p>
            
            <p><strong>API Version:</strong> 2.0 | <strong>Last Updated:</strong> August 2025</p>
        </div>
    </body>
    </html>
    """
    return docs_html

# ============== MARKETPLACE ENDPOINTS ==============

@app.route("/marketplace")
def marketplace_page():
    """Marketplace page for public bot discovery"""
    with cm.BOT_CONFIGS_LOCK:
        marketplace_bots = []
        for bot_entry in cm.BOT_CONFIGS.values():
            marketplace_config = bot_entry["config"].get("marketplace", {})
            if marketplace_config.get("enabled", False):
                # Create public bot info (no sensitive data)
                public_bot = {
                    "id": bot_entry["id"],
                    "title": marketplace_config.get("title", bot_entry["config"]["bot_name"]),
                    "description": marketplace_config.get("description", ""),
                    "category": marketplace_config.get("category", "other"),
                    "username": marketplace_config.get("username", ""),
                    "website": marketplace_config.get("website", ""),
                    "image_url": marketplace_config.get("image_url", ""),
                    "tags": marketplace_config.get("tags", []),
                    "featured": marketplace_config.get("featured", False),
                    "rating": marketplace_config.get("rating", 0.0),
                    "total_users": marketplace_config.get("total_users", 0),
                    "last_updated": marketplace_config.get("last_updated"),
                    "status": bot_entry.get("status", "unknown")
                }
                marketplace_bots.append(public_bot)
    
    # Sort by featured first, then by rating
    marketplace_bots.sort(key=lambda x: (not x["featured"], -x["rating"]))
    
    context = get_template_context()
    context['marketplace_bots'] = marketplace_bots
    return render_template('marketplace.html', **context)

@app.route("/marketplace/<int:bot_id>")
def bot_detail_page(bot_id):
    """Individual bot details page"""
    with cm.BOT_CONFIGS_LOCK:
        if bot_id not in cm.BOT_CONFIGS:
            return "Бот не найден", 404
        
        bot_entry = cm.BOT_CONFIGS[bot_id]
        marketplace_config = bot_entry["config"].get("marketplace", {})
        
        if not marketplace_config.get("enabled", False):
            return "Бот недоступен в маркетплейсе", 404
        
        public_bot = {
            "id": bot_entry["id"],
            "title": marketplace_config.get("title", bot_entry["config"]["bot_name"]),
            "description": marketplace_config.get("description", ""),
            "category": marketplace_config.get("category", "other"),
            "username": marketplace_config.get("username", ""),
            "website": marketplace_config.get("website", ""),
            "image_url": marketplace_config.get("image_url", ""),
            "tags": marketplace_config.get("tags", []),
            "featured": marketplace_config.get("featured", False),
            "rating": marketplace_config.get("rating", 0.0),
            "total_users": marketplace_config.get("total_users", 0),
            "last_updated": marketplace_config.get("last_updated"),
            "status": bot_entry.get("status", "unknown"),
            "features": {
                "ai_responses": bot_entry["config"].get("enable_ai_responses", True),
                "voice_responses": bot_entry["config"].get("enable_voice_responses", False),
                "voice_type": bot_entry["config"].get("voice_type", "alloy")
            }
        }
    
    context = get_template_context()
    context['bot'] = public_bot
    return render_template('bot_detail.html', **context)

@app.route("/api/marketplace/bots", methods=["GET"])
def get_marketplace_bots_api():
    """Public API to get marketplace bots (no auth required)"""
    try:
        category = request.args.get('category')
        search = request.args.get('search', '').strip().lower()
        featured_only = request.args.get('featured') == 'true'
        
        with cm.BOT_CONFIGS_LOCK:
            marketplace_bots = []
            for bot_entry in cm.BOT_CONFIGS.values():
                marketplace_config = bot_entry["config"].get("marketplace", {})
                if marketplace_config.get("enabled", False):
                    public_bot = {
                        "id": bot_entry["id"],
                        "title": marketplace_config.get("title", bot_entry["config"]["bot_name"]),
                        "description": marketplace_config.get("description", ""),
                        "category": marketplace_config.get("category", "other"),
                        "username": marketplace_config.get("username", ""),
                        "website": marketplace_config.get("website", ""),
                        "image_url": marketplace_config.get("image_url", ""),
                        "tags": marketplace_config.get("tags", []),
                        "featured": marketplace_config.get("featured", False),
                        "rating": marketplace_config.get("rating", 0.0),
                        "total_users": marketplace_config.get("total_users", 0),
                        "last_updated": marketplace_config.get("last_updated"),
                        "status": bot_entry.get("status", "unknown")
                    }
                    
                    # Apply filters
                    if category and public_bot["category"] != category:
                        continue
                    
                    if featured_only and not public_bot["featured"]:
                        continue
                    
                    if search and search not in public_bot["title"].lower() and search not in public_bot["description"].lower():
                        continue
                    
                    marketplace_bots.append(public_bot)
        
        # Sort by featured first, then by rating
        marketplace_bots.sort(key=lambda x: (not x["featured"], -x["rating"]))
        
        return jsonify({
            "success": True,
            "data": marketplace_bots,
            "total": len(marketplace_bots)
        })
        
    except Exception as e:
        logger.error(f"Error getting marketplace bots: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/marketplace/categories", methods=["GET"])
def get_marketplace_categories():
    """Get available bot categories"""
    categories = [
        {"id": "assistant", "name": "🤖 Ассистенты", "description": "Универсальные помощники"},
        {"id": "business", "name": "💼 Бизнес", "description": "Корпоративные решения"},
        {"id": "education", "name": "📚 Образование", "description": "Обучение и развитие"},
        {"id": "entertainment", "name": "🎮 Развлечения", "description": "Игры и досуг"},
        {"id": "productivity", "name": "⚡ Продуктивность", "description": "Повышение эффективности"},
        {"id": "support", "name": "🛠️ Поддержка", "description": "Техническая помощь"},
        {"id": "social", "name": "👥 Социальные", "description": "Общение и сообщества"},
        {"id": "news", "name": "📰 Новости", "description": "Информационные сервисы"},
        {"id": "finance", "name": "💰 Финансы", "description": "Финансовые услуги"},
        {"id": "health", "name": "🏥 Здоровье", "description": "Медицина и фитнес"},
        {"id": "travel", "name": "✈️ Путешествия", "description": "Туризм и поездки"},
        {"id": "food", "name": "🍕 Еда", "description": "Доставка и рецепты"},
        {"id": "other", "name": "📦 Другое", "description": "Прочие категории"}
    ]
    
    return jsonify({
        "success": True,
        "data": categories
    })

if __name__ == '__main__':
    if not os.path.exists(cm.CONFIG_FILE):
        with open(cm.CONFIG_FILE, 'w') as f:
            json.dump({"bots": {}}, f)
    cm.load_configs()
    bm.start_all_bots()
    
    logger.info("🚀 Telegram Bot Manager API v2.0 Starting...")
    logger.info("🔄 AUTO-UPDATE TEST: System ready for auto-update verification!")
    logger.info("⚡ FORCED RESTART: Application must restart to show v3.1.2!")
    logger.info("📚 API v2 Documentation: http://localhost:5000/api/v2/docs")
    logger.info("🌐 Web Interface: http://localhost:5000/")
    logger.info("🔐 Default credentials: admin / securepassword123")
    logger.info("📡 Professional API Endpoints Added:")
    logger.info("   • GET  /api/v2/system/health - System health check")
    logger.info("   • GET  /api/v2/system/info - Detailed system information")
    logger.info("   • GET  /api/v2/system/stats - Real-time statistics")
    logger.info("   • GET  /api/v2/bots - Enhanced bot listing with pagination")
    logger.info("   • POST /api/v2/bots - Create new bot")
    logger.info("   • GET  /api/v2/bots/{id}/status - Detailed bot status")
    logger.info("   • PUT  /api/v2/bots/{id} - Update bot configuration")
    logger.info("   • DELETE /api/v2/bots/{id} - Delete bot")
    logger.info("   • POST /api/v2/bots/{id}/start - Start bot")
    logger.info("   • POST /api/v2/bots/{id}/stop - Stop bot")
    logger.info("   • POST /api/v2/bots/{id}/restart - Restart bot")
    logger.info("⚠️  Remember to change default credentials in production!")
    logger.info("🔧 Запуск Flask-сервера на http://0.0.0.0:60183")
    
    app.run(host="0.0.0.0", port=60183, debug=False, threaded=True)
