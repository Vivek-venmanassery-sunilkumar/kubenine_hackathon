import api from './api';

const teamService = {
  getAll: () => api.get('/manager/teams/'),
  create: (data) => api.post('/manager/teams/', data),
  getById: (id) => api.get(`/manager/teams/${id}/`),
  update: (id, data) => api.put(`/manager/teams/${id}/`, data),
  delete: (id) => api.delete(`/manager/teams/${id}/`),
};

const invitationService = {
  send: (data) => api.post('/manager/invitations/', data),
  getAll: () => api.get('/manager/invitations/'),
  getById: (id) => api.get(`/manager/invitations/${id}/`),
  resend: (id) => api.post(`/manager/invitations/${id}/resend/`),
  cancel: (id) => api.delete(`/manager/invitations/${id}/`),
};

const dashboardService = {
  getOverview: () => api.get('/manager/dashboard/'),
  getStats: () => api.get('/manager/dashboard/stats/'),
};

const scheduleService = {
  // Team schedule configuration
  getTeamConfig: (teamId) => api.get(`/schedule/config/?team_id=${teamId}`),
  saveTeamConfig: (data) => api.post('/schedule/config/', data),
  updateTeamConfig: (data) => api.post('/schedule/config/', data), // Same endpoint for create/update
  
  // Team schedule status
  getTeamStatus: (teamId) => api.get(`/schedule/status/${teamId}/`),
  
  // Schedule generation and management
  generateSchedule: (teamId) => api.post(`/schedule/generate/${teamId}/`),
  getSchedules: (teamId) => api.get(`/schedule/schedules/${teamId}/`),
  getSchedule: (scheduleId) => api.get(`/schedule/schedule/${scheduleId}/`),
  publishSchedule: (scheduleId) => api.post(`/schedule/schedule/${scheduleId}/publish/`),
  
  // Schedule validation
  validateSchedule: (scheduleId) => api.post(`/schedule/schedule/${scheduleId}/validate/`),
};

const managerService = {
  teams: teamService,
  invitations: invitationService,
  dashboard: dashboardService,
  schedule: scheduleService,
};

export default managerService;
export { teamService, invitationService, dashboardService, scheduleService };
