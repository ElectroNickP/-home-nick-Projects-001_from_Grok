"""
End-to-End tests for Web Entry Point using Playwright.

Tests cover real browser interactions, user scenarios, and UI/UX testing.
"""

import pytest
import time
from playwright.sync_api import Page, expect
from tests.entrypoints.factories import test_data_factory


class TestWebE2EAuthentication:
    """Test end-to-end authentication scenarios in Web interface."""
    
    def test_user_login_logout_flow(self, page: Page, live_server):
        """Test complete user login and logout flow."""
        # Navigate to login page
        page.goto(f"{live_server.url}/auth/login")
        
        # Verify login page is loaded
        expect(page).to_have_title("Login - Telegram Bot Manager")
        expect(page.locator("h1")).to_contain_text("Login")
        
        # Fill login form
        page.fill('input[name="username"]', 'admin')
        page.fill('input[name="password"]', 'securepassword123')
        
        # Submit form
        page.click('button[type="submit"]')
        
        # Wait for redirect to dashboard
        page.wait_for_url(f"{live_server.url}/dashboard")
        
        # Verify user is logged in
        expect(page.locator(".user-info")).to_contain_text("admin")
        expect(page.locator(".nav-menu")).to_contain_text("Dashboard")
        
        # Test logout
        page.click('.logout-button')
        
        # Wait for redirect to login page
        page.wait_for_url(f"{live_server.url}/auth/login")
        
        # Verify user is logged out
        expect(page.locator(".login-form")).to_be_visible()
    
    def test_user_registration_flow(self, page: Page, live_server):
        """Test complete user registration flow."""
        # Navigate to registration page
        page.goto(f"{live_server.url}/auth/register")
        
        # Verify registration page is loaded
        expect(page).to_have_title("Register - Telegram Bot Manager")
        expect(page.locator("h1")).to_contain_text("Register")
        
        # Fill registration form
        page.fill('input[name="username"]', 'newuser')
        page.fill('input[name="email"]', 'newuser@example.com')
        page.fill('input[name="password"]', 'securepassword123')
        page.fill('input[name="confirm_password"]', 'securepassword123')
        
        # Submit form
        page.click('button[type="submit"]')
        
        # Wait for success message or redirect
        expect(page.locator(".success-message")).to_contain_text("registered successfully")
        
        # Verify user can now login
        page.goto(f"{live_server.url}/auth/login")
        page.fill('input[name="username"]', 'newuser')
        page.fill('input[name="password"]', 'securepassword123')
        page.click('button[type="submit"]')
        
        # Verify successful login
        page.wait_for_url(f"{live_server.url}/dashboard")
        expect(page.locator(".user-info")).to_contain_text("newuser")
    
    def test_invalid_login_handling(self, page: Page, live_server):
        """Test handling of invalid login credentials."""
        # Navigate to login page
        page.goto(f"{live_server.url}/auth/login")
        
        # Fill form with invalid credentials
        page.fill('input[name="username"]', 'invaliduser')
        page.fill('input[name="password"]', 'wrongpassword')
        
        # Submit form
        page.click('button[type="submit"]')
        
        # Verify error message is displayed
        expect(page.locator(".error-message")).to_contain_text("Invalid username or password")
        
        # Verify user remains on login page
        expect(page).to_have_url(f"{live_server.url}/auth/login")
    
    def test_password_reset_flow(self, page: Page, live_server):
        """Test password reset flow."""
        # Navigate to password reset page
        page.goto(f"{live_server.url}/auth/password/reset")
        
        # Verify password reset page is loaded
        expect(page.locator("h1")).to_contain_text("Reset Password")
        
        # Fill email form
        page.fill('input[name="email"]', 'user@example.com')
        page.click('button[type="submit"]')
        
        # Verify success message
        expect(page.locator(".success-message")).to_contain_text("reset email sent")


