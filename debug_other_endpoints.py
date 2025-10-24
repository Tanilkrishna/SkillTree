import requests
import json
from datetime import datetime

def test_other_endpoints():
    # First authenticate
    test_email = f"test_{datetime.now().strftime('%H%M%S')}@example.com"
    register_data = {
        "email": test_email,
        "password": "TestPass123!",
        "name": "Test User"
    }
    
    print("🔐 Authenticating...")
    response = requests.post(
        "https://code-cleanup-54.preview.emergentagent.com/api/auth/register",
        json=register_data,
        headers={'Content-Type': 'application/json'},
        timeout=10
    )
    
    if response.status_code != 200:
        print(f"❌ Authentication failed: {response.text}")
        return
    
    token = response.json()['token']
    headers = {
        'Authorization': f'Bearer {token}'
    }
    
    print("✅ Authentication successful")
    
    # Test achievements
    print("\n🏆 Testing Achievements...")
    try:
        response = requests.get(
            "https://code-cleanup-54.preview.emergentagent.com/api/achievements",
            headers=headers,
            timeout=30
        )
        
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print("✅ Achievements - SUCCESS")
            print(f"Number of achievements: {len(result)}")
            for achievement in result:
                status = "🔓 Unlocked" if achievement.get('unlocked') else "🔒 Locked"
                print(f"  - {achievement.get('name')}: {status}")
        else:
            print(f"❌ Achievements - FAILED: {response.text}")
    except Exception as e:
        print(f"❌ Achievements - ERROR: {str(e)}")
    
    # Test activity feed
    print("\n📈 Testing Activity Feed...")
    try:
        response = requests.get(
            "https://code-cleanup-54.preview.emergentagent.com/api/activity-feed",
            headers=headers,
            timeout=30
        )
        
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print("✅ Activity Feed - SUCCESS")
            print(f"Number of activities: {len(result)}")
            for activity in result:
                print(f"  - {activity.get('title')}: {activity.get('description')}")
        else:
            print(f"❌ Activity Feed - FAILED: {response.text}")
    except Exception as e:
        print(f"❌ Activity Feed - ERROR: {str(e)}")
    
    # Test dashboard stats
    print("\n📊 Testing Dashboard Stats...")
    try:
        response = requests.get(
            "https://code-cleanup-54.preview.emergentagent.com/api/dashboard/stats",
            headers=headers,
            timeout=30
        )
        
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print("✅ Dashboard Stats - SUCCESS")
            print(f"Stats: {json.dumps(result, indent=2)}")
        else:
            print(f"❌ Dashboard Stats - FAILED: {response.text}")
    except Exception as e:
        print(f"❌ Dashboard Stats - ERROR: {str(e)}")

if __name__ == "__main__":
    test_other_endpoints()