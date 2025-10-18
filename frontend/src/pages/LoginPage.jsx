import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import { setUser, setRole } from '../store/authSlice';
import { fetchUserRoles } from '../store/authSlice';
import authService from '../services/authService';

const LoginPage = () => {
  const [formData, setFormData] = useState({
    email: '',
    password: ''
  });
  const [error, setError] = useState('');
  
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const { loading } = useSelector((state) => state.auth);

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    try {
      const data = await authService.login(formData.email, formData.password);
      
      // Store user data in Redux
      dispatch(setUser(data.user));
      dispatch(setRole(data.user.role));
      
      // Fetch user roles and permissions and wait for completion
      await dispatch(fetchUserRoles()).unwrap();
      
      // Tokens are automatically stored in HTTP-only cookies
      // No need to handle them in JavaScript
      
      // Redirect based on role
      if (data.user.role === 'admin') {
        navigate('/admin-dashboard');
      } else if (data.user.role === 'manager') {
        navigate('/manager-dashboard');
      } else {
        navigate('/member-dashboard');
      }
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <div className="h-screen w-screen overflow-hidden bg-gradient-to-br from-amber-50 via-stone-100 to-neutral-200 flex flex-col">
      {/* Compact Header */}
      <header className="bg-white/80 backdrop-blur-sm shadow-sm flex-shrink-0">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-3">
            <div className="flex items-center">
              <h1 className="text-xl font-bold text-gray-900">On Call 24/7</h1>
            </div>
            <button
              onClick={() => navigate('/')}
              className="text-gray-600 hover:text-gray-900 text-sm font-medium px-3 py-1 rounded-md hover:bg-gray-100 transition-colors"
            >
              ← Back to Home
            </button>
          </div>
        </div>
      </header>

      {/* Main Content - Centered and Compact */}
      <main className="flex-1 flex items-center justify-center px-4 sm:px-6 lg:px-8 py-4">
        <div className="w-full max-w-sm">
          <div className="text-center mb-6">
            <h2 className="text-3xl font-bold text-gray-900 mb-1">
              Welcome Back
            </h2>
            <p className="text-gray-700">
              Sign in to your account
            </p>
          </div>

          <div className="bg-white/90 backdrop-blur-sm rounded-2xl shadow-xl p-6">
            <form className="space-y-4" onSubmit={handleSubmit}>
              <div className="space-y-3">
                <div>
                  <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">
                    Email Address
                  </label>
                  <input
                    id="email"
                    name="email"
                    type="email"
                    autoComplete="email"
                    required
                    className="w-full px-3 py-3 text-base border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-transparent transition-all duration-200 placeholder-gray-400"
                    placeholder="Enter your email"
                    value={formData.email}
                    onChange={handleChange}
                  />
                </div>
                <div>
                  <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-1">
                    Password
                  </label>
                  <input
                    id="password"
                    name="password"
                    type="password"
                    autoComplete="current-password"
                    required
                    className="w-full px-3 py-3 text-base border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-transparent transition-all duration-200 placeholder-gray-400"
                    placeholder="Enter your password"
                    value={formData.password}
                    onChange={handleChange}
                  />
                </div>
              </div>

              {error && (
                <div className="bg-red-50 border border-red-200 text-red-700 px-3 py-2 rounded-lg text-sm">
                  {error}
                </div>
              )}

              <div>
                <button
                  type="submit"
                  disabled={loading}
                  className="w-full bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-600 hover:to-orange-600 text-white font-bold py-3 px-4 rounded-lg text-base transition-all duration-200 transform hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none shadow-lg"
                >
                  {loading ? (
                    <div className="flex items-center justify-center">
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                      Signing in...
                    </div>
                  ) : (
                    'Sign In'
                  )}
                </button>
              </div>
            </form>
          </div>

          <div className="text-center mt-4">
            <p className="text-xs text-gray-600">
              Don't have an account? Contact your administrator.
            </p>
          </div>
        </div>
      </main>

      {/* Compact Footer */}
      <footer className="bg-white/80 backdrop-blur-sm flex-shrink-0">
        <div className="max-w-4xl mx-auto py-3 px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <p className="text-gray-600 text-xs">
              &copy; 2025 On Call 24/7. All rights reserved.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default LoginPage;
