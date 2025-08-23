"""
Unit tests for authentication API endpoints (API Entry Point).

Tests cover all authentication-related API endpoints including
login, logout, register, password reset, and token management.
"""

import pytest
import json
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from tests.entrypoints.factories import test_data_factory


class TestAuthLoginAPI:
    """Test authentication login API endpoint functionality."""
    
    def test_login_success(self, api_client, mock_use_cases):
        """Test successful POST /api/auth/login endpoint."""
        user_data = {
            'id': 1,
            'username': 'admin',
            'role': 'admin',
            'permissions': ['read', 'write', 'admin']
        }
        mock_use_cases['system'].authenticate_user.return_value = {
            'success': True,
            'user': user_data,
            'token': 'valid_jwt_token_123'
        }
        
        login_data = {
            'username': 'admin',
            'password': 'securepassword123'
        }
        
        response = api_client.post('/api/auth/login', json=login_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert data['user']['username'] == 'admin'
        assert data['user']['role'] == 'admin'
        assert 'token' in data
        assert data['token'] == 'valid_jwt_token_123'
        mock_use_cases['system'].authenticate_user.assert_called_once()
    
    def test_login_invalid_credentials(self, api_client, mock_use_cases):
        """Test POST /api/auth/login endpoint with invalid credentials."""
        mock_use_cases['system'].authenticate_user.return_value = {
            'success': False,
            'error': 'Invalid username or password'
        }
        
        login_data = {
            'username': 'admin',
            'password': 'wrongpassword'
        }
        
        response = api_client.post('/api/auth/login', json=login_data)
        
        assert response.status_code == 401
        data = response.json()
        assert data['success'] is False
        assert 'error' in data
        assert 'Invalid username or password' in data['error']['message']
    
    def test_login_missing_fields(self, api_client):
        """Test POST /api/auth/login endpoint with missing fields."""
        login_data = {'username': 'admin'}  # Missing password
        
        response = api_client.post('/api/auth/login', json=login_data)
        
        assert response.status_code == 422  # Validation error
        data = response.json()
        assert 'detail' in data
    
    def test_login_empty_fields(self, api_client):
        """Test POST /api/auth/login endpoint with empty fields."""
        login_data = {
            'username': '',
            'password': ''
        }
        
        response = api_client.post('/api/auth/login', json=login_data)
        
        assert response.status_code == 422  # Validation error
        data = response.json()
        assert 'detail' in data
    
    def test_login_server_error(self, api_client, mock_use_cases):
        """Test POST /api/auth/login endpoint with server error."""
        mock_use_cases['system'].authenticate_user.side_effect = Exception("Database connection failed")
        
        login_data = {
            'username': 'admin',
            'password': 'password123'
        }
        
        response = api_client.post('/api/auth/login', json=login_data)
        
        assert response.status_code == 500
        data = response.json()
        assert 'error' in data
        assert 'Database connection failed' in data['error']['message']


class TestAuthLogoutAPI:
    """Test authentication logout API endpoint functionality."""
    
    def test_logout_success(self, authenticated_api_client, mock_use_cases):
        """Test successful POST /api/auth/logout endpoint."""
        mock_use_cases['system'].logout_user.return_value = {
            'success': True,
            'message': 'Logged out successfully'
        }
        
        response = authenticated_api_client.post('/api/auth/logout')
        
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert data['message'] == 'Logged out successfully'
        mock_use_cases['system'].logout_user.assert_called_once()
    
    def test_logout_without_authentication(self, api_client):
        """Test POST /api/auth/logout endpoint without authentication."""
        response = api_client.post('/api/auth/logout')
        
        assert response.status_code == 401
        data = response.json()
        assert 'error' in data
        assert 'Unauthorized' in data['error']['message']
    
    def test_logout_server_error(self, authenticated_api_client, mock_use_cases):
        """Test POST /api/auth/logout endpoint with server error."""
        mock_use_cases['system'].logout_user.side_effect = Exception("Server error")
        
        response = authenticated_api_client.post('/api/auth/logout')
        
        assert response.status_code == 500
        data = response.json()
        assert 'error' in data
        assert 'Server error' in data['error']['message']


class TestAuthRegisterAPI:
    """Test authentication register API endpoint functionality."""
    
    def test_register_success(self, api_client, mock_use_cases):
        """Test successful POST /api/auth/register endpoint."""
        user_data = {
            'id': 2,
            'username': 'newuser',
            'role': 'user'
        }
        mock_use_cases['system'].register_user.return_value = {
            'success': True,
            'user': user_data,
            'message': 'User registered successfully'
        }
        
        register_data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'securepassword123',
            'confirm_password': 'securepassword123'
        }
        
        response = api_client.post('/api/auth/register', json=register_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data['success'] is True
        assert data['user']['username'] == 'newuser'
        assert data['user']['role'] == 'user'
        assert data['message'] == 'User registered successfully'
        mock_use_cases['system'].register_user.assert_called_once()
    
    def test_register_existing_username(self, api_client, mock_use_cases):
        """Test POST /api/auth/register endpoint with existing username."""
        mock_use_cases['system'].register_user.return_value = {
            'success': False,
            'error': 'Username already exists'
        }
        
        register_data = {
            'username': 'existinguser',
            'email': 'existinguser@example.com',
            'password': 'securepassword123',
            'confirm_password': 'securepassword123'
        }
        
        response = api_client.post('/api/auth/register', json=register_data)
        
        assert response.status_code == 409  # Conflict
        data = response.json()
        assert data['success'] is False
        assert 'error' in data
        assert 'Username already exists' in data['error']['message']
    
    def test_register_password_mismatch(self, api_client):
        """Test POST /api/auth/register endpoint with password mismatch."""
        register_data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'securepassword123',
            'confirm_password': 'differentpassword'
        }
        
        response = api_client.post('/api/auth/register', json=register_data)
        
        assert response.status_code == 422  # Validation error
        data = response.json()
        assert 'detail' in data
    
    def test_register_weak_password(self, api_client, mock_use_cases):
        """Test POST /api/auth/register endpoint with weak password."""
        mock_use_cases['system'].register_user.return_value = {
            'success': False,
            'error': 'Password is too weak'
        }
        
        register_data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': '123',
            'confirm_password': '123'
        }
        
        response = api_client.post('/api/auth/register', json=register_data)
        
        assert response.status_code == 400
        data = response.json()
        assert data['success'] is False
        assert 'error' in data
        assert 'Password is too weak' in data['error']['message']
    
    def test_register_missing_fields(self, api_client):
        """Test POST /api/auth/register endpoint with missing fields."""
        register_data = {
            'username': 'newuser',
            'email': 'newuser@example.com'
            # Missing password and confirm_password
        }
        
        response = api_client.post('/api/auth/register', json=register_data)
        
        assert response.status_code == 422  # Validation error
        data = response.json()
        assert 'detail' in data
    
    def test_register_invalid_email(self, api_client):
        """Test POST /api/auth/register endpoint with invalid email."""
        register_data = {
            'username': 'newuser',
            'email': 'invalid-email',
            'password': 'securepassword123',
            'confirm_password': 'securepassword123'
        }
        
        response = api_client.post('/api/auth/register', json=register_data)
        
        assert response.status_code == 422  # Validation error
        data = response.json()
        assert 'detail' in data


