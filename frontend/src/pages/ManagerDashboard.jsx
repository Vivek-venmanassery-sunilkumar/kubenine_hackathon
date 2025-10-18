import React, { useState, useEffect } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';
import { logout } from '../store/authSlice';
import authService from '../services/authService';
import managerService from '../services/managerService';

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

  // Load data on component mount
  useEffect(() => {
    const loadAllData = async () => {
      await loadTeams();
      await loadInvitations();
      await loadTeamMembers();
    };
    loadAllData();
  }, []);

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
      } catch (error) {
        console.error('Error creating team:', error);
        toast.error('Failed to create team: ' + (error.response?.data?.detail || error.message));
      } finally {
        setLoading(false);
      }
    }
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
        toast.error('Failed to send invitation: ' + (error.response?.data?.detail || error.message));
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
            </div>


            {/* Tab Content */}
            {activeTab === 'teams' && (
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
                                <button className="text-blue-600 hover:text-blue-800 font-medium text-sm">Edit</button>
                                <button className="text-red-600 hover:text-red-800 font-medium text-sm">Delete</button>
                              </div>
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

            {activeTab === 'invitations' && (
              <div className="space-y-6">
                <div className="bg-gradient-to-r from-green-50 to-emerald-50 p-6 rounded-xl border border-green-200">
                  <h3 className="text-xl font-bold text-gray-900 mb-4">Invite New Member</h3>
                  <form onSubmit={handleInviteMember} className="space-y-4">
                    <div className="flex gap-4">
                      <input
                        type="email"
                        value={inviteEmail}
                        onChange={(e) => setInviteEmail(e.target.value)}
                        placeholder="Enter member email address"
                        className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                        required
                        disabled={loading}
                      />
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
                        disabled={loading || !inviteEmail.trim() || !selectedTeam}
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
          </div>
        </div>
      </main>
    </div>
  );
};

export default ManagerDashboard;
