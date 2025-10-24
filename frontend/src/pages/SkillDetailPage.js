import { useState, useEffect } from 'react';
import axios from 'axios';
import { API } from '@/App';
import { useNavigate, useParams } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { TreePine, LogOut, CheckCircle, Clock, ArrowLeft, Sparkles } from 'lucide-react';
import { toast } from 'sonner';

export default function SkillDetailPage({ user, onLogout }) {
  const navigate = useNavigate();
  const { skillId } = useParams();
  const [skill, setSkill] = useState(null);
  const [lessons, setLessons] = useState([]);
  const [loading, setLoading] = useState(true);
  const [generatingLesson, setGeneratingLesson] = useState(null);

  useEffect(() => {
    fetchSkillAndLessons();
  }, [skillId]);

  const fetchSkillAndLessons = async () => {
    try {
      const [skillRes, lessonsRes] = await Promise.all([
        axios.get(`${API}/skills/${skillId}`),
        axios.get(`${API}/skills/${skillId}/lessons`)
      ]);
      setSkill(skillRes.data);
      setLessons(lessonsRes.data);
    } catch (error) {
      toast.error('Failed to load skill details');
    }
    setLoading(false);
  };

  const completeLesson = async (lessonId) => {
    try {
      const response = await axios.post(`${API}/lessons/${lessonId}/complete`);
      toast.success('Lesson completed!');
      if (response.data.progress_percent === 100) {
        toast.success('Skill completed! 🎉');
      }
      fetchSkillAndLessons();
    } catch (error) {
      toast.error('Failed to complete lesson');
    }
  };

  const generateLessonContent = async (lesson) => {
    setGeneratingLesson(lesson.id);
    try {
      const response = await axios.post(`${API}/ai/generate-lesson-content`, {
        skill_name: skill.name,
        lesson_title: lesson.title
      });
      toast.success('AI content generated!');
      // Update lesson content locally
      setLessons(lessons.map(l => 
        l.id === lesson.id ? { ...l, content: response.data.content } : l
      ));
    } catch (error) {
      toast.error('Failed to generate content');
    }
    setGeneratingLesson(null);
  };

  const completeSkill = async () => {
    try {
      const response = await axios.post(`${API}/user-skills/${skillId}/complete`);
      toast.success(`Skill completed! +${response.data.xp_earned} XP 🎉`);
      navigate('/skill-tree');
    } catch (error) {
      toast.error('Failed to complete skill');
    }
  };

  if (loading) {
    return <div className="flex items-center justify-center min-h-screen">Loading...</div>;
  }

  const completedLessons = lessons.filter(l => l.completed).length;
  const progressPercent = lessons.length > 0 ? Math.round((completedLessons / lessons.length) * 100) : 0;

  return (
    <div className="min-h-screen">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-10" data-testid="skill-detail-header">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <TreePine className="w-8 h-8 text-purple-600" />
              <h1 className="text-2xl font-bold">SkillTree</h1>
            </div>
            <nav className="flex items-center gap-4">
              <Button variant="ghost" onClick={() => navigate('/dashboard')} data-testid="nav-dashboard-btn">Dashboard</Button>
              <Button variant="ghost" onClick={() => navigate('/skill-tree')} data-testid="nav-skill-tree-btn">Skill Tree</Button>
              <Button variant="ghost" onClick={() => navigate('/integrations')} data-testid="nav-integrations-btn">Integrations</Button>
              <Button variant="outline" size="sm" onClick={onLogout} data-testid="logout-btn">
                <LogOut className="w-4 h-4 mr-2" />
                Logout
              </Button>
            </nav>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8" data-testid="skill-detail-main">
        <Button variant="ghost" onClick={() => navigate('/skill-tree')} className="mb-6" data-testid="back-to-tree-btn">
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back to Skill Tree
        </Button>

        {/* Skill Header */}
        <Card className="mb-8" data-testid="skill-header-card">
          <CardHeader>
            <div className="flex items-start justify-between">
              <div>
                <CardTitle className="text-3xl mb-2">{skill.name}</CardTitle>
                <CardDescription className="text-lg">{skill.description}</CardDescription>
                <div className="flex gap-2 mt-3">
                  <Badge variant="secondary">{skill.category}</Badge>
                  <Badge variant="secondary">{skill.difficulty}</Badge>
                  <Badge variant="secondary">{skill.xp_value} XP</Badge>
                </div>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-gray-600">Overall Progress</span>
              <span className="text-sm font-semibold">{progressPercent}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-3">
              <div
                className="bg-purple-600 h-3 rounded-full transition-all"
                style={{ width: `${progressPercent}%` }}
              ></div>
            </div>
            {progressPercent === 100 && (
              <Button className="w-full mt-4" onClick={completeSkill} data-testid="complete-skill-btn">
                Complete Skill & Earn {skill.xp_value} XP
              </Button>
            )}
          </CardContent>
        </Card>

        {/* Lessons List */}
        <div className="space-y-4" data-testid="lessons-list">
          <h2 className="text-2xl font-bold mb-4">Lessons ({completedLessons}/{lessons.length})</h2>
          {lessons.map((lesson, index) => (
            <Card key={lesson.id} className="card-hover" data-testid={`lesson-card-${lesson.id}`}>
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3">
                      <span className="text-sm font-semibold text-gray-500">Lesson {index + 1}</span>
                      {lesson.completed && <CheckCircle className="w-5 h-5 text-green-500" />}
                    </div>
                    <CardTitle className="text-xl mt-1">{lesson.title}</CardTitle>
                    <div className="flex items-center gap-2 mt-2 text-sm text-gray-600">
                      <Clock className="w-4 h-4" />
                      <span>{lesson.estimated_time} minutes</span>
                    </div>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="prose prose-sm max-w-none mb-4" data-testid={`lesson-content-${lesson.id}`}>
                  <p className="text-gray-700 whitespace-pre-wrap">{lesson.content}</p>
                </div>
                <div className="flex gap-2">
                  {!lesson.completed && (
                    <Button onClick={() => completeLesson(lesson.id)} data-testid={`complete-lesson-btn-${lesson.id}`}>
                      Mark as Complete
                    </Button>
                  )}
                  <Button
                    variant="outline"
                    onClick={() => generateLessonContent(lesson)}
                    disabled={generatingLesson === lesson.id}
                    data-testid={`generate-content-btn-${lesson.id}`}
                  >
                    <Sparkles className="w-4 h-4 mr-2" />
                    {generatingLesson === lesson.id ? 'Generating...' : 'AI Enhance Content'}
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </main>
    </div>
  );
}