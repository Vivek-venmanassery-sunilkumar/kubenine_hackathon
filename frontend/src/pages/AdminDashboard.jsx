import React, { useState, useEffect } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';
import { logout } from '../store/authSlice';
import authService from '../services/authService';
import adminService from '../services/adminService';

const AdminDashboard = () => {
  const { user, role } = useSelector((state) => state.auth);
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('organizations');
  const [organizations, setOrganizations] = useState([]);
  const [managers, setManagers] = useState([]);
  const [availableManagers, setAvailableManagers] = useState([]);
  const [newOrgName, setNewOrgName] = useState('');
  const [selectedManager, setSelectedManager] = useState('');
  const [newManagerName, setNewManagerName] = useState('');
  const [newManagerEmail, setNewManagerEmail] = useState('');
  const [newManagerPassword, setNewManagerPassword] = useState('');
  const [editingManager, setEditingManager] = useState(null);
  const [editManagerName, setEditManagerName] = useState('');
  const [editManagerEmail, setEditManagerEmail] = useState('');
  const [editManagerPassword, setEditManagerPassword] = useState('');
  const [editingOrganization, setEditingOrganization] = useState(null);
  const [editOrgName, setEditOrgName] = useState('');
  const [editSelectedManager, setEditSelectedManager] = useState('');
  const [loading, setLoading] = useState(false);

  // Load data on component mount
  useEffect(() => {
    loadOrganizations();
    loadManagers();
    loadAvailableManagers();
  }, []);

  const loadOrganizations = async () => {
    try {
      const response = await adminService.organizations.getAll();
      setOrganizations(response.data);
    } catch (error) {
      console.error('Error loading organizations:', error);
      toast.error('Failed to load organizations');
    }
  };

  const loadManagers = async () => {
    try {
      const response = await adminService.managers.getAll();
      setManagers(response.data);
    } catch (error) {
      console.error('Error loading managers:', error);
      toast.error('Failed to load managers');
    }
  };

  const loadAvailableManagers = async () => {
    try {
      const response = await adminService.managers.getAvailable();
      setAvailableManagers(response.data.managers || []);
    } catch (error) {
      console.error('Error loading available managers:', error);
      toast.error('Failed to load available managers');
    }
  };

  const handleLogout = async () => {
    try {
      await authService.logout();
      dispatch(logout());
      navigate('/');
    } catch (error) {
      console.error('Logout error:', error);
      dispatch(logout()); // Logout locally even if server request fails
      navigate('/');
    }
  };

  const handleCreateOrganization = async (e) => {
    e.preventDefault();
    if (newOrgName.trim() && selectedManager) {
      setLoading(true);
      try {
        const response = await adminService.organizations.create({
          org_name: newOrgName.trim(),
          manager_id: parseInt(selectedManager)
        });
        setOrganizations([...organizations, response.data]);
        setNewOrgName('');
        setSelectedManager('');
        loadAvailableManagers(); // Refresh available managers
        toast.success('Organization created successfully!');
      } catch (error) {
        console.error('Error creating organization:', error);
        toast.error('Failed to create organization: ' + (error.response?.data?.detail || error.message));
      } finally {
        setLoading(false);
      }
    }
  };

  const handleCreateManager = async (e) => {
    e.preventDefault();
    if (newManagerName.trim() && newManagerEmail.trim() && newManagerPassword.trim()) {
      setLoading(true);
      try {
        const response = await adminService.managers.register({
          name: newManagerName.trim(),
          email: newManagerEmail.trim(),
          password: newManagerPassword.trim()
        });
        setManagers([...managers, response.data]);
        setNewManagerName('');
        setNewManagerEmail('');
        setNewManagerPassword('');
        toast.success('Manager created successfully!');
      } catch (error) {
        console.error('Error creating manager:', error);
        toast.error('Failed to create manager: ' + (error.response?.data?.detail || error.message));
      } finally {
        setLoading(false);
      }
    }
  };

  const handleEditManager = (manager) => {
    setEditingManager(manager);
    setEditManagerName(manager.name || '');
    setEditManagerEmail(manager.email || '');
    setEditManagerPassword(''); // Don't pre-fill password for security
  };

  const handleCancelEdit = () => {
    setEditingManager(null);
    setEditManagerName('');
    setEditManagerEmail('');
    setEditManagerPassword('');
  };

  const handleUpdateManager = async (e) => {
    e.preventDefault();
    if (editingManager && editManagerName.trim() && editManagerEmail.trim()) {
      setLoading(true);
      try {
        const updateData = {
          name: editManagerName.trim(),
          email: editManagerEmail.trim()
        };
        
        // Only include password if it's provided
        if (editManagerPassword.trim()) {
          updateData.password = editManagerPassword.trim();
        }

        const response = await adminService.managers.update(editingManager.id, updateData);
        
        // Update the managers list
        setManagers(managers.map(manager => 
          manager.id === editingManager.id ? response.data : manager
        ));
        
        // Reset form
        handleCancelEdit();
        toast.success('Manager updated successfully!');
      } catch (error) {
        console.error('Error updating manager:', error);
        toast.error('Failed to update manager: ' + (error.response?.data?.detail || error.message));
      } finally {
        setLoading(false);
      }
    }
  };

  const handleEditOrganization = (organization) => {
    setEditingOrganization(organization);
    setEditOrgName(organization.org_name || '');
    setEditSelectedManager(organization.manager_id ? organization.manager_id.toString() : '');
  };

  const handleCancelEditOrganization = () => {
    setEditingOrganization(null);
    setEditOrgName('');
    setEditSelectedManager('');
  };

  const handleUpdateOrganization = async (e) => {
    e.preventDefault();
    if (editingOrganization && editOrgName.trim() && editSelectedManager) {
      setLoading(true);
      try {
        const updateData = {
          org_name: editOrgName.trim(),
          manager_id: parseInt(editSelectedManager)
        };

        const response = await adminService.organizations.update(editingOrganization.id, updateData);
        
        // Update the organizations list
        setOrganizations(organizations.map(org => 
          org.id === editingOrganization.id ? response.data : org
        ));
        
        // Reset form
        handleCancelEditOrganization();
        loadAvailableManagers(); // Refresh available managers
        toast.success('Organization updated successfully!');
      } catch (error) {
        console.error('Error updating organization:', error);
        toast.error('Failed to update organization: ' + (error.response?.data?.detail || error.message));
      } finally {
        setLoading(false);
      }
    }
  };

  return (
    <div className="min-h-screen w-screen overflow-x-hidden bg-gradient-to-br from-amber-50 via-stone-100 to-neutral-200">
      {/* Header */}
      <header className="bg-white/90 backdrop-blur-sm shadow-lg">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div>
              <h1 className="text-4xl font-bold text-gray-900">Admin Dashboard</h1>
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
                OnCall Scheduler Admin Panel
              </h2>
              <p className="text-lg text-gray-700 mb-2">
                Manage organizations and managers
              </p>
              <p className="text-sm text-gray-600">
                Complete administrative control over your on-call scheduling system
              </p>
            </div>
            
            {/* Tab Navigation */}
            <div className="flex space-x-1 mb-8 bg-gray-100 p-1 rounded-xl">
              <button
                onClick={() => setActiveTab('organizations')}
                className={`flex-1 py-3 px-6 rounded-lg font-medium transition-all duration-200 ${
                  activeTab === 'organizations'
                    ? 'bg-white text-amber-600 shadow-md'
                    : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
                }`}
              >
                <div className="flex items-center justify-center space-x-2">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                  </svg>
                  <span>Manage Organizations</span>
                </div>
              </button>
              <button
                onClick={() => setActiveTab('managers')}
                className={`flex-1 py-3 px-6 rounded-lg font-medium transition-all duration-200 ${
                  activeTab === 'managers'
                    ? 'bg-white text-amber-600 shadow-md'
                    : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
                }`}
              >
                <div className="flex items-center justify-center space-x-2">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5-9a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0z" />
                  </svg>
                  <span>Manage Managers</span>
                </div>
              </button>
            </div>


            {/* Tab Content */}
            {activeTab === 'organizations' && (
              <div className="space-y-6">
                {/* Create New Organization Form */}
                {!editingOrganization && (
                  <div className="bg-gradient-to-r from-amber-50 to-orange-50 p-6 rounded-xl border border-amber-200">
                    <h3 className="text-xl font-bold text-gray-900 mb-4">Create New Organization</h3>
                    <form onSubmit={handleCreateOrganization} className="space-y-4">
                      <div className="flex gap-4">
                        <input
                          type="text"
                          value={newOrgName}
                          onChange={(e) => setNewOrgName(e.target.value)}
                          placeholder="Enter organization name"
                          className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-transparent"
                          required
                          disabled={loading}
                        />
                        <select
                          value={selectedManager}
                          onChange={(e) => setSelectedManager(e.target.value)}
                          className="px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-transparent min-w-[200px]"
                          required
                          disabled={loading || availableManagers.length === 0}
                        >
                          <option value="">Select Manager</option>
                          {availableManagers.length === 0 ? (
                            <option value="" disabled>No available managers</option>
                          ) : (
                            availableManagers.map((manager) => (
                              <option key={manager.id} value={manager.id}>
                                {manager.name} ({manager.email})
                              </option>
                            ))
                          )}
                        </select>
                      </div>
                      {availableManagers.length === 0 && (
                        <div className="text-amber-600 text-sm bg-amber-50 p-3 rounded-lg border border-amber-200">
                          <strong>No available managers:</strong> All managers are already assigned to organizations. 
                          Create a new manager first or reassign an existing manager.
                        </div>
                      )}
                      <div className="flex justify-end">
                        <button
                          type="submit"
                          disabled={loading}
                          className="bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-600 hover:to-orange-600 disabled:from-gray-400 disabled:to-gray-500 text-white font-bold py-3 px-6 rounded-lg transition-all duration-200 transform hover:scale-105 shadow-lg disabled:transform-none"
                        >
                          {loading ? 'Creating...' : 'Create Organization'}
                        </button>
                      </div>
                    </form>
                  </div>
                )}

                {/* Edit Organization Form */}
                {editingOrganization && (
                  <div className="bg-gradient-to-r from-green-50 to-emerald-50 p-6 rounded-xl border border-green-200">
                    <h3 className="text-xl font-bold text-gray-900 mb-4">Edit Organization: {editingOrganization.org_name}</h3>
                    <form onSubmit={handleUpdateOrganization} className="space-y-4">
                      <div className="flex gap-4">
                        <input
                          type="text"
                          value={editOrgName}
                          onChange={(e) => setEditOrgName(e.target.value)}
                          placeholder="Enter organization name"
                          className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                          required
                          disabled={loading}
                        />
                        <select
                          value={editSelectedManager}
                          onChange={(e) => setEditSelectedManager(e.target.value)}
                          className="px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent min-w-[200px]"
                          required
                          disabled={loading}
                        >
                          <option value="">Select Manager</option>
                          {/* Show current manager + available managers */}
                          {editingOrganization && (
                            <option value={editingOrganization.manager_id}>
                              {editingOrganization.manager_name} ({editingOrganization.manager_email}) - Current
                            </option>
                          )}
                          {availableManagers.map((manager) => (
                            <option key={manager.id} value={manager.id}>
                              {manager.name} ({manager.email})
                            </option>
                          ))}
                        </select>
                      </div>
                      <div className="flex justify-end space-x-3">
                        <button
                          type="button"
                          onClick={handleCancelEditOrganization}
                          disabled={loading}
                          className="bg-gray-500 hover:bg-gray-600 disabled:bg-gray-400 text-white font-bold py-3 px-6 rounded-lg transition-all duration-200 transform hover:scale-105 shadow-lg disabled:transform-none"
                        >
                          Cancel
                        </button>
                        <button
                          type="submit"
                          disabled={loading}
                          className="bg-gradient-to-r from-green-500 to-emerald-500 hover:from-green-600 hover:to-emerald-600 disabled:from-gray-400 disabled:to-gray-500 text-white font-bold py-3 px-6 rounded-lg transition-all duration-200 transform hover:scale-105 shadow-lg disabled:transform-none"
                        >
                          {loading ? 'Updating...' : 'Update Organization'}
                        </button>
                      </div>
                    </form>
                  </div>
                )}

                <div className="bg-white p-6 rounded-xl border border-gray-200">
                  <h3 className="text-xl font-bold text-gray-900 mb-4">Organizations ({organizations.length})</h3>
                  {organizations.length === 0 ? (
                    <p className="text-gray-500 text-center py-8">No organizations created yet</p>
                  ) : (
                    <div className="space-y-3">
                      {organizations.map((org) => (
                        <div key={org.id} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                          <div>
                            <h4 className="font-semibold text-gray-900">{org.org_name}</h4>
                            {org.manager_name && (
                              <p className="text-sm text-blue-600 font-medium">Manager: {org.manager_name} ({org.manager_email})</p>
                            )}
                            <p className="text-sm text-gray-500">Created: {new Date(org.created_at).toLocaleDateString()}</p>
                          </div>
                          <div className="flex space-x-2">
                            <button 
                              onClick={() => handleEditOrganization(org)}
                              disabled={loading}
                              className="text-amber-600 hover:text-amber-800 font-medium disabled:text-gray-400 disabled:cursor-not-allowed"
                            >
                              Edit
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            )}

            {activeTab === 'managers' && (
              <div className="space-y-6">
                {/* Create New Manager Form */}
                {!editingManager && (
                  <div className="bg-gradient-to-r from-blue-50 to-indigo-50 p-6 rounded-xl border border-blue-200">
                    <h3 className="text-xl font-bold text-gray-900 mb-4">Create New Manager</h3>
                    <form onSubmit={handleCreateManager} className="space-y-4">
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <input
                          type="text"
                          value={newManagerName}
                          onChange={(e) => setNewManagerName(e.target.value)}
                          placeholder="Manager name"
                          className="px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                          required
                          disabled={loading}
                        />
                        <input
                          type="email"
                          value={newManagerEmail}
                          onChange={(e) => setNewManagerEmail(e.target.value)}
                          placeholder="Manager email"
                          className="px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                          required
                          disabled={loading}
                        />
                        <input
                          type="password"
                          value={newManagerPassword}
                          onChange={(e) => setNewManagerPassword(e.target.value)}
                          placeholder="Manager password (min 8 characters)"
                          className="px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                          required
                          minLength={8}
                          disabled={loading}
                        />
                      </div>
                      <div className="flex justify-end">
                        <button
                          type="submit"
                          disabled={loading}
                          className="bg-gradient-to-r from-blue-500 to-indigo-500 hover:from-blue-600 hover:to-indigo-600 disabled:from-gray-400 disabled:to-gray-500 text-white font-bold py-3 px-6 rounded-lg transition-all duration-200 transform hover:scale-105 shadow-lg disabled:transform-none"
                        >
                          {loading ? 'Creating...' : 'Create Manager'}
                        </button>
                      </div>
                    </form>
                  </div>
                )}

                {/* Edit Manager Form */}
                {editingManager && (
                  <div className="bg-gradient-to-r from-green-50 to-emerald-50 p-6 rounded-xl border border-green-200">
                    <h3 className="text-xl font-bold text-gray-900 mb-4">Edit Manager: {editingManager.name}</h3>
                    <form onSubmit={handleUpdateManager} className="space-y-4">
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <input
                          type="text"
                          value={editManagerName}
                          onChange={(e) => setEditManagerName(e.target.value)}
                          placeholder="Manager name"
                          className="px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                          required
                          disabled={loading}
                        />
                        <input
                          type="email"
                          value={editManagerEmail}
                          onChange={(e) => setEditManagerEmail(e.target.value)}
                          placeholder="Manager email"
                          className="px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                          required
                          disabled={loading}
                        />
                        <input
                          type="password"
                          value={editManagerPassword}
                          onChange={(e) => setEditManagerPassword(e.target.value)}
                          placeholder="New password (leave blank to keep current)"
                          className="px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                          minLength={8}
                          disabled={loading}
                        />
                      </div>
                      <div className="flex justify-end space-x-3">
                        <button
                          type="button"
                          onClick={handleCancelEdit}
                          disabled={loading}
                          className="bg-gray-500 hover:bg-gray-600 disabled:bg-gray-400 text-white font-bold py-3 px-6 rounded-lg transition-all duration-200 transform hover:scale-105 shadow-lg disabled:transform-none"
                        >
                          Cancel
                        </button>
                        <button
                          type="submit"
                          disabled={loading}
                          className="bg-gradient-to-r from-green-500 to-emerald-500 hover:from-green-600 hover:to-emerald-600 disabled:from-gray-400 disabled:to-gray-500 text-white font-bold py-3 px-6 rounded-lg transition-all duration-200 transform hover:scale-105 shadow-lg disabled:transform-none"
                        >
                          {loading ? 'Updating...' : 'Update Manager'}
                        </button>
                      </div>
                    </form>
                  </div>
                )}

                <div className="bg-white p-6 rounded-xl border border-gray-200">
                  <h3 className="text-xl font-bold text-gray-900 mb-4">Managers ({managers.length})</h3>
                  {managers.length === 0 ? (
                    <p className="text-gray-500 text-center py-8">No managers created yet</p>
                  ) : (
                    <div className="space-y-3">
                      {managers.map((manager) => (
                        <div key={manager.id} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                          <div>
                            <h4 className="font-semibold text-gray-900">{manager.name}</h4>
                            <p className="text-sm text-gray-600">{manager.email}</p>
                            <p className="text-sm text-gray-500">Created: {new Date(manager.createdAt).toLocaleDateString()}</p>
                          </div>
                          <div className="flex space-x-2">
                            <button 
                              onClick={() => handleEditManager(manager)}
                              disabled={loading}
                              className="text-blue-600 hover:text-blue-800 font-medium disabled:text-gray-400 disabled:cursor-not-allowed"
                            >
                              Edit
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
};

export default AdminDashboard;
