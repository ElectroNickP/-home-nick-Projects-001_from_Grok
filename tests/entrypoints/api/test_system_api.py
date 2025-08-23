"""
Unit tests for system API endpoints (API Entry Point).

Tests cover all system-related API endpoints including
status, config, backup, restore, update, logs, cleanup, validate.
"""

import pytest
import json
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from tests.entrypoints.factories import test_data_factory


class TestSystemStatusAPI:
    """Test system status API endpoint functionality."""
    
    def test_get_system_status_success(self, api_client, mock_use_cases):
        """Test successful GET /api/system/status endpoint."""
        status_data = test_data_factory.create_system_status()
        mock_use_cases['system'].get_system_status.return_value = status_data
        
        response = api_client.get('/api/system/status')
        
        assert response.status_code == 200
        data = response.json()
        assert 'status' in data
        assert 'uptime' in data
        assert 'version' in data
        assert 'bots' in data
        assert 'conversations' in data
        mock_use_cases['system'].get_system_status.assert_called_once()
    
    def test_get_system_status_detailed(self, api_client, mock_use_cases):
        """Test GET /api/system/status endpoint with detailed parameter."""
        status_data = test_data_factory.create_system_status()
        mock_use_cases['system'].get_system_status.return_value = status_data
        
        response = api_client.get('/api/system/status?detailed=true')
        
        assert response.status_code == 200
        data = response.json()
        assert 'status' in data
        assert 'memory' in data
        assert 'cpu' in data
        assert 'disk' in data
        assert 'network' in data
        mock_use_cases['system'].get_system_status.assert_called_once_with(detailed=True)
    
    def test_get_system_status_server_error(self, api_client, mock_use_cases):
        """Test GET /api/system/status endpoint with server error."""
        mock_use_cases['system'].get_system_status.side_effect = Exception("Server error")
        
        response = api_client.get('/api/system/status')
        
        assert response.status_code == 500
        data = response.json()
        assert 'error' in data
        assert 'Server error' in data['error']['message']


class TestSystemConfigAPI:
    """Test system config API endpoint functionality."""
    
    def test_get_system_config_success(self, api_client, mock_use_cases):
        """Test successful GET /api/system/config endpoint."""
        config_data = {
            'database': {'url': 'sqlite:///bot_manager.db'},
            'telegram': {'api_timeout': 30},
            'logging': {'level': 'INFO'},
            'security': {'session_timeout': 3600}
        }
        mock_use_cases['system'].get_system_config.return_value = config_data
        
        response = api_client.get('/api/system/config')
        
        assert response.status_code == 200
        data = response.json()
        assert 'database' in data
        assert 'telegram' in data
        assert 'logging' in data
        assert 'security' in data
        assert data['database']['url'] == 'sqlite:///bot_manager.db'
        assert data['telegram']['api_timeout'] == 30
        mock_use_cases['system'].get_system_config.assert_called_once()
    
    def test_update_system_config_success(self, api_client, mock_use_cases):
        """Test successful PUT /api/system/config endpoint."""
        updated_config = {'logging': {'level': 'DEBUG'}}
        mock_use_cases['system'].update_system_config.return_value = updated_config
        
        config_data = {'logging': {'level': 'DEBUG'}}
        
        response = api_client.put('/api/system/config', json=config_data)
        
        assert response.status_code == 200
        data = response.json()
        assert 'logging' in data
        assert data['logging']['level'] == 'DEBUG'
        mock_use_cases['system'].update_system_config.assert_called_once()
    
    def test_update_system_config_validation_error(self, api_client, mock_use_cases):
        """Test PUT /api/system/config endpoint with validation error."""
        mock_use_cases['system'].update_system_config.side_effect = ValueError('Invalid log level')
        
        config_data = {'logging': {'level': 'INVALID'}}
        
        response = api_client.put('/api/system/config', json=config_data)
        
        assert response.status_code == 400
        data = response.json()
        assert 'error' in data
        assert 'Invalid log level' in data['error']['message']
    
    def test_reset_system_config_success(self, api_client, mock_use_cases):
        """Test successful POST /api/system/config/reset endpoint."""
        default_config = {'database': {'url': 'sqlite:///bot_manager.db'}}
        mock_use_cases['system'].reset_system_config.return_value = default_config
        
        response = api_client.post('/api/system/config/reset')
        
        assert response.status_code == 200
        data = response.json()
        assert 'database' in data
        assert data['database']['url'] == 'sqlite:///bot_manager.db'
        mock_use_cases['system'].reset_system_config.assert_called_once()
    
    def test_get_system_config_server_error(self, api_client, mock_use_cases):
        """Test GET /api/system/config endpoint with server error."""
        mock_use_cases['system'].get_system_config.side_effect = Exception("Server error")
        
        response = api_client.get('/api/system/config')
        
        assert response.status_code == 500
        data = response.json()
        assert 'error' in data
        assert 'Server error' in data['error']['message']


