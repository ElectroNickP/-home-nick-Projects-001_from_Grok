"""
Performance tests for API Entry Point using Locust.

Tests cover load testing, stress testing, and scalability testing.
"""

import pytest
import time
import threading
import requests
import json
from locust import HttpUser, task, between
from fastapi.testclient import TestClient
from tests.entrypoints.factories import test_data_factory


class TestAPIPerformanceLoad:
    """Test API performance under normal load conditions."""
    
    def test_api_response_time_baseline(self, authenticated_api_client, mock_use_cases):
        """Test baseline API response times for all endpoints."""
        # Prepare test data
        bots_data = [test_data_factory.create_bot_config(id=1, name="Test Bot", status="running")]
        mock_use_cases['bot_management'].list_bots.return_value = {
            'success': True,
            'bots': bots_data,
            'total': 1
        }
        
        # Test response times for key endpoints
        endpoints_to_test = [
            ('GET', '/api/bots'),
            ('GET', '/api/bots/1'),
            ('GET', '/api/conversations'),
            ('GET', '/api/conversations/1'),
            ('GET', '/api/system/status'),
            ('GET', '/health'),
            ('GET', '/ready'),
            ('GET', '/live')
        ]
        
        for method, endpoint in endpoints_to_test:
            start_time = time.time()
            if method == 'GET':
                response = authenticated_api_client.get(endpoint)
            else:
                response = authenticated_api_client.post(endpoint)
            response_time = time.time() - start_time
            
            # Verify response is successful
            assert response.status_code in [200, 201], f"Endpoint {endpoint} failed with status {response.status_code}"
            
            # Verify response time is within acceptable limits
            assert response_time < 0.5, f"Response time {response_time}s for {endpoint} exceeds 0.5s baseline"
    
    def test_api_throughput_baseline(self, authenticated_api_client, mock_use_cases):
        """Test API throughput under baseline load."""
        # Prepare test data
        bots_data = [test_data_factory.create_bot_config(id=1, name="Test Bot", status="running")]
        mock_use_cases['bot_management'].list_bots.return_value = {
            'success': True,
            'bots': bots_data,
            'total': 1
        }
        
        # Test concurrent requests
        num_requests = 10
        results = []
        errors = []
        
        def make_request():
            try:
                start_time = time.time()
                response = authenticated_api_client.get('/api/bots')
                response_time = time.time() - start_time
                results.append((response.status_code, response_time))
            except Exception as e:
                errors.append(str(e))
        
        # Start concurrent requests
        threads = []
        for _ in range(num_requests):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        # Wait for all requests to complete
        for thread in threads:
            thread.join()
        
        # Verify all requests succeeded
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == num_requests
        
        # Verify all responses are successful
        status_codes = [result[0] for result in results]
        assert all(status == 200 for status in status_codes)
        
        # Calculate average response time
        response_times = [result[1] for result in results]
        avg_response_time = sum(response_times) / len(response_times)
        
        # Verify average response time is acceptable
        assert avg_response_time < 0.3, f"Average response time {avg_response_time}s exceeds 0.3s baseline"
    
    def test_api_memory_usage_baseline(self, authenticated_api_client, mock_use_cases):
        """Test API memory usage under baseline load."""
        import psutil
        import os
        
        # Get initial memory usage
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Prepare test data
        bots_data = [
            test_data_factory.create_bot_config(id=i, name=f"Bot {i}", status="running")
            for i in range(1, 51)  # 50 bots
        ]
        mock_use_cases['bot_management'].list_bots.return_value = {
            'success': True,
            'bots': bots_data,
            'total': 50
        }
        
        # Make multiple requests to test memory usage
        for _ in range(10):
            response = authenticated_api_client.get('/api/bots')
            assert response.status_code == 200
        
        # Get final memory usage
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Verify memory increase is reasonable (less than 50MB)
        assert memory_increase < 50, f"Memory increase {memory_increase}MB exceeds 50MB baseline"


