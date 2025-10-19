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

  // Removed unused endpoint: getById

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
   * Get managers who are not assigned to any organization
   * @returns {Promise} API response with available managers list
   */
  getAvailable: () => api.get('/admin/managers/available/'),

  /**
   * Register a new manager
   * @param {Object} data - Manager registration data
   * @param {string} data.name - Manager name
   * @param {string} data.email - Manager email
   * @param {string} data.password - Manager password (min 8 characters)
   * @returns {Promise} API response with created manager data
   */
  register: (data) => api.post('/auth/register/manager/', data),

  // Removed unused endpoint: getById

  /**
   * Update manager
   * @param {number} id - Manager ID
   * @param {Object} data - Updated manager data
   * @param {string} data.name - Manager name
   * @param {string} data.email - Manager email
   * @param {string} [data.password] - New password (optional)
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

// Removed unused dashboardService - not used anywhere in the codebase

// Combined admin service object for easy importing
const adminService = {
  organizations: organizationService,
  managers: managerService,
};

export default adminService;
