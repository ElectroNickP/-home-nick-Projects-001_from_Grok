"""
Web interface routes for Telegram Bot Manager

This module handles web page routing including:
- Main dashboard (index page)
- Bot dialogs page
- Marketplace pages
- Static file serving

Extracted from monolithic app.py during refactoring.
"""

import logging
from flask import Blueprint, request, render_template, send_from_directory

import config_manager as cm
from shared.auth import login_required
from shared.utils import serialize_bot_entry, get_template_context

logger = logging.getLogger(__name__)

# Create web blueprint
web_bp = Blueprint('web', __name__)


@web_bp.route("/static/<path:filename>")
def static_files(filename):
    """
    Serve static files (logos, styles, etc.)
    """
    return send_from_directory("static", filename)


@web_bp.route("/")
@login_required
def index_page():
    """
    Main dashboard page displaying all bots
    """
    with cm.BOT_CONFIGS_LOCK:
        bots_list = [serialize_bot_entry(b) for b in cm.BOT_CONFIGS.values()]

    context = get_template_context()
    context["bots"] = bots_list
    return render_template("index.html", **context)


@web_bp.route("/dialogs/<int:bot_id>")
@login_required
def dialogs_page(bot_id):
    """
    Bot dialogs page showing conversations for specific bot
    
    Args:
        bot_id: ID of the bot to show dialogs for
    """
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
        "bot_id": bot_id,
        "bot_name": bot_name,
        "conversations": bot_convs,
        "selected_conv_key": selected_key,
        "selected_conversation": selected_conv,
    })
    return render_template("dialogs.html", **context)


@web_bp.route("/marketplace")
def marketplace_page():
    """
    Marketplace page for public bot discovery
    """
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
                    "status": bot_entry.get("status", "unknown"),
                }
                marketplace_bots.append(public_bot)

    # Sort by featured first, then by rating
    marketplace_bots.sort(key=lambda x: (not x["featured"], -x["rating"]))

    context = get_template_context()
    context["marketplace_bots"] = marketplace_bots
    return render_template("marketplace.html", **context)


@web_bp.route("/marketplace/<int:bot_id>")
def bot_detail_page(bot_id):
    """
    Individual bot details page
    
    Args:
        bot_id: ID of the bot to show details for
    """
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
            "long_description": marketplace_config.get("long_description", ""),
            "screenshots": marketplace_config.get("screenshots", []),
            "support_contact": marketplace_config.get("support_contact", ""),
            "privacy_policy": marketplace_config.get("privacy_policy", ""),
            "terms_of_service": marketplace_config.get("terms_of_service", ""),
        }

    context = get_template_context()
    context["bot"] = public_bot
    return render_template("bot_detail.html", **context)





