import api from './api';

class AuthService {
  // Login user
  async login(email, password) {
    try {
      const response = await api.post('/auth/login/', {
        email,
        password,
      });
      return response.data;
    } catch (error) {
      throw new Error(
        error.response?.data?.error || 
        error.response?.data?.detail || 
        'Login failed'
      );
    }
  }

  // Logout user
  async logout() {
    try {
      const response = await api.post('/auth/logout/');
      return response.data;
    } catch (error) {
      throw new Error(
        error.response?.data?.error || 
        error.response?.data?.detail || 
        'Logout failed'
      );
    }
  }

  // Refresh access token
  async refreshToken() {
    try {
      const response = await api.post('/auth/refresh/');
      return response.data;
    } catch (error) {
      throw new Error(
        error.response?.data?.error || 
        error.response?.data?.detail || 
        'Token refresh failed'
      );
    }
  }

  // Register manager (admin only)
  async registerManager(email, password, name = '') {
    try {
      const response = await api.post('/auth/register/manager/', {
        email,
        password,
        name,
      });
      return response.data;
    } catch (error) {
      throw new Error(
        error.response?.data?.error || 
        error.response?.data?.detail || 
        'Manager registration failed'
      );
    }
  }

  // Get current user info
  async getCurrentUser() {
    try {
      const response = await api.get('/users/me/');
      return response.data;
    } catch (error) {
      throw new Error(
        error.response?.data?.error || 
        error.response?.data?.detail || 
        'Failed to get user info'
      );
    }
  }

  // Check if user is authenticated
  async checkAuth() {
    try {
      const response = await api.get('/users/me/');
      return response.data;
    } catch (error) {
      return null;
    }
  }

  // Get user roles and permissions
  async getRoles() {
    try {
      const response = await api.get('/auth/roles/');
      return response.data;
    } catch (error) {
      throw new Error(
        error.response?.data?.error || 
        error.response?.data?.detail || 
        'Failed to get user roles'
      );
    }
  }
}

export default new AuthService();
