"""
Unit tests for system commands (CLI Entry Point).

Tests cover all system-related CLI commands including
status, config, backup, backups, restore, update, logs, cleanup, validate.
"""

import pytest
import json
from unittest.mock import Mock, patch
from click.testing import CliRunner
from tests.entrypoints.factories import test_data_factory


class TestSystemStatusCommand:
    """Test system status command functionality."""
    
    def test_system_status_success(self, cli_runner, mock_use_cases):
        """Test system status command with valid status."""
        status_data = test_data_factory.create_system_status()
        mock_use_cases['system'].get_system_status.return_value = status_data
        
        result = cli_runner.invoke(cli_runner.app, ['system', 'status'])
        
        assert result.exit_code == 0
        assert 'System Status' in result.output
        assert 'uptime' in result.output.lower()
        assert 'version' in result.output.lower()
        assert 'bots' in result.output.lower()
        assert 'conversations' in result.output.lower()
        mock_use_cases['system'].get_system_status.assert_called_once()
    
    def test_system_status_detailed(self, cli_runner, mock_use_cases):
        """Test system status command with detailed output."""
        status_data = test_data_factory.create_system_status()
        mock_use_cases['system'].get_system_status.return_value = status_data
        
        result = cli_runner.invoke(cli_runner.app, ['system', 'status', '--detailed'])
        
        assert result.exit_code == 0
        assert 'Detailed System Status' in result.output
        assert 'memory' in result.output.lower()
        assert 'cpu' in result.output.lower()
        assert 'disk' in result.output.lower()
        assert 'network' in result.output.lower()
        mock_use_cases['system'].get_system_status.assert_called_once_with(detailed=True)
    
    def test_system_status_json_format(self, cli_runner, mock_use_cases):
        """Test system status command with JSON output."""
        status_data = test_data_factory.create_system_status()
        mock_use_cases['system'].get_system_status.return_value = status_data
        
        result = cli_runner.invoke(cli_runner.app, ['system', 'status', '--format', 'json'])
        
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert 'status' in data
        assert 'uptime' in data
        assert 'version' in data
        assert 'bots' in data
        assert 'conversations' in data
    
    def test_system_status_csv_format(self, cli_runner, mock_use_cases):
        """Test system status command with CSV output."""
        status_data = test_data_factory.create_system_status()
        mock_use_cases['system'].get_system_status.return_value = status_data
        
        result = cli_runner.invoke(cli_runner.app, ['system', 'status', '--format', 'csv'])
        
        assert result.exit_code == 0
        assert 'status,uptime,version' in result.output.lower()
    
    def test_system_status_server_error(self, cli_runner, mock_use_cases):
        """Test system status command with server error."""
        mock_use_cases['system'].get_system_status.side_effect = Exception("Server error")
        
        result = cli_runner.invoke(cli_runner.app, ['system', 'status'])
        
        assert result.exit_code == 1
        assert 'Error:' in result.output
        assert 'Server error' in result.output