class TestAPIPerformanceStress:
    """Test API performance under stress conditions."""
    
    def test_api_high_concurrency(self, authenticated_api_client, mock_use_cases):
        """Test API performance under high concurrency."""
        # Prepare test data
        bots_data = [test_data_factory.create_bot_config(id=1, name="Test Bot", status="running")]
        mock_use_cases['bot_management'].list_bots.return_value = {
            'success': True,
            'bots': bots_data,
            'total': 1
        }
        
        # Test with high concurrency
        num_concurrent_requests = 50
        results = []
        errors = []
        
        def make_request():
            try:
                start_time = time.time()
                response = authenticated_api_client.get('/api/bots')
                response_time = time.time() - start_time
                results.append((response.status_code, response_time))
            except Exception as e:
                errors.append(str(e))
        
        # Start high concurrency requests
        threads = []
        for _ in range(num_concurrent_requests):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        # Wait for all requests to complete
        for thread in threads:
            thread.join()
        
        # Verify most requests succeeded (allow some failures under stress)
        success_rate = len([r for r in results if r[0] == 200]) / len(results)
        assert success_rate >= 0.9, f"Success rate {success_rate} below 90% under stress"
        
        # Verify average response time is still reasonable
        if results:
            response_times = [result[1] for result in results if result[0] == 200]
            if response_times:
                avg_response_time = sum(response_times) / len(response_times)
                assert avg_response_time < 1.0, f"Average response time {avg_response_time}s exceeds 1.0s under stress"
    
    def test_api_large_payload_handling(self, authenticated_api_client, mock_use_cases):
        """Test API performance with large payloads."""
        # Prepare large bot data
        large_bot_data = {
            'name': 'Large Test Bot',
            'token': 'test_token_large',
            'description': 'A' * 50000  # 50KB description
        }
        
        bot_data = test_data_factory.create_bot_config(id=1, name="Large Test Bot", status="created")
        mock_use_cases['bot_management'].create_bot.return_value = {
            'success': True,
            'bot': bot_data,
            'message': 'Bot created successfully'
        }
        
        # Test creating bot with large payload
        start_time = time.time()
        response = authenticated_api_client.post('/api/bots', json=large_bot_data)
        response_time = time.time() - start_time
        
        # Verify response is successful
        assert response.status_code == 201
        data = response.json()
        assert data['success'] is True
        
        # Verify response time is reasonable for large payload
        assert response_time < 2.0, f"Response time {response_time}s for large payload exceeds 2.0s"
    
    def test_api_memory_leak_detection(self, authenticated_api_client, mock_use_cases):
        """Test for memory leaks during repeated operations."""
        import psutil
        import os
        
        # Get initial memory usage
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Prepare test data
        bots_data = [test_data_factory.create_bot_config(id=1, name="Test Bot", status="running")]
        mock_use_cases['bot_management'].list_bots.return_value = {
            'success': True,
            'bots': bots_data,
            'total': 1
        }
        
        # Perform repeated operations
        for i in range(100):
            response = authenticated_api_client.get('/api/bots')
            assert response.status_code == 200
            
            # Check memory every 20 requests
            if i % 20 == 0:
                current_memory = process.memory_info().rss / 1024 / 1024  # MB
                memory_increase = current_memory - initial_memory
                
                # Verify memory increase is not excessive
                assert memory_increase < 100, f"Memory increase {memory_increase}MB after {i} requests exceeds 100MB"
        
        # Final memory check
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        total_memory_increase = final_memory - initial_memory
        
        # Verify total memory increase is reasonable
        assert total_memory_increase < 100, f"Total memory increase {total_memory_increase}MB exceeds 100MB"


