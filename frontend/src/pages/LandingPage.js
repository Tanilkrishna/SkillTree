import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Sparkles, TrendingUp, Target, Zap, Trophy, BookOpen, Users, ArrowRight, Github, Linkedin, Youtube, Brain, Rocket, CheckCircle2 } from 'lucide-react';

const LandingPage = () => {
  const navigate = useNavigate();
  const [scrollY, setScrollY] = useState(0);

  useEffect(() => {
    const handleScroll = () => setScrollY(window.scrollY);
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const features = [
    {
      icon: <Target className="w-8 h-8" />,
      title: "Interactive Skill Tree",
      description: "Visualize your learning journey with a beautiful, gamified skill tree that tracks your progress in real-time"
    },
    {
      icon: <Brain className="w-8 h-8" />,
      title: "AI-Powered Recommendations",
      description: "Get personalized skill suggestions based on your goals, progress, and industry trends using advanced AI"
    },
    {
      icon: <BookOpen className="w-8 h-8" />,
      title: "Structured Lessons",
      description: "Follow curated learning paths with bite-sized lessons designed to maximize retention and understanding"
    },
    {
      icon: <Trophy className="w-8 h-8" />,
      title: "Achievements & Rewards",
      description: "Earn badges, unlock achievements, and level up as you master new skills and complete challenges"
    },
    {
      icon: <Zap className="w-8 h-8" />,
      title: "Real-time Progress Tracking",
      description: "Monitor your XP, level, and completion rates with detailed analytics and beautiful visualizations"
    },
    {
      icon: <Users className="w-8 h-8" />,
      title: "External Integrations",
      description: "Connect your GitHub, LinkedIn, and YouTube to sync your real-world achievements and projects"
    }
  ];

  const integrations = [
    { icon: <Github className="w-6 h-6" />, name: "GitHub" },
    { icon: <Linkedin className="w-6 h-6" />, name: "LinkedIn" },
    { icon: <Youtube className="w-6 h-6" />, name: "YouTube" }
  ];

  const stats = [
    { number: "20+", label: "Skills Available" },
    { number: "100+", label: "Lessons" },
    { number: "AI", label: "Powered" },
    { number: "∞", label: "Growth Potential" }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-purple-950 to-slate-900 text-white overflow-hidden">
      {/* Animated Background Elements */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-20 left-10 w-72 h-72 bg-purple-500/10 rounded-full blur-3xl animate-pulse"></div>
        <div className="absolute bottom-20 right-10 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl animate-pulse delay-1000"></div>
        <div className="absolute top-1/2 left-1/2 w-64 h-64 bg-pink-500/10 rounded-full blur-3xl animate-pulse delay-2000"></div>
      </div>

      {/* Navigation */}
      <nav className="relative z-10 container mx-auto px-6 py-6 flex justify-between items-center fade-in">
        <div className="flex items-center gap-2">
          <div className="w-10 h-10 bg-gradient-to-br from-purple-500 to-pink-500 rounded-lg flex items-center justify-center">
            <Sparkles className="w-6 h-6" />
          </div>
          <span className="text-2xl font-bold bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">
            SkillTree
          </span>
        </div>
        <div className="flex gap-4">
          <button
            onClick={() => navigate('/auth')}
            className="px-6 py-2 rounded-lg border border-white/20 hover:bg-white/10 transition-all duration-300 hover:scale-105"
          >
            Sign In
          </button>
          <button
            onClick={() => navigate('/auth')}
            className="px-6 py-2 rounded-lg bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 transition-all duration-300 hover:scale-105 shadow-lg shadow-purple-500/50"
          >
            Get Started
          </button>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative z-10 container mx-auto px-6 pt-20 pb-32">
        <div className="max-w-4xl mx-auto text-center">
          <div className="inline-flex items-center gap-2 px-4 py-2 bg-white/10 rounded-full mb-8 backdrop-blur-sm fade-in-up animation-delay-100">
            <Rocket className="w-4 h-4 text-purple-400" />
            <span className="text-sm">AI-Powered Learning Platform</span>
          </div>
          
          <h1 className="text-6xl md:text-7xl font-bold mb-6 fade-in-up animation-delay-200">
            Master Your Skills,
            <br />
            <span className="bg-gradient-to-r from-purple-400 via-pink-400 to-blue-400 bg-clip-text text-transparent">
              Visualize Your Growth
            </span>
          </h1>
          
          <p className="text-xl text-gray-300 mb-12 max-w-2xl mx-auto fade-in-up animation-delay-300">
            Transform your learning journey with an interactive skill tree, AI-powered recommendations, 
            and gamified progress tracking. Level up your career one skill at a time.
          </p>
          
          <div className="flex flex-col sm:flex-row gap-4 justify-center fade-in-up animation-delay-400">
            <button
              onClick={() => navigate('/auth')}
              className="group px-8 py-4 rounded-lg bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 transition-all duration-300 hover:scale-105 shadow-xl shadow-purple-500/50 flex items-center justify-center gap-2"
            >
              <span className="font-semibold">Start Learning Free</span>
              <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
            </button>
            <button
              onClick={() => document.getElementById('features').scrollIntoView({ behavior: 'smooth' })}
              className="px-8 py-4 rounded-lg border border-white/20 hover:bg-white/10 transition-all duration-300 hover:scale-105"
            >
              Explore Features
            </button>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8 mt-20 fade-in-up animation-delay-500">
            {stats.map((stat, index) => (
              <div key={index} className="text-center">
                <div className="text-4xl font-bold bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent mb-2">
                  {stat.number}
                </div>
                <div className="text-sm text-gray-400">{stat.label}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Floating Skill Nodes Animation */}
        <div className="absolute top-1/4 left-10 w-16 h-16 bg-gradient-to-br from-purple-500/20 to-pink-500/20 rounded-full backdrop-blur-sm border border-white/10 flex items-center justify-center animate-float">
          <TrendingUp className="w-8 h-8 text-purple-400" />
        </div>
        <div className="absolute top-1/3 right-20 w-20 h-20 bg-gradient-to-br from-blue-500/20 to-cyan-500/20 rounded-full backdrop-blur-sm border border-white/10 flex items-center justify-center animate-float animation-delay-1000">
          <Brain className="w-10 h-10 text-blue-400" />
        </div>
        <div className="absolute bottom-20 left-1/4 w-12 h-12 bg-gradient-to-br from-pink-500/20 to-purple-500/20 rounded-full backdrop-blur-sm border border-white/10 flex items-center justify-center animate-float animation-delay-2000">
          <Trophy className="w-6 h-6 text-pink-400" />
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="relative z-10 py-20 bg-white/5 backdrop-blur-sm">
        <div className="container mx-auto px-6">
          <div className="text-center mb-16 fade-in-up">
            <div className="inline-flex items-center gap-2 px-4 py-2 bg-white/10 rounded-full mb-4 backdrop-blur-sm">
              <Sparkles className="w-4 h-4 text-purple-400" />
              <span className="text-sm">Features</span>
            </div>
            <h2 className="text-4xl md:text-5xl font-bold mb-4">
              Everything You Need to
              <br />
              <span className="bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">
                Accelerate Your Learning
              </span>
            </h2>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            {features.map((feature, index) => (
              <div
                key={index}
                className="group p-8 rounded-2xl bg-white/5 backdrop-blur-sm border border-white/10 hover:bg-white/10 transition-all duration-300 hover:scale-105 hover:shadow-xl hover:shadow-purple-500/20 fade-in-up"
                style={{ animationDelay: `${index * 100}ms` }}
              >
                <div className="w-16 h-16 bg-gradient-to-br from-purple-500/20 to-pink-500/20 rounded-xl flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
                  {feature.icon}
                </div>
                <h3 className="text-xl font-bold mb-2">{feature.title}</h3>
                <p className="text-gray-400">{feature.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Integrations Section */}
      <section className="relative z-10 py-20">
        <div className="container mx-auto px-6">
          <div className="max-w-3xl mx-auto text-center fade-in-up">
            <h2 className="text-4xl font-bold mb-4">
              Connect Your Learning Ecosystem
            </h2>
            <p className="text-gray-400 mb-12">
              Seamlessly integrate with your favorite platforms to track real-world achievements
            </p>
            <div className="flex justify-center gap-6">
              {integrations.map((integration, index) => (
                <div
                  key={index}
                  className="w-20 h-20 bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl flex items-center justify-center hover:bg-white/10 transition-all duration-300 hover:scale-110 cursor-pointer"
                  style={{ animationDelay: `${index * 100}ms` }}
                >
                  {integration.icon}
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="relative z-10 py-20">
        <div className="container mx-auto px-6">
          <div className="max-w-4xl mx-auto text-center p-12 rounded-3xl bg-gradient-to-r from-purple-500/20 to-pink-500/20 backdrop-blur-sm border border-white/10 fade-in-up">
            <h2 className="text-4xl md:text-5xl font-bold mb-4">
              Ready to Level Up?
            </h2>
            <p className="text-xl text-gray-300 mb-8">
              Join thousands of learners visualizing their growth and achieving their goals
            </p>
            <button
              onClick={() => navigate('/auth')}
              className="group px-8 py-4 rounded-lg bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 transition-all duration-300 hover:scale-105 shadow-xl shadow-purple-500/50 inline-flex items-center gap-2"
            >
              <span className="font-semibold text-lg">Get Started for Free</span>
              <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
            </button>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="relative z-10 py-12 border-t border-white/10">
        <div className="container mx-auto px-6">
          <div className="flex flex-col md:flex-row justify-between items-center">
            <div className="flex items-center gap-2 mb-4 md:mb-0">
              <div className="w-8 h-8 bg-gradient-to-br from-purple-500 to-pink-500 rounded-lg flex items-center justify-center">
                <Sparkles className="w-5 h-5" />
              </div>
              <span className="text-xl font-bold">SkillTree</span>
            </div>
            <div className="text-gray-400 text-sm">
              © 2025 SkillTree. Empowering learners worldwide.
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default LandingPage;