class TestSystemConfigCommand:
    """Test system config command functionality."""
    
    def test_system_config_show(self, cli_runner, mock_use_cases):
        """Test system config show command."""
        config_data = {
            'database': {'url': 'sqlite:///bot_manager.db'},
            'telegram': {'api_timeout': 30},
            'logging': {'level': 'INFO'},
            'security': {'session_timeout': 3600}
        }
        mock_use_cases['system'].get_system_config.return_value = config_data
        
        result = cli_runner.invoke(cli_runner.app, ['system', 'config', 'show'])
        
        assert result.exit_code == 0
        assert 'System Configuration' in result.output
        assert 'database' in result.output
        assert 'telegram' in result.output
        assert 'logging' in result.output
        assert 'security' in result.output
        mock_use_cases['system'].get_system_config.assert_called_once()
    
    def test_system_config_show_json_format(self, cli_runner, mock_use_cases):
        """Test system config show command with JSON output."""
        config_data = {'database': {'url': 'sqlite:///bot_manager.db'}}
        mock_use_cases['system'].get_system_config.return_value = config_data
        
        result = cli_runner.invoke(cli_runner.app, ['system', 'config', 'show', '--format', 'json'])
        
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert 'database' in data
        assert data['database']['url'] == 'sqlite:///bot_manager.db'
    
    def test_system_config_update(self, cli_runner, mock_use_cases):
        """Test system config update command."""
        updated_config = {'logging': {'level': 'DEBUG'}}
        mock_use_cases['system'].update_system_config.return_value = updated_config
        
        result = cli_runner.invoke(cli_runner.app, [
            'system', 'config', 'update',
            '--logging-level', 'DEBUG'
        ])
        
        assert result.exit_code == 0
        assert 'Configuration updated successfully' in result.output
        mock_use_cases['system'].update_system_config.assert_called_once()
    
    def test_system_config_update_validation_error(self, cli_runner, mock_use_cases):
        """Test system config update command with validation error."""
        mock_use_cases['system'].update_system_config.side_effect = ValueError('Invalid log level')
        
        result = cli_runner.invoke(cli_runner.app, [
            'system', 'config', 'update',
            '--logging-level', 'INVALID'
        ])
        
        assert result.exit_code == 1
        assert 'Error:' in result.output
        assert 'Invalid log level' in result.output
    
    def test_system_config_reset(self, cli_runner, mock_use_cases):
        """Test system config reset command."""
        default_config = {'database': {'url': 'sqlite:///bot_manager.db'}}
        mock_use_cases['system'].reset_system_config.return_value = default_config
        
        result = cli_runner.invoke(cli_runner.app, ['system', 'config', 'reset'], input='y\n')
        
        assert result.exit_code == 0
        assert 'Configuration reset to defaults' in result.output
        mock_use_cases['system'].reset_system_config.assert_called_once()
    
    def test_system_config_reset_without_confirmation(self, cli_runner, mock_use_cases):
        """Test system config reset command without confirmation."""
        result = cli_runner.invoke(cli_runner.app, ['system', 'config', 'reset'], input='n\n')
        
        assert result.exit_code == 0
        assert 'Operation cancelled' in result.output
        mock_use_cases['system'].reset_system_config.assert_not_called()


