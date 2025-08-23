"""
API v2 System Routes for Telegram Bot Manager

This module handles modern API v2 system endpoints:
- GET /api/v2/system/health - health check
- GET /api/v2/system/info - detailed system information  
- GET /api/v2/system/stats - system statistics
- GET /api/v2/docs - API documentation

Extracted from monolithic app.py during refactoring.
"""

import logging
import os
import sys
import time
from datetime import datetime

import psutil
from flask import Blueprint

import config_manager as cm
import version
from shared.auth import api_v2_auth_required, api_login_required
from shared.utils import api_response

logger = logging.getLogger(__name__)

# Create API v2 system blueprint
api_v2_system_bp = Blueprint('api_v2_system', __name__, url_prefix='/api/v2')


@api_v2_system_bp.route("/system/health", methods=["GET"])
@api_v2_auth_required
def health_check():
    """
    System health check endpoint
    
    Returns:
        JSON health status with individual component checks
    """
    try:
        health_status = {
            "status": "healthy",
            "checks": {
                "database": "healthy",
                "memory": "healthy", 
                "disk": "healthy",
                "bots": "healthy",
            },
        }

        # Check config file access
        try:
            if os.path.exists(cm.CONFIG_FILE):
                with open(cm.CONFIG_FILE) as f:
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
            disk = psutil.disk_usage("/")
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
                running_bots = sum(
                    1 for bot in cm.BOT_CONFIGS.values() if bot.get("status") == "running"
                )

            if total_bots > 0 and running_bots == 0:
                health_status["checks"]["bots"] = "warning"
        except Exception:
            health_status["checks"]["bots"] = "unknown"

        status_code = 200 if health_status["status"] == "healthy" else 503
        return api_response(health_status, f"System is {health_status['status']}", status_code)

    except Exception as e:
        logger.error(f"Health check error: {e}")
        return api_response(error="Health check failed", status_code=500)


@api_v2_system_bp.route("/system/info", methods=["GET"])
@api_v2_auth_required
def system_info():
    """
    Get detailed system information
    
    Returns:
        JSON with comprehensive system metrics and application info
    """
    try:
        # System metrics
        cpu_count = psutil.cpu_count()
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage("/")
        boot_time = datetime.fromtimestamp(psutil.boot_time())

        # Process info
        process = psutil.Process()
        process_memory = process.memory_info()

        # Bot statistics
        with cm.BOT_CONFIGS_LOCK:
            total_bots = len(cm.BOT_CONFIGS)
            running_bots = sum(
                1 for bot in cm.BOT_CONFIGS.values() if bot.get("status") == "running"
            )
            voice_bots = sum(
                1
                for bot in cm.BOT_CONFIGS.values()
                if bot["config"].get("enable_voice_responses", False)
            )

        # Version info
        version_info = version.get_version_info()

        system_data = {
            "application": {
                "name": "Telegram Bot Manager",
                "version": version_info.version_string,
                "full_version": version_info.full_version_string,
                "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
                "process_memory_mb": round(process_memory.rss / (1024**2), 2),
                "uptime_seconds": round(time.time() - process.create_time(), 1),
            },
            "system": {
                "platform": sys.platform,
                "cpu_cores": cpu_count,
                "cpu_percent": psutil.cpu_percent(interval=0.1),
                "memory": {
                    "total_gb": round(memory.total / (1024**3), 2),
                    "available_gb": round(memory.available / (1024**3), 2),
                    "used_percent": memory.percent,
                },
                "disk": {
                    "total_gb": round(disk.total / (1024**3), 2),
                    "free_gb": round(disk.free / (1024**3), 2),
                    "used_percent": round((disk.used / disk.total) * 100, 1),
                },
                "boot_time": boot_time.isoformat(),
                "uptime_hours": round((datetime.now() - boot_time).total_seconds() / 3600, 1),
            },
            "bots": {
                "total": total_bots,
                "running": running_bots,
                "stopped": total_bots - running_bots,
                "voice_enabled": voice_bots,
            },
        }

        return api_response(system_data, "System information retrieved")

    except Exception as e:
        logger.error(f"Error getting system info: {e}")
        return api_response(error="Failed to retrieve system information", status_code=500)


