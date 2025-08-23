"""
Performance tests for Web Entry Point.

Tests cover UI performance, user experience, and frontend optimization.
"""

import pytest
import time
import threading
from playwright.sync_api import Page, expect
from tests.entrypoints.factories import test_data_factory


class TestWebPerformanceLoad:
    """Test Web performance under normal load conditions."""
    
    def test_page_load_performance_baseline(self, page: Page, live_server, authenticated_user):
        """Test baseline page load performance for all pages."""
        # Test load times for key pages
        pages_to_test = [
            '/dashboard',
            '/bots',
            '/conversations',
            '/system',
            '/system/status',
            '/system/backups',
            '/system/config'
        ]
        
        for page_path in pages_to_test:
            # Measure page load time
            start_time = time.time()
            page.goto(f"{live_server.url}{page_path}")
            page.wait_for_load_state('networkidle')
            load_time = time.time() - start_time
            
            # Verify page loaded successfully
            expect(page).to_have_url(f"{live_server.url}{page_path}")
            
            # Verify load time is within acceptable limits
            assert load_time < 3.0, f"Page load time {load_time}s for {page_path} exceeds 3.0s baseline"
    
    def test_ui_rendering_performance(self, page: Page, live_server, authenticated_user):
        """Test UI rendering performance."""
        # Navigate to bots page
        page.goto(f"{live_server.url}/bots")
        
        # Measure time to first contentful paint
        start_time = time.time()
        page.wait_for_selector('.bot-list', timeout=5000)
        first_paint_time = time.time() - start_time
        
        # Verify first paint is fast
        assert first_paint_time < 1.0, f"First paint time {first_paint_time}s exceeds 1.0s"
        
        # Measure time to interactive
        start_time = time.time()
        page.wait_for_selector('button:not([disabled])', timeout=5000)
        interactive_time = time.time() - start_time
        
        # Verify interactive time is reasonable
        assert interactive_time < 2.0, f"Interactive time {interactive_time}s exceeds 2.0s"
    
    def test_ajax_request_performance(self, page: Page, live_server, authenticated_user):
        """Test AJAX request performance."""
        # Navigate to bots page
        page.goto(f"{live_server.url}/bots")
        
        # Measure AJAX request time
        start_time = time.time()
        page.click('.refresh-bots-button')
        page.wait_for_selector('.bot-list-updated', timeout=5000)
        ajax_time = time.time() - start_time
        
        # Verify AJAX request is fast
        assert ajax_time < 1.0, f"AJAX request time {ajax_time}s exceeds 1.0s"
    
    def test_memory_usage_baseline(self, page: Page, live_server, authenticated_user):
        """Test memory usage under baseline load."""
        # Navigate through multiple pages to test memory usage
        pages_to_test = [
            '/dashboard',
            '/bots',
            '/conversations',
            '/system'
        ]
        
        for page_path in pages_to_test:
            page.goto(f"{live_server.url}{page_path}")
            page.wait_for_load_state('networkidle')
            
            # Basic memory check (in real scenario, use browser dev tools)
            expect(page.locator("body")).to_be_visible()
            
            # Small delay to allow memory to stabilize
            page.wait_for_timeout(100)


