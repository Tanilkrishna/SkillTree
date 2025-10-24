import { useState, useEffect } from 'react';
import axios from 'axios';
import { API } from '@/App';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { TreePine, LogOut, Github, Linkedin, Youtube, CheckCircle, Link as LinkIcon } from 'lucide-react';
import { toast } from 'sonner';

export default function IntegrationsPage({ user, onLogout }) {
  const navigate = useNavigate();
  const [integrations, setIntegrations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [connecting, setConnecting] = useState(null);

  useEffect(() => {
    fetchIntegrations();
  }, []);

  const fetchIntegrations = async () => {
    try {
      const response = await axios.get(`${API}/integrations`);
      setIntegrations(response.data);
    } catch (error) {
      toast.error('Failed to load integrations');
    }
    setLoading(false);
  };

  const connectPlatform = async (platform) => {
    setConnecting(platform);
    try {
      const response = await axios.post(`${API}/integrations/connect/${platform}`);
      toast.success(`${platform} connected successfully!`);
      fetchIntegrations();
    } catch (error) {
      toast.error(`Failed to connect ${platform}`);
    }
    setConnecting(null);
  };

  const syncPlatform = async (platform) => {
    try {
      const response = await axios.get(`${API}/integrations/${platform}/sync`);
      toast.success(`${platform} synced successfully!`);
    } catch (error) {
      toast.error(`Failed to sync ${platform}`);
    }
  };

  const getPlatformIcon = (platform) => {
    switch (platform) {
      case 'github':
        return <Github className="w-8 h-8" />;
      case 'linkedin':
        return <Linkedin className="w-8 h-8" />;
      case 'youtube':
        return <Youtube className="w-8 h-8" />;
      default:
        return <LinkIcon className="w-8 h-8" />;
    }
  };

  const getPlatformColor = (platform) => {
    switch (platform) {
      case 'github':
        return 'bg-gray-900 text-white';
      case 'linkedin':
        return 'bg-blue-600 text-white';
      case 'youtube':
        return 'bg-red-600 text-white';
      default:
        return 'bg-gray-600 text-white';
    }
  };

  return (
    <div className="min-h-screen">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-10" data-testid="integrations-header">
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
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8" data-testid="integrations-main">
        <div className="mb-8">
          <h2 className="text-3xl font-bold mb-2">Connect Learning Platforms 🔗</h2>
          <p className="text-gray-600">Link your learning sources to automatically track your progress</p>
          <Badge variant="secondary" className="mt-2">Demo Mode - Mock Data</Badge>
        </div>

        {loading ? (
          <div className="text-center py-12">Loading integrations...</div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {integrations.map((integration) => (
              <Card key={integration.id} className="card-hover" data-testid={`integration-card-${integration.platform}`}>
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-3">
                      <div className={`p-3 rounded-lg ${getPlatformColor(integration.platform)}`}>
                        {getPlatformIcon(integration.platform)}
                      </div>
                      <div>
                        <CardTitle className="text-xl capitalize">{integration.platform}</CardTitle>
                        <div className="flex items-center gap-2 mt-1">
                          {integration.connected && (
                            <Badge variant="secondary" className="bg-green-100 text-green-800">
                              <CheckCircle className="w-3 h-3 mr-1" />
                              Connected
                            </Badge>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  {integration.connected && integration.mock_data && (
                    <div className="mb-4 p-3 bg-gray-50 rounded-lg" data-testid={`mock-data-${integration.platform}`}>
                      <CardDescription className="font-semibold mb-2">Mock Data:</CardDescription>
                      <ul className="text-sm space-y-1">
                        {Object.entries(integration.mock_data).map(([key, value]) => (
                          <li key={key} className="text-gray-700">
                            <span className="font-medium">{key.replace(/_/g, ' ')}:</span> {Array.isArray(value) ? value.join(', ') : value}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                  <div className="space-y-2">
                    {!integration.connected ? (
                      <Button
                        className="w-full"
                        onClick={() => connectPlatform(integration.platform)}
                        disabled={connecting === integration.platform}
                        data-testid={`connect-btn-${integration.platform}`}
                      >
                        {connecting === integration.platform ? 'Connecting...' : `Connect ${integration.platform}`}
                      </Button>
                    ) : (
                      <Button
                        variant="outline"
                        className="w-full"
                        onClick={() => syncPlatform(integration.platform)}
                        data-testid={`sync-btn-${integration.platform}`}
                      >
                        Sync Data
                      </Button>
                    )}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}

        {/* Info Section */}
        <Card className="mt-8" data-testid="info-card">
          <CardHeader>
            <CardTitle>About Integrations</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-gray-600 mb-4">
              In production, these integrations would connect to real APIs and automatically track your learning activities:
            </p>
            <ul className="space-y-2 text-gray-700">
              <li><strong>GitHub:</strong> Track repositories, commits, and programming languages used</li>
              <li><strong>LinkedIn:</strong> Import professional skills and completed courses</li>
              <li><strong>YouTube:</strong> Monitor learning playlists and educational content watched</li>
            </ul>
            <p className="text-sm text-gray-500 mt-4">
              Currently showing mock data for demonstration purposes.
            </p>
          </CardContent>
        </Card>
      </main>
    </div>
  );
}