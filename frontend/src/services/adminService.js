import api from './api';

/**
 * Admin Dashboard Service
 * Handles all API calls related to admin dashboard functionality
 */

// Organization Management
export const organizationService = {
  /**
   * Get all organizations
   * @returns {Promise} API response with organizations list
   */
  getAll: () => api.get('/admin/organizations/'),

  /**
   * Create a new organization
   * @param {Object} data - Organization data
   * @param {string} data.name - Organization name
   * @param {string} [data.description] - Organization description
   * @returns {Promise} API response with created organization
   */
  create: (data) => api.post('/admin/organizations/', data),

  /**
   * Get organization by ID
   * @param {number} id - Organization ID
   * @returns {Promise} API response with organization data
   */
  getById: (id) => api.get(`/admin/organizations/${id}/`),

  /**
   * Update organization
   * @param {number} id - Organization ID
   * @param {Object} data - Updated organization data
   * @returns {Promise} API response with updated organization
   */
  update: (id, data) => api.put(`/admin/organizations/${id}/`, data),

  /**
   * Delete organization
   * @param {number} id - Organization ID
   * @returns {Promise} API response
   */
  delete: (id) => api.delete(`/admin/organizations/${id}/`),
};

// Manager Management
export const managerService = {
  /**
   * Get all managers with their organization information
   * @returns {Promise} API response with managers list
   */
  getAll: () => api.get('/admin/managers/'),

  /**
   * Register a new manager
   * @param {Object} data - Manager registration data
   * @param {string} data.name - Manager name
   * @param {string} data.email - Manager email
   * @param {string} data.password - Manager password (min 8 characters)
   * @param {number} data.organization_id - Organization ID to assign manager to
   * @returns {Promise} API response with created manager data
   */
  register: (data) => api.post('/admin/managers/', data),

  /**
   * Get manager by ID
   * @param {number} id - Manager ID
   * @returns {Promise} API response with manager data
   */
  getById: (id) => api.get(`/admin/managers/${id}/`),

  /**
   * Update manager
   * @param {number} id - Manager ID
   * @param {Object} data - Updated manager data
   * @returns {Promise} API response with updated manager
   */
  update: (id, data) => api.put(`/admin/managers/${id}/`, data),

  /**
   * Delete manager
   * @param {number} id - Manager ID
   * @returns {Promise} API response
   */
  delete: (id) => api.delete(`/admin/managers/${id}/`),
};

// Dashboard Statistics
export const dashboardService = {
  /**
   * Get dashboard overview data
   * @returns {Promise} API response with dashboard data
   */
  getOverview: () => api.get('/admin/dashboard/'),

  /**
   * Get dashboard statistics
   * @returns {Promise} API response with dashboard statistics
   */
  getStats: () => api.get('/admin/dashboard/stats/'),
};

// Combined admin service object for easy importing
const adminService = {
  organizations: organizationService,
  managers: managerService,
  dashboard: dashboardService,
};

export default adminService;
