import requests
import json
from datetime import datetime

class AdditionalAPITester:
    def __init__(self, base_url="https://code-cleanup-54.preview.emergentagent.com"):
        self.base_url = base_url
        self.token = None
        
    def authenticate(self):
        """Get authentication token"""
        # Register a test user
        test_email = f"test_{datetime.now().strftime('%H%M%S')}@example.com"
        register_data = {
            "email": test_email,
            "password": "TestPass123!",
            "name": "Test User"
        }
        
        response = requests.post(
            f"{self.base_url}/api/auth/register",
            json=register_data,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            self.token = data['token']
            return True
        return False
    
    def test_ai_lesson_content_extended(self):
        """Test AI lesson content generation with extended timeout"""
        print("🤖 Testing AI Lesson Content Generation (Extended Timeout)...")
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.token}'
        }
        
        data = {
            "skill_name": "HTML",
            "lesson_title": "Advanced HTML"
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/ai/generate-lesson-content",
                json=data,
                headers=headers,
                timeout=30  # Extended timeout
            )
            
            print(f"Status Code: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                print("✅ AI Lesson Content Generation - SUCCESS")
                print(f"Content Length: {len(result.get('content', ''))}")
                if result.get('content'):
                    print(f"Content Preview: {result['content'][:200]}...")
                return True
            else:
                print(f"❌ AI Lesson Content Generation - FAILED: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ AI Lesson Content Generation - ERROR: {str(e)}")
            return False
    
    def test_achievements_endpoint(self):
        """Test achievements endpoint"""
        print("🏆 Testing Achievements Endpoint...")
        
        headers = {
            'Authorization': f'Bearer {self.token}'
        }
        
        try:
            response = requests.get(
                f"{self.base_url}/api/achievements",
                headers=headers,
                timeout=10
            )
            
            print(f"Status Code: {response.status_code}")
            if response.status_code == 200:
                achievements = response.json()
                print("✅ Achievements Endpoint - SUCCESS")
                print(f"Number of achievements: {len(achievements)}")
                for achievement in achievements:
                    status = "🔓 Unlocked" if achievement.get('unlocked') else "🔒 Locked"
                    print(f"  - {achievement.get('name')}: {status}")
                return True
            else:
                print(f"❌ Achievements Endpoint - FAILED: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Achievements Endpoint - ERROR: {str(e)}")
            return False
    
    def test_activity_feed_endpoint(self):
        """Test activity feed endpoint"""
        print("📈 Testing Activity Feed Endpoint...")
        
        headers = {
            'Authorization': f'Bearer {self.token}'
        }
        
        try:
            response = requests.get(
                f"{self.base_url}/api/activity-feed",
                headers=headers,
                timeout=10
            )
            
            print(f"Status Code: {response.status_code}")
            if response.status_code == 200:
                activities = response.json()
                print("✅ Activity Feed Endpoint - SUCCESS")
                print(f"Number of activities: {len(activities)}")
                for activity in activities:
                    print(f"  - {activity.get('title')}: {activity.get('description')}")
                return True
            else:
                print(f"❌ Activity Feed Endpoint - FAILED: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Activity Feed Endpoint - ERROR: {str(e)}")
            return False
    
    def run_additional_tests(self):
        """Run additional tests for specific endpoints"""
        print("🚀 Running Additional API Tests")
        print("=" * 50)
        
        if not self.authenticate():
            print("❌ Authentication failed")
            return False
        
        print("✅ Authentication successful")
        
        # Test the specific endpoints that need verification
        ai_result = self.test_ai_lesson_content_extended()
        achievements_result = self.test_achievements_endpoint()
        activity_result = self.test_activity_feed_endpoint()
        
        print("\n" + "=" * 50)
        print("📊 Additional Test Results:")
        print(f"  AI Lesson Content: {'✅ PASS' if ai_result else '❌ FAIL'}")
        print(f"  Achievements: {'✅ PASS' if achievements_result else '❌ FAIL'}")
        print(f"  Activity Feed: {'✅ PASS' if activity_result else '❌ FAIL'}")
        
        return ai_result and achievements_result and activity_result

if __name__ == "__main__":
    tester = AdditionalAPITester()
    tester.run_additional_tests()