class TestSystemBackupCommand:
    """Test system backup command functionality."""
    
    def test_system_backup_create(self, cli_runner, mock_use_cases):
        """Test system backup create command."""
        backup_info = test_data_factory.create_backup_info()
        mock_use_cases['system'].create_backup.return_value = backup_info
        
        result = cli_runner.invoke(cli_runner.app, ['system', 'backup', 'create'])
        
        assert result.exit_code == 0
        assert 'Backup created successfully' in result.output
        assert backup_info['filename'] in result.output
        assert str(backup_info['size']) in result.output
        mock_use_cases['system'].create_backup.assert_called_once()
    
    def test_system_backup_create_with_description(self, cli_runner, mock_use_cases):
        """Test system backup create command with description."""
        backup_info = test_data_factory.create_backup_info()
        mock_use_cases['system'].create_backup.return_value = backup_info
        
        result = cli_runner.invoke(cli_runner.app, [
            'system', 'backup', 'create',
            '--description', 'Pre-update backup'
        ])
        
        assert result.exit_code == 0
        assert 'Backup created successfully' in result.output
        mock_use_cases['system'].create_backup.assert_called_once_with(description='Pre-update backup')
    
    def test_system_backup_create_server_error(self, cli_runner, mock_use_cases):
        """Test system backup create command with server error."""
        mock_use_cases['system'].create_backup.side_effect = Exception("Backup failed")
        
        result = cli_runner.invoke(cli_runner.app, ['system', 'backup', 'create'])
        
        assert result.exit_code == 1
        assert 'Error:' in result.output
        assert 'Backup failed' in result.output
    
    def test_system_backup_list(self, cli_runner, mock_use_cases):
        """Test system backup list command."""
        backups = [
            test_data_factory.create_backup_info(id=1, filename='backup_2024_01_15.sql'),
            test_data_factory.create_backup_info(id=2, filename='backup_2024_01_14.sql')
        ]
        mock_use_cases['system'].list_backups.return_value = backups
        
        result = cli_runner.invoke(cli_runner.app, ['system', 'backup', 'list'])
        
        assert result.exit_code == 0
        assert 'backup_2024_01_15.sql' in result.output
        assert 'backup_2024_01_14.sql' in result.output
        assert 'ID' in result.output
        assert 'Filename' in result.output
        assert 'Size' in result.output
        assert 'Created' in result.output
        mock_use_cases['system'].list_backups.assert_called_once()
    
    def test_system_backup_list_empty(self, cli_runner, mock_use_cases):
        """Test system backup list command with no backups."""
        mock_use_cases['system'].list_backups.return_value = []
        
        result = cli_runner.invoke(cli_runner.app, ['system', 'backup', 'list'])
        
        assert result.exit_code == 0
        assert 'No backups found' in result.output
        mock_use_cases['system'].list_backups.assert_called_once()
    
    def test_system_backup_list_json_format(self, cli_runner, mock_use_cases):
        """Test system backup list command with JSON output."""
        backups = [test_data_factory.create_backup_info(id=1, filename='backup.sql')]
        mock_use_cases['system'].list_backups.return_value = backups
        
        result = cli_runner.invoke(cli_runner.app, ['system', 'backup', 'list', '--format', 'json'])
        
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]['id'] == 1
        assert data[0]['filename'] == 'backup.sql'
    
    def test_system_backup_show(self, cli_runner, mock_use_cases):
        """Test system backup show command."""
        backup_info = test_data_factory.create_backup_info()
        mock_use_cases['system'].get_backup.return_value = backup_info
        
        result = cli_runner.invoke(cli_runner.app, ['system', 'backup', 'show', '1'])
        
        assert result.exit_code == 0
        assert 'Backup Details' in result.output
        assert backup_info['filename'] in result.output
        assert str(backup_info['size']) in result.output
        mock_use_cases['system'].get_backup.assert_called_once_with(1)
    
    def test_system_backup_show_not_found(self, cli_runner, mock_use_cases):
        """Test system backup show command with non-existent backup."""
        mock_use_cases['system'].get_backup.return_value = None
        
        result = cli_runner.invoke(cli_runner.app, ['system', 'backup', 'show', '999'])
        
        assert result.exit_code == 1
        assert 'Backup not found' in result.output
        assert 'Error:' in result.output
    
    def test_system_backup_delete(self, cli_runner, mock_use_cases):
        """Test system backup delete command."""
        mock_use_cases['system'].delete_backup.return_value = True
        
        result = cli_runner.invoke(cli_runner.app, ['system', 'backup', 'delete', '1'], input='y\n')
        
        assert result.exit_code == 0
        assert 'Backup deleted successfully' in result.output
        mock_use_cases['system'].delete_backup.assert_called_once_with(1)
    
    def test_system_backup_delete_without_confirmation(self, cli_runner, mock_use_cases):
        """Test system backup delete command without confirmation."""
        result = cli_runner.invoke(cli_runner.app, ['system', 'backup', 'delete', '1'], input='n\n')
        
        assert result.exit_code == 0
        assert 'Operation cancelled' in result.output
        mock_use_cases['system'].delete_backup.assert_not_called()
    
    def test_system_backup_delete_force_flag(self, cli_runner, mock_use_cases):
        """Test system backup delete command with force flag."""
        mock_use_cases['system'].delete_backup.return_value = True
        
        result = cli_runner.invoke(cli_runner.app, ['system', 'backup', 'delete', '1', '--force'])
        
        assert result.exit_code == 0
        assert 'Backup deleted successfully' in result.output
        mock_use_cases['system'].delete_backup.assert_called_once_with(1)


class TestSystemRestoreCommand:
    """Test system restore command functionality."""
    
    def test_system_restore_success(self, cli_runner, mock_use_cases):
        """Test system restore command with confirmation."""
        mock_use_cases['system'].restore_backup.return_value = {
            'success': True,
            'message': 'System restored successfully'
        }
        
        result = cli_runner.invoke(cli_runner.app, ['system', 'restore', '1'], input='y\n')
        
        assert result.exit_code == 0
        assert 'System restored successfully' in result.output
        mock_use_cases['system'].restore_backup.assert_called_once_with(1)
    
    def test_system_restore_without_confirmation(self, cli_runner, mock_use_cases):
        """Test system restore command without confirmation."""
        result = cli_runner.invoke(cli_runner.app, ['system', 'restore', '1'], input='n\n')
        
        assert result.exit_code == 0
        assert 'Operation cancelled' in result.output
        mock_use_cases['system'].restore_backup.assert_not_called()
    
    def test_system_restore_force_flag(self, cli_runner, mock_use_cases):
        """Test system restore command with force flag."""
        mock_use_cases['system'].restore_backup.return_value = {
            'success': True,
            'message': 'System restored successfully'
        }
        
        result = cli_runner.invoke(cli_runner.app, ['system', 'restore', '1', '--force'])
        
        assert result.exit_code == 0
        assert 'System restored successfully' in result.output
        mock_use_cases['system'].restore_backup.assert_called_once_with(1)
    
    def test_system_restore_backup_not_found(self, cli_runner, mock_use_cases):
        """Test system restore command with non-existent backup."""
        mock_use_cases['system'].restore_backup.return_value = {
            'success': False,
            'error': 'Backup not found'
        }
        
        result = cli_runner.invoke(cli_runner.app, ['system', 'restore', '999', '--force'])
        
        assert result.exit_code == 1
        assert 'Backup not found' in result.output
        assert 'Error:' in result.output
    
    def test_system_restore_corrupted_backup(self, cli_runner, mock_use_cases):
        """Test system restore command with corrupted backup."""
        mock_use_cases['system'].restore_backup.return_value = {
            'success': False,
            'error': 'Backup file is corrupted'
        }
        
        result = cli_runner.invoke(cli_runner.app, ['system', 'restore', '1', '--force'])
        
        assert result.exit_code == 1
        assert 'Backup file is corrupted' in result.output
        assert 'Error:' in result.output


