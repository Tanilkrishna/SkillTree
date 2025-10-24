import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { toast } from 'sonner';
import { API } from '@/App';

const AdminPage = ({ user, onLogout }) => {
  const navigate = useNavigate();
  const [skills, setSkills] = useState([]);
  const [loading, setLoading] = useState(false);
  const [generatedLessons, setGeneratedLessons] = useState([]);
  
  const [formData, setFormData] = useState({
    skill_id: '',
    new_skill_name: '',
    new_skill_category: '',
    topic: '',
    difficulty: 'beginner',
    xp_points: 100,
    lesson_count: 5,
    learning_objective: ''
  });

  useEffect(() => {
    if (!user?.is_admin) {
      toast.error('Admin access required');
      navigate('/dashboard');
      return;
    }
    fetchSkills();
  }, [user, navigate]);

  const fetchSkills = async () => {
    try {
      const response = await axios.get(`${API}/admin/skills`);
      setSkills(response.data);
    } catch (error) {
      toast.error('Failed to fetch skills');
    }
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setGeneratedLessons([]);

    try {
      // Validate form
      if (formData.skill_id === 'new' && (!formData.new_skill_name || !formData.new_skill_category)) {
        toast.error('Please provide skill name and category for new skill');
        setLoading(false);
        return;
      }

      if (!formData.topic || !formData.learning_objective) {
        toast.error('Please fill in all required fields');
        setLoading(false);
        return;
      }

      // Prepare request data
      const requestData = {
        skill_id: formData.skill_id === 'new' ? null : formData.skill_id,
        new_skill_name: formData.skill_id === 'new' ? formData.new_skill_name : null,
        new_skill_category: formData.skill_id === 'new' ? formData.new_skill_category : null,
        topic: formData.topic,
        difficulty: formData.difficulty,
        xp_points: parseInt(formData.xp_points),
        lesson_count: parseInt(formData.lesson_count),
        learning_objective: formData.learning_objective
      };

      const response = await axios.post(`${API}/admin/lessons/generate`, requestData);
      
      toast.success(response.data.message);
      setGeneratedLessons(response.data.lessons);
      
      // Refresh skills list if new skill was created
      if (formData.skill_id === 'new') {
        await fetchSkills();
      }
      
      // Reset form
      setFormData({
        skill_id: '',
        new_skill_name: '',
        new_skill_category: '',
        topic: '',
        difficulty: 'beginner',
        xp_points: 100,
        lesson_count: 5,
        learning_objective: ''
      });
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to generate lessons');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-purple-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <button
                onClick={() => navigate('/dashboard')}
                className="text-indigo-600 hover:text-indigo-700 font-semibold"
              >
                ← Back to Dashboard
              </button>
              <h1 className="text-2xl font-bold text-gray-900">Admin Panel</h1>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-600">{user?.name}</span>
              <button
                onClick={onLogout}
                className="px-4 py-2 text-sm text-red-600 hover:text-red-700 font-medium"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-white rounded-xl shadow-lg p-8">
          <h2 className="text-3xl font-bold text-gray-900 mb-2">AI Lesson Generator</h2>
          <p className="text-gray-600 mb-8">Create new lessons using AI based on topics and difficulty levels</p>

          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Skill Selection */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Select Skill or Create New
              </label>
              <select
                name="skill_id"
                value={formData.skill_id}
                onChange={handleInputChange}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                required
              >
                <option value="">-- Select a skill --</option>
                <option value="new">🆕 Create New Skill</option>
                {skills.map(skill => (
                  <option key={skill.id} value={skill.id}>
                    {skill.name} ({skill.category})
                  </option>
                ))}
              </select>
            </div>

            {/* New Skill Fields */}
            {formData.skill_id === 'new' && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 p-4 bg-indigo-50 rounded-lg">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    New Skill Name *
                  </label>
                  <input
                    type="text"
                    name="new_skill_name"
                    value={formData.new_skill_name}
                    onChange={handleInputChange}
                    placeholder="e.g., Advanced React Hooks"
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                    required={formData.skill_id === 'new'}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Category *
                  </label>
                  <select
                    name="new_skill_category"
                    value={formData.new_skill_category}
                    onChange={handleInputChange}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                    required={formData.skill_id === 'new'}
                  >
                    <option value="">-- Select category --</option>
                    <option value="Web Development">Web Development</option>
                    <option value="Backend Development">Backend Development</option>
                    <option value="Database">Database</option>
                    <option value="Data Science">Data Science</option>
                    <option value="DevOps">DevOps</option>
                    <option value="Mobile Development">Mobile Development</option>
                    <option value="AI/ML">AI/ML</option>
                    <option value="Cloud Computing">Cloud Computing</option>
                  </select>
                </div>
              </div>
            )}

            {/* Topic */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Topic / Subject *
              </label>
              <input
                type="text"
                name="topic"
                value={formData.topic}
                onChange={handleInputChange}
                placeholder="e.g., React Custom Hooks, Docker Compose, SQL Joins"
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                required
              />
            </div>

            {/* Learning Objective */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Learning Objective / Focus Area *
              </label>
              <textarea
                name="learning_objective"
                value={formData.learning_objective}
                onChange={handleInputChange}
                placeholder="Describe what learners should achieve after completing these lessons..."
                rows={4}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                required
              />
            </div>

            {/* Difficulty, XP, and Lesson Count */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Difficulty Level
                </label>
                <select
                  name="difficulty"
                  value={formData.difficulty}
                  onChange={handleInputChange}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                >
                  <option value="beginner">Beginner</option>
                  <option value="intermediate">Intermediate</option>
                  <option value="advanced">Advanced</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  XP Points per Lesson
                </label>
                <input
                  type="number"
                  name="xp_points"
                  value={formData.xp_points}
                  onChange={handleInputChange}
                  min="10"
                  max="1000"
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Number of Lessons
                </label>
                <input
                  type="number"
                  name="lesson_count"
                  value={formData.lesson_count}
                  onChange={handleInputChange}
                  min="1"
                  max="20"
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                />
              </div>
            </div>

            {/* Submit Button */}
            <div className="flex justify-end">
              <button
                type="submit"
                disabled={loading}
                className="px-8 py-3 bg-indigo-600 text-white font-semibold rounded-lg hover:bg-indigo-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
              >
                {loading ? '🤖 Generating Lessons...' : '✨ Generate Lessons with AI'}
              </button>
            </div>
          </form>

          {/* Generated Lessons Display */}
          {generatedLessons.length > 0 && (
            <div className="mt-12 border-t pt-8">
              <h3 className="text-2xl font-bold text-gray-900 mb-6">
                ✅ Generated Lessons ({generatedLessons.length})
              </h3>
              <div className="space-y-6">
                {generatedLessons.map((lesson, index) => (
                  <div key={lesson.id} className="bg-gradient-to-r from-green-50 to-emerald-50 rounded-lg p-6 border border-green-200">
                    <div className="flex items-start justify-between mb-3">
                      <div>
                        <span className="inline-block px-3 py-1 bg-green-600 text-white text-xs font-semibold rounded-full mb-2">
                          Lesson {index + 1}
                        </span>
                        <h4 className="text-xl font-bold text-gray-900">{lesson.title}</h4>
                      </div>
                      <span className="text-sm text-gray-600">⏱️ {lesson.estimated_time} min</span>
                    </div>
                    <p className="text-gray-700 whitespace-pre-wrap mb-4">{lesson.content}</p>
                    {lesson.resources && lesson.resources.length > 0 && (
                      <div className="mt-4">
                        <p className="text-sm font-semibold text-gray-700 mb-2">📚 Resources:</p>
                        <ul className="space-y-1">
                          {lesson.resources.map((resource, idx) => (
                            <li key={idx}>
                              <a
                                href={resource.url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-sm text-indigo-600 hover:text-indigo-700 hover:underline"
                              >
                                {resource.title} →
                              </a>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
};

export default AdminPage;
