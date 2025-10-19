import axios from 'axios';
import { 
  parseAPIError, 
  handleNetworkError, 
  createErrorHandler,
  ERROR_TYPES 
} from '../utils/errorHandler';

// Create axios instance with base configuration
const api = axios.create({
  baseURL: '/api', // Use proxy instead of direct URL
  timeout: 10000,
  withCredentials: true, // Important for HTTP-only cookies
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth headers
api.interceptors.request.use(
  (config) => {
    // Get JWT token from localStorage
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle common errors
api.interceptors.response.use(
  (response) => {
    return response;
  },
  async (error) => {
    // Handle different types of errors
    if (error.response) {
      // Server responded with error status
      const structuredError = await parseAPIError(error.response, error.response.data);
      
      // Handle specific error types
      if (structuredError.type === ERROR_TYPES.UNAUTHORIZED) {
        // Clear stored tokens and redirect to login
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        // You can dispatch a logout action here if using Redux
      }
      
      return Promise.reject(structuredError);
    } else if (error.request) {
      // Network error
      const structuredError = handleNetworkError(error);
      return Promise.reject(structuredError);
    } else {
      // Other error
      return Promise.reject(error);
    }
  }
);

// Create error handler for API calls
export const createAPIErrorHandler = (showNotification, navigate) => {
  return createErrorHandler(showNotification, navigate);
};

// Default error handler
export const defaultAPIErrorHandler = createAPIErrorHandler(
  (notification) => {
    // Default notification handler - replace with your notification system
    console.error('API Error:', notification);
    if (notification.type === 'error') {
      alert(notification.message);
    }
  },
  (path) => {
    // Default navigation handler - replace with your router
    console.log('Navigate to:', path);
    window.location.href = path;
  }
);

export default api;