class TestSystemUpdateCommand:
    """Test system update command functionality."""
    
    def test_system_update_check(self, cli_runner, mock_use_cases):
        """Test system update check command."""
        update_info = test_data_factory.create_update_info()
        mock_use_cases['system'].check_for_updates.return_value = update_info
        
        result = cli_runner.invoke(cli_runner.app, ['system', 'update', 'check'])
        
        assert result.exit_code == 0
        assert 'Update Check' in result.output
        assert update_info['current_version'] in result.output
        assert update_info['latest_version'] in result.output
        assert 'available' in result.output.lower()
        mock_use_cases['system'].check_for_updates.assert_called_once()
    
    def test_system_update_check_no_updates(self, cli_runner, mock_use_cases):
        """Test system update check command with no updates available."""
        update_info = {
            'current_version': '1.0.0',
            'latest_version': '1.0.0',
            'update_available': False,
            'message': 'System is up to date'
        }
        mock_use_cases['system'].check_for_updates.return_value = update_info
        
        result = cli_runner.invoke(cli_runner.app, ['system', 'update', 'check'])
        
        assert result.exit_code == 0
        assert 'System is up to date' in result.output
        assert 'No updates available' in result.output
    
    def test_system_update_apply(self, cli_runner, mock_use_cases):
        """Test system update apply command."""
        mock_use_cases['system'].apply_update.return_value = {
            'success': True,
            'message': 'System updated successfully',
            'new_version': '1.1.0'
        }
        
        result = cli_runner.invoke(cli_runner.app, ['system', 'update', 'apply'], input='y\n')
        
        assert result.exit_code == 0
        assert 'System updated successfully' in result.output
        assert '1.1.0' in result.output
        mock_use_cases['system'].apply_update.assert_called_once()
    
    def test_system_update_apply_without_confirmation(self, cli_runner, mock_use_cases):
        """Test system update apply command without confirmation."""
        result = cli_runner.invoke(cli_runner.app, ['system', 'update', 'apply'], input='n\n')
        
        assert result.exit_code == 0
        assert 'Operation cancelled' in result.output
        mock_use_cases['system'].apply_update.assert_not_called()
    
    def test_system_update_apply_force_flag(self, cli_runner, mock_use_cases):
        """Test system update apply command with force flag."""
        mock_use_cases['system'].apply_update.return_value = {
            'success': True,
            'message': 'System updated successfully'
        }
        
        result = cli_runner.invoke(cli_runner.app, ['system', 'update', 'apply', '--force'])
        
        assert result.exit_code == 0
        assert 'System updated successfully' in result.output
        mock_use_cases['system'].apply_update.assert_called_once()
    
    def test_system_update_apply_no_updates(self, cli_runner, mock_use_cases):
        """Test system update apply command with no updates available."""
        mock_use_cases['system'].apply_update.return_value = {
            'success': False,
            'error': 'No updates available'
        }
        
        result = cli_runner.invoke(cli_runner.app, ['system', 'update', 'apply', '--force'])
        
        assert result.exit_code == 1
        assert 'No updates available' in result.output
        assert 'Error:' in result.output
    
    def test_system_update_apply_failed(self, cli_runner, mock_use_cases):
        """Test system update apply command with update failure."""
        mock_use_cases['system'].apply_update.return_value = {
            'success': False,
            'error': 'Update failed: Network error'
        }
        
        result = cli_runner.invoke(cli_runner.app, ['system', 'update', 'apply', '--force'])
        
        assert result.exit_code == 1
        assert 'Update failed: Network error' in result.output
        assert 'Error:' in result.output


