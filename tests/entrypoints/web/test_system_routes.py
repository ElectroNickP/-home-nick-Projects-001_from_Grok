"""
Unit tests for system routes (Web Entry Point).

Tests cover all system-related routes including status, configuration,
backup management, updates, and AJAX endpoints.
"""

import pytest
import json
from unittest.mock import Mock, patch
from tests.entrypoints.factories import test_data_factory


class TestSystemRoutesAuthentication:
    """Test authentication for system routes."""
    
    def test_system_status_requires_authentication(self, web_client):
        """Test that system status route requires authentication."""
        response = web_client.get('/system/status')
        
        assert response.status_code == 302  # Redirect to login
        assert '/login' in response.location
    
    def test_system_config_requires_authentication(self, web_client):
        """Test that system config route requires authentication."""
        response = web_client.get('/system/config')
        
        assert response.status_code == 302  # Redirect to login
        assert '/login' in response.location
    
    def test_system_backup_requires_authentication(self, web_client):
        """Test that system backup route requires authentication."""
        response = web_client.post('/system/backup')
        
        assert response.status_code == 302  # Redirect to login
        assert '/login' in response.location


class TestSystemStatusRoute:
    """Test system status route functionality."""
    
    def test_system_status_returns_200(self, authenticated_web_client, mock_use_cases):
        """Test that system status route returns 200 status."""
        status_data = test_data_factory.create_system_status()
        mock_use_cases['system'].get_system_status.return_value = status_data
        
        response = authenticated_web_client.get('/system/status')
        
        assert response.status_code == 200
        assert b'running' in response.data.lower()
        assert b'3.6.0' in response.data
        mock_use_cases['system'].get_system_status.assert_called_once()
    
    def test_system_status_use_case_called(self, authenticated_web_client, mock_use_cases):
        """Test that use case is called for system status."""
        mock_use_cases['system'].get_system_status.return_value = {}
        
        authenticated_web_client.get('/system/status')
        
        mock_use_cases['system'].get_system_status.assert_called_once()
    
    def test_system_status_with_detailed_info(self, authenticated_web_client, mock_use_cases):
        """Test system status with detailed information."""
        status_data = test_data_factory.create_system_status(
            status='running',
            uptime=7200,
            memory_usage=1024,
            cpu_usage=45.5,
            active_bots=3,
            total_conversations=25
        )
        mock_use_cases['system'].get_system_status.return_value = status_data
        
        response = authenticated_web_client.get('/system/status')
        
        assert response.status_code == 200
        assert b'1024' in response.data
        assert b'45.5' in response.data
        assert b'3' in response.data
        assert b'25' in response.data


