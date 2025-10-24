import requests
import sys
import json
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/app/frontend/.env')

class SkillTreeAPITester:
    def __init__(self, base_url=None):
        if base_url is None:
            # Test against internal backend URL since we're running inside the container
            self.base_url = "http://localhost:8001"
        else:
            self.base_url = base_url
        self.session_token = None
        self.user_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def log_test(self, name, success, details=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
        
        result = {
            "test_name": name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {name}")
        if details:
            print(f"    Details: {details}")

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None, cookies=None):
        """Run a single API test"""
        url = f"{self.base_url}/api/{endpoint}"
        test_headers = {'Content-Type': 'application/json'}
        
        if headers:
            test_headers.update(headers)

        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers, cookies=cookies, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=test_headers, cookies=cookies, timeout=10)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=test_headers, cookies=cookies, timeout=10)

            success = response.status_code == expected_status
            details = f"Status: {response.status_code}, Expected: {expected_status}"
            
            if not success:
                try:
                    error_detail = response.json().get('detail', 'No error detail')
                    details += f", Error: {error_detail}"
                except Exception:
                    details += f", Response: {response.text[:200]}"
            
            self.log_test(name, success, details)
            
            if success:
                try:
                    return True, response.json()
                except Exception:
                    return True, {}
            else:
                return False, response

        except Exception as e:
            self.log_test(name, False, f"Exception: {str(e)}")
            return False, {}

    def test_auth_changes(self):
        """Test authentication changes - removed endpoints should return 404"""
        print("\n🔐 Testing Authentication Changes...")
        
        # Test that /auth/register returns 404 (should be removed)
        register_data = {
            "email": "test@example.com",
            "password": "TestPass123!",
            "name": "Test User"
        }
        
        self.run_test(
            "Auth Register Endpoint (Should be 404)",
            "POST",
            "auth/register",
            404,
            data=register_data
        )
        
        # Test that /auth/login returns 404 (should be removed)
        login_data = {
            "email": "test@example.com",
            "password": "TestPass123!"
        }
        
        self.run_test(
            "Auth Login Endpoint (Should be 404)",
            "POST",
            "auth/login",
            404,
            data=login_data
        )
        
        # Test /auth/oauth/session exists but fails with invalid session_id
        oauth_data = {
            "session_id": "invalid_session_id_12345"
        }
        
        self.run_test(
            "OAuth Session with Invalid ID (Should fail)",
            "POST",
            "auth/oauth/session",
            400,  # Should return 400 for invalid session_id
            data=oauth_data
        )
        
        # Test /auth/oauth/session fails without session_id
        self.run_test(
            "OAuth Session without session_id (Should fail)",
            "POST",
            "auth/oauth/session",
            400,  # Should return 400 for missing session_id
            data={}
        )
        
        # Test /auth/me returns 401 for unauthenticated users
        self.run_test(
            "Get Current User Unauthenticated (Should be 401)",
            "GET",
            "auth/me",
            401
        )
        
        # Test /auth/logout works (should return success even without session)
        self.run_test(
            "Logout Endpoint",
            "POST",
            "auth/logout",
            200
        )
        
        return True

    def test_protected_endpoints_without_auth(self):
        """Test that protected endpoints return 401 without authentication"""
        print("\n🔒 Testing Protected Endpoints Without Auth...")
        
        # Test skills endpoints require authentication
        self.run_test(
            "Get Skills Unauthenticated (Should be 401)",
            "GET",
            "skills",
            401
        )
        
        # Test dashboard stats requires authentication
        self.run_test(
            "Get Dashboard Stats Unauthenticated (Should be 401)",
            "GET",
            "dashboard/stats",
            401
        )
        
        # Test AI recommendations require authentication
        self.run_test(
            "AI Recommendations Unauthenticated (Should be 401)",
            "POST",
            "ai/recommend-skills",
            401
        )
        
        # Test integrations require authentication
        self.run_test(
            "Get Integrations Unauthenticated (Should be 401)",
            "GET",
            "integrations",
            401
        )
        
        return True

    def test_seed_data_endpoint(self):
        """Test seed data endpoint (should work without auth)"""
        print("\n🌱 Testing Seed Data Endpoint...")
        
        # Seed data should work without authentication
        success, response_data = self.run_test(
            "Seed Data Endpoint",
            "POST",
            "seed-data",
            200
        )
        
        return success

    def test_skills_endpoints_without_auth(self):
        """Test skills endpoints without authentication (should return 401)"""
        print("\n🎯 Testing Skills Endpoints Without Auth...")
        
        # Test /api/skills (list all skills)
        self.run_test(
            "List Skills Unauthenticated (Should be 401)",
            "GET",
            "skills",
            401
        )
        
        # Test /api/user-skills/{skill_id}/start
        self.run_test(
            "Start Skill Unauthenticated (Should be 401)",
            "POST",
            "user-skills/skill-1/start",
            401
        )
        
        # Test /api/user-skills/{skill_id}/complete
        self.run_test(
            "Complete Skill Unauthenticated (Should be 401)",
            "POST",
            "user-skills/skill-1/complete",
            401
        )
        
        return True

    def test_lessons_endpoints_without_auth(self):
        """Test lessons endpoints without authentication (should return 401)"""
        print("\n📚 Testing Lessons Endpoints Without Auth...")
        
        # Test /api/skills/{skill_id}/lessons
        self.run_test(
            "Get Lessons Unauthenticated (Should be 401)",
            "GET",
            "skills/skill-1/lessons",
            401
        )
        
        # Test /api/lessons/{lesson_id}/complete (this is the endpoint with fixed variable name)
        self.run_test(
            "Complete Lesson Unauthenticated (Should be 401)",
            "POST",
            "lessons/lesson-1-1/complete",
            401
        )
        
        return True

    def test_ai_endpoints_without_auth(self):
        """Test AI endpoints without authentication (should return 401)"""
        print("\n🤖 Testing AI Endpoints Without Auth...")
        
        # Test /api/ai/recommend-skills
        self.run_test(
            "AI Recommend Skills Unauthenticated (Should be 401)",
            "POST",
            "ai/recommend-skills",
            401
        )
        
        # Test /api/ai/generate-lesson-content
        self.run_test(
            "AI Generate Lesson Content Unauthenticated (Should be 401)",
            "POST",
            "ai/generate-lesson-content",
            401,
            data={"skill_name": "Python", "lesson_title": "Variables"}
        )
        
        return True

    def test_integrations_endpoints_without_auth(self):
        """Test integration endpoints without authentication (should return 401)"""
        print("\n🔗 Testing Integration Endpoints Without Auth...")
        
        # Test /api/integrations
        self.run_test(
            "Get Integrations Unauthenticated (Should be 401)",
            "GET",
            "integrations",
            401
        )
        
        # Test /api/integrations/{platform}/connect
        for platform in ['github', 'linkedin', 'youtube']:
            self.run_test(
                f"Connect {platform.title()} Unauthenticated (Should be 401)",
                "POST",
                f"integrations/{platform}/connect",
                401,
                data={}
            )
        
        return True

    def test_dashboard_endpoints_without_auth(self):
        """Test dashboard endpoints without authentication (should return 401)"""
        print("\n📊 Testing Dashboard Endpoints Without Auth...")
        
        # Test /api/dashboard/stats
        self.run_test(
            "Get Dashboard Stats Unauthenticated (Should be 401)",
            "GET",
            "dashboard/stats",
            401
        )
        
        # Test /api/achievements
        self.run_test(
            "Get Achievements Unauthenticated (Should be 401)",
            "GET",
            "achievements",
            401
        )
        
        # Test /api/activity-feed
        self.run_test(
            "Get Activity Feed Unauthenticated (Should be 401)",
            "GET",
            "activity-feed",
            401
        )
        
        return True

    def test_endpoint_existence(self):
        """Test that all expected endpoints exist (not 404)"""
        print("\n🔍 Testing Endpoint Existence...")
        
        # These should return 401 (auth required) not 404 (not found)
        endpoints_to_check = [
            ("GET", "skills"),
            ("GET", "skills/skill-1"),
            ("POST", "user-skills/skill-1/start"),
            ("POST", "user-skills/skill-1/complete"),
            ("GET", "skills/skill-1/lessons"),
            ("POST", "lessons/lesson-1-1/complete"),
            ("POST", "ai/recommend-skills"),
            ("POST", "ai/generate-lesson-content"),
            ("GET", "integrations"),
            ("POST", "integrations/github/connect"),
            ("GET", "dashboard/stats"),
            ("GET", "achievements"),
            ("GET", "activity-feed")
        ]
        
        for method, endpoint in endpoints_to_check:
            success, response = self.run_test(
                f"Endpoint Exists: {method} {endpoint}",
                method,
                endpoint,
                401,  # Should be 401 (auth required), not 404 (not found)
                data={} if method == "POST" else None
            )
        
        return True

    def test_backend_health(self):
        """Test if backend is running and responding"""
        print("\n🏥 Testing Backend Health...")
        
        try:
            # Test a simple endpoint to see if backend is running
            url = f"{self.base_url}/api/seed-data"
            response = requests.post(url, timeout=10)
            
            if response.status_code in [200, 400, 401, 404]:
                self.log_test("Backend Health Check", True, f"Backend responding (Status: {response.status_code})")
                return True
            else:
                self.log_test("Backend Health Check", False, f"Unexpected status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Backend Health Check", False, f"Backend not responding: {str(e)}")
            return False

    def run_all_tests(self):
        """Run complete test suite focused on authentication changes"""
        print("🚀 Starting SkillTree Authentication Test Suite")
        print(f"Testing against: {self.base_url}")
        print("=" * 60)
        
        # Test backend health first
        if not self.test_backend_health():
            print("❌ Backend not responding - stopping tests")
            return False
        
        # Test authentication changes (main focus)
        self.test_auth_changes()
        
        # Test protected endpoints without authentication
        self.test_protected_endpoints_without_auth()
        
        # Test seed data endpoint (should work without auth)
        self.test_seed_data_endpoint()
        
        # Print summary
        print("\n" + "=" * 60)
        print(f"📊 Test Results: {self.tests_passed}/{self.tests_run} passed")
        print(f"Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        # Show failed tests
        failed_tests = [t for t in self.test_results if not t['success']]
        if failed_tests:
            print(f"\n❌ Failed Tests ({len(failed_tests)}):")
            for test in failed_tests:
                print(f"  - {test['test_name']}: {test['details']}")
        else:
            print("\n✅ All tests passed!")
        
        return len(failed_tests) == 0

def main():
    tester = SkillTreeAPITester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())