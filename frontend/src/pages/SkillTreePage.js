import { useState, useEffect } from 'react';
import axios from 'axios';
import { API } from '@/App';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { TreePine, LogOut, Lock, Play, CheckCircle, ChevronRight } from 'lucide-react';
import { toast } from 'sonner';
import * as LucideIcons from 'lucide-react';

export default function SkillTreePage({ user, onLogout }) {
  const navigate = useNavigate();
  const [skills, setSkills] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchSkills();
  }, []);

  const fetchSkills = async () => {
    try {
      const response = await axios.get(`${API}/skills`);
      setSkills(response.data);
    } catch (error) {
      toast.error('Failed to load skills');
    }
    setLoading(false);
  };

  const startSkill = async (skillId) => {
    try {
      await axios.post(`${API}/user-skills/${skillId}/start`);
      toast.success('Skill started!');
      fetchSkills();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to start skill');
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'in_progress':
        return <Play className="w-5 h-5 text-blue-500" />;
      case 'locked':
        return <Lock className="w-5 h-5 text-gray-400" />;
      default:
        return <ChevronRight className="w-5 h-5 text-gray-500" />;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800';
      case 'in_progress':
        return 'bg-blue-100 text-blue-800';
      case 'locked':
        return 'bg-gray-100 text-gray-600';
      default:
        return 'bg-purple-100 text-purple-800';
    }
  };

  const getDifficultyColor = (difficulty) => {
    switch (difficulty) {
      case 'beginner':
        return 'bg-green-100 text-green-800';
      case 'intermediate':
        return 'bg-yellow-100 text-yellow-800';
      case 'advanced':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getIconComponent = (iconName) => {
    const Icon = LucideIcons[iconName];
    return Icon ? <Icon className="w-6 h-6" /> : <LucideIcons.Code className="w-6 h-6" />;
  };

  // Group skills by category
  const groupedSkills = skills.reduce((acc, skill) => {
    if (!acc[skill.category]) {
      acc[skill.category] = [];
    }
    acc[skill.category].push(skill);
    return acc;
  }, {});

  return (
    <div className="min-h-screen">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-10" data-testid="skill-tree-header">
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
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8" data-testid="skill-tree-main">
        <div className="mb-8">
          <h2 className="text-3xl font-bold mb-2">Your Skill Tree 🌳</h2>
          <p className="text-gray-600">Explore and master skills to level up your expertise</p>
        </div>

        {loading ? (
          <div className="text-center py-12">Loading skills...</div>
        ) : (
          <div className="space-y-8">
            {Object.entries(groupedSkills).map(([category, categorySkills]) => (
              <div key={category} data-testid={`category-${category.toLowerCase().replace(/\s+/g, '-')}`}>
                <h3 className="text-2xl font-semibold mb-4">{category}</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {categorySkills.map((skill) => (
                    <Card
                      key={skill.id}
                      className={`card-hover ${skill.user_status === 'locked' ? 'opacity-60' : ''}`}
                      data-testid={`skill-card-${skill.id}`}
                    >
                      <CardHeader>
                        <div className="flex items-start justify-between">
                          <div className="flex items-center gap-3">
                            <div className="p-2 bg-purple-100 rounded-lg">
                              {getIconComponent(skill.icon)}
                            </div>
                            <div>
                              <CardTitle className="text-lg">{skill.name}</CardTitle>
                              <div className="flex gap-2 mt-1">
                                <Badge variant="secondary" className={getDifficultyColor(skill.difficulty)}>
                                  {skill.difficulty}
                                </Badge>
                              </div>
                            </div>
                          </div>
                          {getStatusIcon(skill.user_status)}
                        </div>
                      </CardHeader>
                      <CardContent>
                        <CardDescription className="mb-4">{skill.description}</CardDescription>
                        <div className="flex items-center justify-between mb-3">
                          <span className="text-sm text-gray-600">Progress</span>
                          <span className="text-sm font-semibold">{skill.user_progress || 0}%</span>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-2 mb-4">
                          <div
                            className="bg-purple-600 h-2 rounded-full transition-all"
                            style={{ width: `${skill.user_progress || 0}%` }}
                          ></div>
                        </div>
                        <div className="flex gap-2">
                          {skill.user_status === 'locked' ? (
                            <Button variant="outline" size="sm" disabled className="w-full" data-testid={`skill-locked-btn-${skill.id}`}>
                              <Lock className="w-4 h-4 mr-2" />
                              Locked
                            </Button>
                          ) : skill.user_status === 'available' ? (
                            <Button
                              size="sm"
                              className="w-full"
                              onClick={() => startSkill(skill.id)}
                              data-testid={`skill-start-btn-${skill.id}`}
                            >
                              Start Learning
                            </Button>
                          ) : (
                            <Button
                              size="sm"
                              className="w-full"
                              onClick={() => navigate(`/skills/${skill.id}`)}
                              data-testid={`skill-continue-btn-${skill.id}`}
                            >
                              {skill.user_status === 'completed' ? 'Review' : 'Continue'}
                            </Button>
                          )}
                        </div>
                        <div className="mt-3 text-sm text-gray-500">
                          {skill.xp_value} XP
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}