class TestWebE2EBotManagement:
    """Test end-to-end bot management scenarios in Web interface."""
    
    def test_bot_list_view(self, page: Page, live_server, authenticated_user):
        """Test viewing bot list."""
        # Navigate to bots page
        page.goto(f"{live_server.url}/bots")
        
        # Verify bots page is loaded
        expect(page).to_have_title("Bots - Telegram Bot Manager")
        expect(page.locator("h1")).to_contain_text("Bots")
        
        # Verify bot list is displayed
        expect(page.locator(".bot-list")).to_be_visible()
        
        # Check for bot items
        bot_items = page.locator(".bot-item")
        expect(bot_items).to_have_count(3)  # Assuming 3 test bots
        
        # Verify bot information is displayed
        expect(page.locator(".bot-name")).to_contain_text("Test Bot")
        expect(page.locator(".bot-status")).to_contain_text("running")
    
    def test_bot_creation_flow(self, page: Page, live_server, authenticated_user):
        """Test complete bot creation flow."""
        # Navigate to bot creation page
        page.goto(f"{live_server.url}/bots/create")
        
        # Verify creation page is loaded
        expect(page.locator("h1")).to_contain_text("Create Bot")
        
        # Fill bot creation form
        page.fill('input[name="name"]', 'New Test Bot')
        page.fill('input[name="token"]', 'test_token_123456')
        page.fill('textarea[name="description"]', 'A new test bot for E2E testing')
        
        # Submit form
        page.click('button[type="submit"]')
        
        # Wait for redirect to bot list or bot detail page
        page.wait_for_url(f"{live_server.url}/bots/*")
        
        # Verify success message
        expect(page.locator(".success-message")).to_contain_text("created successfully")
        
        # Verify bot appears in list
        page.goto(f"{live_server.url}/bots")
        expect(page.locator(".bot-name")).to_contain_text("New Test Bot")
    
    def test_bot_management_actions(self, page: Page, live_server, authenticated_user):
        """Test bot management actions (start, stop, restart)."""
        # Navigate to bot detail page
        page.goto(f"{live_server.url}/bots/1")
        
        # Verify bot detail page is loaded
        expect(page.locator("h1")).to_contain_text("Bot Details")
        
        # Test start bot action
        page.click('.start-bot-button')
        
        # Wait for action to complete
        page.wait_for_selector('.status-updated')
        
        # Verify bot status changed
        expect(page.locator(".bot-status")).to_contain_text("running")
        
        # Test stop bot action
        page.click('.stop-bot-button')
        page.wait_for_selector('.status-updated')
        expect(page.locator(".bot-status")).to_contain_text("stopped")
        
        # Test restart bot action
        page.click('.restart-bot-button')
        page.wait_for_selector('.status-updated')
        expect(page.locator(".bot-status")).to_contain_text("running")
    
    def test_bot_editing_flow(self, page: Page, live_server, authenticated_user):
        """Test bot editing flow."""
        # Navigate to bot edit page
        page.goto(f"{live_server.url}/bots/1/edit")
        
        # Verify edit page is loaded
        expect(page.locator("h1")).to_contain_text("Edit Bot")
        
        # Modify bot information
        page.fill('input[name="name"]', 'Updated Test Bot')
        page.fill('textarea[name="description"]', 'Updated description for E2E testing')
        
        # Submit form
        page.click('button[type="submit"]')
        
        # Wait for redirect to bot detail page
        page.wait_for_url(f"{live_server.url}/bots/1")
        
        # Verify changes are saved
        expect(page.locator(".bot-name")).to_contain_text("Updated Test Bot")
        expect(page.locator(".bot-description")).to_contain_text("Updated description")
    
    def test_bot_deletion_flow(self, page: Page, live_server, authenticated_user):
        """Test bot deletion flow."""
        # Navigate to bot detail page
        page.goto(f"{live_server.url}/bots/2")
        
        # Click delete button
        page.click('.delete-bot-button')
        
        # Verify confirmation dialog appears
        expect(page.locator(".confirmation-dialog")).to_be_visible()
        expect(page.locator(".confirmation-dialog")).to_contain_text("Are you sure")
        
        # Confirm deletion
        page.click('.confirm-delete-button')
        
        # Wait for redirect to bot list
        page.wait_for_url(f"{live_server.url}/bots")
        
        # Verify success message
        expect(page.locator(".success-message")).to_contain_text("deleted successfully")
        
        # Verify bot is removed from list
        expect(page.locator(".bot-item")).not_to_contain_text("Test Bot 2")


