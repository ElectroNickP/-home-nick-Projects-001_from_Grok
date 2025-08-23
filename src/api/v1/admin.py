"""
Admin bot management routes for API v1
"""

import os
import sys
import json
import threading
import asyncio
from flask import Blueprint, request, jsonify

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

# Import shared utilities
from shared.auth import api_login_required
from shared.utils import api_response

# Import configuration manager
import config_manager as cm

# Import logger
import logging
logger = logging.getLogger(__name__)

# Create blueprint
admin_bp = Blueprint('api_v1_admin', __name__, url_prefix='/api')


@admin_bp.route("/admin-bot", methods=["GET"])
@api_login_required
def get_admin_bot_status():
    """Получить статус административного бота"""
    try:
        admin_config = cm.ADMIN_BOT_CONFIG
        return jsonify(
            {
                "enabled": admin_config.get("enabled", False),
                "status": "running" if admin_config.get("enabled") else "stopped",
                "admin_users": admin_config.get("admin_users", []),
                "notifications": admin_config.get("notifications", {}),
            }
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@admin_bp.route("/admin-bot", methods=["POST"])
@api_login_required
def create_admin_bot():
    """Создать/настроить административного бота"""
    try:
        data = request.get_json()
        required = ["token", "admin_users"]
        if not all(field in data for field in required):
            return jsonify({"error": "Отсутствуют обязательные поля"}), 400

        # Валидация токена
        if not data["token"] or len(data["token"]) < 10:
            return jsonify({"error": "Неверный формат токена"}), 400

        # Валидация списка администраторов
        if not data["admin_users"] or not isinstance(data["admin_users"], list):
            return jsonify({"error": "Список администраторов должен быть массивом"}), 400

        # Обновляем конфигурацию
        cm.ADMIN_BOT_CONFIG.update(
            {
                "enabled": True,
                "token": data["token"],
                "admin_users": data["admin_users"],
                "notifications": data.get(
                    "notifications",
                    {"bot_status": True, "high_cpu": True, "errors": True, "weekly_stats": False},
                ),
            }
        )
        
        # Сохраняем конфигурацию в файл
        cm.save_configs_async()

        # Запускаем админ-бота
        try:
            from admin_bot import AdminBot, set_admin_bot

            admin_bot = AdminBot(data["token"], data["admin_users"], data.get("notifications", {}))
            set_admin_bot(admin_bot)

            # Исправленный запуск в отдельном потоке
            def run_admin_bot():
                try:
                    # Создаем новый event loop для потока
                    asyncio.set_event_loop(asyncio.new_event_loop())
                    loop = asyncio.get_event_loop()
                    
                    # Запускаем бота
                    loop.run_until_complete(admin_bot.start())
                except Exception as e:
                    logger.error(f"Ошибка запуска админ-бота: {e}")
                finally:
                    try:
                        loop.close()
                    except:
                        pass

            # Создаем и запускаем поток
            admin_thread = threading.Thread(target=run_admin_bot, daemon=True)
            admin_thread.start()

            logger.info(
                f"Административный бот запущен для {len(data['admin_users'])} пользователей"
            )

        except Exception as e:
            logger.error(f"Ошибка создания админ-бота: {e}")
            return jsonify({"error": f"Ошибка создания бота: {str(e)}"}), 500

        return jsonify({"success": True, "message": "Административный бот создан и запущен"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@admin_bp.route("/admin-bot", methods=["DELETE"])
@api_login_required
def stop_admin_bot():
    """Остановить административного бота"""
    try:
        from admin_bot import get_admin_bot

        admin_bot = get_admin_bot()
        if admin_bot:
            # Останавливаем бота
            try:
                # Помечаем бота как остановленного
                admin_bot.is_running = False
                # Очищаем глобальную ссылку
                from admin_bot import set_admin_bot
                set_admin_bot(None)
                logger.info("AdminBot остановлен")
            except Exception as e:
                logger.error(f"Ошибка остановки админ-бота: {e}")

        # Обновляем конфигурацию
        cm.ADMIN_BOT_CONFIG["enabled"] = False
        cm.ADMIN_BOT_CONFIG["token"] = ""
        cm.ADMIN_BOT_CONFIG["admin_users"] = []
        
        # Сохраняем конфигурацию в файл
        cm.save_configs_async()

        logger.info("Административный бот остановлен")
        return jsonify({"success": True, "message": "Административный бот остановлен"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500
