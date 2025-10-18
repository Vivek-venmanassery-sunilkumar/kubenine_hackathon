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

const managerService = {
  teams: teamService,
  invitations: invitationService,
  dashboard: dashboardService,
};

export default managerService;
export { teamService, invitationService, dashboardService };