@api_v2_system_bp.route("/system/stats", methods=["GET"])
@api_v2_auth_required
def get_stats_v2():
    """
    Get system statistics
    
    Returns:
        JSON with real-time system and application statistics
    """
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
                    "config_size_kb": round(config_size / 1024, 2),
                },
            },
            "bots": {
                "total": len(bots),
                "running": running_bots,
                "stopped": len(bots) - running_bots,
                "voice_enabled": voice_enabled,
                "voice_disabled": len(bots) - voice_enabled,
            },
            "system": {
                "cpu_percent": psutil.cpu_percent(interval=0.1),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_percent": round(
                    (psutil.disk_usage("/").used / psutil.disk_usage("/").total) * 100, 1
                ),
            },
        }

        return api_response(stats_data, "Statistics retrieved")

    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        return api_response(error="Failed to retrieve statistics", status_code=500)


@api_v2_system_bp.route("/docs", methods=["GET"])
@api_login_required  
def api_docs():
    """
    API Documentation endpoint
    
    Returns:
        HTML documentation for API v2 endpoints
    """
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
            <h1>🚀 Telegram Bot Manager API v2.0</h1>
            <p>Professional API for managing Telegram bots with enterprise features.</p>
            
            <h2>🔐 Authentication</h2>
            <p>API v2 supports both session-based and HTTP Basic authentication.</p>
            
            <h2>🏥 System Endpoints</h2>
            
            <div class="endpoint">
                <span class="method get">GET</span> <code>/api/v2/system/health</code>
                <div class="description">System health check with component status</div>
            </div>
            
            <div class="endpoint">
                <span class="method get">GET</span> <code>/api/v2/system/info</code>
                <div class="description">Detailed system information and metrics</div>
            </div>
            
            <div class="endpoint">
                <span class="method get">GET</span> <code>/api/v2/system/stats</code>
                <div class="description">Real-time system and application statistics</div>
            </div>
            
            <h2>🤖 Bot Management Endpoints</h2>
            
            <div class="endpoint">
                <span class="method get">GET</span> <code>/api/v2/bots</code>
                <div class="description">List all bots with filtering and pagination</div>
            </div>
            
            <div class="endpoint">
                <span class="method post">POST</span> <code>/api/v2/bots</code>
                <div class="description">Create new bot with validation</div>
            </div>
            
            <div class="endpoint">
                <span class="method get">GET</span> <code>/api/v2/bots/{id}</code>
                <div class="description">Get specific bot configuration</div>
            </div>
            
            <div class="endpoint">
                <span class="method put">PUT</span> <code>/api/v2/bots/{id}</code>
                <div class="description">Update bot configuration</div>
            </div>
            
            <div class="endpoint">
                <span class="method delete">DELETE</span> <code>/api/v2/bots/{id}</code>
                <div class="description">Delete bot configuration</div>
            </div>
            
            <h2>📱 Telegram Integration</h2>
            
            <div class="endpoint">
                <span class="method post">POST</span> <code>/api/v2/telegram/validate-token</code>
                <div class="description">Validate Telegram bot token and fetch bot info</div>
            </div>
            
            <h2>📋 Response Format</h2>
            <p>All API v2 responses use standardized JSON format:</p>
            <pre><code>{
  "success": true,
  "data": {...},
  "message": "Success message",
  "timestamp": "2025-08-22T20:00:00.000Z"
}</code></pre>
            
            <p style="margin-top: 40px; color: #7f8c8d; text-align: center;">
                Generated by Telegram Bot Manager v2.0
            </p>
        </div>
    </body>
    </html>
    """
    return docs_html



