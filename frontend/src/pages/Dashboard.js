import { useState, useEffect } from 'react';
import axios from 'axios';
import { API } from '@/App';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { TreePine, Trophy, TrendingUp, BookOpen, LogOut, Network, Link as LinkIcon, Award, Star, Zap, Layers, CheckCircle } from 'lucide-react';
import { toast } from 'sonner';
import * as LucideIcons from 'lucide-react';

export default function Dashboard({ user, onLogout }) {
  const navigate = useNavigate();
  const [stats, setStats] = useState(null);
  const [recommendations, setRecommendations] = useState(null);
  const [loadingRecs, setLoadingRecs] = useState(false);
  const [achievements, setAchievements] = useState([]);
  const [activities, setActivities] = useState([]);

  useEffect(() => {
    fetchStats();
    fetchAchievements();
    fetchActivities();
  }, []);

  const fetchStats = async () => {
    try {
      const response = await axios.get(`${API}/dashboard/stats`);
      setStats(response.data);
    } catch (error) {
      toast.error('Failed to load stats');
    }
  };

  const fetchAchievements = async () => {
    try {
      const response = await axios.get(`${API}/achievements`);
      setAchievements(response.data);
    } catch (error) {
      console.error('Failed to load achievements');
    }
  };

  const fetchActivities = async () => {
    try {
      const response = await axios.get(`${API}/activity-feed`);
      setActivities(response.data);
    } catch (error) {
      console.error('Failed to load activities');
    }
  };

  const getRecommendations = async () => {
    setLoadingRecs(true);
    try {
      const response = await axios.post(`${API}/ai/recommend-skills`);
      setRecommendations(response.data);
      toast.success('AI recommendations loaded!');
    } catch (error) {
      toast.error('Failed to get recommendations');
    }
    setLoadingRecs(false);
  };

  const getIconComponent = (iconName) => {
    const Icon = LucideIcons[iconName];
    return Icon ? <Icon className="w-4 h-4" /> : <LucideIcons.Trophy className="w-4 h-4" />;
  };

  const formatTimestamp = (timestamp) => {
    if (!timestamp) return '';
    const date = new Date(timestamp);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  };

  const progressToNextLevel = stats ? ((stats.total_xp % 1000) / 1000) * 100 : 0;

  return (
    <div className="min-h-screen">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-10" data-testid="dashboard-header">
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
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8" data-testid="dashboard-main">
        {/* Welcome Section */}
        <div className="mb-8">
          <h2 className="text-3xl font-bold mb-2">Welcome back, {user.name}! 👋</h2>
          <p className="text-gray-600">Continue your learning journey</p>
        </div>

        {/* Stats Grid */}
        {stats && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <Card className="card-hover" data-testid="level-card">
              <CardHeader className="pb-2">
                <CardDescription>Current Level</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex items-center gap-3">
                  <Trophy className="w-8 h-8 text-yellow-500" />
                  <div>
                    <div className="text-3xl font-bold">{stats.level}</div>
                    <div className="text-sm text-gray-600">{stats.total_xp} XP</div>
                  </div>
                </div>
                <div className="mt-4">
                  <Progress value={progressToNextLevel} className="h-2" />
                  <p className="text-xs text-gray-500 mt-1">{Math.round(progressToNextLevel)}% to level {stats.level + 1}</p>
                </div>
              </CardContent>
            </Card>

            <Card className="card-hover" data-testid="completed-skills-card">
              <CardHeader className="pb-2">
                <CardDescription>Skills Completed</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex items-center gap-3">
                  <BookOpen className="w-8 h-8 text-green-500" />
                  <div className="text-3xl font-bold">{stats.skills_completed}</div>
                </div>
                <p className="text-sm text-gray-600 mt-2">Out of {stats.total_skills} total skills</p>
              </CardContent>
            </Card>

            <Card className="card-hover" data-testid="in-progress-card">
              <CardHeader className="pb-2">
                <CardDescription>In Progress</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex items-center gap-3">
                  <TrendingUp className="w-8 h-8 text-blue-500" />
                  <div className="text-3xl font-bold">{stats.skills_in_progress}</div>
                </div>
                <p className="text-sm text-gray-600 mt-2">Active learning tracks</p>
              </CardContent>
            </Card>

            <Card className="card-hover" data-testid="completion-rate-card">
              <CardHeader className="pb-2">
                <CardDescription>Completion Rate</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex items-center gap-3">
                  <Network className="w-8 h-8 text-purple-500" />
                  <div className="text-3xl font-bold">{stats.completion_rate}%</div>
                </div>
                <p className="text-sm text-gray-600 mt-2">Overall progress</p>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Quick Actions */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          <Card data-testid="quick-actions-card">
            <CardHeader>
              <CardTitle>Quick Actions</CardTitle>
              <CardDescription>Jump into your learning journey</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <Button className="w-full justify-start" variant="outline" onClick={() => navigate('/skill-tree')} data-testid="view-skill-tree-btn">
                <Network className="w-4 h-4 mr-2" />
                View Skill Tree
              </Button>
              <Button className="w-full justify-start" variant="outline" onClick={() => navigate('/integrations')} data-testid="connect-platforms-btn">
                <LinkIcon className="w-4 h-4 mr-2" />
                Connect Learning Platforms
              </Button>
            </CardContent>
          </Card>

          <Card data-testid="ai-recommendations-card">
            <CardHeader>
              <CardTitle>AI Recommendations</CardTitle>
              <CardDescription>Get personalized skill suggestions</CardDescription>
            </CardHeader>
            <CardContent>
              {!recommendations ? (
                <Button onClick={getRecommendations} disabled={loadingRecs} className="w-full" data-testid="get-recommendations-btn">
                  {loadingRecs ? 'Loading...' : 'Get AI Recommendations'}
                </Button>
              ) : (
                <div className="space-y-3" data-testid="recommendations-list">
                  <p className="text-sm text-gray-600 whitespace-pre-wrap">{recommendations.recommendations}</p>
                  <Button onClick={getRecommendations} variant="outline" size="sm" disabled={loadingRecs} data-testid="refresh-recommendations-btn">
                    Refresh Recommendations
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Achievements */}
        <div className="mb-8">
          <h3 className="text-2xl font-bold mb-4">Achievements 🏆</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4" data-testid="achievements-grid">
            {achievements.map((achievement) => (
              <Card
                key={achievement.id}
                className={`text-center card-hover ${!achievement.unlocked ? 'opacity-50 grayscale' : ''}`}
                data-testid={`achievement-${achievement.id}`}
              >
                <CardContent className="pt-6">
                  <div className={`inline-flex p-4 rounded-full mb-3 ${achievement.unlocked ? 'bg-yellow-100' : 'bg-gray-100'}`}>
                    {getIconComponent(achievement.icon)}
                  </div>
                  <h4 className="font-semibold text-sm mb-1">{achievement.name}</h4>
                  <p className="text-xs text-gray-600">{achievement.description}</p>
                  {achievement.unlocked && (
                    <Badge variant="secondary" className="mt-2 bg-green-100 text-green-800">
                      <CheckCircle className="w-3 h-3 mr-1" />
                      Unlocked
                    </Badge>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>
        </div>

        {/* Activity Feed */}
        {activities.length > 0 && (
          <Card data-testid="activity-feed-card">
            <CardHeader>
              <CardTitle>Recent Activity</CardTitle>
              <CardDescription>Your learning journey timeline</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4" data-testid="activity-list">
                {activities.map((activity, index) => (
                  <div key={index} className="flex items-start gap-3 pb-4 border-b last:border-0" data-testid={`activity-${index}`}>
                    <div className="p-2 bg-green-100 rounded-full">
                      {getIconComponent(activity.icon)}
                    </div>
                    <div className="flex-1">
                      <p className="font-semibold text-sm">{activity.title}</p>
                      <p className="text-xs text-gray-600">{activity.description}</p>
                      <p className="text-xs text-gray-500 mt-1">{formatTimestamp(activity.timestamp)}</p>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}
      </main>
    </div>
  );
}