class TestAPIPerformanceScalability:
    """Test API performance scalability."""
    
    def test_api_scalability_with_data_size(self, authenticated_api_client, mock_use_cases):
        """Test API performance as data size increases."""
        # Test with different data sizes
        data_sizes = [10, 50, 100, 500, 1000]
        
        for size in data_sizes:
            # Prepare test data of specified size
            bots_data = [
                test_data_factory.create_bot_config(id=i, name=f"Bot {i}", status="running")
                for i in range(1, size + 1)
            ]
            mock_use_cases['bot_management'].list_bots.return_value = {
                'success': True,
                'bots': bots_data,
                'total': size
            }
            
            # Measure response time
            start_time = time.time()
            response = authenticated_api_client.get('/api/bots')
            response_time = time.time() - start_time
            
            # Verify response is successful
            assert response.status_code == 200
            data = response.json()
            assert data['success'] is True
            assert len(data['bots']) == size
            
            # Verify response time scales reasonably
            if size <= 100:
                assert response_time < 0.5, f"Response time {response_time}s for {size} items exceeds 0.5s"
            elif size <= 500:
                assert response_time < 1.0, f"Response time {response_time}s for {size} items exceeds 1.0s"
            else:
                assert response_time < 2.0, f"Response time {response_time}s for {size} items exceeds 2.0s"
    
    def test_api_pagination_performance(self, authenticated_api_client, mock_use_cases):
        """Test API performance with pagination."""
        # Prepare large dataset
        total_items = 1000
        page_sizes = [10, 25, 50, 100]
        
        for page_size in page_sizes:
            # Calculate expected pages
            total_pages = (total_items + page_size - 1) // page_size
            
            for page in range(1, min(6, total_pages + 1)):  # Test first 5 pages
                # Prepare paginated data
                start_idx = (page - 1) * page_size
                end_idx = min(start_idx + page_size, total_items)
                
                bots_data = [
                    test_data_factory.create_bot_config(id=i, name=f"Bot {i}", status="running")
                    for i in range(start_idx + 1, end_idx + 1)
                ]
                
                mock_use_cases['bot_management'].list_bots.return_value = {
                    'success': True,
                    'bots': bots_data,
                    'total': total_items,
                    'page': page,
                    'per_page': page_size
                }
                
                # Measure response time
                start_time = time.time()
                response = authenticated_api_client.get(f'/api/bots?page={page}&per_page={page_size}')
                response_time = time.time() - start_time
                
                # Verify response is successful
                assert response.status_code == 200
                data = response.json()
                assert data['success'] is True
                assert data['page'] == page
                assert data['per_page'] == page_size
                
                # Verify response time is consistent regardless of page size
                assert response_time < 0.5, f"Response time {response_time}s for page {page} with size {page_size} exceeds 0.5s"
    
    def test_api_concurrent_users_simulation(self, authenticated_api_client, mock_use_cases):
        """Test API performance with simulated concurrent users."""
        # Prepare test data
        bots_data = [test_data_factory.create_bot_config(id=1, name="Test Bot", status="running")]
        mock_use_cases['bot_management'].list_bots.return_value = {
            'success': True,
            'bots': bots_data,
            'total': 1
        }
        
        # Simulate different numbers of concurrent users
        user_counts = [5, 10, 20, 50]
        
        for user_count in user_counts:
            results = []
            errors = []
            
            def user_simulation():
                """Simulate a single user making multiple requests."""
                user_results = []
                for _ in range(5):  # Each user makes 5 requests
                    try:
                        start_time = time.time()
                        response = authenticated_api_client.get('/api/bots')
                        response_time = time.time() - start_time
                        user_results.append((response.status_code, response_time))
                        time.sleep(0.1)  # Small delay between requests
                    except Exception as e:
                        errors.append(str(e))
                results.extend(user_results)
            
            # Start user simulation threads
            threads = []
            for _ in range(user_count):
                thread = threading.Thread(target=user_simulation)
                threads.append(thread)
                thread.start()
            
            # Wait for all users to complete
            for thread in threads:
                thread.join()
            
            # Calculate metrics
            total_requests = len(results)
            successful_requests = len([r for r in results if r[0] == 200])
            success_rate = successful_requests / total_requests if total_requests > 0 else 0
            
            # Verify success rate is acceptable
            assert success_rate >= 0.95, f"Success rate {success_rate} for {user_count} users below 95%"
            
            # Calculate average response time
            if successful_requests > 0:
                response_times = [r[1] for r in results if r[0] == 200]
                avg_response_time = sum(response_times) / len(response_times)
                
                # Verify response time scales reasonably with user count
                if user_count <= 10:
                    assert avg_response_time < 0.5, f"Average response time {avg_response_time}s for {user_count} users exceeds 0.5s"
                elif user_count <= 20:
                    assert avg_response_time < 1.0, f"Average response time {avg_response_time}s for {user_count} users exceeds 1.0s"
                else:
                    assert avg_response_time < 2.0, f"Average response time {avg_response_time}s for {user_count} users exceeds 2.0s"