class TestSystemBackupAPI:
    """Test system backup API endpoint functionality."""
    
    def test_create_backup_success(self, api_client, mock_use_cases):
        """Test successful POST /api/system/backup endpoint."""
        backup_info = test_data_factory.create_backup_info()
        mock_use_cases['system'].create_backup.return_value = backup_info
        
        backup_data = {'description': 'Test backup'}
        
        response = api_client.post('/api/system/backup', json=backup_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data['id'] == backup_info['id']
        assert data['filename'] == backup_info['filename']
        assert data['size'] == backup_info['size']
        mock_use_cases['system'].create_backup.assert_called_once_with(description='Test backup')
    
    def test_create_backup_server_error(self, api_client, mock_use_cases):
        """Test POST /api/system/backup endpoint with server error."""
        mock_use_cases['system'].create_backup.side_effect = Exception("Backup failed")
        
        backup_data = {'description': 'Test backup'}
        
        response = api_client.post('/api/system/backup', json=backup_data)
        
        assert response.status_code == 500
        data = response.json()
        assert 'error' in data
        assert 'Backup failed' in data['error']['message']
    
    def test_list_backups_success(self, api_client, mock_use_cases):
        """Test successful GET /api/system/backup endpoint."""
        backups = [
            test_data_factory.create_backup_info(id=1, filename='backup_2024_01_15.sql'),
            test_data_factory.create_backup_info(id=2, filename='backup_2024_01_14.sql')
        ]
        mock_use_cases['system'].list_backups.return_value = backups
        
        response = api_client.get('/api/system/backup')
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]['id'] == 1
        assert data[0]['filename'] == 'backup_2024_01_15.sql'
        assert data[1]['id'] == 2
        assert data[1]['filename'] == 'backup_2024_01_14.sql'
        mock_use_cases['system'].list_backups.assert_called_once()
    
    def test_list_backups_empty(self, api_client, mock_use_cases):
        """Test GET /api/system/backup endpoint with no backups."""
        mock_use_cases['system'].list_backups.return_value = []
        
        response = api_client.get('/api/system/backup')
        
        assert response.status_code == 200
        data = response.json()
        assert data == []
        mock_use_cases['system'].list_backups.assert_called_once()
    
    def test_get_backup_success(self, api_client, mock_use_cases):
        """Test successful GET /api/system/backup/{backup_id} endpoint."""
        backup_info = test_data_factory.create_backup_info()
        mock_use_cases['system'].get_backup.return_value = backup_info
        
        response = api_client.get('/api/system/backup/1')
        
        assert response.status_code == 200
        data = response.json()
        assert data['id'] == backup_info['id']
        assert data['filename'] == backup_info['filename']
        assert data['size'] == backup_info['size']
        mock_use_cases['system'].get_backup.assert_called_once_with(1)
    
    def test_get_backup_not_found(self, api_client, mock_use_cases):
        """Test GET /api/system/backup/{backup_id} endpoint with non-existent backup."""
        mock_use_cases['system'].get_backup.return_value = None
        
        response = api_client.get('/api/system/backup/999')
        
        assert response.status_code == 404
        data = response.json()
        assert 'error' in data
        assert 'Backup not found' in data['error']['message']
    
    def test_delete_backup_success(self, api_client, mock_use_cases):
        """Test successful DELETE /api/system/backup/{backup_id} endpoint."""
        mock_use_cases['system'].delete_backup.return_value = True
        
        response = api_client.delete('/api/system/backup/1')
        
        assert response.status_code == 204  # No content
        mock_use_cases['system'].delete_backup.assert_called_once_with(1)
    
    def test_delete_backup_not_found(self, api_client, mock_use_cases):
        """Test DELETE /api/system/backup/{backup_id} endpoint with non-existent backup."""
        mock_use_cases['system'].delete_backup.return_value = False
        
        response = api_client.delete('/api/system/backup/999')
        
        assert response.status_code == 404
        data = response.json()
        assert 'error' in data
        assert 'Backup not found' in data['error']['message']


