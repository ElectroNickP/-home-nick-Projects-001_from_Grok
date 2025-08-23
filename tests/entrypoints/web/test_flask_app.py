"""
Unit tests for Flask application (Web Entry Point).

Tests cover application creation, configuration, middleware,
error handling, and basic functionality.
"""

import pytest
from unittest.mock import Mock, patch
from flask import Flask
from core.entrypoints.web.flask_app import create_app
from core.entrypoints.config import EntryPointConfig
from core.entrypoints.factories import EntryPointFactory


class TestFlaskAppCreation:
    """Test Flask application creation and configuration."""
    
    def test_create_app_returns_flask_instance(self, test_config: EntryPointConfig, entry_point_factory: EntryPointFactory):
        """Test that create_app returns a Flask application instance."""
        app = create_app(test_config, entry_point_factory)
        
        assert isinstance(app, Flask)
        assert app.name == 'core.entrypoints.web.flask_app'
    
    def test_app_configuration(self, test_config: EntryPointConfig, entry_point_factory: EntryPointFactory):
        """Test that app is configured correctly."""
        app = create_app(test_config, entry_point_factory)
        
        assert app.config['SECRET_KEY'] == test_config.secret_key
        assert app.config['DEBUG'] == test_config.debug
    
    def test_blueprints_registered(self, test_config: EntryPointConfig, entry_point_factory: EntryPointFactory):
        """Test that all blueprints are registered."""
        app = create_app(test_config, entry_point_factory)
        
        blueprint_names = [bp.name for bp in app.blueprints.values()]
        expected_blueprints = ['bot_routes', 'conversation_routes', 'system_routes']
        
        for blueprint_name in expected_blueprints:
            assert blueprint_name in blueprint_names
    
    def test_error_handlers_registered(self, test_config: EntryPointConfig, entry_point_factory: EntryPointFactory):
        """Test that error handlers are registered."""
        app = create_app(test_config, entry_point_factory)
        
        # Check if error handlers exist
        assert 404 in app.error_handler_spec[None]
        assert 500 in app.error_handler_spec[None]
    
    def test_session_configuration(self, test_config: EntryPointConfig, entry_point_factory: EntryPointFactory):
        """Test session configuration."""
        app = create_app(test_config, entry_point_factory)
        
        # Check session configuration
        assert app.config['SESSION_COOKIE_SECURE'] is False  # Should be False in debug mode
        assert app.config['SESSION_COOKIE_HTTPONLY'] is True
        assert app.config['PERMANENT_SESSION_LIFETIME'].total_seconds() == 3600  # 1 hour


class TestFlaskAppRoutes:
    """Test basic route functionality."""
    
    def test_root_route_redirects_to_login(self, web_client):
        """Test that root route redirects to login page."""
        response = web_client.get('/')
        
        assert response.status_code == 302  # Redirect
        assert '/login' in response.location
    
    def test_login_route_accessible(self, web_client):
        """Test that login route is accessible."""
        response = web_client.get('/login')
        
        assert response.status_code == 200
        assert b'login' in response.data.lower()
    
    def test_logout_route_accessible(self, web_client):
        """Test that logout route is accessible."""
        response = web_client.get('/logout')
        
        assert response.status_code == 200
        assert b'logout' in response.data.lower()


