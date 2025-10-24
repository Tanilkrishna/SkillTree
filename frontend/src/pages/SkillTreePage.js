import { useState, useEffect } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { TreePine, LogOut, Lock, CheckCircle2, Play, Sparkles } from 'lucide-react';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const SkillTreePage = ({ user, onLogout }) => {
  const navigate = useNavigate();
  const [skills, setSkills] = useState([]);
  const [recommendations, setRecommendations] = useState(null);
  const [loading, setLoading] = useState(true);
  const [loadingRecs, setLoadingRecs] = useState(false);
  const [filter, setFilter] = useState('all');

  useEffect(() => {
    fetchSkills();
  }, []);

  const fetchSkills = async () => {
    try {
      const response = await axios.get(`${API}/skills`, { withCredentials: true });
      setSkills(response.data);
    } catch (error) {
      toast.error('Failed to load skills');
    } finally {
      setLoading(false);
    }
  };

  const handleGetRecommendations = async () => {
    setLoadingRecs(true);
    try {
      const response = await axios.post(`${API}/ai/recommend-skills`, {}, { withCredentials: true });
      setRecommendations(response.data);
      toast.success('AI recommendations generated!');
    } catch (error) {
      toast.error('Failed to get recommendations');
    } finally {
      setLoadingRecs(false);
    }
  };

  const filteredSkills = skills.filter(skill => {
    if (filter === 'all') return true;
    if (filter === 'completed') return skill.user_status === 'completed';
    if (filter === 'in_progress') return skill.user_status === 'in_progress';
    if (filter === 'available') return skill.user_status === 'available' || (skill.user_status !== 'locked' && skill.user_status !== 'completed' && skill.user_status !== 'in_progress');
    return false;
  });

  const groupedSkills = filteredSkills.reduce((acc, skill) => {
    if (!acc[skill.category]) acc[skill.category] = [];
    acc[skill.category].push(skill);
    return acc;
  }, {});

  const getStatusIcon = (status) => {
    if (status === 'completed') return <CheckCircle2 className="w-5 h-5 text-green-600" />;
    if (status === 'in_progress') return <Play className="w-5 h-5 text-blue-600" />;
    if (status === 'locked') return <Lock className="w-5 h-5 text-gray-400" />;
    return <div className="w-5 h-5 rounded-full border-2 border-gray-300" />;
  };

  const getStatusBadge = (status, difficulty) => {
    const statusColors = {
      completed: 'bg-green-100 text-green-700',
      in_progress: 'bg-blue-100 text-blue-700',
      locked: 'bg-gray-100 text-gray-500',
      available: 'bg-purple-100 text-purple-700'
    };
    const difficultyColors = {
      beginner: 'bg-green-100 text-green-700',
      intermediate: 'bg-yellow-100 text-yellow-700',
      advanced: 'bg-red-100 text-red-700'
    };
    return { statusColor: statusColors[status] || 'bg-purple-100 text-purple-700', difficultyColor: difficultyColors[difficulty] };
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-pulse text-white text-xl">Loading skill tree...</div>
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

      <main className="max-w-7xl mx-auto px-4 py-8" data-testid="skill-tree-page">
        {/* Header Section */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-4xl font-bold text-white mb-2">Your Skill Tree</h2>
              <p className="text-white/80">Explore and master new skills on your learning journey</p>
            </div>
            <Button
              size="lg"
              onClick={handleGetRecommendations}
              disabled={loadingRecs}
              className="bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600"
              data-testid="get-recommendations-button"
            >
              <Sparkles className="w-5 h-5 mr-2" />
              {loadingRecs ? 'Getting Recommendations...' : 'AI Recommendations'}
            </Button>
          </div>

          {/* AI Recommendations */}
          {recommendations && (
            <Card className="relative overflow-hidden mb-6 border-0 shadow-2xl" data-testid="recommendations-card">
              {/* Animated gradient background */}
              <div className="absolute inset-0 bg-gradient-to-br from-purple-600 via-pink-500 to-blue-600 opacity-90" />
              <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHZpZXdCb3g9IjAgMCA2MCA2MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48ZyBmaWxsPSJub25lIiBmaWxsLXJ1bGU9ImV2ZW5vZGQiPjxnIGZpbGw9IiNmZmYiIGZpbGwtb3BhY2l0eT0iMC4wNSI+PHBhdGggZD0iTTM2IDM0djItaDJ2LTJoLTJ6bTAtNHYyaDJ2LTJoLTJ6bTAgNHYyaDJ2LTJoLTJ6Ii8+PC9nPjwvZz48L3N2Zz4=')] opacity-20" />
              
              <div className="relative p-8">
                {/* Header with pulsing AI icon */}
                <div className="flex items-center gap-3 mb-6">
                  <div className="relative">
                    <div className="absolute inset-0 bg-white/30 rounded-full blur-xl animate-pulse" />
                    <div className="relative w-12 h-12 bg-white/20 backdrop-blur-sm rounded-full flex items-center justify-center border-2 border-white/40">
                      <Sparkles className="w-7 h-7 text-white animate-pulse" />
                    </div>
                  </div>
                  <div>
                    <h3 className="text-2xl font-bold text-white flex items-center gap-2">
                      AI Skill Recommendations
                    </h3>
                    <p className="text-white/80 text-sm">Powered by advanced AI analysis</p>
                  </div>
                </div>

                {/* AI Message Box */}
                <div className="bg-white/95 backdrop-blur-md rounded-2xl p-6 shadow-xl border border-white/20">
                  {/* AI Badge */}
                  <div className="inline-flex items-center gap-2 px-3 py-1 bg-gradient-to-r from-purple-100 to-pink-100 rounded-full mb-4">
                    <div className="w-2 h-2 bg-purple-500 rounded-full animate-pulse" />
                    <span className="text-xs font-semibold text-purple-700">AI Generated Response</span>
                  </div>

                  {/* Recommendations Content */}
                  <div className="prose prose-lg max-w-none">
                    <div className="text-gray-800 leading-relaxed whitespace-pre-wrap font-medium">
                      {recommendations.recommendations}
                    </div>
                  </div>

                  {/* Decorative elements */}
                  <div className="mt-6 pt-4 border-t border-gray-200 flex items-center justify-between">
                    <div className="flex items-center gap-2 text-sm text-gray-500">
                      <div className="flex gap-1">
                        {[...Array(3)].map((_, i) => (
                          <div key={i} className="w-1.5 h-1.5 bg-purple-400 rounded-full animate-pulse" style={{ animationDelay: `${i * 200}ms` }} />
                        ))}
                      </div>
                      <span>Analyzing your learning path...</span>
                    </div>
                    <div className="flex items-center gap-1 text-xs text-gray-400">
                      <Sparkles className="w-3 h-3" />
                      <span>AI Powered</span>
                    </div>
                  </div>
                </div>

                {/* Refresh hint */}
                <div className="mt-4 text-center">
                  <p className="text-white/70 text-sm">
                    💡 Tip: Get new recommendations as you progress in your skills
                  </p>
                </div>
              </div>
            </Card>
          )}

          {/* Filters */}
          <div className="flex gap-3">
            {['all', 'available', 'in_progress', 'completed'].map((f) => (
              <Button
                key={f}
                variant={filter === f ? 'default' : 'outline'}
                onClick={() => setFilter(f)}
                className={filter !== f ? 'bg-white/90 text-gray-700' : ''}
                data-testid={`filter-${f}-button`}
              >
                {f.replace('_', ' ').toUpperCase()}
              </Button>
            ))}
          </div>
        </div>

        {/* Skills by Category */}
        {Object.entries(groupedSkills).map(([category, categorySkills]) => (
          <div key={category} className="mb-8" data-testid={`category-${category}`}>
            <h3 className="text-2xl font-bold text-white mb-4">{category}</h3>
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
              {categorySkills.map((skill) => {
                const { statusColor, difficultyColor } = getStatusBadge(skill.user_status, skill.difficulty);
                return (
                  <Card
                    key={skill.id}
                    className={`p-5 cursor-pointer transition-all hover:shadow-lg ${
                      skill.user_status === 'locked' ? 'opacity-60 cursor-not-allowed' : ''
                    }`}
                    onClick={() => skill.user_status !== 'locked' && navigate(`/skills/${skill.id}`)}
                    data-testid={`skill-card-${skill.id}`}
                  >
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex items-center gap-3">
                        {getStatusIcon(skill.user_status)}
                        <h4 className="font-bold text-lg">{skill.name}</h4>
                      </div>
                    </div>
                    <p className="text-sm text-gray-600 mb-3">{skill.description}</p>
                    <div className="flex items-center gap-2 mb-3">
                      <Badge className={difficultyColor}>{skill.difficulty}</Badge>
                      <Badge className="bg-gray-100 text-gray-700">{skill.xp_value} XP</Badge>
                      {skill.user_status && (
                        <Badge className={statusColor}>
                          {skill.user_status === 'in_progress' ? 'In Progress' : skill.user_status}
                        </Badge>
                      )}
                    </div>
                    {skill.user_status === 'in_progress' && (
                      <div className="mt-2">
                        <div className="flex justify-between text-xs text-gray-600 mb-1">
                          <span>Progress</span>
                          <span>{skill.user_progress}%</span>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-2">
                          <div
                            className="bg-blue-600 h-2 rounded-full transition-all"
                            style={{ width: `${skill.user_progress}%` }}
                          />
                        </div>
                      </div>
                    )}
                  </Card>
                );
              })}
            </div>
          </div>
        ))}
      </main>
    </div>
  );
};

export default SkillTreePage;