class TestSystemRestoreAPI:
    """Test system restore API endpoint functionality."""
    
    def test_restore_backup_success(self, api_client, mock_use_cases):
        """Test successful POST /api/system/backup/{backup_id}/restore endpoint."""
        mock_use_cases['system'].restore_backup.return_value = {
            'success': True,
            'message': 'System restored successfully'
        }
        
        response = api_client.post('/api/system/backup/1/restore')
        
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert data['message'] == 'System restored successfully'
        mock_use_cases['system'].restore_backup.assert_called_once_with(1)
    
    def test_restore_backup_not_found(self, api_client, mock_use_cases):
        """Test POST /api/system/backup/{backup_id}/restore endpoint with non-existent backup."""
        mock_use_cases['system'].restore_backup.return_value = {
            'success': False,
            'error': 'Backup not found'
        }
        
        response = api_client.post('/api/system/backup/999/restore')
        
        assert response.status_code == 404
        data = response.json()
        assert 'error' in data
        assert 'Backup not found' in data['error']['message']
    
    def test_restore_backup_corrupted(self, api_client, mock_use_cases):
        """Test POST /api/system/backup/{backup_id}/restore endpoint with corrupted backup."""
        mock_use_cases['system'].restore_backup.return_value = {
            'success': False,
            'error': 'Backup file is corrupted'
        }
        
        response = api_client.post('/api/system/backup/1/restore')
        
        assert response.status_code == 400
        data = response.json()
        assert 'error' in data
        assert 'Backup file is corrupted' in data['error']['message']


class TestSystemUpdateAPI:
    """Test system update API endpoint functionality."""
    
    def test_check_for_updates_success(self, api_client, mock_use_cases):
        """Test successful GET /api/system/update/check endpoint."""
        update_info = test_data_factory.create_update_info()
        mock_use_cases['system'].check_for_updates.return_value = update_info
        
        response = api_client.get('/api/system/update/check')
        
        assert response.status_code == 200
        data = response.json()
        assert data['current_version'] == update_info['current_version']
        assert data['latest_version'] == update_info['latest_version']
        assert data['update_available'] == update_info['update_available']
        mock_use_cases['system'].check_for_updates.assert_called_once()
    
    def test_check_for_updates_no_updates(self, api_client, mock_use_cases):
        """Test GET /api/system/update/check endpoint with no updates available."""
        update_info = {
            'current_version': '1.0.0',
            'latest_version': '1.0.0',
            'update_available': False,
            'message': 'System is up to date'
        }
        mock_use_cases['system'].check_for_updates.return_value = update_info
        
        response = api_client.get('/api/system/update/check')
        
        assert response.status_code == 200
        data = response.json()
        assert data['update_available'] is False
        assert data['message'] == 'System is up to date'
    
    def test_apply_update_success(self, api_client, mock_use_cases):
        """Test successful POST /api/system/update/apply endpoint."""
        mock_use_cases['system'].apply_update.return_value = {
            'success': True,
            'message': 'System updated successfully',
            'new_version': '1.1.0'
        }
        
        response = api_client.post('/api/system/update/apply')
        
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert data['message'] == 'System updated successfully'
        assert data['new_version'] == '1.1.0'
        mock_use_cases['system'].apply_update.assert_called_once()
    
    def test_apply_update_no_updates(self, api_client, mock_use_cases):
        """Test POST /api/system/update/apply endpoint with no updates available."""
        mock_use_cases['system'].apply_update.return_value = {
            'success': False,
            'error': 'No updates available'
        }
        
        response = api_client.post('/api/system/update/apply')
        
        assert response.status_code == 400
        data = response.json()
        assert 'error' in data
        assert 'No updates available' in data['error']['message']
    
    def test_apply_update_failed(self, api_client, mock_use_cases):
        """Test POST /api/system/update/apply endpoint with update failure."""
        mock_use_cases['system'].apply_update.return_value = {
            'success': False,
            'error': 'Update failed: Network error'
        }
        
        response = api_client.post('/api/system/update/apply')
        
        assert response.status_code == 500
        data = response.json()
        assert 'error' in data
        assert 'Update failed: Network error' in data['error']['message']


