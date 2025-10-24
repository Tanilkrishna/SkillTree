#!/usr/bin/env python3
"""
Comprehensive Admin System Test for SkillTree
Tests admin functionality with proper authentication simulation
"""

import requests
import json
import sys
import os
from datetime import datetime, timezone
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/app/frontend/.env')

class AdminSystemTester:
    def __init__(self, base_url=None):
        if base_url is None:
            self.base_url = "http://localhost:8001"
        else:
            self.base_url = base_url
        
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        self.session_cookies = None
        self.user_id = None
        self.is_admin = False

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

    def make_request(self, method, endpoint, data=None, timeout=30):
        """Make authenticated request"""
        url = f"{self.base_url}/api/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, cookies=self.session_cookies, timeout=timeout)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, cookies=self.session_cookies, timeout=timeout)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, cookies=self.session_cookies, timeout=timeout)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, cookies=self.session_cookies, timeout=timeout)
            
            return response
        except Exception as e:
            print(f"Request failed: {str(e)}")
            return None

    def simulate_user_session(self):
        """Simulate creating a user session for testing"""
        print("\n👤 Simulating User Session Creation...")
        
        # Since we can't easily create real OAuth sessions in testing,
        # we'll use a mock approach by directly inserting into database
        # In a real scenario, this would be done through OAuth flow
        
        # For testing purposes, we'll create a session cookie manually
        # This simulates what would happen after successful OAuth
        test_session_token = "test_session_token_12345"
        self.session_cookies = {'session_token': test_session_token}
        
        # Create test user in database (simulating OAuth user creation)
        import pymongo
        from pymongo import MongoClient
        
        try:
            # Connect to MongoDB
            mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
            client = MongoClient(mongo_url)
            db = client['skilltree_db']
            
            # Create test user
            test_user = {
                'id': 'test-admin-user-123',
                'email': 'admin.test@skilltree.com',
                'name': 'Admin Test User',
                'picture': None,
                'xp': 0,
                'level': 1,
                'is_admin': False,  # Will be promoted later
                'auth_type': 'oauth',
                'created_at': datetime.now(timezone.utc).isoformat()
            }
            
            # Insert or update user
            db.users.replace_one({'id': test_user['id']}, test_user, upsert=True)
            
            # Create session (expires in 1 hour)
            from datetime import timedelta
            expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
            test_session = {
                'user_id': test_user['id'],
                'session_token': test_session_token,
                'expires_at': expires_at.isoformat(),
                'created_at': datetime.now(timezone.utc).isoformat()
            }
            
            # Insert or update session
            db.user_sessions.replace_one({'session_token': test_session_token}, test_session, upsert=True)
            
            self.user_id = test_user['id']
            client.close()
            
            self.log_test("User Session Simulation", True, f"Created test user: {test_user['email']}")
            return True
            
        except Exception as e:
            self.log_test("User Session Simulation", False, f"Failed to create test user: {str(e)}")
            return False

    def test_auth_me_endpoint(self):
        """Test /auth/me endpoint to verify session"""
        print("\n🔐 Testing Authentication Status...")
        
        response = self.make_request('GET', 'auth/me')
        
        if response and response.status_code == 200:
            user_data = response.json()
            self.is_admin = user_data.get('is_admin', False)
            self.log_test("Auth Me Endpoint", True, f"User: {user_data.get('email')}, Admin: {self.is_admin}")
            return True, user_data
        else:
            status = response.status_code if response else "No response"
            self.log_test("Auth Me Endpoint", False, f"Status: {status}")
            return False, {}

    def test_promote_to_admin(self):
        """Test promoting user to admin"""
        print("\n⚡ Testing Admin Promotion...")
        
        response = self.make_request('POST', 'admin/promote-me')
        
        if response and response.status_code == 200:
            result = response.json()
            self.is_admin = result.get('is_admin', False)
            self.log_test("Promote to Admin", True, f"Admin status: {self.is_admin}")
            return True
        else:
            status = response.status_code if response else "No response"
            error = ""
            if response:
                try:
                    error = response.json().get('detail', '')
                except:
                    error = response.text[:200]
            self.log_test("Promote to Admin", False, f"Status: {status}, Error: {error}")
            return False

    def test_admin_skills_endpoint(self):
        """Test admin skills management endpoint"""
        print("\n📚 Testing Admin Skills Management...")
        
        if not self.is_admin:
            self.log_test("Admin Skills (Not Admin)", False, "User is not admin")
            return False
        
        response = self.make_request('GET', 'admin/skills')
        
        if response and response.status_code == 200:
            skills = response.json()
            self.log_test("Admin Get Skills", True, f"Retrieved {len(skills)} skills")
            return True, skills
        else:
            status = response.status_code if response else "No response"
            self.log_test("Admin Get Skills", False, f"Status: {status}")
            return False, []

    def test_admin_lesson_generation(self):
        """Test AI-powered lesson generation"""
        print("\n🤖 Testing AI Lesson Generation...")
        
        if not self.is_admin:
            self.log_test("Admin Lesson Generation (Not Admin)", False, "User is not admin")
            return False
        
        # Test 1: Generate lessons for existing skill
        lesson_data = {
            "skill_id": "skill-1",
            "topic": "HTML Forms and Validation",
            "difficulty": "beginner",
            "xp_points": 100,
            "lesson_count": 2,  # Reduced for faster testing
            "learning_objective": "Learn to create and validate HTML forms with different input types"
        }
        
        print("  Testing lesson generation for existing skill...")
        response = self.make_request('POST', 'admin/lessons/generate', data=lesson_data, timeout=60)
        
        if response and response.status_code == 200:
            result = response.json()
            lessons = result.get('lessons', [])
            self.log_test("Generate Lessons (Existing Skill)", True, f"Generated {len(lessons)} lessons")
            
            # Verify lesson structure
            if lessons:
                lesson = lessons[0]
                required_fields = ['id', 'skill_id', 'title', 'content', 'order', 'estimated_time', 'resources']
                missing_fields = [field for field in required_fields if field not in lesson]
                
                if not missing_fields:
                    self.log_test("Lesson Structure Validation", True, "All required fields present")
                else:
                    self.log_test("Lesson Structure Validation", False, f"Missing fields: {missing_fields}")
            
            return True, result
        else:
            status = response.status_code if response else "No response"
            error = ""
            if response:
                try:
                    error = response.json().get('detail', '')
                except:
                    error = response.text[:200]
            self.log_test("Generate Lessons (Existing Skill)", False, f"Status: {status}, Error: {error}")
            return False, {}

    def test_admin_lesson_generation_new_skill(self):
        """Test lesson generation with new skill creation"""
        print("\n🆕 Testing Lesson Generation with New Skill...")
        
        if not self.is_admin:
            self.log_test("Admin New Skill Generation (Not Admin)", False, "User is not admin")
            return False
        
        lesson_data = {
            "skill_id": None,
            "new_skill_name": "Advanced Testing Techniques",
            "new_skill_category": "Quality Assurance",
            "topic": "Automated Testing Strategies",
            "difficulty": "intermediate",
            "xp_points": 150,
            "lesson_count": 2,
            "learning_objective": "Master advanced automated testing techniques and strategies"
        }
        
        response = self.make_request('POST', 'admin/lessons/generate', data=lesson_data, timeout=60)
        
        if response and response.status_code == 200:
            result = response.json()
            skill_id = result.get('skill_id')
            lessons = result.get('lessons', [])
            self.log_test("Generate Lessons (New Skill)", True, f"Created skill {skill_id} with {len(lessons)} lessons")
            return True, result
        else:
            status = response.status_code if response else "No response"
            error = ""
            if response:
                try:
                    error = response.json().get('detail', '')
                except:
                    error = response.text[:200]
            self.log_test("Generate Lessons (New Skill)", False, f"Status: {status}, Error: {error}")
            return False, {}

    def test_admin_validation_errors(self):
        """Test admin endpoint validation"""
        print("\n🔍 Testing Admin Validation...")
        
        if not self.is_admin:
            self.log_test("Admin Validation (Not Admin)", False, "User is not admin")
            return False
        
        # Test invalid lesson generation data
        invalid_data = {
            "skill_id": "non-existent-skill-id",
            "topic": "",  # Empty topic
            "difficulty": "invalid-level",
            "xp_points": -100,  # Negative XP
            "lesson_count": 0,  # Zero lessons
            "learning_objective": ""
        }
        
        response = self.make_request('POST', 'admin/lessons/generate', data=invalid_data)
        
        # Should return 400 or 422 for validation errors
        if response and response.status_code in [400, 422, 404]:
            self.log_test("Admin Validation Errors", True, f"Properly rejected invalid data (Status: {response.status_code})")
            return True
        else:
            status = response.status_code if response else "No response"
            self.log_test("Admin Validation Errors", False, f"Unexpected status: {status}")
            return False

    def test_non_admin_access(self):
        """Test that non-admin users cannot access admin endpoints"""
        print("\n🚫 Testing Non-Admin Access Restriction...")
        
        # Temporarily remove admin status for testing
        if self.is_admin:
            # Update user to non-admin in database
            import pymongo
            from pymongo import MongoClient
            
            try:
                mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
                client = MongoClient(mongo_url)
                db = client['skilltree_db']
                
                # Set user as non-admin
                db.users.update_one({'id': self.user_id}, {'$set': {'is_admin': False}})
                client.close()
                
                # Test admin endpoint access
                response = self.make_request('GET', 'admin/skills')
                
                if response and response.status_code == 403:
                    self.log_test("Non-Admin Access Restriction", True, "Properly blocked non-admin access")
                    
                    # Restore admin status
                    client = MongoClient(mongo_url)
                    db = client['skilltree_db']
                    db.users.update_one({'id': self.user_id}, {'$set': {'is_admin': True}})
                    client.close()
                    
                    return True
                else:
                    status = response.status_code if response else "No response"
                    self.log_test("Non-Admin Access Restriction", False, f"Expected 403, got {status}")
                    return False
                    
            except Exception as e:
                self.log_test("Non-Admin Access Restriction", False, f"Database error: {str(e)}")
                return False
        else:
            self.log_test("Non-Admin Access Restriction", False, "User is already non-admin")
            return False

    def run_comprehensive_admin_tests(self):
        """Run complete admin system test suite"""
        print("🚀 Starting Comprehensive Admin System Tests")
        print("🎯 Focus: Admin functionality with authentication")
        print(f"Testing against: {self.base_url}")
        print("=" * 70)
        
        # Step 1: Create test user session
        if not self.simulate_user_session():
            print("❌ Failed to create test session - stopping tests")
            return False
        
        # Step 2: Test authentication
        success, user_data = self.test_auth_me_endpoint()
        if not success:
            print("❌ Authentication failed - stopping tests")
            return False
        
        # Step 3: Promote to admin
        if not self.test_promote_to_admin():
            print("❌ Admin promotion failed - stopping tests")
            return False
        
        # Step 4: Test admin endpoints
        self.test_admin_skills_endpoint()
        
        # Step 5: Test AI lesson generation (high priority)
        self.test_admin_lesson_generation()
        self.test_admin_lesson_generation_new_skill()
        
        # Step 6: Test validation
        self.test_admin_validation_errors()
        
        # Step 7: Test access control
        self.test_non_admin_access()
        
        # Print summary
        print("\n" + "=" * 70)
        print(f"📊 Admin Test Results: {self.tests_passed}/{self.tests_run} passed")
        print(f"Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        # Show failed tests
        failed_tests = [t for t in self.test_results if not t['success']]
        if failed_tests:
            print(f"\n❌ Failed Tests ({len(failed_tests)}):")
            for test in failed_tests:
                print(f"  - {test['test_name']}: {test['details']}")
        else:
            print("\n✅ All admin tests passed!")
        
        return len(failed_tests) == 0

def main():
    tester = AdminSystemTester()
    success = tester.run_comprehensive_admin_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())