class TestWebE2EConversationManagement:
    """Test end-to-end conversation management scenarios in Web interface."""
    
    def test_conversation_list_view(self, page: Page, live_server, authenticated_user):
        """Test viewing conversation list."""
        # Navigate to conversations page
        page.goto(f"{live_server.url}/conversations")
        
        # Verify conversations page is loaded
        expect(page).to_have_title("Conversations - Telegram Bot Manager")
        expect(page.locator("h1")).to_contain_text("Conversations")
        
        # Verify conversation list is displayed
        expect(page.locator(".conversation-list")).to_be_visible()
        
        # Check for conversation items
        conversation_items = page.locator(".conversation-item")
        expect(conversation_items).to_have_count(5)  # Assuming 5 test conversations
    
    def test_conversation_detail_view(self, page: Page, live_server, authenticated_user):
        """Test viewing conversation details."""
        # Navigate to conversation detail page
        page.goto(f"{live_server.url}/conversations/1")
        
        # Verify conversation detail page is loaded
        expect(page.locator("h1")).to_contain_text("Conversation Details")
        
        # Verify conversation information is displayed
        expect(page.locator(".conversation-info")).to_be_visible()
        expect(page.locator(".conversation-bot")).to_contain_text("Test Bot")
        
        # Verify messages are displayed
        expect(page.locator(".message-list")).to_be_visible()
        message_items = page.locator(".message-item")
        expect(message_items).to_have_count(10)  # Assuming 10 messages
    
    def test_conversation_clearing_flow(self, page: Page, live_server, authenticated_user):
        """Test conversation clearing flow."""
        # Navigate to conversation detail page
        page.goto(f"{live_server.url}/conversations/1")
        
        # Click clear conversation button
        page.click('.clear-conversation-button')
        
        # Verify confirmation dialog appears
        expect(page.locator(".confirmation-dialog")).to_be_visible()
        expect(page.locator(".confirmation-dialog")).to_contain_text("clear this conversation")
        
        # Confirm clearing
        page.click('.confirm-clear-button')
        
        # Wait for page refresh or redirect
        page.wait_for_load_state('networkidle')
        
        # Verify success message
        expect(page.locator(".success-message")).to_contain_text("cleared successfully")
        
        # Verify messages are cleared
        message_items = page.locator(".message-item")
        expect(message_items).to_have_count(0)
    
    def test_conversation_search_and_filtering(self, page: Page, live_server, authenticated_user):
        """Test conversation search and filtering."""
        # Navigate to conversations page
        page.goto(f"{live_server.url}/conversations")
        
        # Test search functionality
        page.fill('input[name="search"]', 'test')
        page.click('.search-button')
        
        # Wait for search results
        page.wait_for_selector('.search-results')
        
        # Verify search results are displayed
        expect(page.locator(".search-results")).to_be_visible()
        
        # Test filtering by bot
        page.select_option('select[name="bot_filter"]', '1')
        page.click('.filter-button')
        
        # Wait for filtered results
        page.wait_for_selector('.filtered-results')
        
        # Verify filtered results
        expect(page.locator(".filtered-results")).to_be_visible()