class TestSystemLogsAPI:
    """Test system logs API endpoint functionality."""
    
    def test_get_system_logs_success(self, api_client, mock_use_cases):
        """Test successful GET /api/system/logs endpoint."""
        logs = [
            {'timestamp': '2024-01-15 10:30:00', 'level': 'INFO', 'message': 'System started'},
            {'timestamp': '2024-01-15 10:31:00', 'level': 'ERROR', 'message': 'Connection failed'}
        ]
        mock_use_cases['system'].get_system_logs.return_value = logs
        
        response = api_client.get('/api/system/logs')
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]['timestamp'] == '2024-01-15 10:30:00'
        assert data[0]['level'] == 'INFO'
        assert data[0]['message'] == 'System started'
        assert data[1]['timestamp'] == '2024-01-15 10:31:00'
        assert data[1]['level'] == 'ERROR'
        assert data[1]['message'] == 'Connection failed'
        mock_use_cases['system'].get_system_logs.assert_called_once()
    
    def test_get_system_logs_with_filters(self, api_client, mock_use_cases):
        """Test GET /api/system/logs endpoint with query parameters."""
        logs = [{'timestamp': '2024-01-15 10:30:00', 'level': 'ERROR', 'message': 'Connection failed'}]
        mock_use_cases['system'].get_system_logs.return_value = logs
        
        response = api_client.get('/api/system/logs?level=ERROR&limit=10&tail=50')
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]['level'] == 'ERROR'
        mock_use_cases['system'].get_system_logs.assert_called_once_with(level='ERROR', limit=10, tail=50)
    
    def test_get_system_logs_empty(self, api_client, mock_use_cases):
        """Test GET /api/system/logs endpoint with no logs."""
        mock_use_cases['system'].get_system_logs.return_value = []
        
        response = api_client.get('/api/system/logs')
        
        assert response.status_code == 200
        data = response.json()
        assert data == []
        mock_use_cases['system'].get_system_logs.assert_called_once()
    
    def test_get_system_logs_server_error(self, api_client, mock_use_cases):
        """Test GET /api/system/logs endpoint with server error."""
        mock_use_cases['system'].get_system_logs.side_effect = Exception("Server error")
        
        response = api_client.get('/api/system/logs')
        
        assert response.status_code == 500
        data = response.json()
        assert 'error' in data
        assert 'Server error' in data['error']['message']


class TestSystemCleanupAPI:
    """Test system cleanup API endpoint functionality."""
    
    def test_cleanup_system_success(self, api_client, mock_use_cases):
        """Test successful POST /api/system/cleanup endpoint."""
        cleanup_result = {
            'success': True,
            'message': 'Cleanup completed successfully',
            'files_removed': 5,
            'space_freed': '2.5 MB'
        }
        mock_use_cases['system'].cleanup_system.return_value = cleanup_result
        
        response = api_client.post('/api/system/cleanup')
        
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert data['message'] == 'Cleanup completed successfully'
        assert data['files_removed'] == 5
        assert data['space_freed'] == '2.5 MB'
        mock_use_cases['system'].cleanup_system.assert_called_once()
    
    def test_cleanup_system_dry_run(self, api_client, mock_use_cases):
        """Test POST /api/system/cleanup endpoint with dry run."""
        cleanup_result = {
            'success': True,
            'message': 'Dry run completed',
            'files_to_remove': 5,
            'space_to_free': '2.5 MB'
        }
        mock_use_cases['system'].cleanup_system.return_value = cleanup_result
        
        response = api_client.post('/api/system/cleanup?dry_run=true')
        
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert data['message'] == 'Dry run completed'
        assert data['files_to_remove'] == 5
        assert data['space_to_free'] == '2.5 MB'
        mock_use_cases['system'].cleanup_system.assert_called_once_with(dry_run=True)
    
    def test_cleanup_system_failed(self, api_client, mock_use_cases):
        """Test POST /api/system/cleanup endpoint with failure."""
        mock_use_cases['system'].cleanup_system.return_value = {
            'success': False,
            'error': 'Cleanup failed: Permission denied'
        }
        
        response = api_client.post('/api/system/cleanup')
        
        assert response.status_code == 500
        data = response.json()
        assert 'error' in data
        assert 'Cleanup failed: Permission denied' in data['error']['message']


class TestSystemValidateAPI:
    """Test system validate API endpoint functionality."""
    
    def test_validate_system_success(self, api_client, mock_use_cases):
        """Test successful POST /api/system/validate endpoint."""
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
        
        response = api_client.post('/api/system/validate')
        
        assert response.status_code == 200
        data = response.json()
        assert data['valid'] is True
        assert data['message'] == 'System validation passed'
        assert len(data['checks']) == 3
        assert data['checks'][0]['name'] == 'Database Connection'
        assert data['checks'][0]['status'] == 'OK'
        mock_use_cases['system'].validate_system.assert_called_once()
    
    def test_validate_system_with_issues(self, api_client, mock_use_cases):
        """Test POST /api/system/validate endpoint with validation issues."""
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
        
        response = api_client.post('/api/system/validate')
        
        assert response.status_code == 400
        data = response.json()
        assert data['valid'] is False
        assert data['message'] == 'System validation failed'
        assert len(data['checks']) == 3
        assert data['checks'][1]['status'] == 'ERROR'
        assert data['checks'][2]['status'] == 'WARNING'
        mock_use_cases['system'].validate_system.assert_called_once()
    
    def test_validate_system_server_error(self, api_client, mock_use_cases):
        """Test POST /api/system/validate endpoint with server error."""
        mock_use_cases['system'].validate_system.side_effect = Exception("Validation service unavailable")
        
        response = api_client.post('/api/system/validate')
        
        assert response.status_code == 500
        data = response.json()
        assert 'error' in data
        assert 'Validation service unavailable' in data['error']['message']


