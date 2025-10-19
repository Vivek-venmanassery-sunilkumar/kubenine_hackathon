import React, { useState, useEffect } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { useNavigate } from 'react-router-dom';
import { logout } from '../store/authSlice';
import authService from '../services/authService';
import memberService from '../services/memberService';
import { getErrorMessage } from '../utils/errorHandler';

const MemberDashboard = () => {
  const { user, role, roles } = useSelector((state) => state.auth);
  const dispatch = useDispatch();
  const navigate = useNavigate();

  // State for schedule data
  const [schedule, setSchedule] = useState({});
  const [mySlots, setMySlots] = useState([]);
  const [teamSchedule, setTeamSchedule] = useState([]);
  const [teamMembers, setTeamMembers] = useState([]);
  const [swapRequests, setSwapRequests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0]);
  const [showSwapModal, setShowSwapModal] = useState(false);
  const [selectedSlot, setSelectedSlot] = useState(null);
  const [availableSlots, setAvailableSlots] = useState([]);

  // Get next 7 days
  const getNext7Days = () => {
    const days = [];
    const today = new Date();
    for (let i = 0; i < 7; i++) {
      const date = new Date(today);
      date.setDate(today.getDate() + i);
      days.push(date.toISOString().split('T')[0]);
    }
    return days;
  };

  const next7Days = getNext7Days();

  // Load schedule data
  const loadScheduleData = async () => {
    try {
      setLoading(true);
      setError(null);

      const [scheduleResponse, mySlotsResponse, teamScheduleResponse, teamMembersResponse, swapRequestsResponse] = await Promise.all([
        memberService.schedule.getMySchedule(),
        memberService.schedule.getMySlots(),
        memberService.schedule.getTeamSchedule(),
        memberService.teamMembers.getAll(),
        memberService.swapRequests.getAll()
      ]);

      // The API response structure has the data directly in the response
      setSchedule(scheduleResponse.schedule || {});
      setMySlots(mySlotsResponse.slots || []);
      setTeamSchedule(teamScheduleResponse.schedules || []);
      setTeamMembers(teamMembersResponse.members || []);
      setSwapRequests(swapRequestsResponse || []);
    } catch (error) {
      console.error('Error loading schedule data:', error);
      setError(getErrorMessage(error));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadScheduleData();
  }, []);

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

  // Handle slot click for swapping
  const handleSlotClick = (slot) => {
    if (slot.can_swap && slot.is_my_slot) {
      setSelectedSlot(slot);
      // Get available slots for swapping (other team members' slots)
      const available = teamSchedule
        .flatMap(schedule => schedule.timeslots || [])
        .filter(ts => 
          ts.assigned_member && 
          ts.assigned_member !== user.id && 
          !ts.is_break &&
          new Date(ts.start_datetime) > new Date()
        );
      setAvailableSlots(available);
      setShowSwapModal(true);
    }
  };

  // Handle swap request creation
  const handleCreateSwapRequest = async (responderSlotId) => {
    try {
      await memberService.swapRequests.create(selectedSlot.id, responderSlotId);
      setShowSwapModal(false);
      setSelectedSlot(null);
      setAvailableSlots([]);
      // Reload schedule data
      await loadScheduleData();
    } catch (error) {
      console.error('Error creating swap request:', error);
      setError(getErrorMessage(error));
    }
  };

  // Handle swap request acceptance
  const handleAcceptSwap = async (swapRequestId) => {
    try {
      await memberService.swapRequests.accept(swapRequestId);
      // Reload schedule data
      await loadScheduleData();
    } catch (error) {
      console.error('Error accepting swap request:', error);
      setError(getErrorMessage(error));
    }
  };

  // Handle swap request rejection
  const handleRejectSwap = async (swapRequestId) => {
    try {
      await memberService.swapRequests.reject(swapRequestId);
      // Reload schedule data
      await loadScheduleData();
    } catch (error) {
      console.error('Error rejecting swap request:', error);
      setError(getErrorMessage(error));
    }
  };

  // Get slots for a specific date
  const getSlotsForDate = (date) => {
    return schedule[date] || [];
  };

  // Get member name for a slot
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
      
      // If assigned_member is just an ID, try to find the member in team members
      if (typeof slot.assigned_member === 'number' && teamMembers && Array.isArray(teamMembers)) {
        const member = teamMembers.find(m => 
          m.member === slot.assigned_member || 
          m.id === slot.assigned_member ||
          m.member_id === slot.assigned_member
        );
        if (member) {
          return member.member_name || member.name || `Member ${slot.assigned_member}`;
        }
      }
      
      // Fallback to member ID
      return `Member ${slot.assigned_member}`;
    }
    return 'Unassigned';
  };

  // Check if a slot belongs to the current user
  const isMySlot = (slot) => {
    return slot.is_my_slot || (slot.assigned_member && slot.assigned_member === user?.id);
  };

  // Format time for display
  const formatTime = (datetime) => {
    return new Date(datetime).toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      hour12: true
    });
  };

  // Format date for display
  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      weekday: 'short',
      month: 'short',
      day: 'numeric'
    });
  };

  return (
    <div className="min-h-screen w-screen overflow-x-hidden bg-gradient-to-br from-amber-50 via-stone-100 to-neutral-200">
      {/* Header */}
      <header className="bg-white/90 backdrop-blur-sm shadow-lg">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div>
              <h1 className="text-4xl font-bold text-gray-900">Member Dashboard</h1>
              <p className="text-lg text-gray-700 mt-1">Welcome back, {user?.name || user?.email}</p>
              <p className="text-sm text-amber-600 font-medium">Role: {role}</p>
              <div className="mt-3 flex gap-3 text-sm">
                <span className={`px-3 py-1 rounded-full ${roles.is_admin ? 'bg-red-100 text-red-800 border border-red-200' : 'bg-gray-100 text-gray-600'}`}>
                  Admin: {roles.is_admin ? 'Yes' : 'No'}
                </span>
                <span className={`px-3 py-1 rounded-full ${roles.is_manager ? 'bg-blue-100 text-blue-800 border border-blue-200' : 'bg-gray-100 text-gray-600'}`}>
                  Manager: {roles.is_manager ? 'Yes' : 'No'}
                </span>
                <span className={`px-3 py-1 rounded-full ${roles.is_member ? 'bg-green-100 text-green-800 border border-green-200' : 'bg-gray-100 text-gray-600'}`}>
                  Member: {roles.is_member ? 'Yes' : 'No'}
                </span>
              </div>
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
                My Schedule - Next 7 Days
              </h2>
              <p className="text-lg text-gray-700 mb-2">
                View your upcoming shifts and manage swap requests
              </p>
              <p className="text-sm text-gray-600">
                Click on your slots to request swaps with team members
              </p>
            </div>

            {/* Error Display */}
            {error && (
              <div className="mb-6 bg-red-50 border border-red-200 rounded-lg p-4">
                <div className="flex items-center">
                  <svg className="w-5 h-5 text-red-400 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <p className="text-red-800">{error}</p>
                </div>
              </div>
            )}

            {/* Loading State */}
            {loading && (
              <div className="flex justify-center items-center py-12">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-amber-500"></div>
              </div>
            )}

            {/* Calendar View */}
            {!loading && (
              <div className="space-y-6">
                {/* 7-Day Calendar Grid */}
                <div className="grid grid-cols-1 md:grid-cols-7 gap-4">
                  {next7Days.map((date) => {
                    const slots = getSlotsForDate(date);
                    const isToday = date === new Date().toISOString().split('T')[0];
                    
                    return (
                      <div
                        key={date}
                        className={`bg-white rounded-lg border-2 p-4 min-h-[200px] ${
                          isToday ? 'border-amber-400 bg-amber-50' : 'border-gray-200'
                        }`}
                      >
                        <div className="text-center mb-3">
                          <h3 className="font-bold text-gray-900">{formatDate(date)}</h3>
                          {isToday && (
                            <span className="text-xs bg-amber-500 text-white px-2 py-1 rounded-full">
                              Today
                            </span>
                          )}
                        </div>
                        
                        <div className="space-y-2">
                          {slots.length === 0 ? (
                            <p className="text-gray-400 text-sm text-center py-4">No slots</p>
                          ) : (
                            slots.map((slot) => {
                              const isMySlotFlag = isMySlot(slot);
                              const memberName = getMemberName(slot);
                              
                              return (
                                <div
                                  key={slot.id}
                                  onClick={() => handleSlotClick(slot)}
                                  className={`p-2 rounded-lg text-xs cursor-pointer transition-all duration-200 ${
                                    isMySlotFlag
                                      ? slot.can_swap
                                        ? 'bg-blue-100 border border-blue-300 hover:bg-blue-200 hover:shadow-md'
                                        : 'bg-blue-200 border border-blue-400'
                                      : 'bg-gray-100 border border-gray-300'
                                  }`}
                                >
                                  <div className="font-medium text-gray-900">
                                    {formatTime(slot.start_datetime)} - {formatTime(slot.end_datetime)}
                                  </div>
                                  <div className="text-gray-600">
                                    {slot.duration_hours}h
                                  </div>
                                  <div className={`font-medium ${
                                    isMySlotFlag ? 'text-blue-700' : 'text-gray-600'
                                  }`}>
                                    {isMySlotFlag ? 'You' : memberName}
                                  </div>
                                  {isMySlotFlag && slot.can_swap && (
                                    <div className="text-blue-600 text-xs">
                                      Click to swap
                                    </div>
                                  )}
                                  {slot.swap_status && (
                                    <div className={`text-xs ${
                                      slot.swap_status.status === 'pending' ? 'text-yellow-600' : 'text-blue-600'
                                    }`}>
                                      {slot.swap_status.status === 'pending' ? 'Swap pending' : 'Swap received'}
                                    </div>
                                  )}
                                </div>
                              );
                            })
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>

                {/* Swap Requests Section */}
                {swapRequests.length > 0 && (
                  <div className="mt-8">
                    <h3 className="text-xl font-bold text-gray-900 mb-4">Swap Requests</h3>
                    <div className="space-y-4">
                      {swapRequests.map((request) => (
                        <div
                          key={request.id}
                          className="bg-white border border-gray-200 rounded-lg p-4"
                        >
                          <div className="flex justify-between items-start">
                            <div>
                              <p className="font-medium text-gray-900">
                                {request.requester_name || 'Unknown'} wants to swap with {request.responder_name || 'Unknown'}
                              </p>
                              <p className="text-sm text-gray-600">
                                Status: <span className={`font-medium ${
                                  request.status === 'pending' ? 'text-yellow-600' :
                                  request.status === 'accepted' ? 'text-green-600' :
                                  request.status === 'rejected' ? 'text-red-600' : 'text-gray-600'
                                }`}>
                                  {request.status}
                                </span>
                              </p>
                              <p className="text-xs text-gray-500">
                                Requested: {new Date(request.request_date).toLocaleString()}
                              </p>
                            </div>
                            
                            {request.status === 'pending' && request.responder === user.id && (
                              <div className="flex space-x-2">
                                <button
                                  onClick={() => handleAcceptSwap(request.id)}
                                  className="bg-green-500 hover:bg-green-600 text-white px-3 py-1 rounded text-sm"
                                >
                                  Accept
                                </button>
                                <button
                                  onClick={() => handleRejectSwap(request.id)}
                                  className="bg-red-500 hover:bg-red-600 text-white px-3 py-1 rounded text-sm"
                                >
                                  Reject
                                </button>
                              </div>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </main>

      {/* Swap Modal */}
      {showSwapModal && selectedSlot && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-bold text-gray-900 mb-4">
              Request Swap for {formatTime(selectedSlot.start_datetime)} - {formatTime(selectedSlot.end_datetime)}
            </h3>
            
            <div className="space-y-3 mb-6">
              <p className="text-sm text-gray-600">Select a slot to swap with:</p>
              {availableSlots.length === 0 ? (
                <p className="text-gray-400 text-sm">No available slots for swapping</p>
              ) : (
                availableSlots.map((slot) => (
                  <button
                    key={slot.id}
                    onClick={() => handleCreateSwapRequest(slot.id)}
                    className="w-full text-left p-3 bg-gray-50 hover:bg-gray-100 rounded-lg border border-gray-200"
                  >
                    <div className="font-medium text-gray-900">
                      {formatTime(slot.start_datetime)} - {formatTime(slot.end_datetime)}
                    </div>
                    <div className="text-sm text-gray-600">
                      {slot.duration_hours}h with {getMemberName(slot)}
                    </div>
                  </button>
                ))
              )}
            </div>
            
            <div className="flex justify-end space-x-3">
              <button
                onClick={() => setShowSwapModal(false)}
                className="px-4 py-2 text-gray-600 hover:text-gray-800"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default MemberDashboard;
