import { useState, useEffect } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { TreePine, LogOut, Github, Linkedin, Youtube, CheckCircle2, XCircle } from 'lucide-react';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const IntegrationsPage = ({ user, onLogout }) => {
  const navigate = useNavigate();
  const [integrations, setIntegrations] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchIntegrations();
  }, []);

  const fetchIntegrations = async () => {
    try {
      const response = await axios.get(`${API}/integrations`, { withCredentials: true });
      setIntegrations(response.data);
    } catch (error) {
      toast.error('Failed to load integrations');
    } finally {
      setLoading(false);
    }
  };

  const handleConnect = async (platform) => {
    try {
      const response = await axios.post(`${API}/integrations/${platform}/connect`, {}, { withCredentials: true });
      toast.success(response.data.message);
      fetchIntegrations();
    } catch (error) {
      toast.error(`Failed to connect ${platform}`);
    }
  };

  const handleDisconnect = async (platform) => {
    try {
      const response = await axios.post(`${API}/integrations/${platform}/disconnect`, {}, { withCredentials: true });
      toast.success(response.data.message);
      fetchIntegrations();
    } catch (error) {
      toast.error(`Failed to disconnect ${platform}`);
    }
  };

  const getPlatformIcon = (platform) => {
    const icons = {
      github: <Github className="w-8 h-8" />,
      linkedin: <Linkedin className="w-8 h-8" />,
      youtube: <Youtube className="w-8 h-8" />
    };
    return icons[platform];
  };

  const getPlatformColor = (platform) => {
    const colors = {
      github: 'from-gray-700 to-gray-900',
      linkedin: 'from-blue-600 to-blue-800',
      youtube: 'from-red-600 to-red-800'
    };
    return colors[platform];
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-pulse text-white text-xl">Loading integrations...</div>
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
            {user?.is_admin && (
              <Button variant="ghost" className="text-yellow-300 font-semibold" onClick={() => navigate('/admin')} data-testid="admin-nav">
                ⚡ Admin
              </Button>
            )}
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

      <main className="max-w-6xl mx-auto px-4 py-8" data-testid="integrations-page">
        <div className="mb-8">
          <h2 className="text-4xl font-bold text-white mb-2">Connected Learning Sources</h2>
          <p className="text-white/80">Connect your accounts to track learning progress across platforms</p>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {integrations.map((integration) => {
            const platformData = integration.platform_data;
            const isConnected = integration.connected;

            return (
              <Card key={integration.platform} className="overflow-hidden" data-testid={`integration-${integration.platform}`}>
                {/* Platform Header */}
                <div className={`bg-gradient-to-r ${getPlatformColor(integration.platform)} text-white p-6`}>
                  <div className="flex items-center justify-between mb-4">
                    {getPlatformIcon(integration.platform)}
                    {isConnected ? (
                      <CheckCircle2 className="w-6 h-6" data-testid={`${integration.platform}-connected-icon`} />
                    ) : (
                      <XCircle className="w-6 h-6 opacity-50" data-testid={`${integration.platform}-disconnected-icon`} />
                    )}
                  </div>
                  <h3 className="text-2xl font-bold capitalize">{integration.platform}</h3>
                  <p className="text-sm opacity-90 mt-1">
                    {isConnected ? 'Connected' : 'Not connected'}
                  </p>
                </div>

                {/* Platform Data */}
                <div className="p-6">
                  {isConnected && platformData ? (
                    <div className="space-y-3 mb-4">
                      {integration.platform === 'github' && (
                        <>
                          <div className="flex justify-between">
                            <span className="text-gray-600">Repositories</span>
                            <span className="font-semibold" data-testid="github-repos">{platformData.repos_count}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-600">Commits (month)</span>
                            <span className="font-semibold" data-testid="github-commits">{platformData.commits_this_month}</span>
                          </div>
                          <div>
                            <p className="text-gray-600 mb-2">Top Languages:</p>
                            <div className="flex flex-wrap gap-2">
                              {platformData.top_languages.map((lang) => (
                                <Badge key={lang} className="bg-gray-100 text-gray-700" data-testid={`github-language-${lang}`}>
                                  {lang}
                                </Badge>
                              ))}
                            </div>
                          </div>
                        </>
                      )}
                      
                      {integration.platform === 'linkedin' && (
                        <>
                          <div className="flex justify-between">
                            <span className="text-gray-600">Connections</span>
                            <span className="font-semibold" data-testid="linkedin-connections">{platformData.connections}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-600">Courses Completed</span>
                            <span className="font-semibold" data-testid="linkedin-courses">{platformData.courses_completed.length}</span>
                          </div>
                          <div>
                            <p className="text-gray-600 mb-2">Skills Endorsed:</p>
                            <div className="flex flex-wrap gap-2">
                              {platformData.skills_endorsed.slice(0, 3).map((skill) => (
                                <Badge key={skill} className="bg-blue-100 text-blue-700" data-testid={`linkedin-skill-${skill}`}>
                                  {skill}
                                </Badge>
                              ))}
                            </div>
                          </div>
                        </>
                      )}
                      
                      {integration.platform === 'youtube' && (
                        <>
                          <div className="flex justify-between">
                            <span className="text-gray-600">Subscriptions</span>
                            <span className="font-semibold" data-testid="youtube-subscriptions">{platformData.subscriptions}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-600">Learning Playlists</span>
                            <span className="font-semibold" data-testid="youtube-playlists">{platformData.learning_playlists.length}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-600">Watch Time</span>
                            <span className="font-semibold" data-testid="youtube-watch-time">{platformData.total_watch_time_hours}h</span>
                          </div>
                        </>
                      )}
                    </div>
                  ) : (
                    <p className="text-gray-500 mb-4">Connect to see your learning data</p>
                  )}

                  {isConnected ? (
                    <Button
                      variant="outline"
                      className="w-full"
                      onClick={() => handleDisconnect(integration.platform)}
                      data-testid={`disconnect-${integration.platform}-button`}
                    >
                      Disconnect
                    </Button>
                  ) : (
                    <Button
                      className="w-full"
                      onClick={() => handleConnect(integration.platform)}
                      data-testid={`connect-${integration.platform}-button`}
                    >
                      Connect {integration.platform}
                    </Button>
                  )}
                </div>
              </Card>
            );
          })}
        </div>

        {/* Info Section */}
        <Card className="mt-8 p-6 bg-white/95 backdrop-blur-sm" data-testid="info-section">
          <h3 className="text-xl font-bold mb-3">Why Connect?</h3>
          <ul className="space-y-2 text-gray-700">
            <li className="flex items-start gap-2">
              <CheckCircle2 className="w-5 h-5 text-green-600 mt-0.5" />
              <span><strong>GitHub:</strong> Track your coding activity, commits, and technologies used</span>
            </li>
            <li className="flex items-start gap-2">
              <CheckCircle2 className="w-5 h-5 text-green-600 mt-0.5" />
              <span><strong>LinkedIn:</strong> Import completed courses and professional skills</span>
            </li>
            <li className="flex items-start gap-2">
              <CheckCircle2 className="w-5 h-5 text-green-600 mt-0.5" />
              <span><strong>YouTube:</strong> Monitor learning playlists and educational content</span>
            </li>
          </ul>
          <p className="text-sm text-gray-600 mt-4">
            <strong>Note:</strong> For MVP, integrations show sample data. Real OAuth integration requires platform API credentials.
          </p>
        </Card>
      </main>
    </div>
  );
};

export default IntegrationsPage;
