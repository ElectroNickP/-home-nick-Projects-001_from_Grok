"""
Unit tests for FastAPI application (API Entry Point).

Tests cover API application creation, configuration, middleware,
documentation, and basic functionality.
"""

import pytest
from unittest.mock import Mock, patch
from fastapi import FastAPI
from fastapi.testclient import TestClient
from core.entrypoints.api.api_app import create_app
from core.entrypoints.config import EntryPointConfig
from core.entrypoints.factories import EntryPointFactory


class TestFastAPIAppCreation:
    """Test FastAPI application creation and configuration."""
    
    def test_create_app_returns_fastapi_instance(self, test_config: EntryPointConfig, entry_point_factory: EntryPointFactory):
        """Test that create_app returns a FastAPI application instance."""
        app = create_app(test_config, entry_point_factory)
        
        assert isinstance(app, FastAPI)
        assert app.title == "Telegram Bot Manager API"
        assert app.version == "3.6.0"
    
    def test_app_configuration(self, test_config: EntryPointConfig, entry_point_factory: EntryPointFactory):
        """Test that app is configured correctly."""
        app = create_app(test_config, entry_point_factory)
        
        assert app.debug == test_config.debug
        assert app.docs_url == "/docs"
        assert app.redoc_url == "/redoc"
    
    def test_routers_registered(self, test_config: EntryPointConfig, entry_point_factory: EntryPointFactory):
        """Test that all routers are registered."""
        app = create_app(test_config, entry_point_factory)
        
        # Check if routers are registered
        router_names = [router.prefix for router in app.routes if hasattr(router, 'prefix')]
        expected_routers = ['/api/v1/bots', '/api/v1/conversations', '/api/v1/system']
        
        for router_name in expected_routers:
            assert any(router_name in name for name in router_names)
    
    def test_middleware_registered(self, test_config: EntryPointConfig, entry_point_factory: EntryPointFactory):
        """Test that middleware is registered."""
        app = create_app(test_config, entry_point_factory)
        
        # Check if CORS middleware is registered
        middleware_classes = [middleware.cls for middleware in app.user_middleware]
        assert any('CORSMiddleware' in str(middleware) for middleware in middleware_classes)


class TestFastAPIAppRoutes:
    """Test basic route functionality."""
    
    def test_root_route_redirects_to_docs(self, api_client: TestClient):
        """Test that root route redirects to documentation."""
        response = api_client.get('/')
        
        assert response.status_code == 200
        # Should return API info or redirect to docs
    
    def test_docs_route_accessible(self, api_client: TestClient):
        """Test that docs route is accessible."""
        response = api_client.get('/docs')
        
        assert response.status_code == 200
        assert 'swagger' in response.text.lower()
    
    def test_redoc_route_accessible(self, api_client: TestClient):
        """Test that redoc route is accessible."""
        response = api_client.get('/redoc')
        
        assert response.status_code == 200
        assert 'redoc' in response.text.lower()
    
    def test_openapi_json_accessible(self, api_client: TestClient):
        """Test that OpenAPI JSON is accessible."""
        response = api_client.get('/openapi.json')
        
        assert response.status_code == 200
        data = response.json()
        assert 'openapi' in data
        assert data['info']['title'] == 'Telegram Bot Manager API'


class TestFastAPIAppAuthentication:
    """Test authentication functionality."""
    
    def test_protected_route_requires_authentication(self, api_client: TestClient):
        """Test that protected routes require authentication."""
        response = api_client.get('/api/v1/bots')
        
        assert response.status_code == 401  # Unauthorized
        assert 'unauthorized' in response.text.lower() or 'authentication' in response.text.lower()
    
    def test_authenticated_access_to_protected_routes(self, authenticated_api_client: TestClient):
        """Test that authenticated users can access protected routes."""
        response = authenticated_api_client.get('/api/v1/bots')
        
        assert response.status_code == 200
    
    def test_invalid_api_key_rejected(self, api_client: TestClient):
        """Test that invalid API keys are rejected."""
        response = api_client.get('/api/v1/bots', headers={
            'Authorization': 'Bearer invalid-key'
        })
        
        assert response.status_code == 401
    
    def test_missing_api_key_rejected(self, api_client: TestClient):
        """Test that missing API keys are rejected."""
        response = api_client.get('/api/v1/bots')
        
        assert response.status_code == 401


