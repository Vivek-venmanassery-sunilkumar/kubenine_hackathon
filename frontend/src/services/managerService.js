import api from './api';

const teamService = {
  getAll: () => api.get('/manager/teams/'),
  create: (data) => api.post('/manager/teams/', data),
  // Removed unused endpoints: getById, update, delete
};

const invitationService = {
  send: (data) => api.post('/manager/invitations/', data),
  getAll: () => api.get('/manager/invitations/'),
  resend: (id) => api.post(`/manager/invitations/${id}/resend/`),
  cancel: (id) => api.delete(`/manager/invitations/${id}/`),
  // Removed unused endpoint: getById
};

// Removed unused dashboardService - not used anywhere in the codebase

const scheduleService = {
  // Team schedule configuration
  getTeamConfig: (teamId) => api.get(`/schedule/config/?team_id=${teamId}`),
  saveTeamConfig: (data) => api.post('/schedule/config/', data),
  
  // Team schedule status
  getTeamStatus: (teamId) => api.get(`/schedule/status/${teamId}/`),
  
  // Schedule generation
  generateSchedule: (teamId) => api.post(`/schedule/generate/${teamId}/`),
  
  // Removed unused endpoints: updateTeamConfig, getSchedules, getSchedule, publishSchedule, validateSchedule
};

const managerService = {
  teams: teamService,
  invitations: invitationService,
  schedule: scheduleService,
};

export default managerService;
export { teamService, invitationService, scheduleService };
