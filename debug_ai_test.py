import requests
import json
from datetime import datetime

def test_ai_endpoints():
    # First authenticate
    test_email = f"test_{datetime.now().strftime('%H%M%S')}@example.com"
    register_data = {
        "email": test_email,
        "password": "TestPass123!",
        "name": "Test User"
    }
    
    print("🔐 Authenticating...")
    response = requests.post(
        "https://test-agents-hub.preview.emergentagent.com/api/auth/register",
        json=register_data,
        headers={'Content-Type': 'application/json'},
        timeout=10
    )
    
    if response.status_code != 200:
        print(f"❌ Authentication failed: {response.text}")
        return
    
    token = response.json()['token']
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}'
    }
    
    print("✅ Authentication successful")
    
    # Test AI recommendations
    print("\n🤖 Testing AI Skill Recommendations...")
    try:
        response = requests.post(
            "https://test-agents-hub.preview.emergentagent.com/api/ai/recommend-skills",
            headers=headers,
            timeout=60  # Long timeout for AI
        )
        
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print("✅ AI Recommendations - SUCCESS")
            print(f"Response: {json.dumps(result, indent=2)}")
        else:
            print(f"❌ AI Recommendations - FAILED: {response.text}")
    except Exception as e:
        print(f"❌ AI Recommendations - ERROR: {str(e)}")
    
    # Test AI lesson content generation
    print("\n🤖 Testing AI Lesson Content Generation...")
    try:
        data = {
            "skill_name": "HTML",
            "lesson_title": "Advanced HTML"
        }
        
        response = requests.post(
            "https://test-agents-hub.preview.emergentagent.com/api/ai/generate-lesson-content",
            json=data,
            headers=headers,
            timeout=60  # Long timeout for AI
        )
        
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print("✅ AI Lesson Content - SUCCESS")
            print(f"Content: {result.get('content', 'No content')[:200]}...")
        else:
            print(f"❌ AI Lesson Content - FAILED: {response.text}")
    except Exception as e:
        print(f"❌ AI Lesson Content - ERROR: {str(e)}")

if __name__ == "__main__":
    test_ai_endpoints()