class TestSystemLogsCommand:
    """Test system logs command functionality."""
    
    def test_system_logs_basic(self, cli_runner, mock_use_cases):
        """Test system logs command with basic output."""
        logs = [
            {'timestamp': '2024-01-15 10:30:00', 'level': 'INFO', 'message': 'System started'},
            {'timestamp': '2024-01-15 10:31:00', 'level': 'ERROR', 'message': 'Connection failed'}
        ]
        mock_use_cases['system'].get_system_logs.return_value = logs
        
        result = cli_runner.invoke(cli_runner.app, ['system', 'logs'])
        
        assert result.exit_code == 0
        assert 'System started' in result.output
        assert 'Connection failed' in result.output
        assert 'INFO' in result.output
        assert 'ERROR' in result.output
        mock_use_cases['system'].get_system_logs.assert_called_once()
    
    def test_system_logs_with_level_filter(self, cli_runner, mock_use_cases):
        """Test system logs command with level filter."""
        logs = [{'timestamp': '2024-01-15 10:30:00', 'level': 'ERROR', 'message': 'Connection failed'}]
        mock_use_cases['system'].get_system_logs.return_value = logs
        
        result = cli_runner.invoke(cli_runner.app, ['system', 'logs', '--level', 'ERROR'])
        
        assert result.exit_code == 0
        assert 'Connection failed' in result.output
        mock_use_cases['system'].get_system_logs.assert_called_once_with(level='ERROR')
    
    def test_system_logs_with_limit(self, cli_runner, mock_use_cases):
        """Test system logs command with limit."""
        logs = [{'timestamp': '2024-01-15 10:30:00', 'level': 'INFO', 'message': 'System started'}]
        mock_use_cases['system'].get_system_logs.return_value = logs
        
        result = cli_runner.invoke(cli_runner.app, ['system', 'logs', '--limit', '10'])
        
        assert result.exit_code == 0
        mock_use_cases['system'].get_system_logs.assert_called_once_with(limit=10)
    
    def test_system_logs_with_tail(self, cli_runner, mock_use_cases):
        """Test system logs command with tail option."""
        logs = [{'timestamp': '2024-01-15 10:30:00', 'level': 'INFO', 'message': 'System started'}]
        mock_use_cases['system'].get_system_logs.return_value = logs
        
        result = cli_runner.invoke(cli_runner.app, ['system', 'logs', '--tail', '50'])
        
        assert result.exit_code == 0
        mock_use_cases['system'].get_system_logs.assert_called_once_with(tail=50)
    
    def test_system_logs_json_format(self, cli_runner, mock_use_cases):
        """Test system logs command with JSON output."""
        logs = [{'timestamp': '2024-01-15 10:30:00', 'level': 'INFO', 'message': 'System started'}]
        mock_use_cases['system'].get_system_logs.return_value = logs
        
        result = cli_runner.invoke(cli_runner.app, ['system', 'logs', '--format', 'json'])
        
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]['level'] == 'INFO'
        assert data[0]['message'] == 'System started'
    
    def test_system_logs_empty(self, cli_runner, mock_use_cases):
        """Test system logs command with no logs."""
        mock_use_cases['system'].get_system_logs.return_value = []
        
        result = cli_runner.invoke(cli_runner.app, ['system', 'logs'])
        
        assert result.exit_code == 0
        assert 'No logs found' in result.output
        mock_use_cases['system'].get_system_logs.assert_called_once()


