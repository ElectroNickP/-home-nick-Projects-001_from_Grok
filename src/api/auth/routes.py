"""
Authentication routes for Telegram Bot Manager

This module handles user authentication including:
- Login page (GET/POST)
- Logout functionality
- API login endpoint

Extracted from monolithic app.py during refactoring.
"""

import logging
from flask import Blueprint, request, session, redirect, url_for, render_template, jsonify

from shared.auth import verify_credentials

logger = logging.getLogger(__name__)

# Create authentication blueprint
auth_bp = Blueprint('auth', __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login_page():
    """
    Login page handler
    
    GET: Display login form
    POST: Process login credentials
    """
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if verify_credentials(username, password):
            session.permanent = True  # Make session permanent
            session["user_id"] = username
            session["username"] = username
            logger.info(f"User {username} logged in successfully")
            return redirect(url_for("web.index_page"))
        else:
            logger.warning(f"Failed login attempt for username: {username}")
            return render_template("login.html", error="Неверные учетные данные")

    return render_template("login.html")


@auth_bp.route("/logout")
def logout():
    """
    Logout handler - clear session and redirect to login
    """
    username = session.get("username", "unknown")
    session.clear()
    logger.info(f"User {username} logged out")
    return redirect(url_for("auth.login_page"))


@auth_bp.route("/api/login", methods=["POST"])
def api_login():
    """
    API login endpoint for programmatic authentication
    
    Expected JSON payload:
    {
        "username": "admin",
        "password": "password"
    }
    
    Returns:
        JSON response with success status and message
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                "success": False, 
                "message": "JSON payload required"
            }), 400
            
        username = data.get("username")
        password = data.get("password")

        if not username or not password:
            return jsonify({
                "success": False, 
                "message": "Username and password required"
            }), 400

        if verify_credentials(username, password):
            session.permanent = True  # Make session permanent
            session["user_id"] = username
            session["username"] = username
            logger.info(f"User {username} logged in via API")
            return jsonify({
                "success": True, 
                "message": "Авторизация успешна"
            })
        else:
            logger.warning(f"Failed API login attempt for username: {username}")
            return jsonify({
                "success": False, 
                "message": "Неверные учетные данные"
            }), 401
            
    except Exception as e:
        logger.error(f"API login error: {e}")
        return jsonify({
            "success": False, 
            "message": "Internal server error"
        }), 500