class TestSystemHealthAPI:
    """Test system health API endpoint functionality."""
    
    def test_health_check_success(self, api_client):
        """Test successful GET /api/system/health endpoint."""
        response = api_client.get('/api/system/health')
        
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'healthy'
        assert 'timestamp' in data
    
    def test_health_check_detailed(self, api_client, mock_use_cases):
        """Test GET /api/system/health endpoint with detailed parameter."""
        status_data = test_data_factory.create_system_status()
        mock_use_cases['system'].get_system_status.return_value = status_data
        
        response = api_client.get('/api/system/health?detailed=true')
        
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'healthy'
        assert 'timestamp' in data
        assert 'system_status' in data
        mock_use_cases['system'].get_system_status.assert_called_once()


class TestSystemAPIErrorHandling:
    """Test system API error handling."""
    
    def test_api_server_error(self, api_client, mock_use_cases):
        """Test API endpoint with server error."""
        mock_use_cases['system'].get_system_status.side_effect = Exception("Server error")
        
        response = api_client.get('/api/system/status')
        
        assert response.status_code == 500
        data = response.json()
        assert 'error' in data
        assert 'Server error' in data['error']['message']
    
    def test_api_network_error(self, api_client, mock_use_cases):
        """Test API endpoint with network error."""
        mock_use_cases['system'].get_system_status.side_effect = ConnectionError("Network error")
        
        response = api_client.get('/api/system/status')
        
        assert response.status_code == 500
        data = response.json()
        assert 'error' in data
        assert 'Network error' in data['error']['message']
    
    def test_api_timeout_error(self, api_client, mock_use_cases):
        """Test API endpoint with timeout error."""
        mock_use_cases['system'].get_system_status.side_effect = TimeoutError("Request timeout")
        
        response = api_client.get('/api/system/status')
        
        assert response.status_code == 500
        data = response.json()
        assert 'error' in data
        assert 'Request timeout' in data['error']['message']
    
    def test_api_validation_error(self, api_client):
        """Test API endpoint with validation error."""
        response = api_client.put('/api/system/config', json={'invalid': 'data'})
        
        assert response.status_code == 422  # Validation error
        data = response.json()
        assert 'detail' in data


class TestSystemAPIPerformance:
    """Test system API performance."""
    
    def test_api_response_time(self, api_client, mock_use_cases):
        """Test API response time."""
        status_data = test_data_factory.create_system_status()
        mock_use_cases['system'].get_system_status.return_value = status_data
        
        import time
        start_time = time.time()
        response = api_client.get('/api/system/status')
        end_time = time.time()
        
        assert response.status_code == 200
        assert (end_time - start_time) < 1.0  # Response time should be under 1 second
    
    def test_api_concurrent_requests(self, api_client, mock_use_cases):
        """Test API with concurrent requests."""
        status_data = test_data_factory.create_system_status()
        mock_use_cases['system'].get_system_status.return_value = status_data
        
        import threading
        import time
        
        results = []
        errors = []
        
        def make_request():
            try:
                response = api_client.get('/api/system/status')
                results.append(response.status_code)
            except Exception as e:
                errors.append(str(e))
        
        # Start multiple threads
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check results
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == 5
        assert all(status == 200 for status in results)


class TestSystemAPIDocumentation:
    """Test system API documentation."""
    
    def test_api_docs_accessible(self, api_client):
        """Test that API documentation is accessible."""
        response = api_client.get('/docs')
        
        assert response.status_code == 200
        assert 'text/html' in response.headers['content-type']
        assert 'Swagger UI' in response.text
    
    def test_api_openapi_schema(self, api_client):
        """Test that OpenAPI schema is accessible."""
        response = api_client.get('/openapi.json')
        
        assert response.status_code == 200
        data = response.json()
        assert 'openapi' in data
        assert 'paths' in data
        assert '/api/system' in str(data['paths'])
    
    def test_api_redoc_accessible(self, api_client):
        """Test that ReDoc documentation is accessible."""
        response = api_client.get('/redoc')
        
        assert response.status_code == 200
        assert 'text/html' in response.headers['content-type']
        assert 'ReDoc' in response.text






