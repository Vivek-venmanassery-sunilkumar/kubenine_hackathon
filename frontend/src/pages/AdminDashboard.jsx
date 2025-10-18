import React, { useState } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { useNavigate } from 'react-router-dom';
import { logout } from '../store/authSlice';
import authService from '../services/authService';

const AdminDashboard = () => {
  const { user, role } = useSelector((state) => state.auth);
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('organizations');
  const [organizations, setOrganizations] = useState([]);
  const [managers, setManagers] = useState([]);
  const [newOrgName, setNewOrgName] = useState('');
  const [newManagerName, setNewManagerName] = useState('');
  const [newManagerEmail, setNewManagerEmail] = useState('');
  const [selectedOrg, setSelectedOrg] = useState('');

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

  const handleCreateOrganization = (e) => {
    e.preventDefault();
    if (newOrgName.trim()) {
      const newOrg = {
        id: Date.now(),
        name: newOrgName.trim(),
        createdAt: new Date().toISOString()
      };
      setOrganizations([...organizations, newOrg]);
      setNewOrgName('');
    }
  };

  const handleCreateManager = (e) => {
    e.preventDefault();
    if (newManagerName.trim() && newManagerEmail.trim() && selectedOrg) {
      const newManager = {
        id: Date.now(),
        name: newManagerName.trim(),
        email: newManagerEmail.trim(),
        organizationId: selectedOrg,
        organizationName: organizations.find(org => org.id === selectedOrg)?.name || '',
        createdAt: new Date().toISOString()
      };
      setManagers([...managers, newManager]);
      setNewManagerName('');
      setNewManagerEmail('');
      setSelectedOrg('');
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
                <div className="bg-gradient-to-r from-amber-50 to-orange-50 p-6 rounded-xl border border-amber-200">
                  <h3 className="text-xl font-bold text-gray-900 mb-4">Create New Organization</h3>
                  <form onSubmit={handleCreateOrganization} className="flex gap-4">
                    <input
                      type="text"
                      value={newOrgName}
                      onChange={(e) => setNewOrgName(e.target.value)}
                      placeholder="Enter organization name"
                      className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-transparent"
                      required
                    />
                    <button
                      type="submit"
                      className="bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-600 hover:to-orange-600 text-white font-bold py-3 px-6 rounded-lg transition-all duration-200 transform hover:scale-105 shadow-lg"
                    >
                      Create Organization
                    </button>
                  </form>
                </div>

                <div className="bg-white p-6 rounded-xl border border-gray-200">
                  <h3 className="text-xl font-bold text-gray-900 mb-4">Organizations ({organizations.length})</h3>
                  {organizations.length === 0 ? (
                    <p className="text-gray-500 text-center py-8">No organizations created yet</p>
                  ) : (
                    <div className="space-y-3">
                      {organizations.map((org) => (
                        <div key={org.id} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                          <div>
                            <h4 className="font-semibold text-gray-900">{org.name}</h4>
                            <p className="text-sm text-gray-500">Created: {new Date(org.createdAt).toLocaleDateString()}</p>
                          </div>
                          <div className="flex space-x-2">
                            <button className="text-amber-600 hover:text-amber-800 font-medium">Edit</button>
                            <button className="text-red-600 hover:text-red-800 font-medium">Delete</button>
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
                <div className="bg-gradient-to-r from-blue-50 to-indigo-50 p-6 rounded-xl border border-blue-200">
                  <h3 className="text-xl font-bold text-gray-900 mb-4">Create New Manager</h3>
                  <form onSubmit={handleCreateManager} className="space-y-4">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <input
                        type="text"
                        value={newManagerName}
                        onChange={(e) => setNewManagerName(e.target.value)}
                        placeholder="Manager name"
                        className="px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        required
                      />
                      <input
                        type="email"
                        value={newManagerEmail}
                        onChange={(e) => setNewManagerEmail(e.target.value)}
                        placeholder="Manager email"
                        className="px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        required
                      />
                    </div>
                    <div className="flex gap-4">
                      <select
                        value={selectedOrg}
                        onChange={(e) => setSelectedOrg(e.target.value)}
                        className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        required
                      >
                        <option value="">Select Organization</option>
                        {organizations.map((org) => (
                          <option key={org.id} value={org.id}>
                            {org.name}
                          </option>
                        ))}
                      </select>
                      <button
                        type="submit"
                        className="bg-gradient-to-r from-blue-500 to-indigo-500 hover:from-blue-600 hover:to-indigo-600 text-white font-bold py-3 px-6 rounded-lg transition-all duration-200 transform hover:scale-105 shadow-lg"
                      >
                        Create Manager
                      </button>
                    </div>
                  </form>
                </div>

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
                            <p className="text-sm text-amber-600 font-medium">Organization: {manager.organizationName}</p>
                            <p className="text-sm text-gray-500">Created: {new Date(manager.createdAt).toLocaleDateString()}</p>
                          </div>
                          <div className="flex space-x-2">
                            <button className="text-blue-600 hover:text-blue-800 font-medium">Edit</button>
                            <button className="text-red-600 hover:text-red-800 font-medium">Delete</button>
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