class TestSystemCleanupCommand:
    """Test system cleanup command functionality."""
    
    def test_system_cleanup_success(self, cli_runner, mock_use_cases):
        """Test system cleanup command."""
        cleanup_result = {
            'success': True,
            'message': 'Cleanup completed successfully',
            'files_removed': 5,
            'space_freed': '2.5 MB'
        }
        mock_use_cases['system'].cleanup_system.return_value = cleanup_result
        
        result = cli_runner.invoke(cli_runner.app, ['system', 'cleanup'], input='y\n')
        
        assert result.exit_code == 0
        assert 'Cleanup completed successfully' in result.output
        assert '5' in result.output
        assert '2.5 MB' in result.output
        mock_use_cases['system'].cleanup_system.assert_called_once()
    
    def test_system_cleanup_without_confirmation(self, cli_runner, mock_use_cases):
        """Test system cleanup command without confirmation."""
        result = cli_runner.invoke(cli_runner.app, ['system', 'cleanup'], input='n\n')
        
        assert result.exit_code == 0
        assert 'Operation cancelled' in result.output
        mock_use_cases['system'].cleanup_system.assert_not_called()
    
    def test_system_cleanup_force_flag(self, cli_runner, mock_use_cases):
        """Test system cleanup command with force flag."""
        cleanup_result = {
            'success': True,
            'message': 'Cleanup completed successfully',
            'files_removed': 3,
            'space_freed': '1.2 MB'
        }
        mock_use_cases['system'].cleanup_system.return_value = cleanup_result
        
        result = cli_runner.invoke(cli_runner.app, ['system', 'cleanup', '--force'])
        
        assert result.exit_code == 0
        assert 'Cleanup completed successfully' in result.output
        mock_use_cases['system'].cleanup_system.assert_called_once()
    
    def test_system_cleanup_dry_run(self, cli_runner, mock_use_cases):
        """Test system cleanup command with dry run."""
        cleanup_result = {
            'success': True,
            'message': 'Dry run completed',
            'files_to_remove': 5,
            'space_to_free': '2.5 MB'
        }
        mock_use_cases['system'].cleanup_system.return_value = cleanup_result
        
        result = cli_runner.invoke(cli_runner.app, ['system', 'cleanup', '--dry-run'])
        
        assert result.exit_code == 0
        assert 'Dry run completed' in result.output
        assert '5' in result.output
        assert '2.5 MB' in result.output
        mock_use_cases['system'].cleanup_system.assert_called_once_with(dry_run=True)
    
    def test_system_cleanup_failed(self, cli_runner, mock_use_cases):
        """Test system cleanup command with failure."""
        mock_use_cases['system'].cleanup_system.return_value = {
            'success': False,
            'error': 'Cleanup failed: Permission denied'
        }
        
        result = cli_runner.invoke(cli_runner.app, ['system', 'cleanup', '--force'])
        
        assert result.exit_code == 1
        assert 'Cleanup failed: Permission denied' in result.output
        assert 'Error:' in result.output


class TestSystemValidateCommand:
    """Test system validate command functionality."""
    
    def test_system_validate_success(self, cli_runner, mock_use_cases):
        """Test system validate command with valid system."""
        validation_result = {
            'valid': True,
            'message': 'System validation passed',
            'checks': [
                {'name': 'Database Connection', 'status': 'OK'},
                {'name': 'File Permissions', 'status': 'OK'},
                {'name': 'Configuration', 'status': 'OK'}
            ]
        }
        mock_use_cases['system'].validate_system.return_value = validation_result
        
        result = cli_runner.invoke(cli_runner.app, ['system', 'validate'])
        
        assert result.exit_code == 0
        assert 'System validation passed' in result.output
        assert 'Database Connection' in result.output
        assert 'File Permissions' in result.output
        assert 'Configuration' in result.output
        assert 'OK' in result.output
        mock_use_cases['system'].validate_system.assert_called_once()
    
    def test_system_validate_with_issues(self, cli_runner, mock_use_cases):
        """Test system validate command with validation issues."""
        validation_result = {
            'valid': False,
            'message': 'System validation failed',
            'checks': [
                {'name': 'Database Connection', 'status': 'OK'},
                {'name': 'File Permissions', 'status': 'ERROR', 'message': 'Cannot write to logs directory'},
                {'name': 'Configuration', 'status': 'WARNING', 'message': 'Missing optional setting'}
            ]
        }
        mock_use_cases['system'].validate_system.return_value = validation_result
        
        result = cli_runner.invoke(cli_runner.app, ['system', 'validate'])
        
        assert result.exit_code == 1
        assert 'System validation failed' in result.output
        assert 'ERROR' in result.output
        assert 'WARNING' in result.output
        assert 'Cannot write to logs directory' in result.output
        assert 'Missing optional setting' in result.output
        mock_use_cases['system'].validate_system.assert_called_once()
    
    def test_system_validate_json_format(self, cli_runner, mock_use_cases):
        """Test system validate command with JSON output."""
        validation_result = {
            'valid': True,
            'message': 'System validation passed',
            'checks': [{'name': 'Database Connection', 'status': 'OK'}]
        }
        mock_use_cases['system'].validate_system.return_value = validation_result
        
        result = cli_runner.invoke(cli_runner.app, ['system', 'validate', '--format', 'json'])
        
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data['valid'] is True
        assert data['message'] == 'System validation passed'
        assert len(data['checks']) == 1
        assert data['checks'][0]['name'] == 'Database Connection'
        assert data['checks'][0]['status'] == 'OK'
    
    def test_system_validate_server_error(self, cli_runner, mock_use_cases):
        """Test system validate command with server error."""
        mock_use_cases['system'].validate_system.side_effect = Exception("Validation service unavailable")
        
        result = cli_runner.invoke(cli_runner.app, ['system', 'validate'])
        
        assert result.exit_code == 1
        assert 'Error:' in result.output
        assert 'Validation service unavailable' in result.output


