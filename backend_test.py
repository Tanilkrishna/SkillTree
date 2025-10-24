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
            # Use the production URL from frontend/.env
            self.base_url = os.getenv('REACT_APP_BACKEND_URL', 'https://dev-journey-103.preview.emergentagent.com')
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
                except:
                    details += f", Response: {response.text[:200]}"
            
            self.log_test(name, success, details)
            
            if success:
                try:
                    return True, response.json()
                except:
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

    def test_skills_endpoints(self):
        """Test skills-related endpoints"""
        print("\n🎯 Testing Skills Endpoints...")
        
        # First seed data
        self.run_test(
            "Seed Data",
            "POST",
            "seed-data",
            200
        )
        
        # Get all skills
        success, skills_response = self.run_test(
            "Get All Skills",
            "GET",
            "skills",
            200
        )
        
        if success and skills_response:
            skills = skills_response
            if len(skills) > 0:
                skill_id = skills[0]['id']
                
                # Get specific skill
                self.run_test(
                    "Get Specific Skill",
                    "GET",
                    f"skills/{skill_id}",
                    200
                )
                
                # Start a skill
                self.run_test(
                    "Start Skill",
                    "POST",
                    f"user-skills/{skill_id}/start",
                    200
                )
                
                # Update progress
                self.run_test(
                    "Update Skill Progress",
                    "PUT",
                    f"user-skills/{skill_id}/progress",
                    200,
                    data={"progress_percent": 50}
                )
                
                # Complete skill
                self.run_test(
                    "Complete Skill",
                    "POST",
                    f"user-skills/{skill_id}/complete",
                    200
                )
                
                return skill_id
        
        return None

    def test_lessons_endpoints(self, skill_id):
        """Test lessons-related endpoints"""
        print("\n📚 Testing Lessons Endpoints...")
        
        if not skill_id:
            self.log_test("Lessons Test", False, "No skill_id available")
            return
        
        # Get lessons for skill
        success, lessons_response = self.run_test(
            "Get Skill Lessons",
            "GET",
            f"skills/{skill_id}/lessons",
            200
        )
        
        if success and lessons_response:
            lessons = lessons_response
            if len(lessons) > 0:
                lesson_id = lessons[0]['id']
                
                # Complete lesson
                self.run_test(
                    "Complete Lesson",
                    "POST",
                    f"lessons/{lesson_id}/complete",
                    200
                )

    def test_ai_endpoints(self):
        """Test AI-related endpoints"""
        print("\n🤖 Testing AI Endpoints...")
        
        # Test skill recommendations
        self.run_test(
            "AI Skill Recommendations",
            "POST",
            "ai/recommend-skills",
            200
        )
        
        # Test lesson content generation
        self.run_test(
            "AI Generate Lesson Content",
            "POST",
            "ai/generate-lesson-content",
            200,
            data={
                "skill_name": "Python Basics",
                "lesson_title": "Variables and Data Types"
            }
        )

    def test_integrations_endpoints(self):
        """Test integrations-related endpoints"""
        print("\n🔗 Testing Integrations Endpoints...")
        
        # Get integrations
        self.run_test(
            "Get Integrations",
            "GET",
            "integrations",
            200
        )
        
        # Connect platforms
        platforms = ['github', 'linkedin', 'youtube']
        for platform in platforms:
            self.run_test(
                f"Connect {platform.title()}",
                "POST",
                f"integrations/connect/{platform}",
                200
            )
            
            # Sync platform
            self.run_test(
                f"Sync {platform.title()}",
                "GET",
                f"integrations/{platform}/sync",
                200
            )

    def test_dashboard_endpoints(self):
        """Test dashboard-related endpoints"""
        print("\n📊 Testing Dashboard Endpoints...")
        
        self.run_test(
            "Get Dashboard Stats",
            "GET",
            "dashboard/stats",
            200
        )

    def run_all_tests(self):
        """Run complete test suite"""
        print("🚀 Starting SkillTree API Test Suite")
        print(f"Testing against: {self.base_url}")
        print("=" * 50)
        
        # Test authentication first
        if not self.test_auth_flow():
            print("❌ Authentication failed - stopping tests")
            return False
        
        # Test all other endpoints
        skill_id = self.test_skills_endpoints()
        self.test_lessons_endpoints(skill_id)
        self.test_ai_endpoints()
        self.test_integrations_endpoints()
        self.test_dashboard_endpoints()
        
        # Print summary
        print("\n" + "=" * 50)
        print(f"📊 Test Results: {self.tests_passed}/{self.tests_run} passed")
        print(f"Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        # Show failed tests
        failed_tests = [t for t in self.test_results if not t['success']]
        if failed_tests:
            print(f"\n❌ Failed Tests ({len(failed_tests)}):")
            for test in failed_tests:
                print(f"  - {test['test_name']}: {test['details']}")
        
        return self.tests_passed == self.tests_run

def main():
    tester = SkillTreeAPITester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())