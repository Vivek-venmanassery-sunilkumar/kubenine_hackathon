import api from './api';

const memberService = {
  // Schedule related endpoints
  schedule: {
    // Get member's schedule for the next 7 days
    getMySchedule: async () => {
      try {
        const response = await api.get('/member/schedule/');
        return response.data;
      } catch (error) {
        throw error;
      }
    },

    // Get only the current user's assigned slots
    getMySlots: async () => {
      try {
        const response = await api.get('/member/schedule/my_slots/');
        return response.data;
      } catch (error) {
        throw error;
      }
    },

    // Get the full team schedule for the next 7 days
    getTeamSchedule: async () => {
      try {
        const response = await api.get('/member/schedule/team_schedule/');
        return response.data;
      } catch (error) {
        throw error;
      }
    },

    // Get team schedule for managers (separate endpoint for better reliability)
    getManagerTeamSchedule: async () => {
      try {
        const response = await api.get('/member/schedule/manager_team_schedule/');
        return response.data;
      } catch (error) {
        throw error;
      }
    }
  },

  // Swap request related endpoints
  swapRequests: {
    // Get all swap requests (sent and received)
    getAll: async () => {
      try {
        const response = await api.get('/member/swap-requests/');
        return response.data;
      } catch (error) {
        throw error;
      }
    },

    // Removed unused endpoints: getSent, getReceived

    // Create a new swap request
    create: async (requesterSlotId, responderSlotId) => {
      try {
        const response = await api.post('/member/swap-requests/', {
          requester_slot: requesterSlotId,
          responder_slot_id: responderSlotId
        });
        return response.data;
      } catch (error) {
        throw error;
      }
    },

    // Accept a swap request
    accept: async (swapRequestId) => {
      try {
        const response = await api.post(`/member/swap-requests/${swapRequestId}/accept/`);
        return response.data;
      } catch (error) {
        throw error;
      }
    },

    // Reject a swap request
    reject: async (swapRequestId, rejectionReason = '') => {
      try {
        const response = await api.post(`/member/swap-requests/${swapRequestId}/reject/`, {
          rejection_reason: rejectionReason
        });
        return response.data;
      } catch (error) {
        throw error;
      }
    },

    // Removed unused endpoint: getById
  },

  // Team member related endpoints
  teamMembers: {
    // Get all team members
    getAll: async () => {
      try {
        const response = await api.get('/member/team-members/');
        return response.data;
      } catch (error) {
        throw error;
      }
    },

    // Get team members for managers (separate endpoint for better reliability)
    getManagerTeamMembers: async () => {
      try {
        const response = await api.get('/member/team-members/manager_team_members/');
        return response.data;
      } catch (error) {
        throw error;
      }
    }
  }
};

export default memberService;