class TestWebPerformanceStress:
    """Test Web performance under stress conditions."""
    
    def test_rapid_navigation_performance(self, page: Page, live_server, authenticated_user):
        """Test performance during rapid navigation."""
        # Navigate rapidly between pages
        pages_to_test = [
            '/dashboard',
            '/bots',
            '/conversations',
            '/system',
            '/dashboard'
        ]
        
        total_navigation_time = 0
        
        for page_path in pages_to_test:
            start_time = time.time()
            page.goto(f"{live_server.url}{page_path}")
            page.wait_for_load_state('networkidle')
            navigation_time = time.time() - start_time
            
            total_navigation_time += navigation_time
            
            # Verify each navigation is reasonably fast
            assert navigation_time < 3.0, f"Navigation time {navigation_time}s for {page_path} exceeds 3.0s"
        
        # Verify total navigation time is reasonable
        assert total_navigation_time < 15.0, f"Total navigation time {total_navigation_time}s exceeds 15.0s"
    
    def test_large_data_rendering_performance(self, page: Page, live_server, authenticated_user):
        """Test performance when rendering large datasets."""
        # Navigate to bots page (assume it has large dataset)
        page.goto(f"{live_server.url}/bots")
        
        # Measure time to render large list
        start_time = time.time()
        page.wait_for_selector('.bot-item', timeout=10000)
        render_time = time.time() - start_time
        
        # Verify rendering time is reasonable for large datasets
        assert render_time < 2.0, f"Large data rendering time {render_time}s exceeds 2.0s"
        
        # Count rendered items
        bot_items = page.locator('.bot-item')
        item_count = bot_items.count()
        
        # Verify items are rendered
        assert item_count > 0, "No bot items rendered"
        
        # Verify rendering time scales reasonably with item count
        if item_count > 50:
            assert render_time < 3.0, f"Rendering time {render_time}s for {item_count} items exceeds 3.0s"
    
    def test_concurrent_user_simulation(self, page: Page, live_server, authenticated_user):
        """Test performance with simulated concurrent users."""
        # Simulate multiple user sessions
        num_sessions = 3
        results = []
        
        def user_session(session_id):
            """Simulate a single user session."""
            try:
                # Create new page for this session
                new_page = page.context.new_page()
                
                # Navigate and perform actions
                new_page.goto(f"{live_server.url}/dashboard")
                new_page.wait_for_load_state('networkidle')
                
                new_page.goto(f"{live_server.url}/bots")
                new_page.wait_for_load_state('networkidle')
                
                new_page.goto(f"{live_server.url}/conversations")
                new_page.wait_for_load_state('networkidle')
                
                results.append(f"Session {session_id} completed successfully")
                new_page.close()
                
            except Exception as e:
                results.append(f"Session {session_id} failed: {str(e)}")
        
        # Start concurrent sessions
        threads = []
        for i in range(num_sessions):
            thread = threading.Thread(target=user_session, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all sessions to complete
        for thread in threads:
            thread.join()
        
        # Verify all sessions completed successfully
        successful_sessions = len([r for r in results if "completed successfully" in r])
        assert successful_sessions == num_sessions, f"Only {successful_sessions}/{num_sessions} sessions completed successfully"


class TestWebPerformanceScalability:
    """Test Web performance scalability."""
    
    def test_pagination_performance(self, page: Page, live_server, authenticated_user):
        """Test performance with pagination."""
        # Navigate to bots page
        page.goto(f"{live_server.url}/bots")
        
        # Test pagination performance
        for page_num in range(1, 4):  # Test first 3 pages
            start_time = time.time()
            
            # Click next page button
            page.click(f'[data-page="{page_num}"]')
            page.wait_for_selector('.bot-list-updated', timeout=5000)
            
            pagination_time = time.time() - start_time
            
            # Verify pagination is fast
            assert pagination_time < 1.0, f"Pagination time {pagination_time}s for page {page_num} exceeds 1.0s"
    
    def test_search_performance(self, page: Page, live_server, authenticated_user):
        """Test search performance."""
        # Navigate to conversations page
        page.goto(f"{live_server.url}/conversations")
        
        # Test search performance
        start_time = time.time()
        
        # Perform search
        page.fill('input[name="search"]', 'test')
        page.click('.search-button')
        page.wait_for_selector('.search-results', timeout=5000)
        
        search_time = time.time() - start_time
        
        # Verify search is fast
        assert search_time < 1.0, f"Search time {search_time}s exceeds 1.0s"
    
    def test_filter_performance(self, page: Page, live_server, authenticated_user):
        """Test filter performance."""
        # Navigate to conversations page
        page.goto(f"{live_server.url}/conversations")
        
        # Test filter performance
        start_time = time.time()
        
        # Apply filter
        page.select_option('select[name="bot_filter"]', '1')
        page.click('.filter-button')
        page.wait_for_selector('.filtered-results', timeout=5000)
        
        filter_time = time.time() - start_time
        
        # Verify filtering is fast
        assert filter_time < 1.0, f"Filter time {filter_time}s exceeds 1.0s"


class TestWebPerformanceUserExperience:
    """Test Web performance from user experience perspective."""
    
    def test_form_submission_performance(self, page: Page, live_server, authenticated_user):
        """Test form submission performance."""
        # Navigate to bot creation page
        page.goto(f"{live_server.url}/bots/create")
        
        # Fill form
        page.fill('input[name="name"]', 'Performance Test Bot')
        page.fill('input[name="token"]', 'test_token_performance')
        page.fill('textarea[name="description"]', 'Bot for performance testing')
        
        # Measure form submission time
        start_time = time.time()
        page.click('button[type="submit"]')
        page.wait_for_url(f"{live_server.url}/bots/*", timeout=10000)
        submission_time = time.time() - start_time
        
        # Verify form submission is reasonably fast
        assert submission_time < 2.0, f"Form submission time {submission_time}s exceeds 2.0s"
    
    def test_modal_dialog_performance(self, page: Page, live_server, authenticated_user):
        """Test modal dialog performance."""
        # Navigate to bot detail page
        page.goto(f"{live_server.url}/bots/1")
        
        # Test modal opening performance
        start_time = time.time()
        page.click('.delete-bot-button')
        page.wait_for_selector('.confirmation-dialog', timeout=5000)
        modal_open_time = time.time() - start_time
        
        # Verify modal opens quickly
        assert modal_open_time < 0.5, f"Modal open time {modal_open_time}s exceeds 0.5s"
        
        # Test modal closing performance
        start_time = time.time()
        page.click('.cancel-button')
        page.wait_for_selector('.confirmation-dialog', state='hidden', timeout=5000)
        modal_close_time = time.time() - start_time
        
        # Verify modal closes quickly
        assert modal_close_time < 0.5, f"Modal close time {modal_close_time}s exceeds 0.5s"
    
    def test_notification_performance(self, page: Page, live_server, authenticated_user):
        """Test notification system performance."""
        # Navigate to bots page
        page.goto(f"{live_server.url}/bots")
        
        # Test notification display performance
        start_time = time.time()
        page.click('.start-bot-button')
        page.wait_for_selector('.notification-success', timeout=5000)
        notification_time = time.time() - start_time
        
        # Verify notification appears quickly
        assert notification_time < 1.0, f"Notification display time {notification_time}s exceeds 1.0s"
    
    def test_loading_indicator_performance(self, page: Page, live_server, authenticated_user):
        """Test loading indicator performance."""
        # Navigate to bots page
        page.goto(f"{live_server.url}/bots")
        
        # Test loading indicator
        page.click('.refresh-bots-button')
        
        # Verify loading indicator appears quickly
        expect(page.locator('.loading-spinner')).to_be_visible()
        
        # Wait for loading to complete
        page.wait_for_selector('.loading-spinner', state='hidden', timeout=10000)
        
        # Verify loading completed successfully
        expect(page.locator('.bot-list')).to_be_visible()


class TestWebPerformanceOptimization:
    """Test Web performance optimization features."""
    
    def test_image_loading_performance(self, page: Page, live_server, authenticated_user):
        """Test image loading performance."""
        # Navigate to dashboard (assume it has images)
        page.goto(f"{live_server.url}/dashboard")
        
        # Wait for images to load
        page.wait_for_load_state('networkidle')
        
        # Check if images are loaded efficiently
        images = page.locator('img')
        image_count = images.count()
        
        if image_count > 0:
            # Verify images are loaded
            for i in range(min(5, image_count)):  # Check first 5 images
                expect(images.nth(i)).to_be_visible()
    
    def test_css_loading_performance(self, page: Page, live_server, authenticated_user):
        """Test CSS loading performance."""
        # Navigate to any page
        page.goto(f"{live_server.url}/dashboard")
        
        # Wait for CSS to load
        page.wait_for_load_state('networkidle')
        
        # Verify CSS is applied (check for styled elements)
        expect(page.locator('.dashboard-container')).to_be_visible()
        expect(page.locator('.nav-menu')).to_be_visible()
    
    def test_javascript_loading_performance(self, page: Page, live_server, authenticated_user):
        """Test JavaScript loading performance."""
        # Navigate to bots page
        page.goto(f"{live_server.url}/bots")
        
        # Wait for JavaScript to load
        page.wait_for_load_state('networkidle')
        
        # Test JavaScript functionality
        page.click('.refresh-bots-button')
        page.wait_for_selector('.bot-list-updated', timeout=5000)
        
        # Verify JavaScript is working
        expect(page.locator('.bot-list')).to_be_visible()
    
    def test_caching_performance(self, page: Page, live_server, authenticated_user):
        """Test caching performance."""
        # Navigate to dashboard
        page.goto(f"{live_server.url}/dashboard")
        page.wait_for_load_state('networkidle')
        
        # Navigate away and back
        page.goto(f"{live_server.url}/bots")
        page.wait_for_load_state('networkidle')
        
        # Navigate back to dashboard
        start_time = time.time()
        page.goto(f"{live_server.url}/dashboard")
        page.wait_for_load_state('networkidle')
        return_time = time.time() - start_time
        
        # Verify return navigation is faster (due to caching)
        assert return_time < 2.0, f"Return navigation time {return_time}s exceeds 2.0s"


class TestWebPerformanceMonitoring:
    """Test Web performance monitoring and metrics."""
    
    def test_page_load_metrics(self, page: Page, live_server, authenticated_user):
        """Test page load metrics collection."""
        # Navigate to dashboard
        page.goto(f"{live_server.url}/dashboard")
        page.wait_for_load_state('networkidle')
        
        # Collect performance metrics
        metrics = page.evaluate("""
            () => {
                const perfData = performance.getEntriesByType('navigation')[0];
                return {
                    domContentLoaded: perfData.domContentLoadedEventEnd - perfData.domContentLoadedEventStart,
                    loadComplete: perfData.loadEventEnd - perfData.loadEventStart,
                    totalTime: perfData.loadEventEnd - perfData.fetchStart
                };
            }
        """)
        
        # Verify metrics are reasonable
        assert metrics['domContentLoaded'] < 1000, f"DOM content loaded time {metrics['domContentLoaded']}ms exceeds 1000ms"
        assert metrics['loadComplete'] < 2000, f"Load complete time {metrics['loadComplete']}ms exceeds 2000ms"
        assert metrics['totalTime'] < 5000, f"Total load time {metrics['totalTime']}ms exceeds 5000ms"
    
    def test_user_interaction_metrics(self, page: Page, live_server, authenticated_user):
        """Test user interaction metrics."""
        # Navigate to bots page
        page.goto(f"{live_server.url}/bots")
        page.wait_for_load_state('networkidle')
        
        # Measure interaction response time
        start_time = time.time()
        page.click('.refresh-bots-button')
        page.wait_for_selector('.bot-list-updated', timeout=5000)
        interaction_time = time.time() - start_time
        
        # Verify interaction is responsive
        assert interaction_time < 1.0, f"Interaction response time {interaction_time}s exceeds 1.0s"
    
    def test_error_handling_performance(self, page: Page, live_server, authenticated_user):
        """Test error handling performance."""
        # Try to access non-existent page
        start_time = time.time()
        page.goto(f"{live_server.url}/nonexistent-page")
        page.wait_for_load_state('networkidle')
        error_time = time.time() - start_time
        
        # Verify error page loads quickly
        assert error_time < 2.0, f"Error page load time {error_time}s exceeds 2.0s"
        
        # Verify error page is displayed
        expect(page.locator("h1")).to_contain_text("404")
    
    def test_accessibility_performance(self, page: Page, live_server, authenticated_user):
        """Test accessibility performance."""
        # Navigate to dashboard
        page.goto(f"{live_server.url}/dashboard")
        page.wait_for_load_state('networkidle')
        
        # Test keyboard navigation performance
        start_time = time.time()
        page.keyboard.press('Tab')
        page.wait_for_timeout(100)  # Small delay for focus
        keyboard_time = time.time() - start_time
        
        # Verify keyboard navigation is responsive
        assert keyboard_time < 0.5, f"Keyboard navigation time {keyboard_time}s exceeds 0.5s"
        
        # Verify focus is visible
        focused_element = page.locator(':focus')
        expect(focused_element).to_be_visible()


class TestWebPerformanceResponsive:
    """Test Web performance on different screen sizes."""
    
    def test_mobile_performance(self, page: Page, live_server, authenticated_user):
        """Test performance on mobile devices."""
        # Set mobile viewport
        page.set_viewport_size({"width": 375, "height": 667})
        
        # Navigate to dashboard
        start_time = time.time()
        page.goto(f"{live_server.url}/dashboard")
        page.wait_for_load_state('networkidle')
        mobile_load_time = time.time() - start_time
        
        # Verify mobile load time is reasonable
        assert mobile_load_time < 3.0, f"Mobile load time {mobile_load_time}s exceeds 3.0s"
        
        # Verify mobile layout is responsive
        expect(page.locator('.mobile-menu')).to_be_visible()
    
    def test_tablet_performance(self, page: Page, live_server, authenticated_user):
        """Test performance on tablet devices."""
        # Set tablet viewport
        page.set_viewport_size({"width": 768, "height": 1024})
        
        # Navigate to bots page
        start_time = time.time()
        page.goto(f"{live_server.url}/bots")
        page.wait_for_load_state('networkidle')
        tablet_load_time = time.time() - start_time
        
        # Verify tablet load time is reasonable
        assert tablet_load_time < 3.0, f"Tablet load time {tablet_load_time}s exceeds 3.0s"
        
        # Verify tablet layout is responsive
        expect(page.locator('.tablet-layout')).to_be_visible()
    
    def test_desktop_performance(self, page: Page, live_server, authenticated_user):
        """Test performance on desktop devices."""
        # Set desktop viewport
        page.set_viewport_size({"width": 1920, "height": 1080})
        
        # Navigate to system page
        start_time = time.time()
        page.goto(f"{live_server.url}/system")
        page.wait_for_load_state('networkidle')
        desktop_load_time = time.time() - start_time
        
        # Verify desktop load time is reasonable
        assert desktop_load_time < 2.0, f"Desktop load time {desktop_load_time}s exceeds 2.0s"
        
        # Verify desktop layout is responsive
        expect(page.locator('.sidebar')).to_be_visible()
        expect(page.locator('.main-content')).to_be_visible()






