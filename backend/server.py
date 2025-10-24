from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
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
import bcrypt
import jwt
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
class UserRegister(BaseModel):
    email: EmailStr
    password: str
    name: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    email: str
    name: str
    xp: int = 0
    level: int = 1
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
    mock_data: Optional[Dict[str, Any]] = None
    connected_at: Optional[str] = None

# ============= AUTH HELPERS =============
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

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

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    token = credentials.credentials
    payload = decode_token(token)
    user = await db.users.find_one({'id': payload['user_id']}, {'_id': 0})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user

# ============= AUTH ROUTES =============
@api_router.post("/auth/register")
async def register(data: UserRegister):
    existing = await db.users.find_one({'email': data.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user_id = str(uuid.uuid4())
    user_doc = {
        'id': user_id,
        'email': data.email,
        'password_hash': hash_password(data.password),
        'name': data.name,
        'xp': 0,
        'level': 1,
        'created_at': datetime.now(timezone.utc).isoformat()
    }
    
    await db.users.insert_one(user_doc)
    token = create_token(user_id)
    
    return {'token': token, 'user': {'id': user_id, 'email': data.email, 'name': data.name, 'xp': 0, 'level': 1}}

@api_router.post("/auth/login")
async def login(data: UserLogin):
    user = await db.users.find_one({'email': data.email})
    if not user or not verify_password(data.password, user['password_hash']):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_token(user['id'])
    return {'token': token, 'user': {'id': user['id'], 'email': user['email'], 'name': user['name'], 'xp': user['xp'], 'level': user['level']}}

@api_router.get("/auth/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    return {'id': current_user['id'], 'email': current_user['email'], 'name': current_user['name'], 'xp': current_user['xp'], 'level': current_user['level']}

# ============= SKILLS ROUTES =============
@api_router.get("/skills")
async def get_skills(current_user: dict = Depends(get_current_user)):
    skills = await db.skills.find({}, {'_id': 0}).to_list(1000)
    user_skills = await db.user_skills.find({'user_id': current_user['id']}, {'_id': 0}).to_list(1000)
    
    # Map user progress to skills
    user_skill_map = {us['skill_id']: us for us in user_skills}
    
    for skill in skills:
        skill_id = skill['id']
        if skill_id in user_skill_map:
            skill['user_status'] = user_skill_map[skill_id]['status']
            skill['user_progress'] = user_skill_map[skill_id]['progress_percent']
        else:
            # Check if prerequisites are met
            prereqs_met = True
            for prereq_id in skill.get('prerequisites', []):
                if prereq_id not in user_skill_map or user_skill_map[prereq_id]['status'] != 'completed':
                    prereqs_met = False
                    break
            skill['user_status'] = 'available' if (prereqs_met and len(skill.get('prerequisites', [])) > 0) or len(skill.get('prerequisites', [])) == 0 else 'locked'
            skill['user_progress'] = 0
    
    return skills

@api_router.get("/skills/{skill_id}")
async def get_skill(skill_id: str, current_user: dict = Depends(get_current_user)):
    skill = await db.skills.find_one({'id': skill_id}, {'_id': 0})
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    return skill

@api_router.post("/user-skills/{skill_id}/start")
async def start_skill(skill_id: str, current_user: dict = Depends(get_current_user)):
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
    return {'message': 'Skill started', 'user_skill': user_skill_doc}

@api_router.put("/user-skills/{skill_id}/progress")
async def update_progress(skill_id: str, progress: dict, current_user: dict = Depends(get_current_user)):
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
async def complete_skill(skill_id: str, current_user: dict = Depends(get_current_user)):
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
    
    # Award XP
    new_xp = current_user['xp'] + skill['xp_value']
    new_level = 1 + (new_xp // 1000)  # Level up every 1000 XP
    
    await db.users.update_one(
        {'id': current_user['id']},
        {'$set': {'xp': new_xp, 'level': new_level}}
    )
    
    return {'message': 'Skill completed', 'xp_earned': skill['xp_value'], 'total_xp': new_xp, 'level': new_level}

# ============= LESSONS ROUTES =============
@api_router.get("/skills/{skill_id}/lessons")
async def get_lessons(skill_id: str, current_user: dict = Depends(get_current_user)):
    lessons = await db.lessons.find({'skill_id': skill_id}, {'_id': 0}).sort('order', 1).to_list(1000)
    user_lessons = await db.user_lessons.find({'user_id': current_user['id']}, {'_id': 0}).to_list(1000)
    
    user_lesson_map = {ul['lesson_id']: ul for ul in user_lessons}
    
    for lesson in lessons:
        lesson['completed'] = user_lesson_map.get(lesson['id'], {}).get('completed', False)
    
    return lessons

@api_router.post("/lessons/{lesson_id}/complete")
async def complete_lesson(lesson_id: str, current_user: dict = Depends(get_current_user)):
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
    
    # Update skill progress
    skill_id = lesson['skill_id']
    all_lessons = await db.lessons.find({'skill_id': skill_id}, {'_id': 0}).to_list(1000)
    completed_lessons = await db.user_lessons.find({
        'user_id': current_user['id'],
        'lesson_id': {'$in': [l['id'] for l in all_lessons]},
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
async def recommend_skills(current_user: dict = Depends(get_current_user)):
    user_skills = await db.user_skills.find({'user_id': current_user['id']}, {'_id': 0}).to_list(1000)
    all_skills = await db.skills.find({}, {'_id': 0}).to_list(1000)
    
    completed_skills = [us['skill_id'] for us in user_skills if us['status'] == 'completed']
    completed_skill_names = [s['name'] for s in all_skills if s['id'] in completed_skills]
    
    # Use AI to recommend next skills
    api_key = os.environ.get('EMERGENT_LLM_KEY')
    chat = LlmChat(
        api_key=api_key,
        session_id=f"recommend_{current_user['id']}_{datetime.now(timezone.utc).timestamp()}",
        system_message="You are a learning path advisor. Based on completed skills, recommend the next 3 skills to learn. Respond in JSON format with an array of objects containing 'skill_name' and 'reason'."
    ).with_model("openai", "gpt-4o-mini")
    
    available_skills = [s for s in all_skills if s['id'] not in completed_skills]
    available_skill_names = [s['name'] for s in available_skills[:20]]  # Limit to first 20 for context
    
    prompt = f"User has completed these skills: {', '.join(completed_skill_names) if completed_skill_names else 'None'}. Available skills to learn: {', '.join(available_skill_names)}. Recommend 3 next skills and explain why."
    
    user_message = UserMessage(text=prompt)
    response = await chat.send_message(user_message)
    
    return {'recommendations': response, 'completed_skills': completed_skill_names}

@api_router.post("/ai/generate-lesson-content")
async def generate_lesson_content(data: dict, current_user: dict = Depends(get_current_user)):
    skill_name = data.get('skill_name', '')
    lesson_title = data.get('lesson_title', '')
    
    api_key = os.environ.get('EMERGENT_LLM_KEY')
    chat = LlmChat(
        api_key=api_key,
        session_id=f"lesson_{current_user['id']}_{datetime.now(timezone.utc).timestamp()}",
        system_message="You are an expert instructor. Create detailed, engaging lesson content for the given skill and topic."
    ).with_model("openai", "gpt-4o-mini")
    
    prompt = f"Create a comprehensive lesson about '{lesson_title}' for the skill '{skill_name}'. Include explanations, examples, and key takeaways."
    
    user_message = UserMessage(text=prompt)
    response = await chat.send_message(user_message)
    
    return {'content': response}

# ============= INTEGRATIONS ROUTES =============
@api_router.get("/integrations")
async def get_integrations(current_user: dict = Depends(get_current_user)):
    connections = await db.external_connections.find({'user_id': current_user['id']}, {'_id': 0}).to_list(1000)
    
    platforms = ['github', 'linkedin', 'youtube']
    result = []
    
    for platform in platforms:
        conn = next((c for c in connections if c['platform'] == platform), None)
        if conn:
            result.append(conn)
        else:
            result.append({
                'id': str(uuid.uuid4()),
                'user_id': current_user['id'],
                'platform': platform,
                'connected': False,
                'mock_data': None
            })
    
    return result

@api_router.post("/integrations/connect/{platform}")
async def connect_platform(platform: str, current_user: dict = Depends(get_current_user)):
    if platform not in ['github', 'linkedin', 'youtube']:
        raise HTTPException(status_code=400, detail="Invalid platform")
    
    # Mock data based on platform
    mock_data = {
        'github': {'repos': 15, 'commits_this_month': 42, 'languages': ['Python', 'JavaScript', 'TypeScript']},
        'linkedin': {'connections': 350, 'skills_endorsed': ['Web Development', 'React', 'Python'], 'courses_completed': 8},
        'youtube': {'subscribed_channels': 25, 'learning_playlists': 12, 'watch_time_hours': 156}
    }
    
    existing = await db.external_connections.find_one({'user_id': current_user['id'], 'platform': platform})
    
    if existing:
        await db.external_connections.update_one(
            {'id': existing['id']},
            {'$set': {'connected': True, 'mock_data': mock_data[platform], 'connected_at': datetime.now(timezone.utc).isoformat()}}
        )
    else:
        conn_doc = {
            'id': str(uuid.uuid4()),
            'user_id': current_user['id'],
            'platform': platform,
            'connected': True,
            'mock_data': mock_data[platform],
            'connected_at': datetime.now(timezone.utc).isoformat()
        }
        await db.external_connections.insert_one(conn_doc)
    
    return {'message': f'{platform} connected successfully', 'mock_data': mock_data[platform]}

@api_router.get("/integrations/{platform}/sync")
async def sync_platform(platform: str, current_user: dict = Depends(get_current_user)):
    connection = await db.external_connections.find_one({'user_id': current_user['id'], 'platform': platform})
    if not connection or not connection['connected']:
        raise HTTPException(status_code=400, detail="Platform not connected")
    
    return {'message': 'Sync successful', 'data': connection['mock_data']}

# ============= DASHBOARD ROUTES =============
@api_router.get("/dashboard/stats")
async def get_dashboard_stats(current_user: dict = Depends(get_current_user)):
    user_skills = await db.user_skills.find({'user_id': current_user['id']}, {'_id': 0}).to_list(1000)
    all_skills = await db.skills.find({}, {'_id': 0}).to_list(1000)
    
    completed = len([us for us in user_skills if us['status'] == 'completed'])
    in_progress = len([us for us in user_skills if us['status'] == 'in_progress'])
    total_skills = len(all_skills)
    
    return {
        'total_xp': current_user['xp'],
        'level': current_user['level'],
        'skills_completed': completed,
        'skills_in_progress': in_progress,
        'total_skills': total_skills,
        'completion_rate': round((completed / total_skills * 100), 1) if total_skills > 0 else 0
    }

# ============= SEED DATA ROUTE =============
@api_router.post("/seed-data")
async def seed_data():
    # Check if already seeded
    existing_skills = await db.skills.count_documents({})
    if existing_skills > 0:
        return {'message': 'Data already seeded'}
    
    # Seed skills with tree structure
    skills_data = [
        {'id': 'skill-1', 'name': 'HTML Basics', 'description': 'Learn the fundamentals of HTML', 'category': 'Web Development', 'difficulty': 'beginner', 'prerequisites': [], 'xp_value': 100, 'icon': 'Code', 'position': {'x': 0, 'y': 0}},
        {'id': 'skill-2', 'name': 'CSS Fundamentals', 'description': 'Master styling with CSS', 'category': 'Web Development', 'difficulty': 'beginner', 'prerequisites': ['skill-1'], 'xp_value': 150, 'icon': 'Palette', 'position': {'x': 1, 'y': 0}},
        {'id': 'skill-3', 'name': 'JavaScript Basics', 'description': 'Introduction to JavaScript programming', 'category': 'Programming', 'difficulty': 'beginner', 'prerequisites': ['skill-1'], 'xp_value': 200, 'icon': 'Code2', 'position': {'x': 0, 'y': 1}},
        {'id': 'skill-4', 'name': 'React Fundamentals', 'description': 'Build UIs with React', 'category': 'Web Development', 'difficulty': 'intermediate', 'prerequisites': ['skill-2', 'skill-3'], 'xp_value': 300, 'icon': 'Component', 'position': {'x': 1, 'y': 1}},
        {'id': 'skill-5', 'name': 'Python Basics', 'description': 'Learn Python programming', 'category': 'Programming', 'difficulty': 'beginner', 'prerequisites': [], 'xp_value': 200, 'icon': 'Code', 'position': {'x': 2, 'y': 0}},
        {'id': 'skill-6', 'name': 'FastAPI', 'description': 'Build APIs with FastAPI', 'category': 'Backend', 'difficulty': 'intermediate', 'prerequisites': ['skill-5'], 'xp_value': 300, 'icon': 'Server', 'position': {'x': 2, 'y': 1}},
        {'id': 'skill-7', 'name': 'MongoDB', 'description': 'NoSQL database fundamentals', 'category': 'Database', 'difficulty': 'intermediate', 'prerequisites': ['skill-5'], 'xp_value': 250, 'icon': 'Database', 'position': {'x': 3, 'y': 1}},
        {'id': 'skill-8', 'name': 'Full-Stack Project', 'description': 'Build a complete application', 'category': 'Project', 'difficulty': 'advanced', 'prerequisites': ['skill-4', 'skill-6', 'skill-7'], 'xp_value': 500, 'icon': 'Rocket', 'position': {'x': 2, 'y': 2}},
    ]
    
    await db.skills.insert_many(skills_data)
    
    # Seed lessons
    lessons_data = [
        {'id': 'lesson-1-1', 'skill_id': 'skill-1', 'title': 'Introduction to HTML', 'content': 'HTML (HyperText Markup Language) is the standard markup language for creating web pages...', 'order': 1, 'estimated_time': 15},
        {'id': 'lesson-1-2', 'skill_id': 'skill-1', 'title': 'HTML Tags and Elements', 'content': 'HTML uses tags to define elements. Tags are enclosed in angle brackets...', 'order': 2, 'estimated_time': 20},
        {'id': 'lesson-1-3', 'skill_id': 'skill-1', 'title': 'HTML Document Structure', 'content': 'Every HTML document has a basic structure with DOCTYPE, html, head, and body tags...', 'order': 3, 'estimated_time': 25},
        
        {'id': 'lesson-2-1', 'skill_id': 'skill-2', 'title': 'CSS Basics', 'content': 'CSS (Cascading Style Sheets) is used to style HTML elements...', 'order': 1, 'estimated_time': 20},
        {'id': 'lesson-2-2', 'skill_id': 'skill-2', 'title': 'CSS Selectors', 'content': 'CSS selectors allow you to target specific HTML elements for styling...', 'order': 2, 'estimated_time': 25},
        
        {'id': 'lesson-3-1', 'skill_id': 'skill-3', 'title': 'JavaScript Introduction', 'content': 'JavaScript is a programming language that adds interactivity to web pages...', 'order': 1, 'estimated_time': 20},
        {'id': 'lesson-3-2', 'skill_id': 'skill-3', 'title': 'Variables and Data Types', 'content': 'JavaScript variables can hold different types of data...', 'order': 2, 'estimated_time': 30},
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