class TestSystemCommandErrorHandling:
    """Test system command error handling."""
    
    def test_system_command_server_error(self, cli_runner, mock_use_cases):
        """Test system command with server error."""
        mock_use_cases['system'].get_system_status.side_effect = Exception("Server error")
        
        result = cli_runner.invoke(cli_runner.app, ['system', 'status'])
        
        assert result.exit_code == 1
        assert 'Error:' in result.output
        assert 'Server error' in result.output
    
    def test_system_command_network_error(self, cli_runner, mock_use_cases):
        """Test system command with network error."""
        mock_use_cases['system'].get_system_status.side_effect = ConnectionError("Network error")
        
        result = cli_runner.invoke(cli_runner.app, ['system', 'status'])
        
        assert result.exit_code == 1
        assert 'Error:' in result.output
        assert 'Network error' in result.output
    
    def test_system_command_timeout_error(self, cli_runner, mock_use_cases):
        """Test system command with timeout error."""
        mock_use_cases['system'].get_system_status.side_effect = TimeoutError("Request timeout")
        
        result = cli_runner.invoke(cli_runner.app, ['system', 'status'])
        
        assert result.exit_code == 1
        assert 'Error:' in result.output
        assert 'Request timeout' in result.output


class TestSystemCommandHelp:
    """Test system command help functionality."""
    
    def test_system_command_help(self, cli_runner):
        """Test system command help."""
        result = cli_runner.invoke(cli_runner.app, ['system', '--help'])
        
        assert result.exit_code == 0
        assert 'Usage:' in result.output
        assert 'Commands:' in result.output
        assert 'status' in result.output
        assert 'config' in result.output
        assert 'backup' in result.output
        assert 'restore' in result.output
        assert 'update' in result.output
        assert 'logs' in result.output
        assert 'cleanup' in result.output
        assert 'validate' in result.output
    
    def test_system_status_help(self, cli_runner):
        """Test system status command help."""
        result = cli_runner.invoke(cli_runner.app, ['system', 'status', '--help'])
        
        assert result.exit_code == 0
        assert 'Usage:' in result.output
        assert 'Options:' in result.output
        assert '--detailed' in result.output
        assert '--format' in result.output
    
    def test_system_config_help(self, cli_runner):
        """Test system config command help."""
        result = cli_runner.invoke(cli_runner.app, ['system', 'config', '--help'])
        
        assert result.exit_code == 0
        assert 'Usage:' in result.output
        assert 'Commands:' in result.output
        assert 'show' in result.output
        assert 'update' in result.output
        assert 'reset' in result.output
    
    def test_system_backup_help(self, cli_runner):
        """Test system backup command help."""
        result = cli_runner.invoke(cli_runner.app, ['system', 'backup', '--help'])
        
        assert result.exit_code == 0
        assert 'Usage:' in result.output
        assert 'Commands:' in result.output
        assert 'create' in result.output
        assert 'list' in result.output
        assert 'show' in result.output
        assert 'delete' in result.output
    
    def test_system_update_help(self, cli_runner):
        """Test system update command help."""
        result = cli_runner.invoke(cli_runner.app, ['system', 'update', '--help'])
        
        assert result.exit_code == 0
        assert 'Usage:' in result.output
        assert 'Commands:' in result.output
        assert 'check' in result.output
        assert 'apply' in result.output








