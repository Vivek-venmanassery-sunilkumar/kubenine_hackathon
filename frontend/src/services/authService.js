import api from './api';
import { getErrorMessage, ERROR_TYPES } from '../utils/errorHandler';

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
      // The error is already structured by the API interceptor
      const message = getErrorMessage(error);
      throw new Error(message);
    }
  }

  // Logout user
  async logout() {
    try {
      const response = await api.post('/auth/logout/');
      return response.data;
    } catch (error) {
      const message = getErrorMessage(error);
      throw new Error(message);
    }
  }

  // Refresh access token
  async refreshToken() {
    try {
      const response = await api.post('/auth/refresh/');
      return response.data;
    } catch (error) {
      const message = getErrorMessage(error);
      throw new Error(message);
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
      const message = getErrorMessage(error);
      throw new Error(message);
    }
  }

  // Get current user info
  async getCurrentUser() {
    try {
      const response = await api.get('/users/me/');
      return response.data;
    } catch (error) {
      const message = getErrorMessage(error);
      throw new Error(message);
    }
  }

  // Check if user is authenticated
  async checkAuth() {
    try {
      const response = await api.get('/users/me/');
      return response.data;
    } catch (error) {
      // For auth check, we don't want to throw errors
      // Just return null if not authenticated
      return null;
    }
  }

  // Get user roles and permissions
  async getRoles() {
    try {
      const response = await api.get('/auth/roles/');
      return response.data;
    } catch (error) {
      const message = getErrorMessage(error);
      throw new Error(message);
    }
  }

  // Register with invitation
  async registerWithInvitation(data) {
    try {
      const response = await api.post('/auth/register/invitation/', data);
      return response.data;
    } catch (error) {
      const message = getErrorMessage(error);
      throw new Error(message);
    }
  }

  // Helper method to check if error is a specific type
  isErrorType(error, type) {
    return error.type === type;
  }

  // Helper method to get error details
  getErrorDetails(error) {
    return error.details || {};
  }
}

export default new AuthService();