class TestSystemConfigRoute:
    """Test system config route functionality."""
    
    def test_system_config_returns_200(self, authenticated_web_client, mock_use_cases):
        """Test that system config route returns 200 status."""
        config_data = {
            'version': '3.6.0',
            'debug': True,
            'web_port': 60183,
            'api_port': 8000,
            'max_bots': 10,
            'backup_enabled': True
        }
        mock_use_cases['system'].get_system_config.return_value = config_data
        
        response = authenticated_web_client.get('/system/config')
        
        assert response.status_code == 200
        assert b'3.6.0' in response.data
        assert b'60183' in response.data
        mock_use_cases['system'].get_system_config.assert_called_once()
    
    def test_system_config_update_success(self, authenticated_web_client, mock_use_cases):
        """Test successful system config update."""
        updated_config = {
            'version': '3.6.0',
            'debug': False,
            'max_bots': 15
        }
        mock_use_cases['system'].update_system_config.return_value = updated_config
        
        response = authenticated_web_client.post('/system/config', data={
            'debug': 'false',
            'max_bots': '15'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        mock_use_cases['system'].update_system_config.assert_called_once()
    
    def test_system_config_update_validation_error(self, authenticated_web_client, mock_use_cases):
        """Test system config update with validation error."""
        mock_use_cases['system'].update_system_config.side_effect = ValueError("Invalid config")
        
        response = authenticated_web_client.post('/system/config', data={
            'max_bots': 'invalid'
        })
        
        assert response.status_code == 200  # Form should be re-rendered with errors
        assert b'Invalid config' in response.data or b'error' in response.data.lower()


class TestSystemBackupRoute:
    """Test system backup route functionality."""
    
    def test_system_backup_list_returns_200(self, authenticated_web_client, mock_use_cases):
        """Test that system backup list route returns 200 status."""
        backups = [
            test_data_factory.create_backup_info(id='backup1'),
            test_data_factory.create_backup_info(id='backup2')
        ]
        mock_use_cases['system'].get_backups.return_value = backups
        
        response = authenticated_web_client.get('/system/backups')
        
        assert response.status_code == 200
        assert b'backup1' in response.data
        assert b'backup2' in response.data
        mock_use_cases['system'].get_backups.assert_called_once()
    
    def test_system_backup_create_success(self, authenticated_web_client, mock_use_cases):
        """Test successful backup creation."""
        backup_id = 'backup_20250101_000000'
        mock_use_cases['system'].create_backup.return_value = backup_id
        
        response = authenticated_web_client.post('/system/backup', follow_redirects=True)
        
        assert response.status_code == 200
        assert backup_id.encode() in response.data
        mock_use_cases['system'].create_backup.assert_called_once()
    
    def test_system_backup_restore_success(self, authenticated_web_client, mock_use_cases):
        """Test successful backup restoration."""
        mock_use_cases['system'].restore_backup.return_value = True
        
        response = authenticated_web_client.post('/system/backups/backup1/restore', follow_redirects=True)
        
        assert response.status_code == 200
        assert b'restored' in response.data.lower()
        mock_use_cases['system'].restore_backup.assert_called_once_with('backup1')
    
    def test_system_backup_delete_success(self, authenticated_web_client, mock_use_cases):
        """Test successful backup deletion."""
        mock_use_cases['system'].delete_backup.return_value = True
        
        response = authenticated_web_client.post('/system/backups/backup1/delete', follow_redirects=True)
        
        assert response.status_code == 200
        assert b'deleted' in response.data.lower()
        mock_use_cases['system'].delete_backup.assert_called_once_with('backup1')
    
    def test_system_backup_not_found(self, authenticated_web_client, mock_use_cases):
        """Test backup operations with non-existent backup."""
        mock_use_cases['system'].restore_backup.return_value = False
        
        response = authenticated_web_client.post('/system/backups/nonexistent/restore', follow_redirects=True)
        
        assert response.status_code == 200
        assert b'not found' in response.data.lower() or b'failed' in response.data.lower()


class TestSystemUpdateRoute:
    """Test system update route functionality."""
    
    def test_system_update_check_returns_200(self, authenticated_web_client, mock_use_cases):
        """Test that system update check route returns 200 status."""
        update_info = test_data_factory.create_update_info(available=True)
        mock_use_cases['system'].check_updates.return_value = update_info
        
        response = authenticated_web_client.get('/system/update/check')
        
        assert response.status_code == 200
        assert b'3.6.1' in response.data
        assert b'available' in response.data.lower()
        mock_use_cases['system'].check_updates.assert_called_once()
    
    def test_system_update_apply_success(self, authenticated_web_client, mock_use_cases):
        """Test successful system update."""
        mock_use_cases['system'].update_system.return_value = True
        
        response = authenticated_web_client.post('/system/update', follow_redirects=True)
        
        assert response.status_code == 200
        assert b'updated' in response.data.lower()
        mock_use_cases['system'].update_system.assert_called_once()
    
    def test_system_update_no_updates_available(self, authenticated_web_client, mock_use_cases):
        """Test system update when no updates are available."""
        update_info = test_data_factory.create_update_info(available=False)
        mock_use_cases['system'].check_updates.return_value = update_info
        
        response = authenticated_web_client.get('/system/update/check')
        
        assert response.status_code == 200
        assert b'up to date' in response.data.lower() or b'no updates' in response.data.lower()
    
    def test_system_update_error(self, authenticated_web_client, mock_use_cases):
        """Test system update with error."""
        mock_use_cases['system'].update_system.side_effect = Exception("Update failed")
        
        response = authenticated_web_client.post('/system/update', follow_redirects=True)
        
        assert response.status_code == 200
        assert b'error' in response.data.lower() or b'failed' in response.data.lower()


class TestSystemLogsRoute:
    """Test system logs route functionality."""
    
    def test_system_logs_returns_200(self, authenticated_web_client, mock_use_cases):
        """Test that system logs route returns 200 status."""
        logs_data = [
            {'timestamp': '2025-01-01T00:00:00Z', 'level': 'INFO', 'message': 'System started'},
            {'timestamp': '2025-01-01T00:01:00Z', 'level': 'INFO', 'message': 'Bot 1 started'}
        ]
        mock_use_cases['system'].get_system_logs.return_value = logs_data
        
        response = authenticated_web_client.get('/system/logs')
        
        assert response.status_code == 200
        assert b'System started' in response.data
        assert b'Bot 1 started' in response.data
        mock_use_cases['system'].get_system_logs.assert_called_once()
    
    def test_system_logs_with_filter(self, authenticated_web_client, mock_use_cases):
        """Test system logs with filter parameters."""
        logs_data = [
            {'timestamp': '2025-01-01T00:00:00Z', 'level': 'ERROR', 'message': 'Error occurred'}
        ]
        mock_use_cases['system'].get_system_logs.return_value = logs_data
        
        response = authenticated_web_client.get('/system/logs?level=ERROR')
        
        assert response.status_code == 200
        assert b'Error occurred' in response.data
        mock_use_cases['system'].get_system_logs.assert_called_once()


class TestSystemCleanupRoute:
    """Test system cleanup route functionality."""
    
    def test_system_cleanup_success(self, authenticated_web_client, mock_use_cases):
        """Test successful system cleanup."""
        cleanup_result = {
            'deleted_files': 10,
            'freed_space': 1024000,
            'cleaned_logs': 5
        }
        mock_use_cases['system'].cleanup_system.return_value = cleanup_result
        
        response = authenticated_web_client.post('/system/cleanup', follow_redirects=True)
        
        assert response.status_code == 200
        assert b'10' in response.data
        assert b'1024000' in response.data
        mock_use_cases['system'].cleanup_system.assert_called_once()


class TestSystemValidateRoute:
    """Test system validation route functionality."""
    
    def test_system_validate_returns_200(self, authenticated_web_client, mock_use_cases):
        """Test that system validation route returns 200 status."""
        validation_result = {
            'valid': True,
            'issues': [],
            'warnings': ['Low disk space']
        }
        mock_use_cases['system'].validate_system.return_value = validation_result
        
        response = authenticated_web_client.get('/system/validate')
        
        assert response.status_code == 200
        assert b'valid' in response.data.lower()
        assert b'Low disk space' in response.data
        mock_use_cases['system'].validate_system.assert_called_once()
    
    def test_system_validate_with_issues(self, authenticated_web_client, mock_use_cases):
        """Test system validation with issues."""
        validation_result = {
            'valid': False,
            'issues': ['Database connection failed', 'Invalid configuration'],
            'warnings': []
        }
        mock_use_cases['system'].validate_system.return_value = validation_result
        
        response = authenticated_web_client.get('/system/validate')
        
        assert response.status_code == 200
        assert b'Database connection failed' in response.data
        assert b'Invalid configuration' in response.data


class TestSystemAJAXRoutes:
    """Test AJAX routes for system operations."""
    
    def test_system_status_ajax(self, authenticated_web_client, mock_use_cases):
        """Test system status AJAX endpoint."""
        status_data = test_data_factory.create_system_status()
        mock_use_cases['system'].get_system_status.return_value = status_data
        
        response = authenticated_web_client.get('/api/system/status')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['data']['status'] == 'running'
    
    def test_system_config_ajax(self, authenticated_web_client, mock_use_cases):
        """Test system config AJAX endpoint."""
        config_data = {'version': '3.6.0', 'debug': True}
        mock_use_cases['system'].get_system_config.return_value = config_data
        
        response = authenticated_web_client.get('/api/system/config')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['data']['version'] == '3.6.0'
    
    def test_system_config_update_ajax(self, authenticated_web_client, mock_use_cases):
        """Test system config update AJAX endpoint."""
        updated_config = {'version': '3.6.0', 'debug': False}
        mock_use_cases['system'].update_system_config.return_value = updated_config
        
        response = authenticated_web_client.put('/api/system/config',
            data=json.dumps({'debug': False}),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['data']['debug'] is False
    
    def test_system_backup_create_ajax(self, authenticated_web_client, mock_use_cases):
        """Test system backup create AJAX endpoint."""
        backup_id = 'backup_20250101_000000'
        mock_use_cases['system'].create_backup.return_value = backup_id
        
        response = authenticated_web_client.post('/api/system/backup')
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['data']['backup_id'] == backup_id
    
    def test_system_backup_list_ajax(self, authenticated_web_client, mock_use_cases):
        """Test system backup list AJAX endpoint."""
        backups = [
            test_data_factory.create_backup_info(id='backup1'),
            test_data_factory.create_backup_info(id='backup2')
        ]
        mock_use_cases['system'].get_backups.return_value = backups
        
        response = authenticated_web_client.get('/api/system/backups')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert len(data['data']) == 2
    
    def test_system_backup_restore_ajax(self, authenticated_web_client, mock_use_cases):
        """Test system backup restore AJAX endpoint."""
        mock_use_cases['system'].restore_backup.return_value = True
        
        response = authenticated_web_client.post('/api/system/backups/backup1/restore')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        mock_use_cases['system'].restore_backup.assert_called_once_with('backup1')
    
    def test_system_backup_delete_ajax(self, authenticated_web_client, mock_use_cases):
        """Test system backup delete AJAX endpoint."""
        mock_use_cases['system'].delete_backup.return_value = True
        
        response = authenticated_web_client.delete('/api/system/backups/backup1')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        mock_use_cases['system'].delete_backup.assert_called_once_with('backup1')
    
    def test_system_update_check_ajax(self, authenticated_web_client, mock_use_cases):
        """Test system update check AJAX endpoint."""
        update_info = test_data_factory.create_update_info(available=True)
        mock_use_cases['system'].check_updates.return_value = update_info
        
        response = authenticated_web_client.get('/api/system/update/check')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['data']['available'] is True
        assert data['data']['latest_version'] == '3.6.1'
    
    def test_system_update_apply_ajax(self, authenticated_web_client, mock_use_cases):
        """Test system update apply AJAX endpoint."""
        mock_use_cases['system'].update_system.return_value = True
        
        response = authenticated_web_client.post('/api/system/update')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        mock_use_cases['system'].update_system.assert_called_once()
    
    def test_system_logs_ajax(self, authenticated_web_client, mock_use_cases):
        """Test system logs AJAX endpoint."""
        logs_data = [
            {'timestamp': '2025-01-01T00:00:00Z', 'level': 'INFO', 'message': 'System started'}
        ]
        mock_use_cases['system'].get_system_logs.return_value = logs_data
        
        response = authenticated_web_client.get('/api/system/logs')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert len(data['data']) == 1
        assert data['data'][0]['message'] == 'System started'
    
    def test_system_cleanup_ajax(self, authenticated_web_client, mock_use_cases):
        """Test system cleanup AJAX endpoint."""
        cleanup_result = {
            'deleted_files': 10,
            'freed_space': 1024000,
            'cleaned_logs': 5
        }
        mock_use_cases['system'].cleanup_system.return_value = cleanup_result
        
        response = authenticated_web_client.post('/api/system/cleanup')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['data']['deleted_files'] == 10
        assert data['data']['freed_space'] == 1024000
    
    def test_system_validate_ajax(self, authenticated_web_client, mock_use_cases):
        """Test system validation AJAX endpoint."""
        validation_result = {
            'valid': True,
            'issues': [],
            'warnings': ['Low disk space']
        }
        mock_use_cases['system'].validate_system.return_value = validation_result
        
        response = authenticated_web_client.get('/api/system/validate')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['data']['valid'] is True
        assert len(data['data']['warnings']) == 1


class TestSystemRoutesErrorHandling:
    """Test error handling in system routes."""
    
    def test_system_status_error_ajax(self, authenticated_web_client, mock_use_cases):
        """Test AJAX endpoint with system status error."""
        mock_use_cases['system'].get_system_status.side_effect = Exception("Status error")
        
        response = authenticated_web_client.get('/api/system/status')
        
        assert response.status_code == 500
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'error' in data['error']['message'].lower()
    
    def test_system_backup_error_ajax(self, authenticated_web_client, mock_use_cases):
        """Test AJAX endpoint with backup error."""
        mock_use_cases['system'].create_backup.side_effect = Exception("Backup failed")
        
        response = authenticated_web_client.post('/api/system/backup')
        
        assert response.status_code == 500
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'error' in data['error']['message'].lower()
    
    def test_system_update_error_ajax(self, authenticated_web_client, mock_use_cases):
        """Test AJAX endpoint with update error."""
        mock_use_cases['system'].update_system.side_effect = Exception("Update failed")
        
        response = authenticated_web_client.post('/api/system/update')
        
        assert response.status_code == 500
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'error' in data['error']['message'].lower()
    
    def test_system_backup_not_found_ajax(self, authenticated_web_client, mock_use_cases):
        """Test AJAX endpoint with non-existent backup."""
        mock_use_cases['system'].restore_backup.return_value = False
        
        response = authenticated_web_client.post('/api/system/backups/nonexistent/restore')
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'not found' in data['error']['message'].lower()


class TestSystemRoutesPagination:
    """Test pagination in system routes."""
    
    def test_system_backup_list_pagination(self, authenticated_web_client, mock_use_cases):
        """Test system backup list with pagination."""
        backups = [test_data_factory.create_backup_info(id=f'backup{i}') for i in range(1, 26)]
        pagination_data = test_data_factory.create_pagination_info(
            page=1, per_page=10, total=25, pages=3
        )
        
        mock_use_cases['system'].get_backups.return_value = {
            'backups': backups[:10],
            'pagination': pagination_data
        }
        
        response = authenticated_web_client.get('/system/backups?page=1&per_page=10')
        
        assert response.status_code == 200
        assert b'page 1' in response.data.lower() or b'1 of 3' in response.data
    
    def test_system_logs_pagination(self, authenticated_web_client, mock_use_cases):
        """Test system logs with pagination."""
        logs_data = [{'timestamp': f'2025-01-01T{i:02d}:00:00Z', 'level': 'INFO', 'message': f'Log {i}'} for i in range(1, 26)]
        pagination_data = test_data_factory.create_pagination_info(
            page=1, per_page=10, total=25, pages=3
        )
        
        mock_use_cases['system'].get_system_logs.return_value = {
            'logs': logs_data[:10],
            'pagination': pagination_data
        }
        
        response = authenticated_web_client.get('/system/logs?page=1&per_page=10')
        
        assert response.status_code == 200
        assert b'page 1' in response.data.lower() or b'1 of 3' in response.data