class TestAPIPerformanceEndpoints:
    """Test performance of specific API endpoints."""
    
    def test_bot_endpoints_performance(self, authenticated_api_client, mock_use_cases):
        """Test performance of bot-related endpoints."""
        # Prepare test data
        bot_data = test_data_factory.create_bot_config(id=1, name="Test Bot", status="running")
        mock_use_cases['bot_management'].get_bot.return_value = {
            'success': True,
            'bot': bot_data
        }
        mock_use_cases['bot_management'].start_bot.return_value = {
            'success': True,
            'message': 'Bot started successfully'
        }
        
        # Test bot detail endpoint
        start_time = time.time()
        response = authenticated_api_client.get('/api/bots/1')
        response_time = time.time() - start_time
        
        assert response.status_code == 200
        assert response_time < 0.3, f"Bot detail response time {response_time}s exceeds 0.3s"
        
        # Test bot start endpoint
        start_time = time.time()
        response = authenticated_api_client.post('/api/bots/1/start')
        response_time = time.time() - start_time
        
        assert response.status_code == 200
        assert response_time < 0.5, f"Bot start response time {response_time}s exceeds 0.5s"
    
    def test_conversation_endpoints_performance(self, authenticated_api_client, mock_use_cases):
        """Test performance of conversation-related endpoints."""
        # Prepare test data with messages
        conversation = test_data_factory.create_conversation(id=1, bot_id=1, user_id=1001)
        messages = test_data_factory.create_messages(100, conversation_id=1)
        conversation['messages'] = messages
        
        mock_use_cases['conversation'].get_conversation.return_value = {
            'success': True,
            'conversation': conversation
        }
        
        # Test conversation detail endpoint with messages
        start_time = time.time()
        response = authenticated_api_client.get('/api/conversations/1')
        response_time = time.time() - start_time
        
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert len(data['conversation']['messages']) == 100
        
        # Verify response time is reasonable for conversation with messages
        assert response_time < 1.0, f"Conversation detail response time {response_time}s exceeds 1.0s"
    
    def test_system_endpoints_performance(self, authenticated_api_client, mock_use_cases):
        """Test performance of system-related endpoints."""
        # Prepare test data
        status_data = test_data_factory.create_system_status()
        mock_use_cases['system'].get_system_status.return_value = {
            'success': True,
            'status': status_data
        }
        
        # Test system status endpoint
        start_time = time.time()
        response = authenticated_api_client.get('/api/system/status')
        response_time = time.time() - start_time
        
        assert response.status_code == 200
        assert response_time < 0.3, f"System status response time {response_time}s exceeds 0.3s"
    
    def test_authentication_endpoints_performance(self, api_client, mock_use_cases):
        """Test performance of authentication endpoints."""
        # Prepare test data
        user_data = {
            'id': 1,
            'username': 'admin',
            'role': 'admin'
        }
        mock_use_cases['system'].authenticate_user.return_value = {
            'success': True,
            'user': user_data,
            'token': 'valid_jwt_token'
        }
        
        # Test login endpoint
        login_data = {
            'username': 'admin',
            'password': 'securepassword123'
        }
        
        start_time = time.time()
        response = api_client.post('/api/auth/login', json=login_data)
        response_time = time.time() - start_time
        
        assert response.status_code == 200
        assert response_time < 0.5, f"Login response time {response_time}s exceeds 0.5s"


