"""
System routes for Flask web application.

This module provides routes for system management operations.
"""

import logging

from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for

from ...domain.entities import AdminBotConfig, SystemConfig
from ...usecases import SystemUseCase

# Create blueprint
system_bp = Blueprint('system', __name__)
system_bp.usecase: SystemUseCase | None = None

logger = logging.getLogger(__name__)


@system_bp.route('/config', methods=['GET', 'POST'])
def system_config():
    """System configuration page."""
    try:
        if request.method == 'GET':
            config = system_bp.usecase.get_system_config()
            admin_config = system_bp.usecase.get_admin_bot_config()
            return render_template('system/config.html',
                                 config=config,
                                 admin_config=admin_config)

        # Handle POST request for updating config
        data = request.form.to_dict()

        # Update system config
        system_config_data = {
            'auto_update_enabled': data.get('auto_update_enabled') == 'on',
            'backup_enabled': data.get('backup_enabled') == 'on',
            'backup_interval_hours': int(data.get('backup_interval_hours', 24)),
            'max_backups': int(data.get('max_backups', 10)),
            'log_level': data.get('log_level', 'INFO'),
            'notification_email': data.get('notification_email', ''),
        }

        system_config_obj = SystemConfig(**system_config_data)
        success = system_bp.usecase.update_system_config(system_config_obj)

        if success:
            flash('System configuration updated successfully', 'success')
        else:
            flash('Failed to update system configuration', 'error')

    except (ValueError, TypeError) as e:
        flash(f'Invalid configuration data: {e}', 'error')
    except Exception as e:
        logger.error(f"Error updating system config: {e}")
        flash('Error updating system configuration', 'error')

    return redirect(url_for('system.system_config'))


@system_bp.route('/status', methods=['GET'])
def system_status():
    """System status page."""
    try:
        stats = system_bp.usecase.get_system_stats()
        return render_template('system/status.html', stats=stats)
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        flash('Error loading system status', 'error')
        return render_template('system/status.html', stats={})


@system_bp.route('/backup', methods=['POST'])
def create_backup():
    """Create system backup."""
    try:
        backup_path = system_bp.usecase.create_backup()
        if backup_path:
            flash(f'Backup created successfully: {backup_path}', 'success')
        else:
            flash('Failed to create backup', 'error')
    except Exception as e:
        logger.error(f"Error creating backup: {e}")
        flash('Error creating backup', 'error')

    return redirect(url_for('system.system_status'))


@system_bp.route('/update', methods=['POST'])
def apply_update():
    """Apply system update."""
    try:
        success = system_bp.usecase.apply_update()
        if success:
            flash('Update applied successfully', 'success')
        else:
            flash('Failed to apply update', 'error')
    except Exception as e:
        logger.error(f"Error applying update: {e}")
        flash('Error applying update', 'error')

    return redirect(url_for('system.system_status'))


@system_bp.route('/backups', methods=['GET'])
def list_backups():
    """List system backups."""
    try:
        backups = system_bp.usecase.list_backups()
        return render_template('system/backups.html', backups=backups)
    except Exception as e:
        logger.error(f"Error listing backups: {e}")
        flash('Error loading backups', 'error')
        return render_template('system/backups.html', backups=[])


@system_bp.route('/backups/<path:backup_file>/restore', methods=['POST'])
def restore_backup(backup_file: str):
    """Restore system from backup."""
    try:
        success = system_bp.usecase.restore_backup(backup_file)
        if success:
            flash('Backup restored successfully', 'success')
        else:
            flash('Failed to restore backup', 'error')
    except Exception as e:
        logger.error(f"Error restoring backup {backup_file}: {e}")
        flash('Error restoring backup', 'error')

    return redirect(url_for('system.list_backups'))


@system_bp.route('/backups/<path:backup_file>/delete', methods=['POST'])
def delete_backup(backup_file: str):
    """Delete system backup."""
    try:
        # Note: This would need to be implemented in the use case
        flash('Backup deletion not implemented yet', 'warning')
    except Exception as e:
        logger.error(f"Error deleting backup {backup_file}: {e}")
        flash('Error deleting backup', 'error')

    return redirect(url_for('system.list_backups'))


# API endpoints for AJAX requests
@system_bp.route('/api/status', methods=['GET'])
def api_system_status():
    """API endpoint to get system status."""
    try:
        stats = system_bp.usecase.get_system_stats()
        return jsonify({
            'success': True,
            'stats': stats
        })
    except Exception as e:
        logger.error(f"API error getting system status: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to get system status'
        }), 500


@system_bp.route('/api/config', methods=['GET'])
def api_get_config():
    """API endpoint to get system configuration."""
    try:
        config = system_bp.usecase.get_system_config()
        admin_config = system_bp.usecase.get_admin_bot_config()

        return jsonify({
            'success': True,
            'config': config.to_dict() if config else None,
            'admin_config': admin_config.to_dict() if admin_config else None
        })
    except Exception as e:
        logger.error(f"API error getting system config: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to get system configuration'
        }), 500


@system_bp.route('/api/config', methods=['PUT'])
def api_update_config():
    """API endpoint to update system configuration."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400

        # Update system config
        if 'system_config' in data:
            system_config_obj = SystemConfig(**data['system_config'])
            success = system_bp.usecase.update_system_config(system_config_obj)
            if not success:
                return jsonify({
                    'success': False,
                    'error': 'Failed to update system configuration'
                }), 500

        # Update admin bot config
        if 'admin_config' in data:
            admin_config_obj = AdminBotConfig(**data['admin_config'])
            success = system_bp.usecase.update_admin_bot_config(admin_config_obj)
            if not success:
                return jsonify({
                    'success': False,
                    'error': 'Failed to update admin bot configuration'
                }), 500

        return jsonify({
            'success': True,
            'message': 'Configuration updated successfully'
        })
    except (ValueError, TypeError) as e:
        return jsonify({
            'success': False,
            'error': f'Invalid configuration data: {e}'
        }), 400
    except Exception as e:
        logger.error(f"API error updating system config: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to update system configuration'
        }), 500


@system_bp.route('/api/backup', methods=['POST'])
def api_create_backup():
    """API endpoint to create backup."""
    try:
        backup_path = system_bp.usecase.create_backup()
        if backup_path:
            return jsonify({
                'success': True,
                'backup_path': backup_path,
                'message': 'Backup created successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to create backup'
            }), 500
    except Exception as e:
        logger.error(f"API error creating backup: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to create backup'
        }), 500


@system_bp.route('/api/update', methods=['POST'])
def api_apply_update():
    """API endpoint to apply update."""
    try:
        success = system_bp.usecase.apply_update()
        if success:
            return jsonify({
                'success': True,
                'message': 'Update applied successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to apply update'
            }), 500
    except Exception as e:
        logger.error(f"API error applying update: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to apply update'
        }), 500


@system_bp.route('/api/backups', methods=['GET'])
def api_list_backups():
    """API endpoint to list backups."""
    try:
        backups = system_bp.usecase.list_backups()
        return jsonify({
            'success': True,
            'backups': backups
        })
    except Exception as e:
        logger.error(f"API error listing backups: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to list backups'
        }), 500










