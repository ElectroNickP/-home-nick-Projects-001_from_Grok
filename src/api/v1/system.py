"""
API v1 System Routes for Telegram Bot Manager

This module handles legacy API v1 system endpoints:
- GET /api/version - version information
- GET /api/check-updates - check for available updates
- POST /api/update - perform application update
- GET /api/update/status - get update status
- GET /api/update/backups - list backups
- POST /api/update/backups/cleanup - cleanup old backups

Extracted from monolithic app.py during refactoring.
"""

import logging
from flask import Blueprint, request, jsonify

import version
from auto_updater import auto_updater
from shared.auth import api_login_required, login_required

logger = logging.getLogger(__name__)

# Create API v1 system blueprint
api_v1_system_bp = Blueprint('api_v1_system', __name__, url_prefix='/api')


@api_v1_system_bp.route("/version", methods=["GET"])
def get_version_api():
    """
    API endpoint for getting version information
    
    Returns:
        JSON version details
    """
    try:
        version_info = version.get_version_info()
        return jsonify(version_info.version_details)
    except Exception as e:
        logger.error(f"Error getting version info: {e}")
        return jsonify({"error": "Failed to get version information"}), 500


def check_for_updates():
    """
    Legacy function - redirects to auto_updater with compatibility format
    
    Returns:
        Tuple (success, message, local_commit, remote_commit, commit_log)
    """
    result = auto_updater.check_for_updates()
    if result["success"]:
        return (
            True,
            result["message"],
            result.get("local_commit", "unknown"),
            result.get("remote_commit", "unknown"),
            result.get("commit_log", []),
        )
    else:
        return False, result["error"], None, None


@api_v1_system_bp.route("/check-updates", methods=["GET"])
@api_login_required
def check_updates_api():
    """
    API endpoint to check for available updates
    
    Returns:
        JSON with update availability and commit information
    """
    try:
        result = check_for_updates()
        if not isinstance(result, tuple) or len(result) < 4:
            return jsonify({"error": "Invalid update check result"}), 500

        success, message, local_commit, remote_commit, *commit_log = result

        if not success:
            return jsonify({"error": message}), 500

        response = {
            "has_updates": (
                local_commit != remote_commit if local_commit and remote_commit else False
            ),
            "message": message,
            "local_commit": local_commit,
            "remote_commit": remote_commit,
            "current_version": version.get_version(),
        }

        if commit_log:
            # commit_log is already a list of commit lines
            response["new_commits"] = commit_log if isinstance(commit_log, list) else []

        return jsonify(response)

    except Exception as e:
        logger.error(f"Error in check_updates_api: {e}")
        return jsonify({"error": str(e)}), 500


@api_v1_system_bp.route("/update", methods=["POST"])
@api_login_required
def update_application():
    """
    API endpoint to perform professional application update
    
    Returns:
        JSON with update result and backup information
    """
    try:
        if auto_updater.is_update_in_progress():
            return jsonify({
                "error": "Update already in progress",
                "status": auto_updater.get_update_status(),
            }), 409

        # Perform professional update with backup and rollback
        result = auto_updater.perform_update()

        if result["success"]:
            logger.info(f"Application update successful: {result['message']}")
            return jsonify({
                "success": True,
                "message": result["message"],
                "backup_id": result.get("backup_id"),
                "new_version": result.get("new_version"),
            })
        else:
            logger.error(f"Application update failed: {result['error']}")
            return jsonify({
                "error": result["error"],
                "backup_id": result.get("backup_id")
            }), 500

    except Exception as e:
        logger.error(f"Error in update_application: {e}")
        return jsonify({"error": str(e)}), 500


@api_v1_system_bp.route("/update/status", methods=["GET"])
@api_login_required
def get_update_status():
    """
    Get current update status with progress information
    
    Returns:
        JSON with current update status and progress
    """
    try:
        status = auto_updater.get_update_status()
        return jsonify({"success": True, "data": status})
    except Exception as e:
        logger.error(f"Error getting update status: {e}")
        return jsonify({"error": str(e)}), 500


@api_v1_system_bp.route("/update/backups", methods=["GET"])
@api_login_required
def list_backups():
    """
    List all available backups
    
    Returns:
        JSON list of available backups with metadata
    """
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


@api_v1_system_bp.route("/update/backups/cleanup", methods=["POST"])
@api_login_required
def cleanup_backups():
    """
    Clean up old backups, keeping only the most recent ones
    
    Expected JSON payload:
    {
        "keep_count": 5  // Number of backups to keep (default: 5)
    }
    
    Returns:
        JSON cleanup result with count of removed backups
    """
    try:
        data = request.get_json() or {}
        keep_count = data.get("keep_count", 5)

        # Validate keep_count
        if not isinstance(keep_count, int) or keep_count < 1:
            return jsonify({
                "error": "keep_count must be a positive integer"
            }), 400

        result = auto_updater.cleanup_old_backups(keep_count)

        if result["success"]:
            logger.info(f"Backup cleanup successful: removed {result.get('removed_count', 0)} backups")
            return jsonify({
                "success": True,
                "message": result["message"],
                "removed_count": result.get("removed_count", 0),
            })
        else:
            logger.error(f"Backup cleanup failed: {result['error']}")
            return jsonify({"error": result["error"]}), 500

    except Exception as e:
        logger.error(f"Error cleaning up backups: {e}")
        return jsonify({"error": str(e)}), 500
