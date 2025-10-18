const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1/';

class ApiService {
  constructor() {
    this.baseURL = API_BASE_URL;
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    const config = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    };

    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('API request failed:', error);
      throw error;
    }
  }

  // User endpoints
  async getUsers() {
    return this.request('users/');
  }

  async getUser(id) {
    return this.request(`users/${id}/`);
  }

  async getCurrentUser() {
    return this.request('users/me/');
  }
}

export default new ApiService();
