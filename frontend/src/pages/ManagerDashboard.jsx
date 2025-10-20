import React, { useState, useEffect } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';
import { logout } from '../store/authSlice';
import authService from '../services/authService';
import managerService from '../services/managerService';
import memberService from '../services/memberService';
import { getErrorMessage } from '../utils/errorHandler';

const ManagerDashboard = () => {
  const { user, role } = useSelector((state) => state.auth);
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('teams');
  const [teams, setTeams] = useState([]);
  const [invitations, setInvitations] = useState([]);
  const [teamMembers, setTeamMembers] = useState([]);
  const [newTeamName, setNewTeamName] = useState('');
  const [inviteEmail, setInviteEmail] = useState('');
  const [selectedTeam, setSelectedTeam] = useState('');
  const [loading, setLoading] = useState(false);
  const [tabLoading, setTabLoading] = useState(false);
  const [teamConfigs, setTeamConfigs] = useState({});
  const [editingConfig, setEditingConfig] = useState(null);
  const [configForm, setConfigForm] = useState({
    timeslot_duration_hours: 4,
    min_break_hours: 12
  });
  const [selectedTeamForSchedule, setSelectedTeamForSchedule] = useState('');
  const [teamSchedules, setTeamSchedules] = useState({});
  const [teamScheduleStatus, setTeamScheduleStatus] = useState({});
  const [teamScheduleByDate, setTeamScheduleByDate] = useState({});

  // Helper function to check if an email has been accepted for a team
  const isEmailAccepted = (email, teamId) => {
    return invitations.some(inv => 
      inv.email.toLowerCase() === email.toLowerCase() && 
      parseInt(inv.team) === parseInt(teamId) && 
      inv.status === 'accepted'
    );
  };

  // Helper function to check if an email has a pending invitation for a team
  const isEmailPending = (email, teamId) => {
    return invitations.some(inv => 
      inv.email.toLowerCase() === email.toLowerCase() && 
      parseInt(inv.team) === parseInt(teamId) && 
      inv.status === 'pending'
    );
  };

  // Helper function to check if an email is already a team member
  const isEmailTeamMember = (email) => {
    return teamMembers.some(member => 
      (member.member_email || member.email || '').toLowerCase() === email.toLowerCase()
    );
  };

  // Helper function to get the team name for an email that's already a member
  const getTeamNameForEmail = (email) => {
    const member = teamMembers.find(member => 
      (member.member_email || member.email || '').toLowerCase() === email.toLowerCase()
    );
    return member ? member.team_name : 'another team';
  };

  // Helper functions for schedule display (same as MemberDashboard)
  const getNext7Days = () => {
    const days = [];
    const today = new Date();
    
    // Get the start of the current week (Sunday)
    const startOfWeek = new Date(today);
    const dayOfWeek = today.getDay(); // 0 = Sunday, 1 = Monday, etc.
    startOfWeek.setDate(today.getDate() - dayOfWeek);
    
    // Generate 7 days starting from the start of the current week
    for (let i = 0; i < 7; i++) {
      const date = new Date(startOfWeek);
      date.setDate(startOfWeek.getDate() + i);
      days.push(date.toISOString().split('T')[0]);
    }
    return days;
  };

  const getSlotsForDate = (date, teamId) => {
    return teamScheduleByDate[teamId]?.[date] || [];
  };

  const formatDate = (date) => {
    return new Date(date).toLocaleDateString('en-US', {
      weekday: 'short',
      month: 'short',
      day: 'numeric'
    });
  };

  const formatTime = (datetime) => {
    return new Date(datetime).toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      hour12: true
    });
  };

  const getMemberName = (slot) => {
    // Use the new API fields if available
    if (slot.assigned_member_name) {
      return slot.assigned_member_name;
    }
    
    // Fallback to old logic if new fields not available
    if (slot.assigned_member) {
      // If assigned_member is an object with name property
      if (typeof slot.assigned_member === 'object' && slot.assigned_member.name) {
        return slot.assigned_member.name;
      }
      
      // If assigned_member is an ID, look up in teamMembers
      if (teamMembers && Array.isArray(teamMembers)) {
        const member = teamMembers.find(m => 
          m.member_id === slot.assigned_member || 
          m.member === slot.assigned_member || 
          m.id === slot.assigned_member
        );
        if (member) {
          return member.member_name || member.name || `Member ${slot.assigned_member}`;
        }
      }
      
      return `Member ${slot.assigned_member}`;
    }
    
    return 'Unassigned';
  };

  // Load data on component mount
  useEffect(() => {
    const loadAllData = async () => {
      await loadTeams();
      await loadInvitations();
      await loadTeamMembers();
      // Load configs and status after teams are loaded
      if (teams.length > 0) {
        await loadTeamConfigs();
        await loadTeamScheduleStatus();
      }
    };
    loadAllData();
  }, []);

  // Load configs and status when teams change
  useEffect(() => {
    if (teams.length > 0) {
      loadTeamConfigs();
      loadTeamScheduleStatus();
    }
  }, [teams]);

  // Load data when tab changes
  useEffect(() => {
    const loadTabData = async () => {
      console.log(`Tab changed to: ${activeTab}`);
      setTabLoading(true);
      
      try {
        switch (activeTab) {
          case 'teams':
            // Teams data is already loaded on mount
            console.log('Teams tab - data already loaded');
            break;
            
          case 'invitations':
            // Reload invitations when switching to invitations tab
            console.log('Invitations tab - reloading invitations');
            await loadInvitations();
            break;
            
          case 'schedule':
            // Reload schedule data when switching to schedule tab
            console.log('Schedule tab - reloading schedule data');
            if (teams.length > 0) {
              await loadTeamConfigs();
              await loadTeamScheduleStatus();
            } else {
              console.log('No teams available for schedule tab');
            }
            break;
            
          default:
            console.log(`Unknown tab: ${activeTab}`);
        }
      } catch (error) {
        console.error(`Error loading data for tab ${activeTab}:`, error);
        toast.error(`Failed to load ${activeTab} data`);
      } finally {
        setTabLoading(false);
      }
    };
    
    loadTabData();
  }, [activeTab]);

  const loadTeams = async () => {
    try {
      const response = await managerService.teams.getAll();
      setTeams(response.data);
    } catch (error) {
      console.error('Error loading teams:', error);
      toast.error('Failed to load teams');
    }
  };

  const loadInvitations = async () => {
    try {
      const response = await managerService.invitations.getAll();
      setInvitations(response.data);
    } catch (error) {
      console.error('Error loading invitations:', error);
      toast.error('Failed to load invitations');
    }
  };

  const loadTeamMembers = async () => {
    try {
      // Get team members through the teams endpoint
      const response = await managerService.teams.getAll();
      // Extract team members from teams data if available
      const members = [];
      response.data.forEach(team => {
        if (team.members && Array.isArray(team.members)) {
          team.members.forEach(member => {
            members.push({ ...member, team_id: team.id, team_name: team.team_name });
          });
        }
      });
      setTeamMembers(members);
    } catch (error) {
      console.error('Error loading team members:', error);
      toast.error('Failed to load team members');
    }
  };

  const loadTeamConfigs = async () => {
    try {
      console.log('Loading team configs for teams:', teams);
      const configs = {};
      for (const team of teams) {
        try {
          console.log(`Loading config for team ${team.id}: ${team.team_name}`);
          const response = await managerService.schedule.getTeamConfig(team.id);
          console.log(`Config loaded for team ${team.id}:`, response.data);
          configs[team.id] = response.data;
        } catch (error) {
          console.error(`Error loading config for team ${team.id}:`, error);
          // Set default config for teams that don't have one
          configs[team.id] = {
            timeslot_duration_hours: 4,
            min_break_hours: 12,
            team: team.id,
            team_name: team.team_name
          };
        }
      }
      console.log('All team configs loaded:', configs);
      setTeamConfigs(configs);
    } catch (error) {
      console.error('Error loading team configs:', error);
    }
  };

  const loadTeamScheduleStatus = async () => {
    try {
      console.log('Loading team schedule status for teams:', teams);
      const statuses = {};
      for (const team of teams) {
        try {
          console.log(`Loading status for team ${team.id}: ${team.team_name}`);
          const response = await managerService.schedule.getTeamStatus(team.id);
          console.log(`Status loaded for team ${team.id}:`, response.data);
          statuses[team.id] = response.data;
        } catch (error) {
          console.error(`Error loading schedule status for team ${team.id}:`, error);
          // Set default status for teams that don't have one
          statuses[team.id] = {
            team_id: team.id,
            team_name: team.team_name,
            member_count: 0,
            required_members: 5,
            can_schedule: false,
            has_schedules: false
          };
        }
      }
      console.log('All team statuses loaded:', statuses);
      setTeamScheduleStatus(statuses);
    } catch (error) {
      console.error('Error loading team schedule statuses:', error);
    }
  };

  const loadTeamSchedule = async (teamId) => {
    try {
      // First load the team status to get member count and requirements
      const statusResponse = await managerService.schedule.getTeamStatus(teamId);
      setTeamScheduleStatus(prev => ({
        ...prev,
        [teamId]: statusResponse.data
      }));

      // Use manager-specific endpoints for better reliability
      const [teamScheduleResponse, teamMembersResponse] = await Promise.all([
        memberService.schedule.getManagerTeamSchedule(),
        memberService.teamMembers.getManagerTeamMembers()
      ]);

      // Use the same data structure handling as MemberDashboard
      const schedules = teamScheduleResponse.schedules || [];
      const teamMembers = teamMembersResponse.members || [];
      
      setTeamSchedules(prev => ({
        ...prev,
        [teamId]: schedules
      }));
      
      // Process schedule data the same way as MemberDashboard
      if (schedules.length > 0) {
        const scheduleByDate = {};
        
        // Process ALL schedules, not just the first one
        schedules.forEach(schedule => {
          if (schedule.timeslots) {
            schedule.timeslots.forEach(timeslot => {
              const dateKey = new Date(timeslot.start_datetime).toISOString().split('T')[0];
              if (!scheduleByDate[dateKey]) {
                scheduleByDate[dateKey] = [];
              }
              scheduleByDate[dateKey].push(timeslot);
            });
          }
        });
        
        setTeamScheduleByDate(prev => ({
          ...prev,
          [teamId]: scheduleByDate
        }));
      }
      
      // Update team members for this team
      setTeamMembers(prev => {
        const teamMembersForTeam = teamMembers.filter(member => 
          member.team_id === teamId || member.team === teamId
        );
        return [...prev.filter(member => 
          member.team_id !== teamId && member.team !== teamId
        ), ...teamMembersForTeam];
      });
      
      return schedules;
    } catch (error) {
      console.error(`Error loading schedule for team ${teamId}:`, error);
      toast.error('Failed to load team schedule');
      return [];
    }
  };

  const handleCreateTeam = async (e) => {
    e.preventDefault();
    if (newTeamName.trim()) {
      setLoading(true);
      try {
        const response = await managerService.teams.create({
          team_name: newTeamName.trim()
        });
        setTeams([...teams, response.data]);
        setNewTeamName('');
        toast.success('Team created successfully!');
        // Reload configs after creating team
        await loadTeamConfigs();
      } catch (error) {
        console.error('Error creating team:', error);
        toast.error('Failed to create team: ' + (error.response?.data?.detail || error.message));
      } finally {
        setLoading(false);
      }
    }
  };

  const handleEditConfig = (teamId) => {
    const config = teamConfigs[teamId];
    setEditingConfig(teamId);
    setConfigForm({
      timeslot_duration_hours: config?.timeslot_duration_hours || 4,
      min_break_hours: config?.min_break_hours || 12
    });
  };

  const handleSaveConfig = async (teamId) => {
    try {
      const response = await managerService.schedule.saveTeamConfig({
        team: teamId,
        ...configForm
      });

      setTeamConfigs({
        ...teamConfigs,
        [teamId]: response.data
      });
      setEditingConfig(null);
      toast.success('Scheduling configuration saved!');
    } catch (error) {
      console.error('Error saving config:', error);
      const errorMessage = error.response?.data?.detail || error.response?.data?.message || 'Failed to save configuration';
      toast.error(errorMessage);
    }
  };

  const handleCancelEdit = () => {
    setEditingConfig(null);
    setConfigForm({
      timeslot_duration_hours: 4,
      min_break_hours: 12
    });
  };

  const handleInviteMember = async (e) => {
    e.preventDefault();
    if (inviteEmail.trim() && selectedTeam) {
      setLoading(true);
      try {
        await managerService.invitations.send({
          email: inviteEmail.trim(),
          team: parseInt(selectedTeam)
        });
        setInviteEmail('');
        setSelectedTeam('');
        toast.success('Invitation sent successfully!');
        // Refresh invitations list
        loadInvitations();
      } catch (error) {
        console.error('Error sending invitation:', error);
        
        // The error is already structured by the API interceptor
        const message = getErrorMessage(error);
        toast.error(message);
      } finally {
        setLoading(false);
      }
    }
  };

  const handleLogout = async () => {
    try {
      await authService.logout();
      dispatch(logout());
      navigate('/');
    } catch (error) {
      console.error('Logout error:', error);
      dispatch(logout());
      navigate('/');
    }
  };

  return (
    <div className="min-h-screen w-screen overflow-x-hidden bg-gradient-to-br from-amber-50 via-stone-100 to-neutral-200">
      {/* Header */}
      <header className="bg-white/90 backdrop-blur-sm shadow-lg">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div>
              <h1 className="text-4xl font-bold text-gray-900">Manager Dashboard</h1>
              <p className="text-lg text-gray-700 mt-1">Welcome back, {user?.name || user?.email}</p>
            </div>
            <button
              onClick={handleLogout}
              className="bg-gradient-to-r from-red-500 to-red-600 hover:from-red-600 hover:to-red-700 text-white px-6 py-3 rounded-xl text-sm font-medium transition-all duration-200 transform hover:scale-105 shadow-lg"
            >
              Logout
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto py-8 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          <div className="bg-white/90 backdrop-blur-sm rounded-2xl shadow-xl p-8">
            <div className="text-center mb-8">
              <h2 className="text-3xl font-bold text-gray-900 mb-4">
                OnCall Scheduler Manager Panel
              </h2>
              <p className="text-lg text-gray-700 mb-2">
                Manage teams and invite members
              </p>
              <p className="text-sm text-gray-600">
                Lead your team with comprehensive management tools
              </p>
            </div>
            
            {/* Tab Navigation */}
            <div className="flex space-x-1 mb-8 bg-gray-100 p-1 rounded-xl">
              <button
                onClick={() => setActiveTab('teams')}
                className={`flex-1 py-3 px-6 rounded-lg font-medium transition-all duration-200 ${
                  activeTab === 'teams'
                    ? 'bg-white text-blue-600 shadow-md'
                    : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
                }`}
              >
                <div className="flex items-center justify-center space-x-2">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                  </svg>
                  <span>Manage Teams</span>
                </div>
              </button>
              <button
                onClick={() => setActiveTab('invitations')}
                className={`flex-1 py-3 px-6 rounded-lg font-medium transition-all duration-200 ${
                  activeTab === 'invitations'
                    ? 'bg-white text-green-600 shadow-md'
                    : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
                }`}
              >
                <div className="flex items-center justify-center space-x-2">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 4.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                  </svg>
                  <span>Invite Members</span>
                </div>
              </button>
              <button
                onClick={() => setActiveTab('schedule')}
                className={`flex-1 py-3 px-6 rounded-lg font-medium transition-all duration-200 ${
                  activeTab === 'schedule'
                    ? 'bg-white text-purple-600 shadow-md'
                    : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
                }`}
              >
                <div className="flex items-center justify-center space-x-2">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                  </svg>
                  <span>Schedule for the Next 7 Days</span>
                </div>
              </button>
            </div>

            {/* Loading Indicator */}
            {tabLoading && (
              <div className="flex items-center justify-center py-8">
                <div className="flex items-center space-x-3">
                  <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
                  <span className="text-gray-600">Loading {activeTab} data...</span>
                </div>
              </div>
            )}

            {/* Tab Content */}
            {!tabLoading && activeTab === 'teams' && (
              <div className="space-y-6">
                <div className="bg-gradient-to-r from-blue-50 to-indigo-50 p-6 rounded-xl border border-blue-200">
                  <h3 className="text-xl font-bold text-gray-900 mb-4">Create New Team</h3>
                  <form onSubmit={handleCreateTeam} className="space-y-4">
                    <div className="flex gap-4">
                      <input
                        type="text"
                        value={newTeamName}
                        onChange={(e) => setNewTeamName(e.target.value)}
                        placeholder="Enter team name"
                        className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        required
                        disabled={loading}
                      />
                    </div>
                    <div className="flex justify-end">
                      <button
                        type="submit"
                        disabled={loading}
                        className="bg-gradient-to-r from-blue-500 to-indigo-500 hover:from-blue-600 hover:to-indigo-600 disabled:from-gray-400 disabled:to-gray-500 text-white font-bold py-3 px-6 rounded-lg transition-all duration-200 transform hover:scale-105 shadow-lg disabled:transform-none"
                      >
                        {loading ? 'Creating...' : 'Create Team'}
                      </button>
                    </div>
                  </form>
                </div>

                <div className="bg-white p-6 rounded-xl border border-gray-200">
                  <h3 className="text-xl font-bold text-gray-900 mb-4">Teams ({teams.length})</h3>
                  {teams.length === 0 ? (
                    <p className="text-gray-500 text-center py-8">No teams created yet</p>
                  ) : (
                    <div className="space-y-6">
                      {teams.map((team) => {
                        // Filter invitations by team ID (now available in the response)
                        const teamInvitations = invitations.filter(inv => parseInt(inv.team) === parseInt(team.id));
                        const teamMembersList = teamMembers.filter(member => parseInt(member.team_id) === parseInt(team.id));
                        const pendingInvitations = teamInvitations.filter(inv => inv.status === 'pending');
                        const acceptedInvitations = teamInvitations.filter(inv => inv.status === 'accepted');
                        
                        return (
                          <div key={team.id} className="border border-gray-200 rounded-lg p-6 bg-gray-50">
                            {/* Team Header */}
                            <div className="flex items-center justify-between mb-4">
                              <div>
                                <h4 className="text-lg font-semibold text-gray-900">{team.team_name}</h4>
                                <p className="text-sm text-blue-600 font-medium">Organization: {team.organization_name}</p>
                                <p className="text-sm text-gray-500">Created: {new Date(team.created_at).toLocaleDateString()}</p>
                              </div>
                              <div className="flex space-x-2">
                                <button 
                                  onClick={() => handleEditConfig(team.id)}
                                  className="text-blue-600 hover:text-blue-800 font-medium text-sm"
                                >
                                  Configure Scheduling
                                </button>
                                <button className="text-red-600 hover:text-red-800 font-medium text-sm">Delete</button>
                              </div>
                            </div>

                            {/* Scheduling Configuration */}
                            <div className="mb-4 p-4 bg-blue-50 rounded-lg border border-blue-200">
                              <h5 className="text-md font-medium text-gray-800 mb-3 flex items-center">
                                <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                                </svg>
                                Scheduling Configuration
                              </h5>
                              
                              {editingConfig === team.id ? (
                                <div className="space-y-3">
                                  <div className="grid grid-cols-2 gap-4">
                                    <div>
                                      <label className="block text-sm font-medium text-gray-700 mb-1">
                                        Timeslot Duration (hours)
                                      </label>
                                      <select
                                        value={configForm.timeslot_duration_hours}
                                        onChange={(e) => setConfigForm({
                                          ...configForm,
                                          timeslot_duration_hours: parseInt(e.target.value)
                                        })}
                                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                      >
                                        {[1, 2, 3, 4, 6, 8].map(hours => (
                                          <option key={hours} value={hours}>{hours} hour{hours !== 1 ? 's' : ''}</option>
                                        ))}
                                      </select>
                                    </div>
                                    <div>
                                      <label className="block text-sm font-medium text-gray-700 mb-1">
                                        Minimum Break (hours)
                                      </label>
                                      <select
                                        value={configForm.min_break_hours}
                                        onChange={(e) => setConfigForm({
                                          ...configForm,
                                          min_break_hours: parseInt(e.target.value)
                                        })}
                                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                      >
                                        {[1, 2, 4, 6, 8, 12, 16, 24].map(hours => (
                                          <option key={hours} value={hours}>{hours} hour{hours !== 1 ? 's' : ''}</option>
                                        ))}
                                      </select>
                                    </div>
                                  </div>
                                  <div className="flex space-x-2">
                                    <button
                                      onClick={() => handleSaveConfig(team.id)}
                                      className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-md text-sm font-medium"
                                    >
                                      Save
                                    </button>
                                    <button
                                      onClick={handleCancelEdit}
                                      className="bg-gray-500 hover:bg-gray-600 text-white px-4 py-2 rounded-md text-sm font-medium"
                                    >
                                      Cancel
                                    </button>
                                  </div>
                                </div>
                              ) : (
                                <div className="space-y-2">
                                  <div className="flex justify-between items-center">
                                    <span className="text-sm text-gray-600">Timeslot Duration:</span>
                                    <span className="text-sm font-medium text-gray-900">
                                      {teamConfigs[team.id]?.timeslot_duration_hours || 4} hours
                                    </span>
                                  </div>
                                  <div className="flex justify-between items-center">
                                    <span className="text-sm text-gray-600">Minimum Break:</span>
                                    <span className="text-sm font-medium text-gray-900">
                                      {teamConfigs[team.id]?.min_break_hours || 12} hours
                                    </span>
                                  </div>
                                  <div className="flex justify-between items-center">
                                    <span className="text-sm text-gray-600">Status:</span>
                                    <span className={`text-sm font-medium px-2 py-1 rounded ${
                                      teamConfigs[team.id] 
                                        ? 'bg-green-100 text-green-800' 
                                        : 'bg-yellow-100 text-yellow-800'
                                    }`}>
                                      {teamConfigs[team.id] ? 'Configured' : 'Not Configured'}
                                    </span>
                                  </div>
                                </div>
                              )}
                            </div>

                            {/* Team Members */}
                            <div className="mb-4">
                              <h5 className="text-md font-medium text-gray-800 mb-2">
                                Team Members ({teamMembersList.length})
                              </h5>
                              {teamMembersList.length === 0 ? (
                                <p className="text-sm text-gray-500 italic">No members yet</p>
                              ) : (
                                <div className="space-y-2">
                                  {teamMembersList.map((member) => (
                                    <div key={member.id} className="flex items-center justify-between bg-white p-3 rounded border">
                                      <div>
                                        <span className="font-medium text-gray-900">{member.member_name || member.name}</span>
                                        <span className="text-sm text-gray-600 ml-2">({member.member_email || member.email})</span>
                                      </div>
                                      <span className="text-xs text-green-600 bg-green-100 px-2 py-1 rounded">
                                        Joined {new Date(member.joined_at).toLocaleDateString()}
                                      </span>
                                    </div>
                                  ))}
                                </div>
                              )}
                            </div>

                            {/* Pending Invitations */}
                            <div>
                              <h5 className="text-md font-medium text-gray-800 mb-2">
                                Pending Invitations ({pendingInvitations.length})
                              </h5>
                              {pendingInvitations.length === 0 ? (
                                <p className="text-sm text-gray-500 italic">No pending invitations</p>
                              ) : (
                                <div className="space-y-2">
                                  {pendingInvitations.map((invitation) => (
                                    <div key={invitation.id} className="flex items-center justify-between bg-yellow-50 p-3 rounded border border-yellow-200">
                                      <div>
                                        <span className="font-medium text-gray-900">{invitation.email}</span>
                                        <span className="text-sm text-gray-600 ml-2">
                                          Invited {new Date(invitation.created_at).toLocaleDateString()}
                                        </span>
                                      </div>
                                      <div className="flex space-x-2">
                                        <span className="text-xs text-yellow-600 bg-yellow-100 px-2 py-1 rounded">
                                          Pending
                                        </span>
                                        <button 
                                          className="text-xs text-blue-600 hover:text-blue-800"
                                          onClick={() => {
                                            if (window.confirm('Resend invitation to ' + invitation.email + '?')) {
                                              managerService.invitations.resend(invitation.id);
                                            }
                                          }}
                                        >
                                          Resend
                                        </button>
                                        <button 
                                          className="text-xs text-red-600 hover:text-red-800"
                                          onClick={() => {
                                            if (window.confirm('Cancel invitation to ' + invitation.email + '?')) {
                                              managerService.invitations.cancel(invitation.id);
                                              loadInvitations();
                                            }
                                          }}
                                        >
                                          Cancel
                                        </button>
                                      </div>
                                    </div>
                                  ))}
                                </div>
                              )}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>
              </div>
            )}

            {!tabLoading && activeTab === 'invitations' && (
              <div className="space-y-6">
                <div className="bg-gradient-to-r from-green-50 to-emerald-50 p-6 rounded-xl border border-green-200">
                  <h3 className="text-xl font-bold text-gray-900 mb-4">Invite New Member</h3>
                  <form onSubmit={handleInviteMember} className="space-y-4">
                    <div className="flex gap-4">
                      <div className="flex-1">
                      <input
                        type="email"
                        value={inviteEmail}
                        onChange={(e) => setInviteEmail(e.target.value)}
                        placeholder="Enter member email address"
                          className={`w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent ${
                            inviteEmail.trim() && isEmailTeamMember(inviteEmail.trim())
                              ? 'border-red-300 bg-red-50'
                              : inviteEmail.trim() && selectedTeam && isEmailAccepted(inviteEmail.trim(), selectedTeam)
                              ? 'border-red-300 bg-red-50'
                              : inviteEmail.trim() && selectedTeam && isEmailPending(inviteEmail.trim(), selectedTeam)
                              ? 'border-yellow-300 bg-yellow-50'
                              : 'border-gray-300'
                          }`}
                        required
                        disabled={loading}
                      />
                        {/* Status indicator */}
                        {inviteEmail.trim() && (
                          <div className="mt-2">
                            {isEmailTeamMember(inviteEmail.trim()) && (
                              <div className="flex items-center text-red-600 text-sm">
                                <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
                                </svg>
                                This email is already a member of {getTeamNameForEmail(inviteEmail.trim())}. Members can only belong to one team at a time.
                              </div>
                            )}
                            {!isEmailTeamMember(inviteEmail.trim()) && selectedTeam && isEmailAccepted(inviteEmail.trim(), selectedTeam) && (
                              <div className="flex items-center text-red-600 text-sm">
                                <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
                                </svg>
                                This email has already been accepted for this team
                              </div>
                            )}
                            {!isEmailTeamMember(inviteEmail.trim()) && selectedTeam && isEmailPending(inviteEmail.trim(), selectedTeam) && (
                              <div className="flex items-center text-yellow-600 text-sm">
                                <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                                </svg>
                                A pending invitation already exists for this email and team
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                      <select
                        value={selectedTeam}
                        onChange={(e) => setSelectedTeam(e.target.value)}
                        className="px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent min-w-[200px]"
                        required
                        disabled={loading}
                      >
                        <option value="">Select Team</option>
                        {teams.filter(team => team.is_active).map((team) => (
                          <option key={team.id} value={team.id}>
                            {team.team_name}
                          </option>
                        ))}
                      </select>
                    </div>
                    <div className="flex justify-end">
                      <button
                        type="submit"
                        disabled={
                          loading || 
                          !inviteEmail.trim() || 
                          !selectedTeam ||
                          isEmailTeamMember(inviteEmail.trim()) ||
                          isEmailAccepted(inviteEmail.trim(), selectedTeam) ||
                          isEmailPending(inviteEmail.trim(), selectedTeam)
                        }
                        className="bg-gradient-to-r from-green-500 to-emerald-500 hover:from-green-600 hover:to-emerald-600 disabled:from-gray-400 disabled:to-gray-500 text-white font-bold py-3 px-6 rounded-lg transition-all duration-200 transform hover:scale-105 shadow-lg disabled:transform-none"
                      >
                        {loading ? 'Sending...' : 'Send Invitation'}
                      </button>
                    </div>
                  </form>
                </div>

                <div className="bg-white p-6 rounded-xl border border-gray-200">
                  <h3 className="text-xl font-bold text-gray-900 mb-4">Invitation Info</h3>
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                    <p className="text-blue-800">
                      <strong>How it works:</strong> When you invite a member, they will receive an email with a secure registration link. 
                      They can use this link to create their account and join your organization.
                    </p>
                  </div>
                </div>
              </div>
            )}

            {!tabLoading && activeTab === 'schedule' && (
              <div className="space-y-6">
                {/* Team Selection */}
                <div className="bg-gradient-to-r from-purple-50 to-indigo-50 p-6 rounded-xl border border-purple-200">
                  <h3 className="text-xl font-bold text-gray-900 mb-4">Select Team to View Schedule for the Next 7 Days</h3>
                  <div className="flex gap-4">
                    <select
                      value={selectedTeamForSchedule}
                      onChange={(e) => {
                        setSelectedTeamForSchedule(e.target.value);
                        if (e.target.value) {
                          loadTeamSchedule(e.target.value);
                        }
                      }}
                      className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                    >
                      <option value="">Choose a team to view their schedule for the next 7 days</option>
                      {teams.map((team) => (
                        <option key={team.id} value={team.id}>
                          {team.team_name}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>

                {/* Schedule Display */}
                {selectedTeamForSchedule && (
                  <div className="bg-white p-6 rounded-xl border border-gray-200">
                    {(() => {
                      const team = teams.find(t => t.id === parseInt(selectedTeamForSchedule));
                      const status = teamScheduleStatus[selectedTeamForSchedule];
                      const schedules = teamSchedules[selectedTeamForSchedule] || [];
                      
                      if (!status) {
                        return (
                          <div className="text-center py-8">
                            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600 mx-auto mb-4"></div>
                            <p className="text-gray-500">Loading team status...</p>
                          </div>
                        );
                      }

                      if (!status.can_generate_schedule) {
                        const needed = status.required_members - status.member_count;
                        return (
                          <div className="text-center py-8">
                            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
                              <svg className="w-12 h-12 text-yellow-600 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
                              </svg>
                              <h4 className="text-lg font-semibold text-yellow-800 mb-2">Insufficient Team Members</h4>
                              <p className="text-yellow-700 mb-4">
                                <strong>{team.team_name}</strong> needs <strong>{needed} more member{needed !== 1 ? 's' : ''}</strong> to start automatic scheduling.
                              </p>
                              <div className="bg-white rounded-lg p-4 border border-yellow-300">
                                <div className="grid grid-cols-2 gap-4 text-sm">
                                  <div>
                                    <span className="text-gray-600">Current Members:</span>
                                    <span className="font-semibold text-gray-900 ml-2">{status.member_count}</span>
                                  </div>
                                  <div>
                                    <span className="text-gray-600">Required Members:</span>
                                    <span className="font-semibold text-gray-900 ml-2">{status.required_members}</span>
                                  </div>
                                </div>
                              </div>
                              <p className="text-sm text-yellow-600 mt-4">
                                Invite more members to enable automatic scheduling for this team.
                              </p>
                            </div>
                          </div>
                        );
                      }

                      if (schedules.length === 0) {
                        return (
                          <div className="text-center py-8">
                            <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
                              <svg className="w-12 h-12 text-blue-600 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                              </svg>
                              <h4 className="text-lg font-semibold text-blue-800 mb-2">Schedule Loading</h4>
                              <p className="text-blue-700 mb-4">
                                The schedule for <strong>{team.team_name}</strong> is being automatically generated and will appear here shortly.
                              </p>
                              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
                            </div>
                          </div>
                        );
                      }

                      // Calendar view for schedules - using same logic as MemberDashboard
                      const next7Days = getNext7Days();
                      
                      return (
                        <div>
                          <div className="flex items-center justify-between mb-6">
                            <h4 className="text-xl font-semibold text-gray-900">
                              {team.team_name} - Schedule for the Next 7 Days
                            </h4>
                            <div className="flex space-x-2">
                              <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                                status.current_schedule?.status === 'published' 
                                  ? 'bg-green-100 text-green-800' 
                                  : 'bg-yellow-100 text-yellow-800'
                              }`}>
                                {status.current_schedule?.status === 'published' ? 'Published' : 'Draft'}
                              </span>
                            </div>
                          </div>

                          {/* 7-Day Calendar Grid - exactly like MemberDashboard */}
                          <div className="grid grid-cols-1 md:grid-cols-7 gap-4">
                            {next7Days.map((date) => {
                              const slots = getSlotsForDate(date, selectedTeamForSchedule);
                              const isToday = date === new Date().toISOString().split('T')[0];
                              
                              return (
                                <div
                                  key={date}
                                  className={`bg-white rounded-lg border-2 p-4 min-h-[200px] ${
                                    isToday ? 'border-purple-400 bg-purple-50' : 'border-gray-200'
                                  }`}
                                >
                                  <div className="text-center mb-3">
                                    <h3 className="font-bold text-gray-900">{formatDate(date)}</h3>
                                    {isToday && (
                                      <span className="text-xs bg-purple-500 text-white px-2 py-1 rounded-full">
                                        Today
                                      </span>
                                    )}
                                  </div>
                                  
                                  <div className="space-y-2">
                                    {slots.length === 0 ? (
                                      <p className="text-gray-400 text-sm text-center py-4">No slots</p>
                                    ) : (
                                      slots.map((slot) => {
                                        const memberName = getMemberName(slot);
                                        
                                        return (
                                          <div
                                            key={slot.id}
                                            className={`p-2 rounded-lg text-xs ${
                                              slot.assigned_member
                                                ? 'bg-green-100 border border-green-300'
                                                : 'bg-gray-100 border border-gray-300'
                                            }`}
                                          >
                                            <div className="font-medium text-gray-900">
                                              {formatTime(slot.start_datetime)} - {formatTime(slot.end_datetime)}
                                            </div>
                                            <div className="text-gray-600">
                                              {slot.duration_hours}h
                                            </div>
                                            <div className="font-medium text-gray-600">
                                              {memberName}
                                            </div>
                                          </div>
                                        );
                                      })
                                    )}
                                  </div>
                                </div>
                              );
                            })}
                          </div>
                        </div>
                      );
                    })()}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
};

export default ManagerDashboard;