class TestAPIPerformanceMonitoring:
    """Test API performance monitoring and metrics."""
    
    def test_api_response_time_distribution(self, authenticated_api_client, mock_use_cases):
        """Test distribution of API response times."""
        # Prepare test data
        bots_data = [test_data_factory.create_bot_config(id=1, name="Test Bot", status="running")]
        mock_use_cases['bot_management'].list_bots.return_value = {
            'success': True,
            'bots': bots_data,
            'total': 1
        }
        
        # Collect response times
        response_times = []
        num_requests = 100
        
        for _ in range(num_requests):
            start_time = time.time()
            response = authenticated_api_client.get('/api/bots')
            response_time = time.time() - start_time
            
            assert response.status_code == 200
            response_times.append(response_time)
        
        # Calculate statistics
        avg_response_time = sum(response_times) / len(response_times)
        min_response_time = min(response_times)
        max_response_time = max(response_times)
        
        # Verify statistics are reasonable
        assert avg_response_time < 0.3, f"Average response time {avg_response_time}s exceeds 0.3s"
        assert min_response_time < 0.1, f"Minimum response time {min_response_time}s exceeds 0.1s"
        assert max_response_time < 1.0, f"Maximum response time {max_response_time}s exceeds 1.0s"
        
        # Verify consistency (standard deviation should be small)
        variance = sum((x - avg_response_time) ** 2 for x in response_times) / len(response_times)
        std_dev = variance ** 0.5
        assert std_dev < 0.1, f"Response time standard deviation {std_dev}s exceeds 0.1s"
    
    def test_api_error_rate_monitoring(self, authenticated_api_client, mock_use_cases):
        """Test monitoring of API error rates."""
        # Prepare test data
        bots_data = [test_data_factory.create_bot_config(id=1, name="Test Bot", status="running")]
        mock_use_cases['bot_management'].list_bots.return_value = {
            'success': True,
            'bots': bots_data,
            'total': 1
        }
        
        # Make multiple requests and track errors
        total_requests = 100
        successful_requests = 0
        failed_requests = 0
        
        for _ in range(total_requests):
            try:
                response = authenticated_api_client.get('/api/bots')
                if response.status_code == 200:
                    successful_requests += 1
                else:
                    failed_requests += 1
            except Exception:
                failed_requests += 1
        
        # Calculate error rate
        error_rate = failed_requests / total_requests
        
        # Verify error rate is very low under normal conditions
        assert error_rate < 0.01, f"Error rate {error_rate} exceeds 1% under normal conditions"
        assert successful_requests > 0, "No successful requests recorded"
    
    def test_api_throughput_monitoring(self, authenticated_api_client, mock_use_cases):
        """Test monitoring of API throughput."""
        # Prepare test data
        bots_data = [test_data_factory.create_bot_config(id=1, name="Test Bot", status="running")]
        mock_use_cases['bot_management'].list_bots.return_value = {
            'success': True,
            'bots': bots_data,
            'total': 1
        }
        
        # Measure throughput over time
        num_requests = 50
        start_time = time.time()
        
        for _ in range(num_requests):
            response = authenticated_api_client.get('/api/bots')
            assert response.status_code == 200
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Calculate throughput (requests per second)
        throughput = num_requests / total_time
        
        # Verify throughput is reasonable
        assert throughput > 10, f"Throughput {throughput} requests/sec below 10 req/sec"
        assert throughput < 1000, f"Throughput {throughput} requests/sec above 1000 req/sec (unrealistic)"
        
        # Verify total time is reasonable
        assert total_time < 10, f"Total time {total_time}s for {num_requests} requests exceeds 10s"


# Locust User class for load testing
class APIUser(HttpUser):
    """Locust user class for API load testing."""
    
    wait_time = between(1, 3)  # Wait 1-3 seconds between requests
    
    def on_start(self):
        """Setup user session."""
        # Login to get authentication token
        login_data = {
            'username': 'admin',
            'password': 'securepassword123'
        }
        response = self.client.post('/api/auth/login', json=login_data)
        if response.status_code == 200:
            data = response.json()
            self.token = data.get('token')
            self.headers = {'Authorization': f'Bearer {self.token}'}
        else:
            self.token = None
            self.headers = {}
    
    @task(3)
    def get_bots(self):
        """Get list of bots."""
        self.client.get('/api/bots', headers=self.headers)
    
    @task(2)
    def get_conversations(self):
        """Get list of conversations."""
        self.client.get('/api/conversations', headers=self.headers)
    
    @task(1)
    def get_system_status(self):
        """Get system status."""
        self.client.get('/api/system/status', headers=self.headers)
    
    @task(1)
    def health_check(self):
        """Health check endpoint."""
        self.client.get('/health')
    
    @task(1)
    def get_bot_detail(self):
        """Get specific bot details."""
        self.client.get('/api/bots/1', headers=self.headers)
    
    @task(1)
    def get_conversation_detail(self):
        """Get specific conversation details."""
        self.client.get('/api/conversations/1', headers=self.headers)