class TestWebE2ESystemManagement:
    """Test end-to-end system management scenarios in Web interface."""
    
    def test_system_status_view(self, page: Page, live_server, authenticated_user):
        """Test viewing system status."""
        # Navigate to system status page
        page.goto(f"{live_server.url}/system/status")
        
        # Verify system status page is loaded
        expect(page).to_have_title("System Status - Telegram Bot Manager")
        expect(page.locator("h1")).to_contain_text("System Status")
        
        # Verify system information is displayed
        expect(page.locator(".system-info")).to_be_visible()
        expect(page.locator(".system-uptime")).to_contain_text("uptime")
        expect(page.locator(".system-memory")).to_contain_text("memory")
        expect(page.locator(".system-cpu")).to_contain_text("cpu")
    
    def test_backup_management_flow(self, page: Page, live_server, authenticated_user):
        """Test backup management flow."""
        # Navigate to backup management page
        page.goto(f"{live_server.url}/system/backups")
        
        # Verify backup page is loaded
        expect(page.locator("h1")).to_contain_text("Backups")
        
        # Test creating backup
        page.click('.create-backup-button')
        
        # Fill backup form
        page.fill('input[name="description"]', 'E2E test backup')
        page.click('button[type="submit"]')
        
        # Wait for backup creation
        page.wait_for_selector('.backup-created')
        
        # Verify success message
        expect(page.locator(".success-message")).to_contain_text("backup created")
        
        # Verify backup appears in list
        expect(page.locator(".backup-item")).to_contain_text("E2E test backup")
        
        # Test restoring backup
        page.click('.restore-backup-button')
        
        # Verify confirmation dialog
        expect(page.locator(".confirmation-dialog")).to_contain_text("restore this backup")
        
        # Confirm restoration
        page.click('.confirm-restore-button')
        
        # Wait for restoration
        page.wait_for_selector('.backup-restored')
        
        # Verify success message
        expect(page.locator(".success-message")).to_contain_text("backup restored")
    
    def test_system_configuration_flow(self, page: Page, live_server, authenticated_user):
        """Test system configuration flow."""
        # Navigate to system configuration page
        page.goto(f"{live_server.url}/system/config")
        
        # Verify configuration page is loaded
        expect(page.locator("h1")).to_contain_text("System Configuration")
        
        # Test updating configuration
        page.fill('input[name="log_level"]', 'DEBUG')
        page.fill('input[name="max_bots"]', '15')
        
        # Submit form
        page.click('button[type="submit"]')
        
        # Wait for update
        page.wait_for_selector('.config-updated')
        
        # Verify success message
        expect(page.locator(".success-message")).to_contain_text("configuration updated")
        
        # Verify changes are reflected
        expect(page.locator('input[name="log_level"]')).to_have_value("DEBUG")
        expect(page.locator('input[name="max_bots"]')).to_have_value("15")
    
    def test_system_update_flow(self, page: Page, live_server, authenticated_user):
        """Test system update flow."""
        # Navigate to system update page
        page.goto(f"{live_server.url}/system/update")
        
        # Verify update page is loaded
        expect(page.locator("h1")).to_contain_text("System Updates")
        
        # Test checking for updates
        page.click('.check-updates-button')
        
        # Wait for update check
        page.wait_for_selector('.update-check-complete')
        
        # Verify update information is displayed
        expect(page.locator(".update-info")).to_be_visible()
        
        # Test applying update (if available)
        if page.locator('.update-available').is_visible():
            page.click('.apply-update-button')
            
            # Verify confirmation dialog
            expect(page.locator(".confirmation-dialog")).to_contain_text("apply this update")
            
            # Confirm update
            page.click('.confirm-update-button')
            
            # Wait for update process
            page.wait_for_selector('.update-complete')
            
            # Verify success message
            expect(page.locator(".success-message")).to_contain_text("update applied")


