"""
Unit tests for authentication (Web Entry Point).

Tests cover authentication, authorization, session management,
and access control for web routes.
"""

import pytest
import json
from unittest.mock import Mock, patch
from flask import session
from tests.entrypoints.factories import test_data_factory


class TestAuthenticationRoutes:
    """Test authentication route functionality."""
    
    def test_login_page_accessible(self, web_client):
        """Test that login page is accessible."""
        response = web_client.get('/login')
        
        assert response.status_code == 200
        assert b'login' in response.data.lower()
        assert b'username' in response.data.lower()
        assert b'password' in response.data.lower()
    
    def test_logout_page_accessible(self, web_client):
        """Test that logout page is accessible."""
        response = web_client.get('/logout')
        
        assert response.status_code == 200
        assert b'logout' in response.data.lower()
    
    def test_register_page_accessible(self, web_client):
        """Test that register page is accessible."""
        response = web_client.get('/register')
        
        assert response.status_code == 200
        assert b'register' in response.data.lower()
        assert b'sign up' in response.data.lower()


class TestLoginFunctionality:
    """Test login functionality."""
    
    def test_successful_login(self, web_client, mock_use_cases):
        """Test successful login."""
        # Mock authentication service
        mock_use_cases['system'].authenticate_user.return_value = {
            'success': True,
            'user': {
                'id': 1,
                'username': 'admin',
                'role': 'admin',
                'permissions': ['read', 'write', 'admin']
            }
        }
        
        response = web_client.post('/login', data={
            'username': 'admin',
            'password': 'securepassword123'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'dashboard' in response.data.lower() or b'welcome' in response.data.lower()
        
        # Check session
        with web_client.session_transaction() as sess:
            assert sess.get('authenticated') is True
            assert sess.get('user_id') == 1
            assert sess.get('username') == 'admin'
            assert sess.get('role') == 'admin'
    
    def test_failed_login_invalid_credentials(self, web_client, mock_use_cases):
        """Test failed login with invalid credentials."""
        mock_use_cases['system'].authenticate_user.return_value = {
            'success': False,
            'error': 'Invalid username or password'
        }
        
        response = web_client.post('/login', data={
            'username': 'admin',
            'password': 'wrongpassword'
        })
        
        assert response.status_code == 200
        assert b'invalid' in response.data.lower() or b'error' in response.data.lower()
        
        # Check session is not created
        with web_client.session_transaction() as sess:
            assert sess.get('authenticated') is None
    
    def test_failed_login_missing_fields(self, web_client):
        """Test failed login with missing fields."""
        response = web_client.post('/login', data={})
        
        assert response.status_code == 200
        assert b'required' in response.data.lower() or b'error' in response.data.lower()
    
    def test_failed_login_empty_fields(self, web_client):
        """Test failed login with empty fields."""
        response = web_client.post('/login', data={
            'username': '',
            'password': ''
        })
        
        assert response.status_code == 200
        assert b'required' in response.data.lower() or b'error' in response.data.lower()
    
    def test_login_with_remember_me(self, web_client, mock_use_cases):
        """Test login with remember me option."""
        mock_use_cases['system'].authenticate_user.return_value = {
            'success': True,
            'user': {
                'id': 1,
                'username': 'admin',
                'role': 'admin'
            }
        }
        
        response = web_client.post('/login', data={
            'username': 'admin',
            'password': 'securepassword123',
            'remember_me': 'on'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        
        # Check session is permanent
        with web_client.session_transaction() as sess:
            assert sess.get('authenticated') is True
            assert sess.get('remember_me') is True


class TestLogoutFunctionality:
    """Test logout functionality."""
    
    def test_successful_logout(self, authenticated_web_client):
        """Test successful logout."""
        response = authenticated_web_client.get('/logout', follow_redirects=True)
        
        assert response.status_code == 200
        assert b'logged out' in response.data.lower() or b'goodbye' in response.data.lower()
        
        # Check session is cleared
        with authenticated_web_client.session_transaction() as sess:
            assert sess.get('authenticated') is None
            assert sess.get('user_id') is None
            assert sess.get('username') is None
    
    def test_logout_clears_all_session_data(self, authenticated_web_client):
        """Test that logout clears all session data."""
        # Add some additional session data
        with authenticated_web_client.session_transaction() as sess:
            sess['some_other_data'] = 'test_value'
            sess['preferences'] = {'theme': 'dark'}
        
        response = authenticated_web_client.get('/logout', follow_redirects=True)
        
        assert response.status_code == 200
        
        # Check all session data is cleared
        with authenticated_web_client.session_transaction() as sess:
            assert len(sess) == 0


class TestRegistrationFunctionality:
    """Test registration functionality."""
    
    def test_successful_registration(self, web_client, mock_use_cases):
        """Test successful user registration."""
        mock_use_cases['system'].register_user.return_value = {
            'success': True,
            'user': {
                'id': 2,
                'username': 'newuser',
                'role': 'user'
            }
        }
        
        response = web_client.post('/register', data={
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'securepassword123',
            'confirm_password': 'securepassword123'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'registered' in response.data.lower() or b'welcome' in response.data.lower()
    
    def test_failed_registration_existing_username(self, web_client, mock_use_cases):
        """Test failed registration with existing username."""
        mock_use_cases['system'].register_user.return_value = {
            'success': False,
            'error': 'Username already exists'
        }
        
        response = web_client.post('/register', data={
            'username': 'existinguser',
            'email': 'existinguser@example.com',
            'password': 'securepassword123',
            'confirm_password': 'securepassword123'
        })
        
        assert response.status_code == 200
        assert b'already exists' in response.data.lower() or b'error' in response.data.lower()
    
    def test_failed_registration_password_mismatch(self, web_client):
        """Test failed registration with password mismatch."""
        response = web_client.post('/register', data={
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'securepassword123',
            'confirm_password': 'differentpassword'
        })
        
        assert response.status_code == 200
        assert b'match' in response.data.lower() or b'error' in response.data.lower()
    
    def test_failed_registration_weak_password(self, web_client, mock_use_cases):
        """Test failed registration with weak password."""
        mock_use_cases['system'].register_user.return_value = {
            'success': False,
            'error': 'Password is too weak'
        }
        
        response = web_client.post('/register', data={
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': '123',
            'confirm_password': '123'
        })
        
        assert response.status_code == 200
        assert b'weak' in response.data.lower() or b'error' in response.data.lower()


class TestSessionManagement:
    """Test session management functionality."""
    
    def test_session_creation_on_login(self, web_client, mock_use_cases):
        """Test session creation on successful login."""
        mock_use_cases['system'].authenticate_user.return_value = {
            'success': True,
            'user': {
                'id': 1,
                'username': 'admin',
                'role': 'admin'
            }
        }
        
        web_client.post('/login', data={
            'username': 'admin',
            'password': 'securepassword123'
        })
        
        with web_client.session_transaction() as sess:
            assert sess.get('authenticated') is True
            assert sess.get('user_id') == 1
            assert sess.get('username') == 'admin'
            assert sess.get('role') == 'admin'
            assert 'session_id' in sess
    
    def test_session_persistence(self, authenticated_web_client):
        """Test that session persists across requests."""
        # First request
        response1 = authenticated_web_client.get('/bots')
        assert response1.status_code == 200
        
        # Second request
        response2 = authenticated_web_client.get('/conversations')
        assert response2.status_code == 200
        
        # Session should still be valid
        with authenticated_web_client.session_transaction() as sess:
            assert sess.get('authenticated') is True
    
    def test_session_timeout(self, authenticated_web_client):
        """Test session timeout functionality."""
        # Simulate session timeout by clearing session
        with authenticated_web_client.session_transaction() as sess:
            sess.clear()
        
        response = authenticated_web_client.get('/bots')
        
        assert response.status_code == 302  # Redirect to login
        assert '/login' in response.location


class TestAccessControl:
    """Test access control and authorization."""
    
    def test_protected_route_requires_authentication(self, web_client):
        """Test that protected routes require authentication."""
        protected_routes = ['/bots', '/conversations', '/system/status', '/dashboard']
        
        for route in protected_routes:
            response = web_client.get(route)
            assert response.status_code == 302  # Redirect to login
            assert '/login' in response.location
    
    def test_authenticated_access_to_protected_routes(self, authenticated_web_client):
        """Test that authenticated users can access protected routes."""
        protected_routes = ['/bots', '/conversations', '/system/status', '/dashboard']
        
        for route in protected_routes:
            response = authenticated_web_client.get(route)
            assert response.status_code == 200
    
    def test_admin_only_routes(self, web_client, mock_use_cases):
        """Test admin-only routes require admin role."""
        # Login as regular user
        mock_use_cases['system'].authenticate_user.return_value = {
            'success': True,
            'user': {
                'id': 2,
                'username': 'user',
                'role': 'user'
            }
        }
        
        web_client.post('/login', data={
            'username': 'user',
            'password': 'password123'
        })
        
        # Try to access admin-only route
        response = web_client.get('/admin/users')
        
        assert response.status_code == 403  # Forbidden
        assert b'forbidden' in response.data.lower() or b'access denied' in response.data.lower()
    
    def test_admin_access_to_admin_routes(self, web_client, mock_use_cases):
        """Test admin users can access admin routes."""
        # Login as admin
        mock_use_cases['system'].authenticate_user.return_value = {
            'success': True,
            'user': {
                'id': 1,
                'username': 'admin',
                'role': 'admin'
            }
        }
        
        web_client.post('/login', data={
            'username': 'admin',
            'password': 'adminpassword123'
        })
        
        # Access admin route
        response = web_client.get('/admin/users')
        
        assert response.status_code == 200


class TestPasswordReset:
    """Test password reset functionality."""
    
    def test_password_reset_request_page(self, web_client):
        """Test password reset request page."""
        response = web_client.get('/password/reset')
        
        assert response.status_code == 200
        assert b'reset' in response.data.lower()
        assert b'email' in response.data.lower()
    
    def test_successful_password_reset_request(self, web_client, mock_use_cases):
        """Test successful password reset request."""
        mock_use_cases['system'].request_password_reset.return_value = {
            'success': True,
            'message': 'Password reset email sent'
        }
        
        response = web_client.post('/password/reset', data={
            'email': 'user@example.com'
        })
        
        assert response.status_code == 200
        assert b'sent' in response.data.lower() or b'email' in response.data.lower()
    
    def test_password_reset_with_token(self, web_client, mock_use_cases):
        """Test password reset with token."""
        mock_use_cases['system'].reset_password.return_value = {
            'success': True,
            'message': 'Password reset successfully'
        }
        
        response = web_client.post('/password/reset/confirm', data={
            'token': 'valid_token_123',
            'new_password': 'newpassword123',
            'confirm_password': 'newpassword123'
        })
        
        assert response.status_code == 200
        assert b'successfully' in response.data.lower() or b'reset' in response.data.lower()


class TestAuthenticationAJAX:
    """Test authentication AJAX endpoints."""
    
    def test_login_ajax_success(self, web_client, mock_use_cases):
        """Test successful AJAX login."""
        mock_use_cases['system'].authenticate_user.return_value = {
            'success': True,
            'user': {
                'id': 1,
                'username': 'admin',
                'role': 'admin'
            }
        }
        
        response = web_client.post('/api/auth/login',
            data=json.dumps({
                'username': 'admin',
                'password': 'securepassword123'
            }),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['user']['username'] == 'admin'
    
    def test_login_ajax_failure(self, web_client, mock_use_cases):
        """Test failed AJAX login."""
        mock_use_cases['system'].authenticate_user.return_value = {
            'success': False,
            'error': 'Invalid credentials'
        }
        
        response = web_client.post('/api/auth/login',
            data=json.dumps({
                'username': 'admin',
                'password': 'wrongpassword'
            }),
            content_type='application/json'
        )
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'Invalid credentials' in data['error']['message']
    
    def test_logout_ajax(self, authenticated_web_client):
        """Test AJAX logout."""
        response = authenticated_web_client.post('/api/auth/logout')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        
        # Check session is cleared
        with authenticated_web_client.session_transaction() as sess:
            assert sess.get('authenticated') is None
    
    def test_check_auth_status_ajax(self, authenticated_web_client):
        """Test AJAX auth status check."""
        response = authenticated_web_client.get('/api/auth/status')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['authenticated'] is True
        assert data['user']['username'] == 'admin'
    
    def test_check_auth_status_ajax_not_authenticated(self, web_client):
        """Test AJAX auth status check when not authenticated."""
        response = web_client.get('/api/auth/status')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['authenticated'] is False


class TestAuthenticationSecurity:
    """Test authentication security features."""
    
    def test_csrf_protection(self, web_client):
        """Test CSRF protection on login form."""
        # Get CSRF token
        response = web_client.get('/login')
        assert response.status_code == 200
        
        # Try to submit without CSRF token
        response = web_client.post('/login', data={
            'username': 'admin',
            'password': 'password123'
        })
        
        assert response.status_code == 400  # Bad Request due to CSRF
    
    def test_password_hashing(self, web_client, mock_use_cases):
        """Test that passwords are properly hashed."""
        mock_use_cases['system'].authenticate_user.return_value = {
            'success': True,
            'user': {
                'id': 1,
                'username': 'admin',
                'role': 'admin'
            }
        }
        
        # Login should work with plain text password
        response = web_client.post('/login', data={
            'username': 'admin',
            'password': 'securepassword123'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        
        # Verify that the authentication service was called with hashed password
        mock_use_cases['system'].authenticate_user.assert_called_once()
        call_args = mock_use_cases['system'].authenticate_user.call_args
        # The password should be hashed, not plain text
        assert call_args[1]['password'] != 'securepassword123'
    
    def test_session_security(self, authenticated_web_client):
        """Test session security features."""
        with authenticated_web_client.session_transaction() as sess:
            # Check session has security attributes
            assert 'session_id' in sess
            assert 'created_at' in sess
            assert 'last_activity' in sess
    
    def test_brute_force_protection(self, web_client, mock_use_cases):
        """Test brute force protection."""
        # Mock failed authentication
        mock_use_cases['system'].authenticate_user.return_value = {
            'success': False,
            'error': 'Invalid credentials'
        }
        
        # Try multiple failed logins
        for i in range(5):
            response = web_client.post('/login', data={
                'username': 'admin',
                'password': f'wrongpassword{i}'
            })
            assert response.status_code == 200
        
        # After multiple failures, should be rate limited
        response = web_client.post('/login', data={
            'username': 'admin',
            'password': 'anotherwrongpassword'
        })
        
        assert response.status_code == 429  # Too Many Requests
        assert b'rate limit' in response.data.lower() or b'too many' in response.data.lower()


class TestAuthenticationErrorHandling:
    """Test authentication error handling."""
    
    def test_database_error_during_login(self, web_client, mock_use_cases):
        """Test handling of database errors during login."""
        mock_use_cases['system'].authenticate_user.side_effect = Exception("Database connection failed")
        
        response = web_client.post('/login', data={
            'username': 'admin',
            'password': 'password123'
        })
        
        assert response.status_code == 500
        assert b'error' in response.data.lower() or b'unavailable' in response.data.lower()
    
    def test_invalid_session_handling(self, web_client):
        """Test handling of invalid session data."""
        # Create invalid session
        with web_client.session_transaction() as sess:
            sess['authenticated'] = True
            sess['user_id'] = 'invalid_id'  # Invalid user ID
        
        response = web_client.get('/bots')
        
        assert response.status_code == 302  # Redirect to login
        assert '/login' in response.location
    
    def test_missing_user_data_handling(self, web_client, mock_use_cases):
        """Test handling of missing user data."""
        mock_use_cases['system'].authenticate_user.return_value = {
            'success': True,
            'user': None  # Missing user data
        }
        
        response = web_client.post('/login', data={
            'username': 'admin',
            'password': 'password123'
        })
        
        assert response.status_code == 500
        assert b'error' in response.data.lower()








