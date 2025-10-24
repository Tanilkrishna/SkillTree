from fastapi import FastAPI, APIRouter, HTTPException, Depends, status, Request, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
import jwt
import httpx
from emergentintegrations.llm.chat import LlmChat, UserMessage

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# JWT Configuration
JWT_SECRET = os.environ.get('JWT_SECRET')
JWT_ALGORITHM = os.environ.get('JWT_ALGORITHM', 'HS256')
JWT_EXPIRATION_HOURS = int(os.environ.get('JWT_EXPIRATION_HOURS', 720))

# Create the main app
app = FastAPI()
api_router = APIRouter(prefix="/api")
security = HTTPBearer()

# ============= MODELS =============
class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    email: str
    name: str
    picture: Optional[str] = None
    xp: int = 0
    level: int = 1
    is_admin: bool = False
    created_at: str
    auth_type: str = "jwt"  # jwt or oauth

class UserSession(BaseModel):
    model_config = ConfigDict(extra="ignore")
    user_id: str
    session_token: str
    expires_at: str
    created_at: str

class Skill(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    name: str
    description: str
    category: str
    difficulty: str  # beginner, intermediate, advanced
    prerequisites: List[str] = []
    xp_value: int
    icon: str
    position: Dict[str, int]  # x, y coordinates for tree visualization

class UserSkill(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    user_id: str
    skill_id: str
    status: str  # locked, in_progress, completed
    progress_percent: int = 0
    started_at: Optional[str] = None
    completed_at: Optional[str] = None

class Lesson(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    skill_id: str
    title: str
    content: str
    order: int
    estimated_time: int  # in minutes
    resources: List[Dict[str, str]] = []  # external links

class UserLesson(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    user_id: str
    lesson_id: str
    completed: bool = False
    completed_at: Optional[str] = None

class ExternalConnection(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    user_id: str
    platform: str  # github, linkedin, youtube
    connected: bool = False
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    platform_data: Optional[Dict[str, Any]] = None
    connected_at: Optional[str] = None

# ============= AUTH HELPERS =============
def create_token(user_id: str) -> str:
    payload = {
        'user_id': user_id,
        'exp': datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def get_current_user_from_request(request: Request) -> dict:
    # Try cookie-based session first (OAuth)
    session_token = request.cookies.get('session_token')
    
    if session_token:
        session = await db.user_sessions.find_one({'session_token': session_token}, {'_id': 0})
        if session:
            expires_at = datetime.fromisoformat(session['expires_at'])
            if expires_at > datetime.now(timezone.utc):
                user = await db.users.find_one({'id': session['user_id']}, {'_id': 0})
                if user:
                    return user
    
    # Try JWT token from Authorization header
    auth_header = request.headers.get('Authorization')
    if auth_header and auth_header.startswith('Bearer '):
        token = auth_header.split(' ')[1]
        payload = decode_token(token)
        user = await db.users.find_one({'id': payload['user_id']}, {'_id': 0})
        if user:
            return user
    
    raise HTTPException(status_code=401, detail="Not authenticated")

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    token = credentials.credentials
    payload = decode_token(token)
    user = await db.users.find_one({'id': payload['user_id']}, {'_id': 0})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user

# ============= AUTH ROUTES =============
@api_router.get("/auth/me")
async def get_me(request: Request):
    current_user = await get_current_user_from_request(request)
    return {'id': current_user['id'], 'email': current_user['email'], 'name': current_user['name'], 'picture': current_user.get('picture'), 'xp': current_user['xp'], 'level': current_user['level'], 'auth_type': current_user.get('auth_type', 'jwt')}

# OAuth Routes
@api_router.post("/auth/oauth/session")
async def create_oauth_session(data: dict, response: Response):
    """Process session_id from Emergent OAuth and create user session"""
    session_id = data.get('session_id')
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id required")
    
    # Fetch user data from Emergent Auth
    try:
        async with httpx.AsyncClient() as client:
            headers = {'X-Session-ID': session_id}
            resp = await client.get(
                'https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data',
                headers=headers,
                timeout=10.0
            )
            resp.raise_for_status()
            oauth_data = resp.json()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to fetch session data: {str(e)}")
    
    # Check if user exists
    user = await db.users.find_one({'email': oauth_data['email']}, {'_id': 0})
    
    if not user:
        # Create new user
        user_id = str(uuid.uuid4())
        user_doc = {
            'id': user_id,
            'email': oauth_data['email'],
            'name': oauth_data['name'],
            'picture': oauth_data.get('picture'),
            'xp': 0,
            'level': 1,
            'auth_type': 'oauth',
            'created_at': datetime.now(timezone.utc).isoformat()
        }
        await db.users.insert_one(user_doc)
        user = user_doc
    
    # Create session
    session_token = oauth_data['session_token']
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    
    session_doc = {
        'user_id': user['id'],
        'session_token': session_token,
        'expires_at': expires_at.isoformat(),
        'created_at': datetime.now(timezone.utc).isoformat()
    }
    
    await db.user_sessions.insert_one(session_doc)
    
    # Set httpOnly cookie
    response.set_cookie(
        key='session_token',
        value=session_token,
        httponly=True,
        secure=True,
        samesite='none',
        max_age=7*24*60*60,
        path='/'
    )
    
    return {
        'user': {
            'id': user['id'],
            'email': user['email'],
            'name': user['name'],
            'picture': user.get('picture'),
            'xp': user['xp'],
            'level': user['level']
        }
    }

@api_router.post("/auth/logout")
async def logout(request: Request, response: Response):
    session_token = request.cookies.get('session_token')
    if session_token:
        await db.user_sessions.delete_many({'session_token': session_token})
    
    response.delete_cookie('session_token', path='/')
    return {'message': 'Logged out successfully'}

# ============= SKILLS ROUTES =============
@api_router.get("/skills")
async def get_skills(request: Request):
    current_user = await get_current_user_from_request(request)
    skills = await db.skills.find({}, {'_id': 0}).to_list(1000)
    user_skills = await db.user_skills.find({'user_id': current_user['id']}, {'_id': 0}).to_list(1000)
    
    user_skill_map = {us['skill_id']: us for us in user_skills}
    
    for skill in skills:
        skill_id = skill['id']
        if skill_id in user_skill_map:
            skill['user_status'] = user_skill_map[skill_id]['status']
            skill['user_progress'] = user_skill_map[skill_id]['progress_percent']
        else:
            prereqs_met = True
            for prereq_id in skill.get('prerequisites', []):
                if prereq_id not in user_skill_map or user_skill_map[prereq_id]['status'] != 'completed':
                    prereqs_met = False
                    break
            skill['user_status'] = 'available' if (prereqs_met and len(skill.get('prerequisites', [])) > 0) or len(skill.get('prerequisites', [])) == 0 else 'locked'
            skill['user_progress'] = 0
    
    return skills

@api_router.get("/skills/{skill_id}")
async def get_skill(skill_id: str, request: Request):
    await get_current_user_from_request(request)
    skill = await db.skills.find_one({'id': skill_id}, {'_id': 0})
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    return skill

@api_router.post("/user-skills/{skill_id}/start")
async def start_skill(skill_id: str, request: Request):
    current_user = await get_current_user_from_request(request)
    skill = await db.skills.find_one({'id': skill_id}, {'_id': 0})
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    
    existing = await db.user_skills.find_one({'user_id': current_user['id'], 'skill_id': skill_id}, {'_id': 0})
    if existing:
        raise HTTPException(status_code=400, detail="Skill already started")
    
    user_skill_doc = {
        'id': str(uuid.uuid4()),
        'user_id': current_user['id'],
        'skill_id': skill_id,
        'status': 'in_progress',
        'progress_percent': 0,
        'started_at': datetime.now(timezone.utc).isoformat(),
        'completed_at': None
    }
    
    await db.user_skills.insert_one(user_skill_doc)
    user_skill_doc.pop('_id', None)
    return {'message': 'Skill started', 'user_skill': user_skill_doc}

@api_router.put("/user-skills/{skill_id}/progress")
async def update_progress(skill_id: str, progress: dict, request: Request):
    current_user = await get_current_user_from_request(request)
    user_skill = await db.user_skills.find_one({'user_id': current_user['id'], 'skill_id': skill_id}, {'_id': 0})
    if not user_skill:
        raise HTTPException(status_code=404, detail="User skill not found")
    
    new_progress = progress.get('progress_percent', 0)
    await db.user_skills.update_one(
        {'id': user_skill['id']},
        {'$set': {'progress_percent': new_progress}}
    )
    
    return {'message': 'Progress updated', 'progress_percent': new_progress}

@api_router.post("/user-skills/{skill_id}/complete")
async def complete_skill(skill_id: str, request: Request):
    current_user = await get_current_user_from_request(request)
    skill = await db.skills.find_one({'id': skill_id}, {'_id': 0})
    user_skill = await db.user_skills.find_one({'user_id': current_user['id'], 'skill_id': skill_id}, {'_id': 0})
    
    if not user_skill:
        raise HTTPException(status_code=404, detail="User skill not found")
    
    await db.user_skills.update_one(
        {'id': user_skill['id']},
        {'$set': {
            'status': 'completed',
            'progress_percent': 100,
            'completed_at': datetime.now(timezone.utc).isoformat()
        }}
    )
    
    new_xp = current_user['xp'] + skill['xp_value']
    new_level = 1 + (new_xp // 1000)
    
    await db.users.update_one(
        {'id': current_user['id']},
        {'$set': {'xp': new_xp, 'level': new_level}}
    )
    
    return {'message': 'Skill completed', 'xp_earned': skill['xp_value'], 'total_xp': new_xp, 'level': new_level}

# ============= LESSONS ROUTES =============
@api_router.get("/skills/{skill_id}/lessons")
async def get_lessons(skill_id: str, request: Request):
    current_user = await get_current_user_from_request(request)
    lessons = await db.lessons.find({'skill_id': skill_id}, {'_id': 0}).sort('order', 1).to_list(1000)
    user_lessons = await db.user_lessons.find({'user_id': current_user['id']}, {'_id': 0}).to_list(1000)
    
    user_lesson_map = {ul['lesson_id']: ul for ul in user_lessons}
    
    for lesson in lessons:
        lesson['completed'] = user_lesson_map.get(lesson['id'], {}).get('completed', False)
    
    return lessons

@api_router.post("/lessons/{lesson_id}/complete")
async def complete_lesson(lesson_id: str, request: Request):
    current_user = await get_current_user_from_request(request)
    lesson = await db.lessons.find_one({'id': lesson_id}, {'_id': 0})
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    
    existing = await db.user_lessons.find_one({'user_id': current_user['id'], 'lesson_id': lesson_id}, {'_id': 0})
    if existing:
        await db.user_lessons.update_one(
            {'id': existing['id']},
            {'$set': {'completed': True, 'completed_at': datetime.now(timezone.utc).isoformat()}}
        )
    else:
        user_lesson_doc = {
            'id': str(uuid.uuid4()),
            'user_id': current_user['id'],
            'lesson_id': lesson_id,
            'completed': True,
            'completed_at': datetime.now(timezone.utc).isoformat()
        }
        await db.user_lessons.insert_one(user_lesson_doc)
    
    skill_id = lesson['skill_id']
    all_lessons = await db.lessons.find({'skill_id': skill_id}, {'_id': 0}).to_list(1000)
    completed_lessons = await db.user_lessons.find({
        'user_id': current_user['id'],
        'lesson_id': {'$in': [lesson_item['id'] for lesson_item in all_lessons]},
        'completed': True
    }, {'_id': 0}).to_list(1000)
    
    progress_percent = int((len(completed_lessons) / len(all_lessons)) * 100) if all_lessons else 0
    
    user_skill = await db.user_skills.find_one({'user_id': current_user['id'], 'skill_id': skill_id}, {'_id': 0})
    if user_skill:
        await db.user_skills.update_one(
            {'id': user_skill['id']},
            {'$set': {'progress_percent': progress_percent}}
        )
    
    return {'message': 'Lesson completed', 'progress_percent': progress_percent}

# ============= AI ROUTES =============
@api_router.post("/ai/recommend-skills")
async def recommend_skills(request: Request):
    current_user = await get_current_user_from_request(request)
    user_skills = await db.user_skills.find({'user_id': current_user['id']}, {'_id': 0}).to_list(1000)
    all_skills = await db.skills.find({}, {'_id': 0}).to_list(1000)
    
    completed_skills = [us['skill_id'] for us in user_skills if us['status'] == 'completed']
    in_progress_skills = [us['skill_id'] for us in user_skills if us['status'] == 'in_progress']
    
    completed_skill_names = [s['name'] for s in all_skills if s['id'] in completed_skills]
    in_progress_skill_names = [s['name'] for s in all_skills if s['id'] in in_progress_skills]
    
    # Use Claude Sonnet 4 for recommendations (safety/deep reasoning)
    api_key = os.environ.get('EMERGENT_LLM_KEY')
    chat = LlmChat(
        api_key=api_key,
        session_id=f"recommend_{current_user['id']}_{datetime.now(timezone.utc).timestamp()}",
        system_message="You are a learning path advisor. Analyze completed and in-progress skills, then recommend the next 3-5 skills to learn. Consider skill difficulty progression and career paths. Respond with clear recommendations and reasoning."
    ).with_model("anthropic", "claude-3-7-sonnet-20250219")
    
    available_skills = [s for s in all_skills if s['id'] not in completed_skills and s['id'] not in in_progress_skills]
    available_skill_names = [f"{s['name']} ({s['difficulty']}, {s['category']})" for s in available_skills[:30]]
    
    prompt = f"""User Profile:
- Completed skills: {', '.join(completed_skill_names) if completed_skill_names else 'None'}
- In-progress skills: {', '.join(in_progress_skill_names) if in_progress_skill_names else 'None'}
- Current Level: {current_user['level']}
- Total XP: {current_user['xp']}

Available skills to learn: {', '.join(available_skill_names)}

Recommend 3-5 next skills with reasoning for each."""
    
    user_message = UserMessage(text=prompt)
    response = await chat.send_message(user_message)
    
    return {'recommendations': response, 'completed_skills': completed_skill_names, 'in_progress_skills': in_progress_skill_names}

@api_router.post("/ai/generate-lesson-content")
async def generate_lesson_content(data: dict, request: Request):
    await get_current_user_from_request(request)
    skill_name = data.get('skill_name', '')
    lesson_title = data.get('lesson_title', '')
    difficulty = data.get('difficulty', 'intermediate')
    
    # Use OpenAI GPT-5 for lesson content generation
    api_key = os.environ.get('EMERGENT_LLM_KEY')
    chat = LlmChat(
        api_key=api_key,
        session_id=f"lesson_{datetime.now(timezone.utc).timestamp()}",
        system_message="You are an expert instructor creating engaging, comprehensive lesson content. Include clear explanations, practical examples, code snippets when relevant, and key takeaways."
    ).with_model("openai", "gpt-5")
    
    prompt = f"""Create a detailed lesson about '{lesson_title}' for the skill '{skill_name}' at {difficulty} level.

Include:
1. Clear introduction and learning objectives
2. Main concepts with explanations
3. Practical examples or code snippets
4. Best practices
5. Key takeaways

Format the content in markdown for easy reading."""
    
    user_message = UserMessage(text=prompt)
    response = await chat.send_message(user_message)
    
    return {'content': response}

@api_router.post("/ai/generate-quiz")
async def generate_quiz(data: dict, request: Request):
    """Generate interactive quiz for a lesson using Gemini"""
    await get_current_user_from_request(request)
    skill_name = data.get('skill_name', '')
    lesson_content = data.get('lesson_content', '')
    
    api_key = os.environ.get('EMERGENT_LLM_KEY')
    chat = LlmChat(
        api_key=api_key,
        session_id=f"quiz_{datetime.now(timezone.utc).timestamp()}",
        system_message="You are a quiz creator. Generate 5 multiple-choice questions based on lesson content. Return JSON format: [{question: string, options: [string], correct: number}]"
    ).with_model("gemini", "gemini-2.5-pro")
    
    prompt = f"Create 5 multiple-choice questions for the skill '{skill_name}' based on this content: {lesson_content[:1000]}"
    
    user_message = UserMessage(text=prompt)
    response = await chat.send_message(user_message)
    
    return {'quiz': response}

# ============= INTEGRATIONS ROUTES =============
@api_router.get("/integrations")
async def get_integrations(request: Request):
    current_user = await get_current_user_from_request(request)
    connections = await db.external_connections.find({'user_id': current_user['id']}, {'_id': 0}).to_list(1000)
    
    platforms = ['github', 'linkedin', 'youtube']
    result = []
    
    for platform in platforms:
        conn = next((c for c in connections if c['platform'] == platform), None)
        if conn:
            result.append({
                'id': conn['id'],
                'platform': platform,
                'connected': conn['connected'],
                'platform_data': conn.get('platform_data'),
                'connected_at': conn.get('connected_at')
            })
        else:
            result.append({
                'id': str(uuid.uuid4()),
                'platform': platform,
                'connected': False,
                'platform_data': None
            })
    
    return result

@api_router.post("/integrations/github/connect")
async def connect_github(data: dict, request: Request):
    """Connect GitHub - mock with sample data for MVP"""
    current_user = await get_current_user_from_request(request)
    
    # Mock GitHub data
    platform_data = {
        'username': 'demo_user',
        'repos_count': 24,
        'commits_this_month': 87,
        'top_languages': ['Python', 'JavaScript', 'TypeScript', 'Go'],
        'recent_repos': [
            {'name': 'skilltree-clone', 'language': 'React', 'stars': 15},
            {'name': 'ml-learning', 'language': 'Python', 'stars': 8},
            {'name': 'api-design', 'language': 'Node.js', 'stars': 5}
        ]
    }
    
    existing = await db.external_connections.find_one({'user_id': current_user['id'], 'platform': 'github'}, {'_id': 0})
    
    if existing:
        await db.external_connections.update_one(
            {'id': existing['id']},
            {'$set': {
                'connected': True,
                'platform_data': platform_data,
                'connected_at': datetime.now(timezone.utc).isoformat()
            }}
        )
    else:
        conn_doc = {
            'id': str(uuid.uuid4()),
            'user_id': current_user['id'],
            'platform': 'github',
            'connected': True,
            'platform_data': platform_data,
            'connected_at': datetime.now(timezone.utc).isoformat()
        }
        await db.external_connections.insert_one(conn_doc)
    
    return {'message': 'GitHub connected successfully', 'data': platform_data}

@api_router.post("/integrations/linkedin/connect")
async def connect_linkedin(data: dict, request: Request):
    """Connect LinkedIn - mock with sample data for MVP"""
    current_user = await get_current_user_from_request(request)
    
    platform_data = {
        'name': current_user['name'],
        'headline': 'Software Engineer',
        'connections': 428,
        'courses_completed': [
            {'title': 'React - The Complete Guide', 'platform': 'LinkedIn Learning', 'completed_date': '2024-11-15'},
            {'title': 'Python for Data Science', 'platform': 'LinkedIn Learning', 'completed_date': '2024-10-20'},
            {'title': 'AWS Certified Solutions Architect', 'platform': 'LinkedIn Learning', 'completed_date': '2024-09-05'}
        ],
        'skills_endorsed': ['React', 'Python', 'Node.js', 'MongoDB', 'AWS']
    }
    
    existing = await db.external_connections.find_one({'user_id': current_user['id'], 'platform': 'linkedin'}, {'_id': 0})
    
    if existing:
        await db.external_connections.update_one(
            {'id': existing['id']},
            {'$set': {
                'connected': True,
                'platform_data': platform_data,
                'connected_at': datetime.now(timezone.utc).isoformat()
            }}
        )
    else:
        conn_doc = {
            'id': str(uuid.uuid4()),
            'user_id': current_user['id'],
            'platform': 'linkedin',
            'connected': True,
            'platform_data': platform_data,
            'connected_at': datetime.now(timezone.utc).isoformat()
        }
        await db.external_connections.insert_one(conn_doc)
    
    return {'message': 'LinkedIn connected successfully', 'data': platform_data}

@api_router.post("/integrations/youtube/connect")
async def connect_youtube(data: dict, request: Request):
    """Connect YouTube - mock with sample data for MVP"""
    current_user = await get_current_user_from_request(request)
    
    platform_data = {
        'channel_name': current_user['name'],
        'subscriptions': 87,
        'learning_playlists': [
            {'name': 'Web Development Tutorials', 'videos': 45, 'watch_time_hours': 28},
            {'name': 'Python Programming', 'videos': 32, 'watch_time_hours': 21},
            {'name': 'Machine Learning Basics', 'videos': 28, 'watch_time_hours': 18}
        ],
        'total_watch_time_hours': 245,
        'top_channels': ['Traversy Media', 'freeCodeCamp', 'Corey Schafer']
    }
    
    existing = await db.external_connections.find_one({'user_id': current_user['id'], 'platform': 'youtube'}, {'_id': 0})
    
    if existing:
        await db.external_connections.update_one(
            {'id': existing['id']},
            {'$set': {
                'connected': True,
                'platform_data': platform_data,
                'connected_at': datetime.now(timezone.utc).isoformat()
            }}
        )
    else:
        conn_doc = {
            'id': str(uuid.uuid4()),
            'user_id': current_user['id'],
            'platform': 'youtube',
            'connected': True,
            'platform_data': platform_data,
            'connected_at': datetime.now(timezone.utc).isoformat()
        }
        await db.external_connections.insert_one(conn_doc)
    
    return {'message': 'YouTube connected successfully', 'data': platform_data}

@api_router.post("/integrations/{platform}/disconnect")
async def disconnect_platform(platform: str, request: Request):
    current_user = await get_current_user_from_request(request)
    
    result = await db.external_connections.update_one(
        {'user_id': current_user['id'], 'platform': platform},
        {'$set': {'connected': False, 'platform_data': None, 'access_token': None}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Connection not found")
    
    return {'message': f'{platform} disconnected successfully'}

# ============= DASHBOARD ROUTES =============
@api_router.get("/dashboard/stats")
async def get_dashboard_stats(request: Request):
    current_user = await get_current_user_from_request(request)
    user_skills = await db.user_skills.find({'user_id': current_user['id']}, {'_id': 0}).to_list(1000)
    all_skills = await db.skills.find({}, {'_id': 0}).to_list(1000)
    
    completed = len([us for us in user_skills if us['status'] == 'completed'])
    in_progress = len([us for us in user_skills if us['status'] == 'in_progress'])
    total_skills = len(all_skills)
    
    # Get recent activity
    recent_completions = sorted(
        [us for us in user_skills if us['status'] == 'completed' and us.get('completed_at')],
        key=lambda x: x['completed_at'],
        reverse=True
    )[:5]
    
    return {
        'total_xp': current_user['xp'],
        'level': current_user['level'],
        'skills_completed': completed,
        'skills_in_progress': in_progress,
        'total_skills': total_skills,
        'completion_rate': round((completed / total_skills * 100), 1) if total_skills > 0 else 0,
        'recent_completions': [rc['skill_id'] for rc in recent_completions]
    }

@api_router.get("/achievements")
async def get_achievements(request: Request):
    current_user = await get_current_user_from_request(request)
    user_skills = await db.user_skills.find({'user_id': current_user['id']}, {'_id': 0}).to_list(1000)
    completed = len([us for us in user_skills if us['status'] == 'completed'])
    
    # Get unique categories completed
    all_skills = await db.skills.find({}, {'_id': 0}).to_list(1000)
    completed_skill_ids = [us['skill_id'] for us in user_skills if us['status'] == 'completed']
    completed_categories = set([s['category'] for s in all_skills if s['id'] in completed_skill_ids])
    
    achievements = [
        {'id': 'first_skill', 'name': 'First Steps', 'description': 'Complete your first skill', 'icon': 'Trophy', 'unlocked': completed >= 1},
        {'id': 'three_skills', 'name': 'On a Roll', 'description': 'Complete 3 skills', 'icon': 'Award', 'unlocked': completed >= 3},
        {'id': 'five_skills', 'name': 'Rising Star', 'description': 'Complete 5 skills', 'icon': 'Star', 'unlocked': completed >= 5},
        {'id': 'ten_skills', 'name': 'Dedicated Learner', 'description': 'Complete 10 skills', 'icon': 'Flame', 'unlocked': completed >= 10},
        {'id': 'level_5', 'name': 'Expert Learner', 'description': 'Reach level 5', 'icon': 'Zap', 'unlocked': current_user['level'] >= 5},
        {'id': 'three_categories', 'name': 'Jack of All Trades', 'description': 'Complete skills in 3 categories', 'icon': 'Layers', 'unlocked': len(completed_categories) >= 3},
    ]
    
    return achievements

@api_router.get("/activity-feed")
async def get_activity_feed(request: Request):
    current_user = await get_current_user_from_request(request)
    user_skills = await db.user_skills.find(
        {'user_id': current_user['id'], 'status': 'completed'}, 
        {'_id': 0}
    ).sort('completed_at', -1).limit(10).to_list(10)
    
    activities = []
    for us in user_skills:
        if us.get('completed_at'):
            skill = await db.skills.find_one({'id': us['skill_id']}, {'_id': 0})
            if skill:
                activities.append({
                    'type': 'skill_completed',
                    'title': f'Completed {skill["name"]}',
                    'description': f'Earned {skill["xp_value"]} XP',
                    'timestamp': us['completed_at'],
                    'icon': 'CheckCircle'
                })
    
    return activities

# ============= SEED DATA ROUTE =============
@api_router.post("/seed-data")
async def seed_data():
    existing_skills = await db.skills.count_documents({})
    if existing_skills > 0:
        return {'message': 'Data already seeded'}
    
    skills_data = [
        # Web Development Path
        {'id': 'skill-1', 'name': 'HTML Basics', 'description': 'Learn the fundamentals of HTML markup language', 'category': 'Web Development', 'difficulty': 'beginner', 'prerequisites': [], 'xp_value': 100, 'icon': 'Code', 'position': {'x': 0, 'y': 0}},
        {'id': 'skill-2', 'name': 'CSS Fundamentals', 'description': 'Master styling with CSS and create beautiful designs', 'category': 'Web Development', 'difficulty': 'beginner', 'prerequisites': ['skill-1'], 'xp_value': 150, 'icon': 'Palette', 'position': {'x': 1, 'y': 0}},
        {'id': 'skill-3', 'name': 'JavaScript Basics', 'description': 'Introduction to JavaScript programming', 'category': 'Web Development', 'difficulty': 'beginner', 'prerequisites': ['skill-1'], 'xp_value': 200, 'icon': 'Code2', 'position': {'x': 0, 'y': 1}},
        {'id': 'skill-4', 'name': 'Responsive Design', 'description': 'Build mobile-friendly websites', 'category': 'Web Development', 'difficulty': 'intermediate', 'prerequisites': ['skill-2'], 'xp_value': 200, 'icon': 'Smartphone', 'position': {'x': 2, 'y': 0}},
        {'id': 'skill-5', 'name': 'React Fundamentals', 'description': 'Build modern UIs with React', 'category': 'Web Development', 'difficulty': 'intermediate', 'prerequisites': ['skill-3'], 'xp_value': 300, 'icon': 'Component', 'position': {'x': 1, 'y': 1}},
        {'id': 'skill-6', 'name': 'Advanced React', 'description': 'Hooks, Context, and Performance', 'category': 'Web Development', 'difficulty': 'advanced', 'prerequisites': ['skill-5'], 'xp_value': 400, 'icon': 'Layers', 'position': {'x': 2, 'y': 1}},
        
        # Backend Path
        {'id': 'skill-7', 'name': 'Python Basics', 'description': 'Learn Python programming fundamentals', 'category': 'Backend', 'difficulty': 'beginner', 'prerequisites': [], 'xp_value': 200, 'icon': 'Code', 'position': {'x': 4, 'y': 0}},
        {'id': 'skill-8', 'name': 'Python OOP', 'description': 'Object-Oriented Programming in Python', 'category': 'Backend', 'difficulty': 'intermediate', 'prerequisites': ['skill-7'], 'xp_value': 250, 'icon': 'Box', 'position': {'x': 5, 'y': 0}},
        {'id': 'skill-9', 'name': 'FastAPI', 'description': 'Build REST APIs with FastAPI', 'category': 'Backend', 'difficulty': 'intermediate', 'prerequisites': ['skill-8'], 'xp_value': 300, 'icon': 'Server', 'position': {'x': 4, 'y': 1}},
        {'id': 'skill-10', 'name': 'API Security', 'description': 'Authentication & Authorization', 'category': 'Backend', 'difficulty': 'advanced', 'prerequisites': ['skill-9'], 'xp_value': 350, 'icon': 'Shield', 'position': {'x': 5, 'y': 1}},
        
        # Database Path
        {'id': 'skill-11', 'name': 'SQL Basics', 'description': 'Relational database fundamentals', 'category': 'Database', 'difficulty': 'beginner', 'prerequisites': [], 'xp_value': 180, 'icon': 'Database', 'position': {'x': 7, 'y': 0}},
        {'id': 'skill-12', 'name': 'MongoDB', 'description': 'NoSQL database with MongoDB', 'category': 'Database', 'difficulty': 'intermediate', 'prerequisites': ['skill-11'], 'xp_value': 250, 'icon': 'Database', 'position': {'x': 6, 'y': 1}},
        {'id': 'skill-13', 'name': 'Database Design', 'description': 'Schema design and optimization', 'category': 'Database', 'difficulty': 'advanced', 'prerequisites': ['skill-12'], 'xp_value': 300, 'icon': 'GitBranch', 'position': {'x': 7, 'y': 1}},
        
        # Data Science Path
        {'id': 'skill-14', 'name': 'Data Analysis', 'description': 'Analyze data with Python', 'category': 'Data Science', 'difficulty': 'intermediate', 'prerequisites': ['skill-7'], 'xp_value': 280, 'icon': 'BarChart', 'position': {'x': 4, 'y': 2}},
        {'id': 'skill-15', 'name': 'Machine Learning', 'description': 'Build ML models with scikit-learn', 'category': 'Data Science', 'difficulty': 'advanced', 'prerequisites': ['skill-14'], 'xp_value': 450, 'icon': 'Brain', 'position': {'x': 5, 'y': 2}},
        
        # DevOps Path
        {'id': 'skill-16', 'name': 'Git & GitHub', 'description': 'Version control with Git', 'category': 'DevOps', 'difficulty': 'beginner', 'prerequisites': [], 'xp_value': 150, 'icon': 'GitBranch', 'position': {'x': 9, 'y': 0}},
        {'id': 'skill-17', 'name': 'Docker Basics', 'description': 'Containerization with Docker', 'category': 'DevOps', 'difficulty': 'intermediate', 'prerequisites': ['skill-16'], 'xp_value': 320, 'icon': 'Package', 'position': {'x': 9, 'y': 1}},
        {'id': 'skill-18', 'name': 'CI/CD', 'description': 'Continuous Integration & Deployment', 'category': 'DevOps', 'difficulty': 'advanced', 'prerequisites': ['skill-17'], 'xp_value': 400, 'icon': 'RefreshCw', 'position': {'x': 9, 'y': 2}},
        
        # Projects
        {'id': 'skill-19', 'name': 'Portfolio Website', 'description': 'Build your personal portfolio', 'category': 'Projects', 'difficulty': 'intermediate', 'prerequisites': ['skill-4', 'skill-5'], 'xp_value': 350, 'icon': 'Globe', 'position': {'x': 2, 'y': 2}},
        {'id': 'skill-20', 'name': 'Full-Stack App', 'description': 'Complete CRUD application', 'category': 'Projects', 'difficulty': 'advanced', 'prerequisites': ['skill-6', 'skill-9', 'skill-12'], 'xp_value': 600, 'icon': 'Rocket', 'position': {'x': 5, 'y': 3}},
    ]
    
    await db.skills.insert_many(skills_data)
    
    lessons_data = [
        # HTML Basics lessons
        {'id': 'lesson-1-1', 'skill_id': 'skill-1', 'title': 'Introduction to HTML', 'content': 'HTML (HyperText Markup Language) is the standard markup language for creating web pages. It describes the structure of web content using elements and tags.\n\nKey Concepts:\n- HTML defines the structure of web content\n- Elements are defined by tags\n- Tags tell the browser how to display content\n- HTML5 is the latest version', 'order': 1, 'estimated_time': 15, 'resources': [{'title': 'MDN HTML Guide', 'url': 'https://developer.mozilla.org/en-US/docs/Web/HTML'}]},
        {'id': 'lesson-1-2', 'skill_id': 'skill-1', 'title': 'HTML Tags and Elements', 'content': 'HTML uses tags to define elements. Tags are enclosed in angle brackets like <tag>.\n\nCommon Tags:\n- <h1> to <h6>: Headings\n- <p>: Paragraphs\n- <a>: Links\n- <img>: Images\n- <div>: Containers\n- <span>: Inline containers', 'order': 2, 'estimated_time': 20, 'resources': []},
        {'id': 'lesson-1-3', 'skill_id': 'skill-1', 'title': 'HTML Document Structure', 'content': 'Every HTML document has a basic structure:\n\n<!DOCTYPE html>\n<html>\n<head>\n  <title>Page Title</title>\n</head>\n<body>\n  Content goes here\n</body>\n</html>\n\nThe DOCTYPE tells browsers this is HTML5.', 'order': 3, 'estimated_time': 25, 'resources': []},
        
        # CSS lessons
        {'id': 'lesson-2-1', 'skill_id': 'skill-2', 'title': 'CSS Basics', 'content': 'CSS (Cascading Style Sheets) is used to style HTML elements. It controls colors, fonts, layouts, and more.\n\nBasic Syntax:\nselector {\n  property: value;\n}\n\nExample:\nh1 {\n  color: blue;\n  font-size: 24px;\n}', 'order': 1, 'estimated_time': 20, 'resources': [{'title': 'CSS Tricks', 'url': 'https://css-tricks.com/'}]},
        {'id': 'lesson-2-2', 'skill_id': 'skill-2', 'title': 'CSS Selectors', 'content': 'CSS selectors target HTML elements:\n\n- Element: p { }\n- Class: .classname { }\n- ID: #idname { }\n- Descendant: div p { }\n- Child: div > p { }\n- Attribute: [type="text"] { }', 'order': 2, 'estimated_time': 25, 'resources': []},
        {'id': 'lesson-2-3', 'skill_id': 'skill-2', 'title': 'CSS Box Model', 'content': 'The box model consists of:\n- Content: The actual content\n- Padding: Space around content\n- Border: Surrounds padding\n- Margin: Space outside border\n\nUnderstanding this is crucial for layouts!', 'order': 3, 'estimated_time': 30, 'resources': []},
        
        # JavaScript lessons
        {'id': 'lesson-3-1', 'skill_id': 'skill-3', 'title': 'JavaScript Introduction', 'content': 'JavaScript is a programming language that adds interactivity to web pages. It runs in the browser and can manipulate HTML and CSS.\n\nKey Features:\n- Dynamic typing\n- Event-driven\n- Runs in browser\n- Can manipulate DOM', 'order': 1, 'estimated_time': 20, 'resources': [{'title': 'JavaScript.info', 'url': 'https://javascript.info/'}]},
        {'id': 'lesson-3-2', 'skill_id': 'skill-3', 'title': 'Variables and Data Types', 'content': 'JavaScript variables:\n\nlet name = "John";  // String\nconst age = 25;     // Number\nlet isActive = true; // Boolean\nlet items = [];     // Array\nlet person = {};    // Object\n\nUse let for variables, const for constants.', 'order': 2, 'estimated_time': 30, 'resources': []},
        
        # Python lessons
        {'id': 'lesson-7-1', 'skill_id': 'skill-7', 'title': 'Python Basics', 'content': 'Python is a versatile programming language known for its readability.\n\nBasic Syntax:\nprint("Hello, World!")\n\nname = "Alice"\nage = 30\n\nif age > 18:\n    print("Adult")\n\nPython uses indentation for code blocks!', 'order': 1, 'estimated_time': 25, 'resources': [{'title': 'Python.org Tutorial', 'url': 'https://docs.python.org/3/tutorial/'}]},
        {'id': 'lesson-7-2', 'skill_id': 'skill-7', 'title': 'Python Data Structures', 'content': 'Python Data Structures:\n\nList: [1, 2, 3]\nTuple: (1, 2, 3)\nDict: {"key": "value"}\nSet: {1, 2, 3}\n\nLists are mutable, tuples are immutable.', 'order': 2, 'estimated_time': 30, 'resources': []},
    ]
    
    await db.lessons.insert_many(lessons_data)
    
    return {'message': 'Data seeded successfully', 'skills_count': len(skills_data), 'lessons_count': len(lessons_data)}

# Include the router
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
