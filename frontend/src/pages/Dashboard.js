import { useState, useEffect } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { TreePine, Trophy, Target, Zap, BookOpen, GitBranch, LogOut, Sparkles } from 'lucide-react';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const Dashboard = ({ user, onLogout }) => {
  const navigate = useNavigate();
  const [stats, setStats] = useState(null);
  const [achievements, setAchievements] = useState([]);
  const [activityFeed, setActivityFeed] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      const [statsRes, achievementsRes, activityRes] = await Promise.all([
        axios.get(`${API}/dashboard/stats`, { withCredentials: true }),
        axios.get(`${API}/achievements`, { withCredentials: true }),
        axios.get(`${API}/activity-feed`, { withCredentials: true })
      ]);
      setStats(statsRes.data);
      setAchievements(achievementsRes.data);
      setActivityFeed(activityRes.data);
    } catch (error) {
      toast.error('Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = async () => {
    try {
      await axios.post(`${API}/auth/logout`, {}, { withCredentials: true });
      onLogout();
    } catch (error) {
      onLogout();
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-pulse text-white text-xl">Loading...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen">
      {/* Header */}
      <header className="bg-white/10 backdrop-blur-md border-b border-white/20" data-testid="dashboard-header">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3 cursor-pointer" onClick={() => navigate('/dashboard')}>
            <TreePine className="w-8 h-8 text-white" />
            <h1 className="text-2xl font-bold text-white">SkillTree</h1>
          </div>
          <nav className="flex items-center gap-4">
            <Button variant="ghost" className="text-white" onClick={() => navigate('/dashboard')} data-testid="dashboard-nav-button">
              Dashboard
            </Button>
            <Button variant="ghost" className="text-white" onClick={() => navigate('/skill-tree')} data-testid="skill-tree-nav-button">
              Skill Tree
            </Button>
            <Button variant="ghost" className="text-white" onClick={() => navigate('/integrations')} data-testid="integrations-nav-button">
              Integrations
            </Button>
            {user?.is_admin && (
              <Button variant="ghost" className="text-yellow-300 font-semibold" onClick={() => navigate('/admin')} data-testid="admin-nav-button">
                ⚡ Admin
              </Button>
            )}
            <Avatar className="w-10 h-10" data-testid="user-avatar">
              <AvatarImage src={user.picture} />
              <AvatarFallback>{user.name.charAt(0).toUpperCase()}</AvatarFallback>
            </Avatar>
            <Button variant="ghost" size="icon" onClick={handleLogout} data-testid="logout-button">
              <LogOut className="w-5 h-5 text-white" />
            </Button>
          </nav>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-8" data-testid="dashboard-main">
        {/* User Profile Card */}
        <Card className="p-6 mb-8 bg-white/95 backdrop-blur-sm" data-testid="profile-card">
          <div className="flex items-center gap-6">
            <Avatar className="w-24 h-24">
              <AvatarImage src={user.picture} />
              <AvatarFallback className="text-3xl">{user.name.charAt(0).toUpperCase()}</AvatarFallback>
            </Avatar>
            <div className="flex-1">
              <h2 className="text-3xl font-bold mb-2" data-testid="user-name">{user.name}</h2>
              <p className="text-gray-600 mb-3" data-testid="user-email">{user.email}</p>
              <div className="flex items-center gap-4">
                <div className="flex items-center gap-2">
                  <Zap className="w-5 h-5 text-yellow-500" />
                  <span className="font-semibold" data-testid="user-level">Level {stats.level}</span>
                </div>
                <div className="flex items-center gap-2">
                  <Trophy className="w-5 h-5 text-purple-500" />
                  <span className="font-semibold" data-testid="user-xp">{stats.total_xp} XP</span>
                </div>
              </div>
            </div>
            <Button size="lg" onClick={() => navigate('/skill-tree')} data-testid="explore-skills-button">
              <TreePine className="w-5 h-5 mr-2" />
              Explore Skills
            </Button>
          </div>
        </Card>

        {/* Stats Grid */}
        <div className="grid md:grid-cols-4 gap-6 mb-8">
          <Card className="p-6 bg-gradient-to-br from-blue-500 to-blue-600 text-white" data-testid="stat-card-completed">
            <Target className="w-8 h-8 mb-3" />
            <p className="text-sm opacity-90">Skills Completed</p>
            <p className="text-3xl font-bold">{stats.skills_completed}</p>
          </Card>
          <Card className="p-6 bg-gradient-to-br from-purple-500 to-purple-600 text-white" data-testid="stat-card-progress">
            <BookOpen className="w-8 h-8 mb-3" />
            <p className="text-sm opacity-90">In Progress</p>
            <p className="text-3xl font-bold">{stats.skills_in_progress}</p>
          </Card>
          <Card className="p-6 bg-gradient-to-br from-green-500 to-green-600 text-white" data-testid="stat-card-completion">
            <Trophy className="w-8 h-8 mb-3" />
            <p className="text-sm opacity-90">Completion Rate</p>
            <p className="text-3xl font-bold">{stats.completion_rate}%</p>
          </Card>
          <Card className="p-6 bg-gradient-to-br from-orange-500 to-orange-600 text-white" data-testid="stat-card-total">
            <GitBranch className="w-8 h-8 mb-3" />
            <p className="text-sm opacity-90">Total Skills</p>
            <p className="text-3xl font-bold">{stats.total_skills}</p>
          </Card>
        </div>

        <div className="grid lg:grid-cols-2 gap-8">
          {/* Achievements */}
          <Card className="p-6" data-testid="achievements-section">
            <h3 className="text-xl font-bold mb-4 flex items-center gap-2">
              <Trophy className="w-6 h-6 text-yellow-500" />
              Achievements
            </h3>
            <div className="space-y-3">
              {achievements.map((achievement) => (
                <div
                  key={achievement.id}
                  className={`flex items-center gap-4 p-3 rounded-lg border-2 transition-all ${
                    achievement.unlocked
                      ? 'bg-green-50 border-green-200'
                      : 'bg-gray-50 border-gray-200 opacity-60'
                  }`}
                  data-testid={`achievement-${achievement.id}`}
                >
                  <div className={`w-12 h-12 rounded-full flex items-center justify-center ${
                    achievement.unlocked ? 'bg-green-100' : 'bg-gray-100'
                  }`}>
                    <Trophy className={`w-6 h-6 ${
                      achievement.unlocked ? 'text-green-600' : 'text-gray-400'
                    }`} />
                  </div>
                  <div className="flex-1">
                    <p className="font-semibold">{achievement.name}</p>
                    <p className="text-sm text-gray-600">{achievement.description}</p>
                  </div>
                  {achievement.unlocked && (
                    <span className="text-green-600 font-semibold">Unlocked!</span>
                  )}
                </div>
              ))}
            </div>
          </Card>

          {/* Activity Feed */}
          <Card className="p-6" data-testid="activity-feed-section">
            <h3 className="text-xl font-bold mb-4 flex items-center gap-2">
              <Sparkles className="w-6 h-6 text-purple-500" />
              Recent Activity
            </h3>
            {activityFeed.length > 0 ? (
              <div className="space-y-3">
                {activityFeed.map((activity, idx) => (
                  <div key={idx} className="flex items-start gap-3 p-3 bg-gray-50 rounded-lg" data-testid={`activity-item-${idx}`}>
                    <div className="w-10 h-10 rounded-full bg-purple-100 flex items-center justify-center">
                      <Trophy className="w-5 h-5 text-purple-600" />
                    </div>
                    <div className="flex-1">
                      <p className="font-medium">{activity.title}</p>
                      <p className="text-sm text-gray-600">{activity.description}</p>
                      <p className="text-xs text-gray-400 mt-1">
                        {new Date(activity.timestamp).toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-gray-500">
                <p>No recent activity</p>
                <p className="text-sm mt-2">Start learning to see your progress here!</p>
              </div>
            )}
          </Card>
        </div>
      </main>
    </div>
  );
};

export default Dashboard;
