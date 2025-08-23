#!/usr/bin/env python3
"""
Test creating a bot with automatic name generation.
"""

import json
import requests

def test_create_bot_with_auto_name():
    """Test creating a bot without providing a name (should auto-generate)."""
    print("🧪 Testing Bot Creation with Auto-Generated Name")
    print("=" * 55)
    
    # Test data for bot creation (without bot_name)
    test_data = {
        "telegram_token": "7684104886:AAHC_yil3ChAqO1ffXCHdEdXiw96jHszm6Y",
        "openai_api_key": "sk-test-fake-key-for-testing-only",
        "assistant_id": "asst_test_fake_id_for_testing",
        "group_context_limit": 15,
        "enable_ai_responses": True,
        "enable_voice_responses": False,
        "marketplace": {"enabled": False}
    }
    
    print(f"\n📝 Test data (no bot_name provided):")
    print(f"   🔑 Token: {test_data['telegram_token'][:15]}...")
    print(f"   🤖 OpenAI Key: {test_data['openai_api_key'][:20]}...")
    print(f"   📋 Assistant ID: {test_data['assistant_id'][:20]}...")
    
    # Test the API endpoint 
    print(f"\n🔗 Testing API v2 endpoint (/api/v2/bots):")
    try:
        response = requests.post(
            "http://localhost:5000/api/v2/bots",
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
            if result.get('success') and result.get('data'):
                bot_data = result['data']
                print(f"   ✅ Bot created successfully!")
                print(f"   📛 Auto-generated name: {bot_data.get('config', {}).get('bot_name', 'N/A')}")
                print(f"   🆔 Bot ID: {bot_data.get('bot_id', bot_data.get('id', 'N/A'))}")
                print(f"   📊 Status: {bot_data.get('status', 'N/A')}")
                print(f"   💬 Message: {result.get('message', 'N/A')}")
                
                # Clean up - delete the test bot
                bot_id = bot_data.get('bot_id', bot_data.get('id'))
                if bot_id:
                    delete_response = requests.delete(
                        f"http://localhost:5000/api/v2/bots/{bot_id}",
                        headers={"Authorization": "Basic YWRtaW46YWRtaW4="},
                        timeout=10
                    )
                    print(f"   🗑️ Test bot deleted (status: {delete_response.status_code})")
            else:
                print(f"   ❌ Unexpected response format: {result}")
        else:
            print(f"   ❌ Error: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Exception: {e}")
    
    print(f"\n🎉 Test completed!")


if __name__ == "__main__":
    test_create_bot_with_auto_name()
