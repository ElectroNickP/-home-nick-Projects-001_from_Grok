"""
Authentication decorators and utilities for Telegram Bot Manager

This module contains authentication-related decorators and utility functions
extracted from the monolithic app.py during refactoring.
"""

import base64
import logging
from functools import wraps

from flask import session, redirect, url_for, jsonify, request

logger = logging.getLogger(__name__)

# User credentials (TODO: move to external config or database)
USERS = {"admin": "admin"}


def verify_credentials(username: str, password: str) -> bool:
    """
    Verify user credentials
    
    Args:
        username: Username to verify
        password: Password to verify
        
    Returns:
        True if credentials are valid, False otherwise
    """
    if username in USERS and USERS[username] == password:
        return True
    return False


def login_required(f):
    """
    Decorator for checking web session authorization
    Redirects to login page if not authenticated
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("auth.login_page"))
        return f(*args, **kwargs)
    
    return decorated_function


def api_login_required(f):
    """
    Decorator for checking API authorization (session + Basic Auth)
    Returns 401 JSON response if not authenticated
    
    Supports:
    1. Session-based auth (for web interface)
    2. HTTP Basic Auth (for API clients)
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # First check session (for web interface)
        if "user_id" in session:
            return f(*args, **kwargs)
            
        # Then check HTTP Basic Auth (for API clients)
        auth_header = request.headers.get('Authorization')
        
        if not auth_header or not auth_header.startswith('Basic '):
            return jsonify({
                "error": "Unauthorized", 
                "message": "Authentication required"
            }), 401
            
        try:
            # Decode Basic Auth
            encoded_creds = auth_header.split(' ')[1]
            decoded_creds = base64.b64decode(encoded_creds).decode('utf-8')
            username, password = decoded_creds.split(':', 1)
            
            # Verify credentials
            if verify_credentials(username, password):
                return f(*args, **kwargs)
            else:
                return jsonify({
                    "error": "Unauthorized", 
                    "message": "Invalid credentials"
                }), 401
                
        except (IndexError, ValueError, UnicodeDecodeError):
            return jsonify({
                "error": "Unauthorized", 
                "message": "Invalid Authorization header"
            }), 401
    
    return decorated_function


def api_v2_auth_required(f):
    """
    Decorator for checking both HTTP Basic Authentication and sessions in API v2
    
    Supports:
    1. Session-based auth (for web interface)
    2. HTTP Basic Auth (for API clients)
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # First check session (for web interface)
        if "user_id" in session:
            return f(*args, **kwargs)
            
        # Then check HTTP Basic Auth (for API clients)
        auth_header = request.headers.get('Authorization')
        
        if not auth_header or not auth_header.startswith('Basic '):
            return jsonify({
                "error": "Unauthorized", 
                "message": "Authentication required"
            }), 401
            
        try:
            # Decode Basic Auth
            encoded_credentials = auth_header[6:]  # Remove 'Basic '
            decoded = base64.b64decode(encoded_credentials).decode('utf-8')
            username, password = decoded.split(':', 1)
            
            # Verify credentials
            if verify_credentials(username, password):
                return f(*args, **kwargs)
            else:
                return jsonify({
                    "error": "Unauthorized", 
                    "message": "Invalid credentials"
                }), 401
                
        except Exception as e:
            logger.error(f"Auth error: {e}")
            return jsonify({
                "error": "Unauthorized", 
                "message": "Invalid authentication format"
            }), 401
    
    return decorated_function
