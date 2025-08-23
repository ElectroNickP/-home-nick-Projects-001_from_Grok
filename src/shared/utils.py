"""
Utility functions for Telegram Bot Manager

This module contains utility functions extracted from the monolithic app.py 
during refactoring. These functions provide common functionality used across
multiple modules.
"""

import socket
import re
from datetime import datetime, UTC
from typing import Dict, Any, Optional, Tuple

from flask import jsonify
import version


def datetime_filter(timestamp: Optional[float]) -> Optional[datetime]:
    """
    Convert Unix timestamp to datetime object
    
    Args:
        timestamp: Unix timestamp or None
        
    Returns:
        datetime object or None if conversion fails
    """
    if timestamp is None:
        return None
    try:
        return datetime.fromtimestamp(timestamp, tz=UTC)
    except (ValueError, TypeError, OSError):
        return None


def find_free_port(start_port: int = 5000, max_attempts: int = 100) -> int:
    """
    Find a free port starting from start_port
    
    Args:
        start_port: Port to start searching from
        max_attempts: Maximum number of ports to try
        
    Returns:
        Free port number
        
    Raises:
        RuntimeError: If no free port found in range
    """
    for port in range(start_port, start_port + max_attempts):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(("", port))
                return port
        except OSError:
            continue
    raise RuntimeError(
        f"Could not find free port in range {start_port}-{start_port + max_attempts}"
    )


def serialize_bot_entry(bot_entry: Dict[str, Any]) -> Dict[str, Any]:
    """
    Serialize bot entry for API v1 compatibility
    
    Args:
        bot_entry: Raw bot configuration entry
        
    Returns:
        Serialized bot entry with id, config, and status
    """
    return {
        "id": bot_entry["id"],
        "config": bot_entry["config"],
        "status": bot_entry.get("status", "unknown"),
    }


def get_template_context() -> Dict[str, Any]:
    """
    Get common template context including version info
    
    Returns:
        Dictionary with version information for templates
    """
    version_info = version.get_version_info()
    return {
        "version": version_info.version_string,
        "full_version": version_info.full_version_string,
        "version_details": version_info.version_details,
    }


def api_response(data=None, message="Success", status_code=200, error=None):
    """
    Standard API response format for API v2 endpoints
    
    Args:
        data: Response data payload
        message: Success message
        status_code: HTTP status code
        error: Error message (if any)
        
    Returns:
        Flask JSON response with standard format
    """
    if error:
        response = {
            "success": False,
            "error": error,
            "timestamp": datetime.now(UTC).isoformat() + "Z",
        }
    else:
        response = {
            "success": True,
            "data": data,
            "message": message,
            "timestamp": datetime.now(UTC).isoformat() + "Z",
        }
    return jsonify(response), status_code