class TestFlaskAppAuthentication:
    """Test authentication functionality."""
    
    def test_protected_route_requires_authentication(self, web_client):
        """Test that protected routes require authentication."""
        response = web_client.get('/bots')
        
        assert response.status_code == 302  # Redirect to login
        assert '/login' in response.location
    
    def test_authenticated_access_to_protected_routes(self, authenticated_web_client):
        """Test that authenticated users can access protected routes."""
        response = authenticated_web_client.get('/bots')
        
        assert response.status_code == 200
    
    def test_session_management(self, web_client):
        """Test session management."""
        # Test login
        response = web_client.post('/login', data={
            'username': 'admin',
            'password': 'securepassword123'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        
        # Test that session is created
        with web_client.session_transaction() as sess:
            assert sess.get('authenticated') is True
            assert sess.get('user') == 'admin'


class TestFlaskAppErrorHandling:
    """Test error handling."""
    
    def test_404_error_handler(self, web_client):
        """Test 404 error handler."""
        response = web_client.get('/nonexistent-route')
        
        assert response.status_code == 404
        assert b'404' in response.data or b'not found' in response.data.lower()
    
    def test_500_error_handler(self, test_config: EntryPointConfig, entry_point_factory: EntryPointFactory):
        """Test 500 error handler."""
        app = create_app(test_config, entry_point_factory)
        app.config['TESTING'] = True
        
        # Create a route that raises an exception
        @app.route('/test-error')
        def test_error():
            raise Exception("Test error")
        
        with app.test_client() as client:
            response = client.get('/test-error')
            
            assert response.status_code == 500
            assert b'500' in response.data or b'error' in response.data.lower()


class TestFlaskAppMiddleware:
    """Test middleware functionality."""
    
    def test_cors_headers(self, web_client):
        """Test CORS headers are set."""
        response = web_client.get('/login')
        
        # Check for CORS headers
        assert 'Access-Control-Allow-Origin' in response.headers or \
               'Access-Control-Allow-Methods' in response.headers
    
    def test_security_headers(self, web_client):
        """Test security headers are set."""
        response = web_client.get('/login')
        
        # Check for security headers
        headers = response.headers
        assert 'X-Content-Type-Options' in headers or \
               'X-Frame-Options' in headers or \
               'X-XSS-Protection' in headers


class TestFlaskAppConfiguration:
    """Test configuration handling."""
    
    def test_development_configuration(self):
        """Test development configuration."""
        config = EntryPointConfig(
            web_host="127.0.0.1",
            web_port=5000,
            api_host="127.0.0.1",
            api_port=8000,
            debug=True,
            secret_key="dev-secret-key",
            api_key="dev-api-key"
        )
        
        factory = Mock(spec=EntryPointFactory)
        app = create_app(config, factory)
        
        assert app.config['DEBUG'] is True
        assert app.config['TESTING'] is False
    
    def test_production_configuration(self):
        """Test production configuration."""
        config = EntryPointConfig(
            web_host="0.0.0.0",
            web_port=80,
            api_host="0.0.0.0",
            api_port=443,
            debug=False,
            secret_key="prod-secret-key",
            api_key="prod-api-key"
        )
        
        factory = Mock(spec=EntryPointFactory)
        app = create_app(config, factory)
        
        assert app.config['DEBUG'] is False
        assert app.config['TESTING'] is False


class TestFlaskAppDependencyInjection:
    """Test dependency injection."""
    
    def test_use_cases_injected(self, test_config: EntryPointConfig, entry_point_factory: EntryPointFactory):
        """Test that use cases are properly injected."""
        app = create_app(test_config, entry_point_factory)
        
        # Check that use cases are available in app context
        with app.app_context():
            assert hasattr(app, 'bot_management_use_case')
            assert hasattr(app, 'conversation_use_case')
            assert hasattr(app, 'system_use_case')
    
    def test_factory_used_for_dependencies(self, test_config: EntryPointConfig):
        """Test that factory is used to create dependencies."""
        mock_factory = Mock(spec=EntryPointFactory)
        mock_factory.create_bot_management_use_case.return_value = Mock()
        mock_factory.create_conversation_use_case.return_value = Mock()
        mock_factory.create_system_use_case.return_value = Mock()
        
        app = create_app(test_config, mock_factory)
        
        # Verify factory methods were called
        mock_factory.create_bot_management_use_case.assert_called_once()
        mock_factory.create_conversation_use_case.assert_called_once()
        mock_factory.create_system_use_case.assert_called_once()


class TestFlaskAppContext:
    """Test application context."""
    
    def test_app_context_available(self, test_config: EntryPointConfig, entry_point_factory: EntryPointFactory):
        """Test that application context is available."""
        app = create_app(test_config, entry_point_factory)
        
        with app.app_context():
            assert app.config is not None
            assert app.name is not None
    
    def test_request_context_available(self, web_client):
        """Test that request context is available."""
        with web_client.application.app_context():
            assert web_client.application.config is not None