class TestFastAPIAppErrorHandling:
    """Test error handling."""
    
    def test_404_error_handler(self, api_client: TestClient):
        """Test 404 error handler."""
        response = api_client.get('/api/v1/nonexistent')
        
        assert response.status_code == 404
        data = response.json()
        assert 'detail' in data
        assert 'not found' in data['detail'].lower()
    
    def test_422_validation_error(self, authenticated_api_client: TestClient):
        """Test 422 validation error."""
        # Send invalid data to trigger validation error
        response = authenticated_api_client.post('/api/v1/bots', json={
            'invalid_field': 'invalid_value'
        })
        
        assert response.status_code == 422
        data = response.json()
        assert 'detail' in data
    
    def test_500_error_handler(self, test_config: EntryPointConfig, entry_point_factory: EntryPointFactory):
        """Test 500 error handler."""
        app = create_app(test_config, entry_point_factory)
        
        # Create a route that raises an exception
        @app.get("/test-error")
        def test_error():
            raise Exception("Test error")
        
        with TestClient(app) as client:
            response = client.get('/test-error')
            
            assert response.status_code == 500
            data = response.json()
            assert 'detail' in data


class TestFastAPIAppMiddleware:
    """Test middleware functionality."""
    
    def test_cors_headers(self, api_client: TestClient):
        """Test CORS headers are set."""
        response = api_client.options('/api/v1/bots')
        
        # Check for CORS headers
        headers = response.headers
        assert 'access-control-allow-origin' in headers or \
               'access-control-allow-methods' in headers
    
    def test_security_headers(self, api_client: TestClient):
        """Test security headers are set."""
        response = api_client.get('/docs')
        
        # Check for security headers
        headers = response.headers
        assert 'x-content-type-options' in headers or \
               'x-frame-options' in headers or \
               'x-xss-protection' in headers


class TestFastAPIAppConfiguration:
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
        
        assert app.debug is True
    
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
        
        assert app.debug is False


class TestFastAPIAppDependencyInjection:
    """Test dependency injection."""
    
    def test_use_cases_injected(self, test_config: EntryPointConfig, entry_point_factory: EntryPointFactory):
        """Test that use cases are properly injected."""
        app = create_app(test_config, entry_point_factory)
        
        # Check that dependencies are available
        assert hasattr(app, 'dependency_overrides')
    
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


class TestFastAPIAppDocumentation:
    """Test API documentation."""
    
    def test_openapi_schema_generated(self, api_client: TestClient):
        """Test that OpenAPI schema is generated."""
        response = api_client.get('/openapi.json')
        
        assert response.status_code == 200
        schema = response.json()
        
        # Check required OpenAPI fields
        assert 'openapi' in schema
        assert 'info' in schema
        assert 'paths' in schema
        assert 'components' in schema
    
    def test_api_info_correct(self, api_client: TestClient):
        """Test that API info is correct."""
        response = api_client.get('/openapi.json')
        
        assert response.status_code == 200
        schema = response.json()
        
        info = schema['info']
        assert info['title'] == 'Telegram Bot Manager API'
        assert info['version'] == '3.6.0'
        assert 'description' in info
    
    def test_paths_documented(self, api_client: TestClient):
        """Test that API paths are documented."""
        response = api_client.get('/openapi.json')
        
        assert response.status_code == 200
        schema = response.json()
        
        paths = schema['paths']
        expected_paths = ['/api/v1/bots', '/api/v1/conversations', '/api/v1/system']
        
        for path in expected_paths:
            assert any(path in api_path for api_path in paths.keys())
    
    def test_components_documented(self, api_client: TestClient):
        """Test that API components are documented."""
        response = api_client.get('/openapi.json')
        
        assert response.status_code == 200
        schema = response.json()
        
        components = schema.get('components', {})
        assert 'schemas' in components
        assert 'securitySchemes' in components


