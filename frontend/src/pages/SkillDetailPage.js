import { useState, useEffect } from 'react';
import axios from 'axios';
import { useNavigate, useParams } from 'react-router-dom';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '@/components/ui/accordion';
import { TreePine, LogOut, CheckCircle2, Clock, BookOpen, ExternalLink, Sparkles, Play } from 'lucide-react';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const SkillDetailPage = ({ user, onLogout }) => {
  const navigate = useNavigate();
  const { skillId } = useParams();
  const [skill, setSkill] = useState(null);
  const [lessons, setLessons] = useState([]);
  const [generatedContent, setGeneratedContent] = useState(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);

  useEffect(() => {
    fetchSkillDetails();
  }, [skillId]);

  const fetchSkillDetails = async () => {
    try {
      const [skillRes, lessonsRes] = await Promise.all([
        axios.get(`${API}/skills/${skillId}`, { withCredentials: true }),
        axios.get(`${API}/skills/${skillId}/lessons`, { withCredentials: true })
      ]);
      setSkill(skillRes.data);
      setLessons(lessonsRes.data);
    } catch (error) {
      toast.error('Failed to load skill details');
    } finally {
      setLoading(false);
    }
  };

  const handleStartSkill = async () => {
    try {
      await axios.post(`${API}/user-skills/${skillId}/start`, {}, { withCredentials: true });
      toast.success('Skill started! Begin your lessons.');
      fetchSkillDetails();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to start skill');
    }
  };

  const handleCompleteLesson = async (lessonId) => {
    try {
      const response = await axios.post(`${API}/lessons/${lessonId}/complete`, {}, { withCredentials: true });
      toast.success(`Lesson completed! Progress: ${response.data.progress_percent}%`);
      fetchSkillDetails();
    } catch (error) {
      toast.error('Failed to complete lesson');
    }
  };

  const handleGenerateContent = async (lessonTitle) => {
    setGenerating(true);
    try {
      const response = await axios.post(
        `${API}/ai/generate-lesson-content`,
        {
          skill_name: skill.name,
          lesson_title: lessonTitle,
          difficulty: skill.difficulty
        },
        { withCredentials: true }
      );
      setGeneratedContent({ title: lessonTitle, content: response.data.content });
      toast.success('AI content generated!');
    } catch (error) {
      toast.error('Failed to generate content');
    } finally {
      setGenerating(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-pulse text-white text-xl">Loading skill...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen">
      {/* Header */}
      <header className="bg-white/10 backdrop-blur-md border-b border-white/20">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3 cursor-pointer" onClick={() => navigate('/dashboard')}>
            <TreePine className="w-8 h-8 text-white" />
            <h1 className="text-2xl font-bold text-white">SkillTree</h1>
          </div>
          <nav className="flex items-center gap-4">
            <Button variant="ghost" className="text-white" onClick={() => navigate('/dashboard')} data-testid="dashboard-nav">
              Dashboard
            </Button>
            <Button variant="ghost" className="text-white" onClick={() => navigate('/skill-tree')} data-testid="skill-tree-nav">
              Skill Tree
            </Button>
            <Button variant="ghost" className="text-white" onClick={() => navigate('/integrations')} data-testid="integrations-nav">
              Integrations
            </Button>
            <Avatar className="w-10 h-10">
              <AvatarImage src={user.picture} />
              <AvatarFallback>{user.name.charAt(0).toUpperCase()}</AvatarFallback>
            </Avatar>
            <Button variant="ghost" size="icon" onClick={onLogout} data-testid="logout-button">
              <LogOut className="w-5 h-5 text-white" />
            </Button>
          </nav>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-4 py-8" data-testid="skill-detail-page">
        {/* Skill Header */}
        <Card className="p-8 mb-8 bg-white/95 backdrop-blur-sm" data-testid="skill-header-card">
          <div className="flex items-start justify-between mb-4">
            <div>
              <h2 className="text-4xl font-bold mb-3" data-testid="skill-name">{skill.name}</h2>
              <p className="text-lg text-gray-600 mb-4" data-testid="skill-description">{skill.description}</p>
              <div className="flex items-center gap-3">
                <Badge className="bg-purple-100 text-purple-700 text-sm" data-testid="skill-difficulty">{skill.difficulty}</Badge>
                <Badge className="bg-blue-100 text-blue-700 text-sm" data-testid="skill-category">{skill.category}</Badge>
                <Badge className="bg-green-100 text-green-700 text-sm" data-testid="skill-xp">{skill.xp_value} XP</Badge>
              </div>
            </div>
            <Button size="lg" onClick={handleStartSkill} data-testid="start-skill-button">
              <Play className="w-5 h-5 mr-2" />
              Start Learning
            </Button>
          </div>
        </Card>

        {/* Lessons */}
        <Card className="p-8 mb-8" data-testid="lessons-section">
          <h3 className="text-2xl font-bold mb-6 flex items-center gap-2">
            <BookOpen className="w-6 h-6 text-blue-600" />
            Lessons ({lessons.length})
          </h3>

          <Accordion type="single" collapsible className="space-y-3">
            {lessons.map((lesson, idx) => (
              <AccordionItem key={lesson.id} value={lesson.id} className="border rounded-lg px-4" data-testid={`lesson-${lesson.id}`}>
                <AccordionTrigger className="hover:no-underline">
                  <div className="flex items-center gap-4 flex-1">
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                      lesson.completed ? 'bg-green-100' : 'bg-gray-100'
                    }`}>
                      {lesson.completed ? (
                        <CheckCircle2 className="w-5 h-5 text-green-600" />
                      ) : (
                        <span className="text-sm font-semibold text-gray-600">{idx + 1}</span>
                      )}
                    </div>
                    <div className="flex-1 text-left">
                      <p className="font-semibold text-lg">{lesson.title}</p>
                      <div className="flex items-center gap-3 mt-1">
                        <span className="text-sm text-gray-500 flex items-center gap-1">
                          <Clock className="w-4 h-4" />
                          {lesson.estimated_time} min
                        </span>
                        {lesson.completed && (
                          <Badge className="bg-green-100 text-green-700 text-xs">Completed</Badge>
                        )}
                      </div>
                    </div>
                  </div>
                </AccordionTrigger>
                <AccordionContent className="pt-4">
                  <div className="prose max-w-none mb-4">
                    <p className="whitespace-pre-wrap text-gray-700">{lesson.content}</p>
                  </div>
                  
                  {lesson.resources && lesson.resources.length > 0 && (
                    <div className="mb-4">
                      <p className="font-semibold mb-2">External Resources:</p>
                      <div className="space-y-2">
                        {lesson.resources.map((resource, ridx) => (
                          <a
                            key={ridx}
                            href={resource.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="flex items-center gap-2 text-blue-600 hover:underline"
                            data-testid={`resource-${ridx}`}
                          >
                            <ExternalLink className="w-4 h-4" />
                            {resource.title}
                          </a>
                        ))}
                      </div>
                    </div>
                  )}

                  <div className="flex gap-3">
                    <Button
                      onClick={() => handleCompleteLesson(lesson.id)}
                      disabled={lesson.completed}
                      data-testid={`complete-lesson-${lesson.id}-button`}
                    >
                      {lesson.completed ? 'Completed' : 'Mark as Complete'}
                    </Button>
                    <Button
                      variant="outline"
                      onClick={() => handleGenerateContent(lesson.title)}
                      disabled={generating}
                      data-testid={`generate-content-${lesson.id}-button`}
                    >
                      <Sparkles className="w-4 h-4 mr-2" />
                      {generating ? 'Generating...' : 'Generate AI Content'}
                    </Button>
                  </div>
                </AccordionContent>
              </AccordionItem>
            ))}
          </Accordion>
        </Card>

        {/* Generated AI Content */}
        {generatedContent && (
          <Card className="p-8 bg-gradient-to-br from-purple-50 to-blue-50" data-testid="generated-content-card">
            <h3 className="text-2xl font-bold mb-4 flex items-center gap-2">
              <Sparkles className="w-6 h-6 text-purple-600" />
              AI-Generated Content: {generatedContent.title}
            </h3>
            <div className="prose max-w-none">
              <p className="whitespace-pre-wrap text-gray-800">{generatedContent.content}</p>
            </div>
          </Card>
        )}
      </main>
    </div>
  );
};

export default SkillDetailPage;