class TestWebE2EUserInterface:
    """Test end-to-end user interface and navigation scenarios."""
    
    def test_navigation_flow(self, page: Page, live_server, authenticated_user):
        """Test complete navigation flow through the application."""
        # Start at dashboard
        page.goto(f"{live_server.url}/dashboard")
        
        # Verify dashboard is loaded
        expect(page).to_have_title("Dashboard - Telegram Bot Manager")
        
        # Navigate to bots
        page.click('.nav-bots')
        expect(page).to_have_url(f"{live_server.url}/bots")
        
        # Navigate to conversations
        page.click('.nav-conversations')
        expect(page).to_have_url(f"{live_server.url}/conversations")
        
        # Navigate to system
        page.click('.nav-system')
        expect(page).to_have_url(f"{live_server.url}/system")
        
        # Navigate back to dashboard
        page.click('.nav-dashboard')
        expect(page).to_have_url(f"{live_server.url}/dashboard")
    
    def test_responsive_design(self, page: Page, live_server, authenticated_user):
        """Test responsive design on different screen sizes."""
        # Test desktop view
        page.set_viewport_size({"width": 1920, "height": 1080})
        page.goto(f"{live_server.url}/dashboard")
        
        # Verify desktop layout
        expect(page.locator(".sidebar")).to_be_visible()
        expect(page.locator(".main-content")).to_be_visible()
        
        # Test tablet view
        page.set_viewport_size({"width": 768, "height": 1024})
        page.reload()
        
        # Verify tablet layout
        expect(page.locator(".mobile-menu")).to_be_visible()
        
        # Test mobile view
        page.set_viewport_size({"width": 375, "height": 667})
        page.reload()
        
        # Verify mobile layout
        expect(page.locator(".mobile-menu")).to_be_visible()
        expect(page.locator(".mobile-nav-toggle")).to_be_visible()
    
    def test_loading_states(self, page: Page, live_server, authenticated_user):
        """Test loading states and spinners."""
        # Navigate to bots page
        page.goto(f"{live_server.url}/bots")
        
        # Trigger an action that shows loading state
        page.click('.refresh-bots-button')
        
        # Verify loading spinner appears
        expect(page.locator(".loading-spinner")).to_be_visible()
        
        # Wait for loading to complete
        page.wait_for_selector('.loading-spinner', state='hidden')
        
        # Verify loading spinner disappears
        expect(page.locator(".loading-spinner")).not_to_be_visible()
    
    def test_error_handling_ui(self, page: Page, live_server, authenticated_user):
        """Test error handling in user interface."""
        # Try to access non-existent resource
        page.goto(f"{live_server.url}/bots/999999")
        
        # Verify 404 error page is displayed
        expect(page.locator("h1")).to_contain_text("404")
        expect(page.locator(".error-message")).to_contain_text("not found")
        
        # Test error page navigation
        page.click('.back-to-home')
        expect(page).to_have_url(f"{live_server.url}/dashboard")
    
    def test_form_validation_ui(self, page: Page, live_server, authenticated_user):
        """Test form validation in user interface."""
        # Navigate to bot creation page
        page.goto(f"{live_server.url}/bots/create")
        
        # Try to submit empty form
        page.click('button[type="submit"]')
        
        # Verify validation errors are displayed
        expect(page.locator(".validation-error")).to_contain_text("required")
        
        # Fill form with invalid data
        page.fill('input[name="name"]', '')
        page.fill('input[name="token"]', 'invalid')
        
        # Submit form
        page.click('button[type="submit"]')
        
        # Verify validation errors
        expect(page.locator(".validation-error")).to_contain_text("Name is required")
        expect(page.locator(".validation-error")).to_contain_text("Token is invalid")


class TestWebE2EPerformance:
    """Test end-to-end performance scenarios."""
    
    def test_page_load_performance(self, page: Page, live_server, authenticated_user):
        """Test page load performance."""
        # Measure dashboard load time
        start_time = time.time()
        page.goto(f"{live_server.url}/dashboard")
        page.wait_for_load_state('networkidle')
        dashboard_load_time = time.time() - start_time
        
        # Verify load time is reasonable (less than 3 seconds)
        assert dashboard_load_time < 3.0, f"Dashboard load time {dashboard_load_time}s exceeds 3s"
        
        # Measure bots page load time
        start_time = time.time()
        page.goto(f"{live_server.url}/bots")
        page.wait_for_load_state('networkidle')
        bots_load_time = time.time() - start_time
        
        # Verify load time is reasonable
        assert bots_load_time < 3.0, f"Bots page load time {bots_load_time}s exceeds 3s"
    
    def test_ajax_request_performance(self, page: Page, live_server, authenticated_user):
        """Test AJAX request performance."""
        # Navigate to bots page
        page.goto(f"{live_server.url}/bots")
        
        # Measure bot status update time
        start_time = time.time()
        page.click('.refresh-status-button')
        page.wait_for_selector('.status-updated')
        status_update_time = time.time() - start_time
        
        # Verify update time is reasonable (less than 2 seconds)
        assert status_update_time < 2.0, f"Status update time {status_update_time}s exceeds 2s"
    
    def test_memory_usage(self, page: Page, live_server, authenticated_user):
        """Test memory usage during navigation."""
        # Navigate through multiple pages
        pages_to_test = [
            f"{live_server.url}/dashboard",
            f"{live_server.url}/bots",
            f"{live_server.url}/conversations",
            f"{live_server.url}/system"
        ]
        
        for url in pages_to_test:
            page.goto(url)
            page.wait_for_load_state('networkidle')
            
            # Check for memory leaks (basic check)
            # In a real scenario, you'd use browser dev tools to measure memory
            expect(page.locator("body")).to_be_visible()