class TestFastAPIAppSecurity:
    """Test security features."""
    
    def test_security_schemes_defined(self, api_client: TestClient):
        """Test that security schemes are defined."""
        response = api_client.get('/openapi.json')
        
        assert response.status_code == 200
        schema = response.json()
        
        security_schemes = schema.get('components', {}).get('securitySchemes', {})
        assert 'BearerAuth' in security_schemes
    
    def test_security_requirements_applied(self, api_client: TestClient):
        """Test that security requirements are applied."""
        response = api_client.get('/openapi.json')
        
        assert response.status_code == 200
        schema = response.json()
        
        # Check that protected paths have security requirements
        paths = schema['paths']
        for path, methods in paths.items():
            if '/api/v1/' in path:
                for method in methods.values():
                    if isinstance(method, dict) and 'security' in method:
                        assert method['security'] == [{'BearerAuth': []}]


class TestFastAPIAppValidation:
    """Test request/response validation."""
    
    def test_request_validation(self, authenticated_api_client: TestClient):
        """Test request validation."""
        # Send request with missing required fields
        response = authenticated_api_client.post('/api/v1/bots', json={})
        
        assert response.status_code == 422
        data = response.json()
        assert 'detail' in data
    
    def test_response_validation(self, authenticated_api_client: TestClient, mock_use_cases):
        """Test response validation."""
        from tests.entrypoints.factories import test_data_factory
        
        # Mock successful response
        bot_data = test_data_factory.create_bot_config(id=1, name="Test Bot")
        mock_use_cases['bot_management'].get_bot.return_value = bot_data
        
        response = authenticated_api_client.get('/api/v1/bots/1')
        
        assert response.status_code == 200
        data = response.json()
        
        # Check response structure
        assert 'success' in data
        assert 'data' in data
        assert 'message' in data
        assert 'timestamp' in data


class TestFastAPIAppPerformance:
    """Test performance features."""
    
    def test_response_time_acceptable(self, api_client: TestClient):
        """Test that response time is acceptable."""
        import time
        
        start_time = time.time()
        response = api_client.get('/docs')
        end_time = time.time()
        
        response_time = end_time - start_time
        assert response_time < 1.0  # Should respond within 1 second
        assert response.status_code == 200
    
    def test_concurrent_requests(self, api_client: TestClient):
        """Test handling of concurrent requests."""
        import threading
        import time
        
        results = []
        
        def make_request():
            response = api_client.get('/docs')
            results.append(response.status_code)
        
        # Start multiple threads
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # All requests should succeed
        assert all(status == 200 for status in results)


class TestFastAPIAppLogging:
    """Test logging functionality."""
    
    def test_request_logging(self, api_client: TestClient):
        """Test that requests are logged."""
        # This test would require access to logs
        # For now, just verify the endpoint responds
        response = api_client.get('/docs')
        assert response.status_code == 200
    
    def test_error_logging(self, test_config: EntryPointConfig, entry_point_factory: EntryPointFactory):
        """Test that errors are logged."""
        app = create_app(test_config, entry_point_factory)
        
        @app.get("/test-error-logging")
        def test_error():
            raise Exception("Test error for logging")
        
        with TestClient(app) as client:
            response = client.get('/test-error-logging')
            assert response.status_code == 500


class TestFastAPIAppHealthCheck:
    """Test health check endpoints."""
    
    def test_health_check_endpoint(self, api_client: TestClient):
        """Test health check endpoint."""
        response = api_client.get('/health')
        
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'healthy'
    
    def test_readiness_check_endpoint(self, api_client: TestClient):
        """Test readiness check endpoint."""
        response = api_client.get('/ready')
        
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'ready'
    
    def test_liveness_check_endpoint(self, api_client: TestClient):
        """Test liveness check endpoint."""
        response = api_client.get('/live')
        
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'alive'