class TestAuthPasswordResetAPI:
    """Test authentication password reset API endpoint functionality."""
    
    def test_request_password_reset_success(self, api_client, mock_use_cases):
        """Test successful POST /api/auth/password/reset endpoint."""
        mock_use_cases['system'].request_password_reset.return_value = {
            'success': True,
            'message': 'Password reset email sent'
        }
        
        reset_data = {'email': 'user@example.com'}
        
        response = api_client.post('/api/auth/password/reset', json=reset_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert data['message'] == 'Password reset email sent'
        mock_use_cases['system'].request_password_reset.assert_called_once_with('user@example.com')
    
    def test_request_password_reset_email_not_found(self, api_client, mock_use_cases):
        """Test POST /api/auth/password/reset endpoint with non-existent email."""
        mock_use_cases['system'].request_password_reset.return_value = {
            'success': False,
            'error': 'Email not found'
        }
        
        reset_data = {'email': 'nonexistent@example.com'}
        
        response = api_client.post('/api/auth/password/reset', json=reset_data)
        
        assert response.status_code == 404
        data = response.json()
        assert data['success'] is False
        assert 'error' in data
        assert 'Email not found' in data['error']['message']
    
    def test_request_password_reset_invalid_email(self, api_client):
        """Test POST /api/auth/password/reset endpoint with invalid email."""
        reset_data = {'email': 'invalid-email'}
        
        response = api_client.post('/api/auth/password/reset', json=reset_data)
        
        assert response.status_code == 422  # Validation error
        data = response.json()
        assert 'detail' in data
    
    def test_confirm_password_reset_success(self, api_client, mock_use_cases):
        """Test successful POST /api/auth/password/reset/confirm endpoint."""
        mock_use_cases['system'].reset_password.return_value = {
            'success': True,
            'message': 'Password reset successfully'
        }
        
        reset_data = {
            'token': 'valid_token_123',
            'new_password': 'newpassword123',
            'confirm_password': 'newpassword123'
        }
        
        response = api_client.post('/api/auth/password/reset/confirm', json=reset_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert data['message'] == 'Password reset successfully'
        mock_use_cases['system'].reset_password.assert_called_once()
    
    def test_confirm_password_reset_invalid_token(self, api_client, mock_use_cases):
        """Test POST /api/auth/password/reset/confirm endpoint with invalid token."""
        mock_use_cases['system'].reset_password.return_value = {
            'success': False,
            'error': 'Invalid or expired token'
        }
        
        reset_data = {
            'token': 'invalid_token',
            'new_password': 'newpassword123',
            'confirm_password': 'newpassword123'
        }
        
        response = api_client.post('/api/auth/password/reset/confirm', json=reset_data)
        
        assert response.status_code == 400
        data = response.json()
        assert data['success'] is False
        assert 'error' in data
        assert 'Invalid or expired token' in data['error']['message']
    
    def test_confirm_password_reset_password_mismatch(self, api_client):
        """Test POST /api/auth/password/reset/confirm endpoint with password mismatch."""
        reset_data = {
            'token': 'valid_token_123',
            'new_password': 'newpassword123',
            'confirm_password': 'differentpassword'
        }
        
        response = api_client.post('/api/auth/password/reset/confirm', json=reset_data)
        
        assert response.status_code == 422  # Validation error
        data = response.json()
        assert 'detail' in data


class TestAuthStatusAPI:
    """Test authentication status API endpoint functionality."""
    
    def test_auth_status_authenticated(self, authenticated_api_client):
        """Test successful GET /api/auth/status endpoint with authenticated user."""
        response = authenticated_api_client.get('/api/auth/status')
        
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert data['authenticated'] is True
        assert 'user' in data
        assert data['user']['username'] == 'admin'
        assert data['user']['role'] == 'admin'
    
    def test_auth_status_not_authenticated(self, api_client):
        """Test GET /api/auth/status endpoint without authentication."""
        response = api_client.get('/api/auth/status')
        
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert data['authenticated'] is False
        assert 'user' not in data


class TestAuthRefreshAPI:
    """Test authentication token refresh API endpoint functionality."""
    
    def test_refresh_token_success(self, authenticated_api_client, mock_use_cases):
        """Test successful POST /api/auth/refresh endpoint."""
        new_token = 'new_jwt_token_456'
        mock_use_cases['system'].refresh_token.return_value = {
            'success': True,
            'token': new_token
        }
        
        response = authenticated_api_client.post('/api/auth/refresh')
        
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert data['token'] == new_token
        mock_use_cases['system'].refresh_token.assert_called_once()
    
    def test_refresh_token_invalid_token(self, api_client, mock_use_cases):
        """Test POST /api/auth/refresh endpoint with invalid token."""
        mock_use_cases['system'].refresh_token.return_value = {
            'success': False,
            'error': 'Invalid token'
        }
        
        response = api_client.post('/api/auth/refresh')
        
        assert response.status_code == 401
        data = response.json()
        assert data['success'] is False
        assert 'error' in data
        assert 'Invalid token' in data['error']['message']
    
    def test_refresh_token_expired_token(self, api_client, mock_use_cases):
        """Test POST /api/auth/refresh endpoint with expired token."""
        mock_use_cases['system'].refresh_token.return_value = {
            'success': False,
            'error': 'Token expired'
        }
        
        response = api_client.post('/api/auth/refresh')
        
        assert response.status_code == 401
        data = response.json()
        assert data['success'] is False
        assert 'error' in data
        assert 'Token expired' in data['error']['message']


class TestAuthProfileAPI:
    """Test authentication profile API endpoint functionality."""
    
    def test_get_profile_success(self, authenticated_api_client):
        """Test successful GET /api/auth/profile endpoint."""
        response = authenticated_api_client.get('/api/auth/profile')
        
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert 'user' in data
        assert data['user']['username'] == 'admin'
        assert data['user']['role'] == 'admin'
    
    def test_get_profile_not_authenticated(self, api_client):
        """Test GET /api/auth/profile endpoint without authentication."""
        response = api_client.get('/api/auth/profile')
        
        assert response.status_code == 401
        data = response.json()
        assert 'error' in data
        assert 'Unauthorized' in data['error']['message']
    
    def test_update_profile_success(self, authenticated_api_client, mock_use_cases):
        """Test successful PUT /api/auth/profile endpoint."""
        updated_user = {
            'id': 1,
            'username': 'admin',
            'email': 'admin@example.com',
            'role': 'admin'
        }
        mock_use_cases['system'].update_user_profile.return_value = {
            'success': True,
            'user': updated_user
        }
        
        profile_data = {
            'email': 'admin@example.com',
            'display_name': 'Administrator'
        }
        
        response = authenticated_api_client.put('/api/auth/profile', json=profile_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert data['user']['email'] == 'admin@example.com'
        mock_use_cases['system'].update_user_profile.assert_called_once()
    
    def test_update_profile_validation_error(self, authenticated_api_client, mock_use_cases):
        """Test PUT /api/auth/profile endpoint with validation error."""
        mock_use_cases['system'].update_user_profile.side_effect = ValueError('Invalid email format')
        
        profile_data = {
            'email': 'invalid-email',
            'display_name': 'Administrator'
        }
        
        response = authenticated_api_client.put('/api/auth/profile', json=profile_data)
        
        assert response.status_code == 400
        data = response.json()
        assert 'error' in data
        assert 'Invalid email format' in data['error']['message']


class TestAuthChangePasswordAPI:
    """Test authentication change password API endpoint functionality."""
    
    def test_change_password_success(self, authenticated_api_client, mock_use_cases):
        """Test successful POST /api/auth/change-password endpoint."""
        mock_use_cases['system'].change_password.return_value = {
            'success': True,
            'message': 'Password changed successfully'
        }
        
        password_data = {
            'current_password': 'oldpassword123',
            'new_password': 'newpassword123',
            'confirm_password': 'newpassword123'
        }
        
        response = authenticated_api_client.post('/api/auth/change-password', json=password_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert data['message'] == 'Password changed successfully'
        mock_use_cases['system'].change_password.assert_called_once()
    
    def test_change_password_wrong_current_password(self, authenticated_api_client, mock_use_cases):
        """Test POST /api/auth/change-password endpoint with wrong current password."""
        mock_use_cases['system'].change_password.return_value = {
            'success': False,
            'error': 'Current password is incorrect'
        }
        
        password_data = {
            'current_password': 'wrongpassword',
            'new_password': 'newpassword123',
            'confirm_password': 'newpassword123'
        }
        
        response = authenticated_api_client.post('/api/auth/change-password', json=password_data)
        
        assert response.status_code == 400
        data = response.json()
        assert data['success'] is False
        assert 'error' in data
        assert 'Current password is incorrect' in data['error']['message']
    
    def test_change_password_mismatch(self, authenticated_api_client):
        """Test POST /api/auth/change-password endpoint with password mismatch."""
        password_data = {
            'current_password': 'oldpassword123',
            'new_password': 'newpassword123',
            'confirm_password': 'differentpassword'
        }
        
        response = authenticated_api_client.post('/api/auth/change-password', json=password_data)
        
        assert response.status_code == 422  # Validation error
        data = response.json()
        assert 'detail' in data
    
    def test_change_password_not_authenticated(self, api_client):
        """Test POST /api/auth/change-password endpoint without authentication."""
        password_data = {
            'current_password': 'oldpassword123',
            'new_password': 'newpassword123',
            'confirm_password': 'newpassword123'
        }
        
        response = api_client.post('/api/auth/change-password', json=password_data)
        
        assert response.status_code == 401
        data = response.json()
        assert 'error' in data
        assert 'Unauthorized' in data['error']['message']


class TestAuthAPIErrorHandling:
    """Test authentication API error handling."""
    
    def test_api_server_error(self, api_client, mock_use_cases):
        """Test API endpoint with server error."""
        mock_use_cases['system'].authenticate_user.side_effect = Exception("Server error")
        
        login_data = {
            'username': 'admin',
            'password': 'password123'
        }
        
        response = api_client.post('/api/auth/login', json=login_data)
        
        assert response.status_code == 500
        data = response.json()
        assert 'error' in data
        assert 'Server error' in data['error']['message']
    
    def test_api_network_error(self, api_client, mock_use_cases):
        """Test API endpoint with network error."""
        mock_use_cases['system'].authenticate_user.side_effect = ConnectionError("Network error")
        
        login_data = {
            'username': 'admin',
            'password': 'password123'
        }
        
        response = api_client.post('/api/auth/login', json=login_data)
        
        assert response.status_code == 500
        data = response.json()
        assert 'error' in data
        assert 'Network error' in data['error']['message']
    
    def test_api_timeout_error(self, api_client, mock_use_cases):
        """Test API endpoint with timeout error."""
        mock_use_cases['system'].authenticate_user.side_effect = TimeoutError("Request timeout")
        
        login_data = {
            'username': 'admin',
            'password': 'password123'
        }
        
        response = api_client.post('/api/auth/login', json=login_data)
        
        assert response.status_code == 500
        data = response.json()
        assert 'error' in data
        assert 'Request timeout' in data['error']['message']
    
    def test_api_validation_error(self, api_client):
        """Test API endpoint with validation error."""
        login_data = {'invalid': 'data'}
        
        response = api_client.post('/api/auth/login', json=login_data)
        
        assert response.status_code == 422  # Validation error
        data = response.json()
        assert 'detail' in data


class TestAuthAPIPerformance:
    """Test authentication API performance."""
    
    def test_api_response_time(self, api_client, mock_use_cases):
        """Test API response time."""
        mock_use_cases['system'].authenticate_user.return_value = {
            'success': True,
            'user': {'username': 'admin', 'role': 'admin'},
            'token': 'valid_token'
        }
        
        import time
        start_time = time.time()
        response = api_client.post('/api/auth/login', json={
            'username': 'admin',
            'password': 'password123'
        })
        end_time = time.time()
        
        assert response.status_code == 200
        assert (end_time - start_time) < 1.0  # Response time should be under 1 second
    
    def test_api_concurrent_requests(self, api_client, mock_use_cases):
        """Test API with concurrent requests."""
        mock_use_cases['system'].authenticate_user.return_value = {
            'success': True,
            'user': {'username': 'admin', 'role': 'admin'},
            'token': 'valid_token'
        }
        
        import threading
        import time
        
        results = []
        errors = []
        
        def make_request():
            try:
                response = api_client.post('/api/auth/login', json={
                    'username': 'admin',
                    'password': 'password123'
                })
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


class TestAuthAPIDocumentation:
    """Test authentication API documentation."""
    
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
        assert '/api/auth' in str(data['paths'])
    
    def test_api_redoc_accessible(self, api_client):
        """Test that ReDoc documentation is accessible."""
        response = api_client.get('/redoc')
        
        assert response.status_code == 200
        assert 'text/html' in response.headers['content-type']
        assert 'ReDoc' in response.text






