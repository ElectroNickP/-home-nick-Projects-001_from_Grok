#!/usr/bin/env python3
"""
Test script for automatic bot name generation during bot creation.
"""

import json
import requests

def test_auto_bot_name_api():
    """Test automatic bot name generation via API."""
    print("🧪 Testing Automatic Bot Name Generation via API")
    print("=" * 55)
    
    # Test data for bot creation (without bot_name)
    test_data = {
        "telegram_token": "7684104886:AAHC_yil3ChAqO1ffXCHdEdXiw96jHszm6Y",
        "openai_api_key": "sk-test-fake-key",
        "assistant_id": "asst_test_fake_id",
        "group_context_limit": 15,
        "enable_ai_responses": True,
        "enable_voice_responses": False,
        "marketplace": {"enabled": False}
    }
    
    print(f"\n📝 Test data (without bot_name):")
    print(f"   🔑 Token: {test_data['telegram_token'][:15]}...")
    print(f"   🤖 OpenAI Key: {test_data['openai_api_key'][:10]}...")
    print(f"   📋 Assistant ID: {test_data['assistant_id']}")
    
    # Test with legacy API endpoint
    print(f"\n🔗 Testing legacy API endpoint (/api/bots):")
    try:
        response = requests.post(
            "http://localhost:5000/api/bots",
            headers={
                "Content-Type": "application/json",
                "Authorization": "Basic YWRtaW46YWRtaW4="  # admin:admin base64
            },
            json=test_data,
            timeout=10
        )
        
        print(f"   📊 Status: {response.status_code}")
        
        if response.status_code == 201:
            result = response.json()
            print(f"   ✅ Bot created successfully!")
            print(f"   📛 Auto-generated name: {result.get('config', {}).get('bot_name', 'N/A')}")
            print(f"   🆔 Bot ID: {result.get('id', 'N/A')}")
        else:
            print(f"   ❌ Error: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Exception: {e}")
    
    print(f"\n🎉 Test completed!")


def test_telegram_validation_endpoint():
    """Test the Telegram token validation endpoint directly."""
    print("\n🧪 Testing Telegram Token Validation Endpoint")
    print("=" * 50)
    
    test_token = "7684104886:AAHC_yil3ChAqO1ffXCHdEdXiw96jHszm6Y"
    
    print(f"\n🔍 Testing token validation endpoint:")
    print(f"   🔑 Token: {test_token[:15]}...")
    
    try:
        # Try without authentication first (should fail)
        response = requests.post(
            "http://localhost:5000/api/v2/telegram/validate-token",
            headers={"Content-Type": "application/json"},
            json={"token": test_token},
            timeout=10
        )
        
        print(f"   📊 Status (no auth): {response.status_code}")
        if response.status_code == 401:
            print(f"   ✅ Authentication required (as expected)")
        
        # Try with basic auth
        response = requests.post(
            "http://localhost:5000/api/v2/telegram/validate-token",
            headers={
                "Content-Type": "application/json",
                "Authorization": "Basic YWRtaW46YWRtaW4="  # admin:admin base64
            },
            json={"token": test_token},
            timeout=10
        )
        
        print(f"   📊 Status (with auth): {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Token validation successful!")
            if result.get('status') == 'success' and result.get('data'):
                bot_info = result['data']
                print(f"   📛 Display name: {bot_info.get('display_name', 'N/A')}")
                print(f"   👤 Username: {bot_info.get('username', 'N/A')}")
                print(f"   🤖 Valid: {bot_info.get('valid', 'N/A')}")
        else:
            print(f"   ❌ Error: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Exception: {e}")


if __name__ == "__main__":
    test_telegram_validation_endpoint()
    # Note: Not running test_auto_bot_name_api() to avoid creating duplicate bots
    print("\n💡 Tip: Open http://localhost:5000/ to test the web interface manually")