def validate_input_data(data: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Validate input data to prevent security attacks
    
    Checks for:
    - SQL injection patterns
    - XSS attack patterns  
    - Path traversal attempts
    - Field length limits
    - Token format validation
    
    Args:
        data: Input data dictionary to validate
        
    Returns:
        Tuple of (is_valid, message)
    """
    # SQL injection patterns
    sql_patterns = [
        r"(\b(union|select|insert|update|delete|drop|create|alter|exec|execute)\b)",
        r"(--|/\*|\*/|;|xp_|sp_)",
        r"(\b(or|and)\b\s+\d+\s*=\s*\d+)",
        r"(\b(union|select)\b.*\bfrom\b)",
        r"(\b(insert|update|delete)\b.*\binto\b)",
        r"(\b(or|and)\b\s*['\"]?\d+['\"]?\s*=\s*['\"]?\d+['\"]?)",
        r"(\b(or|and)\b\s*['\"]?1['\"]?\s*=\s*['\"]?1['\"]?)",
        r"(\b(or|and)\b\s*['\"]?true['\"]?\s*=\s*['\"]?true['\"]?)",
        r"(\b(or|and)\b\s*['\"]?false['\"]?\s*=\s*['\"]?false['\"]?)",
    ]

    # XSS patterns
    xss_patterns = [
        r"<script[^>]*>.*?</script>",
        r"<iframe[^>]*>.*?</iframe>",
        r"javascript:",
        r"on\w+\s*=",
        r"<svg[^>]*>.*?</svg>",
        r"<img[^>]*on\w+\s*=",
    ]

    # Path traversal patterns
    path_patterns = [
        r"\.\./",
        r"\.\.\\",
        r"%2e%2e%2f",
        r"%2e%2e%5c",
        r"etc/passwd",
        r"etc\\passwd",
        r"windows\\system32",
        r"windows/system32",
    ]

    # Field length limits
    max_lengths = {
        "bot_name": 100,
        "telegram_token": 100,
        "openai_api_key": 200,
        "assistant_id": 100,
        "group_context_limit": 10,
        # Marketplace fields
        "title": 150,
        "description": 1000,
        "category": 50,
        "website": 500,
        "image_url": 500,
        "username": 100,
    }

    def validate_field(field_name, field_value, parent_key=""):
        """Helper function to validate individual fields"""
        full_field_name = f"{parent_key}.{field_name}" if parent_key else field_name
        
        if isinstance(field_value, str):
            # Check length limits
            if field_name in max_lengths and len(field_value) > max_lengths[field_name]:
                return (
                    False,
                    f"Field {full_field_name} too long (max {max_lengths[field_name]} characters)",
                )

            # Check for SQL injection
            for pattern in sql_patterns:
                if re.search(pattern, field_value, re.IGNORECASE):
                    return False, f"SQL injection attempt detected in field {full_field_name}"

            # Check for XSS
            for pattern in xss_patterns:
                if re.search(pattern, field_value, re.IGNORECASE):
                    return False, f"XSS attack attempt detected in field {full_field_name}"

            # Check for path traversal
            for pattern in path_patterns:
                if re.search(pattern, field_value, re.IGNORECASE):
                    return False, f"Path traversal attempt detected in field {full_field_name}"

            # Validate token formats
            if field_name == "telegram_token":
                if not re.match(r"^\d+:[A-Za-z0-9_-]{35,}$", field_value):
                    return False, f"Invalid Telegram token format in field {full_field_name}"

            if field_name == "openai_api_key":
                # Support both old (sk-...) and new (sk-proj-...) key formats
                if not re.match(r"^sk-(proj-)?[A-Za-z0-9_-]{20,}$", field_value):
                    return False, f"Invalid OpenAI API key format in field {full_field_name}"
                    
        return True, ""

    # Validate top-level fields
    for field, value in data.items():
        if isinstance(value, dict) and field == "marketplace":
            # Special handling for marketplace object
            for marketplace_field, marketplace_value in value.items():
                is_valid, message = validate_field(marketplace_field, marketplace_value, "marketplace")
                if not is_valid:
                    return is_valid, message
        elif isinstance(value, list) and field == "tags":
            # Handle tags array
            for i, tag in enumerate(value):
                if isinstance(tag, str) and len(tag) > 50:
                    return False, f"Tag {i+1} too long (max 50 characters)"
        else:
            # Regular field validation
            is_valid, message = validate_field(field, value)
            if not is_valid:
                return is_valid, message

    return True, "Data is valid"


def serialize_bot_enhanced(bot_entry: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enhanced bot serialization for API v2 endpoints
    
    Args:
        bot_entry: Raw bot configuration entry
        
    Returns:
        Enhanced serialized bot with additional metadata
    """
    # Get bot name from config (support both 'name' and 'bot_name' fields)
    bot_name = (
        bot_entry["config"].get("name") 
        or bot_entry["config"].get("bot_name") 
        or f"Bot {bot_entry['id']}"
    )
    
    return {
        "id": bot_entry["id"],
        "name": bot_name,
        "config": bot_entry["config"],
        "status": bot_entry.get("status", "stopped"),
        "has_runtime": all([
            bot_entry.get("thread") is not None,
            bot_entry.get("loop") is not None,
            bot_entry.get("stop_event") is not None,
        ]),
        "features": {
            "voice_responses": bot_entry["config"].get("enable_voice_responses", False),
            "voice_model": bot_entry["config"].get("voice_model", "tts-1"),
            "voice_type": bot_entry["config"].get("voice_type", "alloy"),
            "context_limit": bot_entry["config"].get("group_context_limit", 15),
        },
        "created_at": bot_entry.get("created_at"),
        "last_updated": bot_entry.get("last_updated"),
    }
